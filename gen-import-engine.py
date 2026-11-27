#!/usr/bin/env python3
"""Proof-of-concept model-feed import engine.

This is the feed entry point. generate.py is the other one and is not imported
here. Loading this module does not write files.

parse_feed reads one model-feed file into a target-independent model. main
then dispatches:

  pluralbridge   gen-pluralbridge.py
  simplyplural   gen-simplyplural.py
  pluralport     gen-pluralport.py
  pluralkit      gen-pluralkit.py
  lighthouse     not implemented; prints a message and returns 2

The model keeps one record per shared member. A named member uses the key
("named", name), so the same name in several anchors is one person with
several placements. A range such as Member: 1-50 uses
("range", anchor key, declaration line, number), so that span belongs to the
anchor where it was written. Notes, fields, buckets, friends, and custom
fronts are resolved by script id after the file is read.

Avatar settings start at the built-in default (64 by 64, style none), then
Config, then enclosing anchors from the outside inward, then an explicit
member block. A member-block value applies to every placement of that person.
A later placement that omits the attribute does not clear it. Disagreeing
explicit values, or disagreeing inherited values when the member never sets
the attribute, are FeedError.

After a target assigns member["json_id"], _avatar_pngs calls gen-avatars.py.
PluralBridge, Simply Plural, and PluralKit do that, then ask the adapter to
write. PluralPort builds avatar bytes inside its own renderer and does not
call _avatar_pngs. Output paths are selected by this engine's target runners.
The adapters receive those paths and write and package the output. This
module prints a target exception and returns 1 when the runner catches one.
It does not itself restore or delete a file the adapter has already replaced.

Accepted syntax is documented in templates/model-feed-usage.md.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path


class FeedError(Exception):
    """The feed text or an avatar request cannot be used.

    main prints the message and returns 1. The exception does not roll back
    a file an adapter has already replaced. Parse failures happen before the
    runner calls write.
    """


# HEADER_RE requires a colon after the keyword. Bare catalog names such as
# Notes are matched separately, before this pattern. Blank lines are dropped
# before matching, so indentation does not create scope.
HEADER_RE = re.compile(
    r"^(Account|Permission|Visibility|Place|System|Group|Member|Notes|CustomFields|"
    r"PrivacyBuckets|Friends|CustomFronts|Note|Field|Bucket|Friend|CustomFront|"
    r"name|email|visibility|permission|field|note|front|archivedReason|archived|"
    r"bucket|description|trusted|avatar-width|avatar-height|avatar|color)\s*:\s*(.*)$"
)
# Optional account-level catalogs. A feed may omit any of them.
ACCOUNT_BLOCKS = ("Notes", "CustomFields", "PrivacyBuckets", "Friends", "CustomFronts")
# Order used when a scope's explicit avatar keys are copied into JSON config.
AVATAR_ATTRS = ("avatar-width", "avatar-height", "avatar", "color")
AVATAR_STYLES = ("none", "solid", "crosshatch")
# Color has no built-in default. Absence means "derive or leave null" at the adapter.
AVATAR_DEFAULTS = {"avatar-width": 64, "avatar-height": 64, "avatar": "none"}
PERMISSION_TYPES = ("read", "write", "create", "delete", "inherit", "all")
VISIBILITY_TYPES = ("only you", "trusted friends", "all friends", "selected people", "inherit")
RELATION_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*->\s*(.*)$")
SCRIPT_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
RANGE_RE = re.compile(r"^(\d+)-(\d+)$")
ANCHOR_KINDS = {"Place": "place", "System": "system", "Group": "group"}


def _load_sibling(filename, module_name):
    """Load a hyphen-named module beside this file.

    The loaded module's import must not write or generate. Callers invoke
    render and write after this returns. A missing file or an import error
    propagates as the loader's exception, not as FeedError.
    """
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Parser:
    """One feed file. Brackets are scope. Indentation is ignored.

    Raises FeedError with path and line. Callers that catch a target error
    must not write. parse_feed lets FeedError reach main, which prints it
    and returns 1 before dispatch.
    """
    def __init__(self, path, text):
        """Keep parser state. Records are filled during the scan and finished in _resolve.

        Identity, in three layers:

        - Internal key: how this parser tells records apart before any target
          runs. An anchor key is "script:<script id>" when the feed gave one,
          otherwise "gen:<kind>:<n>" from generated_ordinal. A named member key
          is ("named", name). A range member key is
          ("range", anchor key, declaration line, number).
        - Script id: the token the feed author wrote (anchor1, id1, bucket1).
          It is not an internal key and not a target id. Anchors may omit it.
        - json_id: absent here. The selected adapter assigns it on each member
          before _avatar_pngs, when that runner calls _avatar_pngs.

        A tuple of (value, source line) means the feed set that value at that
        line. None means the feed did not set it. That is not the same as an
        explicit false, an empty list, or a target's inherit object. Lists of
        (script id, line) are unresolved references. _resolve turns the ones
        that are ids-only into plain script-id strings and drops later duplicates.

        self.lines is (source line number, stripped text) for non-blank lines.
        self.index is the next line to read. Blank lines are not stored, so
        they cannot open or close a block.
        """
        self.path = str(path)
        self.lines = []
        for number, raw in enumerate(text.splitlines(), 1):
            stripped = raw.strip()
            if stripped:
                self.lines.append((number, stripped))
        self.index = 0
        # Declaration order. See _anchor for the record shape.
        self.anchors = []
        # One dict per shared member, first-seen order. See _new_member.
        self.members = []
        self.member_by_key = {}
        # One dict per placement. See _add_occurrence.
        self.occurrences = []
        # (anchor key, member key). A second placement in the same anchor is an error.
        self.occurrence_keys = set()
        self.notes = []
        self.fields = []
        self.buckets = []
        self.friends = []
        self.custom_fronts = []
        # target_key stays None until _resolve, including an intentionally empty target.
        self.relationships = []
        # None until the Account block sets them. Name and email are required
        # at the end of parse. Permission and visibility may stay None.
        self.account_name = None
        self.account_email = None
        self.account_permission = None
        self.account_visibility = None
        # keyword -> (value, source line) for the optional Config block.
        self.config_avatar = {}
        # Strings printed later as "notice:". "self" is recorded here and kept.
        self.notices = []
        self.anchor_script_ids = {}
        self.anchor_names = {}
        self.note_ids = set()
        self.field_ids = set()
        # Next generated anchor key uses the incremented count, so the first is 1.
        self.generated_ordinal = {"place": 0, "system": 0, "group": 0}
        # (relationship dict, target name, target script id or None, source line).
        self.unresolved = []

    def error(self, line, message):
        """Raise FeedError already prefixed with path and source line."""
        raise FeedError(f"{self.path}:{line}: {message}")

    def peek(self):
        """The next stored line as (number, text), or None at the end. Does not advance."""
        if self.index >= len(self.lines):
            return None
        return self.lines[self.index]

    def pop(self):
        """Return the next stored line and advance. End of file is FeedError."""
        item = self.peek()
        if item is None:
            raise FeedError(f"{self.path}: unexpected end of file")
        self.index += 1
        return item

    def parse(self):
        """Read optional Config, then one required Account, then resolve references.

        Config and Account are the only top-level blocks. Name and email are
        required. Permission, Visibility, anchors, and the catalog blocks are
        optional. Text after the Account block is an error. References are
        checked only after the whole Account is stored, so a Notes block may
        follow the members that cite it.
        """
        if not self.lines:
            raise FeedError(f"{self.path}:1: file is empty")
        number, text = self.pop()
        if text == "Config":
            self._parse_config(number)
            item = self.peek()
            if item is None or item[1] != "Account":
                self.error(item[0] if item else number, "Config must be followed by one Account block")
            number, text = self.pop()
        elif text != "Account":
            self.error(number, "file must begin with Config or one Account block")
        self._expect_open(number)
        self._parse_body("account", None)
        extra = self.peek()
        if extra is not None:
            self.error(extra[0], "text after the Account block")
        self._resolve()
        if self.account_name is None:
            self.error(1, "account name is required")
        if self.account_email is None:
            self.error(1, "account email is required")
        return self._model()

    def _expect_open(self, header_line):
        """Consume the '[' that must follow a header. The error cites the header line."""
        item = self.peek()
        if item is None or item[1] != "[":
            self.error(header_line, "expected '[' to open this block")
        self.pop()

    def _parse_body(self, scope, owner):
        """Read statements until the matching ']'. This method consumes that ']'.

        scope is "account" or "anchor". owner is None for the Account, otherwise
        the anchor dict whose body is open. A nested anchor or member consumes
        its own bracket pair before this loop sees the next statement. A '['
        that is not introduced by such a header is an error.
        """
        while True:
            item = self.peek()
            if item is None:
                self.error(owner["line"] if owner else 1, "unclosed '['")
            number, text = item
            if text == "]":
                self.pop()
                return
            if text == "[":
                self.error(number, "unexpected '['")
            self.pop()
            self._statement(scope, owner, number, text)

    def _statement(self, scope, owner, number, text):
        """Dispatch one line already removed from the cursor.

        Catalog names are bare words. Other statements match HEADER_RE.
        "Label -> target" is a relationship and is legal only in an anchor.
        The line itself is not a bracket; brackets are handled by the reader
        that opened the block or by _anchor, _member, _friend_definition, and
        _custom_front_definition when they see a following '['.
        """
        if text in ACCOUNT_BLOCKS:
            self._definition_block(scope, number, text)
            return
        header = HEADER_RE.match(text)
        if header:
            keyword, rest = header.group(1), header.group(2).strip()
            self._header(scope, owner, number, keyword, rest)
            return
        relation = RELATION_RE.match(text)
        if relation and scope == "anchor":
            self._relationship(owner, number, relation.group(1), relation.group(2).strip())
            return
        self.error(number, f"unrecognized statement {text!r}")

    def _definition_block(self, scope, number, keyword):
        """Read one account catalog and consume its closing ']'.

        Notes and CustomFields are flat quoted rows. Buckets, friends, and
        custom fronts go through _catalog_block because a friend or custom
        front may have its own optional body. These blocks are legal only
        directly inside Account.
        """
        if scope != "account":
            self.error(number, f"{keyword} is only allowed in the Account block")
        self._expect_open(number)
        if keyword == "PrivacyBuckets":
            self._catalog_block(number, "Bucket", self._bucket_definition)
            return
        if keyword == "Friends":
            self._catalog_block(number, "Friend", self._friend_definition)
            return
        if keyword == "CustomFronts":
            self._catalog_block(number, "CustomFront", self._custom_front_definition)
            return
        kind = "note" if keyword == "Notes" else "field"
        while True:
            item = self.peek()
            if item is None:
                self.error(number, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return
            self.pop()
            header = HEADER_RE.match(text)
            if not header:
                self.error(line, f"expected a {keyword} entry")
            name, rest = header.group(1), header.group(2).strip()
            expected = "Note" if kind == "note" else "Field"
            if name != expected:
                self.error(line, f"expected {expected}")
            self._quoted_definition(kind, line, rest)

    def _quoted_definition(self, kind, line, rest):
        """Store one Note or Field. The quoted text may contain a curly apostrophe.

        kind "note" appends {script_id, body, line}. kind "field" appends
        {script_id, label, line}. The pattern is anchored at both ends.
        A repeated script id in that catalog is an error.
        """
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s+'([^']*)'$", rest)
        if not match:
            self.error(line, "expected script id and single-quoted text")
        script_id, body = match.group(1), match.group(2)
        if kind == "note":
            if script_id in self.note_ids:
                self.error(line, f"note {script_id!r} is already defined")
            self.note_ids.add(script_id)
            self.notes.append({"script_id": script_id, "body": body, "line": line})
        else:
            if script_id in self.field_ids:
                self.error(line, f"custom field {script_id!r} is already defined")
            self.field_ids.add(script_id)
            self.fields.append({"script_id": script_id, "label": body, "line": line})

    def _header(self, scope, owner, number, keyword, rest):
        """Apply one keyword statement. scope and owner are the open block.

        Account identity and account Permission/Visibility are only legal in
        the Account. Avatar attributes in an anchor update that anchor's
        avatar dict. Place, System, and Group call _anchor, which may recurse
        into a body. Member is only legal in an anchor and is read by _member,
        including its optional bracket.

        The scope == "member" branch is not reached. No reader calls
        _parse_body with that scope. Member settings are read by _member_bag.
        The branch calls _member_setting, which is not defined.

        An anchor field line appends (script id, line) and, when a quoted value
        is present, (script id, value, line). Those values are not deduplicated
        here. An anchor note line appends (script id, line) to that anchor's
        note_refs. It does not touch any member. Anchor visibility and
        permission store the raw rest string in a (value, line) tuple. They
        are not checked against VISIBILITY_TYPES or PERMISSION_TYPES, and
        anchor "self" does not append a notice.
        """
        if keyword == "Account":
            self.error(number, "only one Account block is allowed")
        if keyword in ("name", "email") and scope == "account":
            self._account_identity(keyword, number, rest)
            return
        if keyword in AVATAR_ATTRS:
            if scope == "account":
                self.error(number, f"{keyword} belongs in a Config block, not the Account block")
            if scope != "anchor":
                self.error(number, f"{keyword} is not allowed in this scope")
            self._set_avatar(owner["avatar"], keyword, number, self._avatar_value(keyword, number, rest))
            return
        if keyword in ("Permission", "Visibility") and scope == "account":
            self._account_setting(keyword, number, rest)
            return
        if keyword in ANCHOR_KINDS:
            if scope not in ("account", "anchor"):
                self.error(number, f"{keyword} is not allowed in this scope")
            self._anchor(ANCHOR_KINDS[keyword], owner, number, rest)
            return
        if keyword == "Member":
            if scope != "anchor":
                self.error(number, "Member is only allowed inside Place, System, or Group")
            self._member(owner, number, rest)
            return
        if scope == "member" and keyword in ("visibility", "permission", "field", "note", "front"):
            self._member_setting(owner, number, keyword, rest)
            return
        if scope == "anchor" and keyword == "field":
            script_id, value = self._field_ref(number, rest)
            self._add_ref(owner["field_refs"], number, script_id, "field")
            if value is not None:
                owner["field_values"].append((script_id, value, number))
            return
        if scope == "anchor" and keyword == "note":
            self._add_ref(owner["note_refs"], number, rest, "note")
            return
        if scope == "anchor" and keyword in ("visibility", "permission"):
            self._anchor_setting(owner, number, keyword, rest)
            return
        self.error(number, f"{keyword} is not allowed in this scope")

    def _account_identity(self, keyword, line, rest):
        """Set account name or email once. A second assignment is an error. Empty rest is an error."""
        if not rest:
            self.error(line, f"account {keyword} requires a value")
        if keyword == "name":
            if self.account_name is not None:
                self.error(line, "account name is already set")
            self.account_name = rest
        else:
            if self.account_email is not None:
                self.error(line, "account email is already set")
            self.account_email = rest

    def _permission_types(self, line, rest):
        """Comma-separated permission types. `all` and `inherit` stay as written."""
        parts = [part.strip() for part in rest.split(",")]
        if not rest or any(not part for part in parts):
            self.error(line, "permission requires one or more types")
        for part in parts:
            if part not in PERMISSION_TYPES:
                self.error(line, f"unknown permission type {part!r}")
        return parts

    def _visibility_value(self, line, rest):
        """Return the visibility token unchanged.

        "self" is accepted and recorded in notices. It is not rewritten to
        "only you". Any other token must be in VISIBILITY_TYPES.
        """
        if not rest:
            self.error(line, "visibility requires a value")
        if rest == "self":
            self.notices.append(
                f"{self.path}:{line}: visibility 'self' is kept as written. "
                "docs/visibility-permissions-roles.txt names this audience 'only you'. "
                "The token was not renamed."
            )
            return rest
        if rest not in VISIBILITY_TYPES:
            self.error(line, f"unknown visibility {rest!r}")
        return rest

    def _account_setting(self, keyword, line, rest):
        """Set account permission (list of types) or visibility (one token), once each.

        None remains None when the Account omits the setting. Adapters decide
        what an omitted setting means. This method does not invent inherit.
        """
        if keyword == "Permission":
            values = self._permission_types(line, rest)
            if self.account_permission is not None:
                self.error(line, "Account Permission is already set")
            self.account_permission = values
        else:
            value = self._visibility_value(line, rest)
            if self.account_visibility is not None:
                self.error(line, "Account Visibility is already set")
            self.account_visibility = value

    def _anchor(self, kind, owner, line, rest):
        """Append one anchor and, when the next line is '[', parse its body.

        The opening '[' is consumed here. _parse_body consumes the closing ']'.
        A missing bracket is legal: the anchor then has no children.

        The record is:
        key, kind ("place", "system", or "group"), name, script_id or None,
        line, parent_key or None for a top-level anchor, field_refs [],
        field_values [], note_refs [], permission None, visibility None,
        avatar {}. note_refs holds (script id, line) until _resolve replaces
        it with script ids. Those ids stay on the anchor and are not copied
        onto members. _resolve_avatars later adds avatar_config.

        Names are unique across all anchors. Script ids are unique across
        anchors that have one. A name without a valid :scriptId keeps script_id
        None and uses the next generated key for that kind.
        """
        if not rest:
            self.error(line, "anchor requires a name")
        name, script_id = self._split_name_id(line, rest)
        if script_id is not None:
            if script_id in self.anchor_script_ids:
                previous = self.anchor_script_ids[script_id]
                self.error(line, f"script id {script_id!r} is already used on line {previous['line']}")
            key = f"script:{script_id}"
        else:
            self.generated_ordinal[kind] += 1
            key = f"gen:{kind}:{self.generated_ordinal[kind]}"
        if name in self.anchor_names:
            previous = self.anchor_names[name]
            self.error(line, f"anchor name {name!r} is already used on line {previous['line']}")
        anchor = {
            "key": key,
            "kind": kind,
            "name": name,
            "script_id": script_id,
            "line": line,
            "parent_key": None if owner is None else owner["key"],
            "field_refs": [],
            "field_values": [],
            "note_refs": [],
            "permission": None,
            "visibility": None,
            "avatar": {},
        }
        self.anchors.append(anchor)
        self.anchor_names[name] = anchor
        if script_id is not None:
            self.anchor_script_ids[script_id] = anchor
        if self.peek() is not None and self.peek()[1] == "[":
            self.pop()
            self._parse_body("anchor", anchor)

    def _split_name_id(self, line, text):
        """Return (name, script id) or (whole text, None).

        The script id is the text after the last colon when that token matches
        SCRIPT_ID_RE. Otherwise the colon is part of the name. An empty name
        before a valid script id is an error.
        """
        if ":" not in text:
            return text.strip(), None
        name, script_id = text.rsplit(":", 1)
        name = name.strip()
        script_id = script_id.strip()
        if not name:
            self.error(line, "missing name before script id")
        if SCRIPT_ID_RE.match(script_id):
            return name, script_id
        return text.strip(), None

    def _member(self, anchor, line, rest):
        """Add one placement per named member, or one member and placement per range number.

        A following '[' is optional. When present, this method consumes it and
        _member_bag consumes the ']'. The same bag is applied to every member
        created by this line, so a range shares one block of settings.

        A named member's key is ("named", name). The second sighting reuses
        that record. A range key is ("range", this anchor's key, this line,
        number), so the same numbers on another line are different members.
        ":" in a member name is rejected. This proof of concept has no member
        script ids.
        """
        if not rest:
            self.error(line, "Member requires a name or a range")
        if ":" in rest:
            self.error(line, "member script ids are not part of this proof of concept")
        created = []
        range_match = RANGE_RE.match(rest)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if start < 1 or end < start:
                self.error(line, "member range must be a positive inclusive span such as 1-250")
            for number in range(start, end + 1):
                # The range belongs to this anchor and this source line. The same
                # numbers written on another anchor are different people.
                key = ("range", anchor["key"], line, number)
                member = self._new_member(key, line, generated=True, anchor_key=anchor["key"], number=number)
                created.append(member)
                self._add_occurrence(anchor, member, line)
        else:
            # The name is the shared identity. A later Member line with the same
            # name adds a placement and does not create a second person.
            key = ("named", rest)
            member = self.member_by_key.get(key)
            if member is None:
                member = self._new_member(key, line, generated=False, name=rest)
            created.append(member)
            self._add_occurrence(anchor, member, line)
        if self.peek() is not None and self.peek()[1] == "[":
            self.pop()
            bag = self._member_bag(line)
            for member in created:
                self._apply_bag(member, anchor, bag)

    def _new_member(self, key, line, generated, name=None, anchor_key=None, number=None):
        """Append a shared member and index it by key.

        generated is True only for a range. name is None for a range; number
        and anchor_key are None for a named member. fronting, archived,
        archived_reason, and description stay None until a member block sets
        them. buckets, field_refs, field_values, and note_refs start empty.
        line is the first declaration. json_id is not created here.
        """
        member = {
            "key": key,
            "generated": generated,
            "name": name,
            "anchor_key": anchor_key,
            "number": number,
            "line": line,
            "fronting": None,
            "fronting_line": None,
            "archived": None,
            "archived_line": None,
            "archived_reason": None,
            "archived_reason_line": None,
            "description": None,
            "buckets": [],
            "field_refs": [],
            "field_values": [],
            "note_refs": [],
        }
        self.members.append(member)
        self.member_by_key[key] = member
        return member

    def _add_occurrence(self, anchor, member, line):
        """Append one placement. The same member may occur in several anchors.

        The record starts with visibility None, permission None, both line
        fields None, and avatar {}. line is the Member line, not a setting line.
        A second occurrence of the same member in this same anchor is an error.
        """
        token = (anchor["key"], member["key"])
        if token in self.occurrence_keys:
            self.error(line, f"member {member.get('name') or member['number']} is already in this anchor")
        self.occurrence_keys.add(token)
        self.occurrences.append({
            "anchor_key": anchor["key"],
            "member_key": member["key"],
            "visibility": None,
            "permission": None,
            "visibility_line": None,
            "permission_line": None,
            "avatar": {},
            "line": line,
        })

    def _member_bag(self, header_line):
        """Read one member bracket and return the bag. This method consumes ']'.

        Inside one bracket, visibility, permission, front, archived,
        archivedReason, description, and each avatar attribute must agree with
        an earlier line in that same bracket. field, note, and bucket lines
        accumulate. A field value of None means the line named the field and
        did not quote a value.

        The bag is not the member record. _apply_bag copies it onto the shared
        member and this placement.
        """
        bag = {
            "visibility": None, "permission": None, "fields": [], "notes": [],
            "front": None, "avatar": {}, "archived": None, "archived_reason": None,
            "description": None, "buckets": [],
        }
        while True:
            item = self.peek()
            if item is None:
                self.error(header_line, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return bag
            self.pop()
            header = HEADER_RE.match(text)
            if not header:
                self.error(line, f"unrecognized member setting {text!r}")
            keyword, rest = header.group(1), header.group(2).strip()
            if keyword == "visibility":
                self._set_once(bag, "visibility", line, self._visibility_value(line, rest), "visibility")
            elif keyword == "permission":
                self._set_once(bag, "permission", line, self._permission_types(line, rest), "permission")
            elif keyword == "field":
                script_id, value = self._field_ref(line, rest)
                bag["fields"].append((script_id, value, line))
            elif keyword == "note":
                self._add_ref(bag["notes"], line, rest, "note")
            elif keyword == "front":
                if rest not in ("true", "false"):
                    self.error(line, "front must be true or false")
                value = rest == "true"
                if bag["front"] is not None and bag["front"][0] != value:
                    self.error(line, f"front conflicts with line {bag['front'][1]}")
                bag["front"] = (value, line)
            elif keyword in AVATAR_ATTRS:
                self._set_avatar(bag["avatar"], keyword, line, self._avatar_value(keyword, line, rest))
            elif keyword == "archived":
                if rest not in ("true", "false"):
                    self.error(line, "archived must be true or false")
                value = rest == "true"
                if bag["archived"] is not None and bag["archived"][0] != value:
                    self.error(line, f"archived conflicts with line {bag['archived'][1]}")
                bag["archived"] = (value, line)
            elif keyword == "archivedReason":
                text = self._quoted(line, rest, "archivedReason")
                if bag["archived_reason"] is not None and bag["archived_reason"][0] != text:
                    self.error(line, f"archivedReason conflicts with line {bag['archived_reason'][1]}")
                bag["archived_reason"] = (text, line)
            elif keyword == "description":
                text = self._quoted(line, rest, "description")
                if bag["description"] is not None and bag["description"][0] != text:
                    self.error(line, f"description conflicts with line {bag['description'][1]}")
                bag["description"] = (text, line)
            elif keyword == "bucket":
                if not SCRIPT_ID_RE.match(rest):
                    self.error(line, "bucket reference must be a script id")
                bag["buckets"].append((rest, line))
            else:
                self.error(line, f"{keyword} is not allowed inside a Member block")

    def _set_once(self, bag, key, line, rest, label):
        """Store (value, line) when the bag slot is empty or already equal.

        rest for visibility is a string. rest for permission is a list of
        types. A different value in the same bag is an error. Empty rest is
        an error.
        """
        if not rest:
            self.error(line, f"{label} requires a value")
        if bag[key] is not None and bag[key][0] != rest:
            self.error(line, f"{label} conflicts with line {bag[key][1]}")
        bag[key] = (rest, line)

    def _apply_bag(self, member, anchor, bag):
        """Copy one member block onto the shared member and this placement.

        Visibility and permission are placement-specific. A different value on
        another anchor is kept. The conflict checks compare only this occurrence,
        which starts empty, so they fire only if this occurrence already holds
        a different value.

        These member-wide settings must agree when two placements both set them.
        Omitting the setting on a later placement leaves the earlier value:
        fronting, archived, archived_reason, and description.

        These accumulate. A repeated script id is not stored twice and is not
        a conflict: field refs, note refs, and bucket refs. A field value is
        stored once. A later quoted value must equal it. A later field line
        with no quoted value does not clear a value already stored.

        Avatar pairs stay on the occurrence. _resolve_avatars decides whether
        an explicit member value covers every placement.
        """
        occurrence = next(
            row for row in reversed(self.occurrences)
            if row["anchor_key"] == anchor["key"] and row["member_key"] == member["key"]
        )
        if bag["visibility"] is not None:
            value, line = bag["visibility"]
            if occurrence["visibility"] is not None and occurrence["visibility"] != value:
                self.error(line, f"visibility conflicts with line {occurrence['visibility_line']}")
            occurrence["visibility"] = value
            occurrence["visibility_line"] = line
        if bag["permission"] is not None:
            value, line = bag["permission"]
            if occurrence["permission"] is not None and occurrence["permission"] != value:
                self.error(line, f"permission conflicts with line {occurrence['permission_line']}")
            occurrence["permission"] = value
            occurrence["permission_line"] = line
        for script_id, value, line in bag["fields"]:
            if script_id not in [item[0] for item in member["field_refs"]]:
                member["field_refs"].append((script_id, line))
            if value is not None:
                previous = next((item for item in member["field_values"] if item[0] == script_id), None)
                if previous is not None and previous[1] != value:
                    self.error(line, f"field {script_id!r} value conflicts with line {previous[2]}")
                if previous is None:
                    member["field_values"].append((script_id, value, line))
        for script_id, line in bag["buckets"]:
            if script_id not in [item[0] for item in member["buckets"]]:
                member["buckets"].append((script_id, line))
        if bag["archived"] is not None:
            value, line = bag["archived"]
            if member["archived"] is not None and member["archived"] != value:
                self.error(
                    line,
                    f"archived:{str(value).lower()} conflicts with archived:"
                    f"{str(member['archived']).lower()} on line {member['archived_line']} "
                    f"for member {member.get('name') or member['number']}",
                )
            member["archived"] = value
            member["archived_line"] = line
        if bag["archived_reason"] is not None:
            value, line = bag["archived_reason"]
            if member["archived_reason"] is not None and member["archived_reason"] != value:
                self.error(line, f"archivedReason conflicts with line {member['archived_reason_line']}")
            member["archived_reason"] = value
            member["archived_reason_line"] = line
        if bag["description"] is not None:
            value, line = bag["description"]
            if member["description"] is not None and member["description"] != value:
                self.error(line, "description conflicts with an earlier description for this member")
            member["description"] = value
        for script_id, line in bag["notes"]:
            if script_id not in [item[0] for item in member["note_refs"]]:
                member["note_refs"].append((script_id, line))
        if bag["avatar"]:
            occurrence["avatar"] = dict(bag["avatar"])
        if bag["front"] is not None:
            value, line = bag["front"]
            if member["fronting"] is not None and member["fronting"] != value:
                self.error(
                    line,
                    f"front:{str(value).lower()} conflicts with front:"
                    f"{str(member['fronting']).lower()} on line {member['fronting_line']} "
                    f"for member {member.get('name') or member['number']}",
                )
            member["fronting"] = value
            member["fronting_line"] = line

    def _quoted(self, line, rest, label):
        """Return the inside of one single-quoted string. The quotes are required."""
        match = re.fullmatch(r"'([^']*)'", rest or "")
        if not match:
            self.error(line, f"{label} requires single-quoted text")
        return match.group(1)

    def _field_ref(self, line, rest):
        """Return (script id, value or None).

        "id1" cites the field. "id1 'Sailor'" also supplies a value. The value
        stays None when the quotes are absent. This does not check that the
        field has been defined.
        """
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*)(?:\s+'([^']*)')?", rest or "")
        if not match:
            self.error(line, "field reference must be a script id, optionally followed by single-quoted text")
        return match.group(1), match.group(2)

    def _catalog_block(self, header_line, expected, store):
        """Read Bucket, Friend, or CustomFront rows until ']'. This method consumes ']'.

        store is the definition method. It may itself consume an optional body
        when the next line is '['.
        """
        while True:
            item = self.peek()
            if item is None:
                self.error(header_line, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return
            self.pop()
            header = HEADER_RE.match(text)
            if not header or header.group(1) != expected:
                self.error(line, f"expected {expected}")
            store(line, header.group(2).strip())

    def _named_script(self, line, rest, label):
        """Return (name, script id). A missing script id is an error for these records."""
        if not rest:
            self.error(line, f"{label} requires a name and script id")
        name, script_id = self._split_name_id(line, rest)
        if script_id is None:
            self.error(line, f"{label} requires a script id")
        return name, script_id

    def _bucket_definition(self, line, rest):
        """Append {script_id, name, line}. Buckets have no body. Script ids are unique."""
        name, script_id = self._named_script(line, rest, "Bucket")
        if any(bucket["script_id"] == script_id for bucket in self.buckets):
            self.error(line, f"bucket {script_id!r} is already defined")
        self.buckets.append({"script_id": script_id, "name": name, "line": line})

    def _friend_definition(self, line, rest):
        """Append a friend and, when the next line is '[', read its body.

        The record starts as script_id, name, line, trusted None, buckets [].
        trusted stays a (bool, line) tuple until _resolve replaces it with the
        bool, or leaves None when the body omitted it. The opening '[' is
        consumed here. _friend_body consumes ']'.
        """
        name, script_id = self._named_script(line, rest, "Friend")
        if any(friend["script_id"] == script_id for friend in self.friends):
            self.error(line, f"friend {script_id!r} is already defined")
        friend = {
            "script_id": script_id, "name": name, "line": line,
            "trusted": None, "buckets": [],
        }
        self.friends.append(friend)
        if self.peek() is not None and self.peek()[1] == "[":
            self.pop()
            self._friend_body(friend, line)

    def _friend_body(self, friend, header_line):
        """Read trusted and bucket lines. This method consumes ']'.

        trusted must agree inside the body. bucket lines accumulate
        (script id, line) and may repeat; _resolve drops later duplicates.
        """
        while True:
            item = self.peek()
            if item is None:
                self.error(header_line, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return
            self.pop()
            header = HEADER_RE.match(text)
            if not header:
                self.error(line, f"unrecognized friend setting {text!r}")
            keyword, rest = header.group(1), header.group(2).strip()
            if keyword == "trusted":
                if rest not in ("true", "false"):
                    self.error(line, "trusted must be true or false")
                value = rest == "true"
                if friend["trusted"] is not None and friend["trusted"][0] != value:
                    self.error(line, f"trusted conflicts with line {friend['trusted'][1]}")
                friend["trusted"] = (value, line)
            elif keyword == "bucket":
                if not SCRIPT_ID_RE.match(rest):
                    self.error(line, "bucket reference must be a script id")
                friend["buckets"].append((rest, line))
            else:
                self.error(line, f"{keyword} is not allowed inside a Friend block")

    def _custom_front_definition(self, line, rest):
        """Append a custom front. It is not a member and has no occurrence.

        The record is script_id, name, line, description None, fronting None,
        fronting_line None. An optional '[' is consumed here. The body reader
        consumes ']'.
        """
        name, script_id = self._named_script(line, rest, "CustomFront")
        if any(front["script_id"] == script_id for front in self.custom_fronts):
            self.error(line, f"custom front {script_id!r} is already defined")
        front = {
            "script_id": script_id, "name": name, "line": line,
            "description": None, "fronting": None, "fronting_line": None,
        }
        self.custom_fronts.append(front)
        if self.peek() is not None and self.peek()[1] == "[":
            self.pop()
            self._custom_front_body(front, line)

    def _custom_front_body(self, front, header_line):
        """Read description and front. This method consumes ']'.

        description is the quoted string, not a (value, line) tuple. A second
        different description in this body is an error. front is a bool.
        fronting None means the body did not say.
        """
        while True:
            item = self.peek()
            if item is None:
                self.error(header_line, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return
            self.pop()
            header = HEADER_RE.match(text)
            if not header:
                self.error(line, f"unrecognized custom front setting {text!r}")
            keyword, rest = header.group(1), header.group(2).strip()
            if keyword == "description":
                text_value = self._quoted(line, rest, "description")
                if front["description"] is not None and front["description"] != text_value:
                    self.error(line, "description conflicts with an earlier description")
                front["description"] = text_value
            elif keyword == "front":
                if rest not in ("true", "false"):
                    self.error(line, "front must be true or false")
                value = rest == "true"
                if front["fronting"] is not None and front["fronting"] != value:
                    self.error(line, f"front conflicts with line {front['fronting_line']}")
                front["fronting"] = value
                front["fronting_line"] = line
            else:
                self.error(line, f"{keyword} is not allowed inside a CustomFront block")

    def _add_ref(self, bucket, line, rest, label):
        """Append (script id, line). Does not check that the id is defined and does not dedupe."""
        if not SCRIPT_ID_RE.match(rest):
            self.error(line, f"{label} reference must be a script id")
        bucket.append((rest, line))

    def _anchor_setting(self, anchor, line, keyword, rest):
        """Store anchor visibility or permission as (raw rest, line).

        The raw string is not split or checked against the account vocabularies.
        A second different value on the same anchor is an error. None means unset.
        """
        if not rest:
            self.error(line, f"{keyword} requires a value")
        slot = "visibility" if keyword == "visibility" else "permission"
        current = anchor[slot]
        if current is not None and current[0] != rest:
            self.error(line, f"{keyword} conflicts with line {current[1]}")
        anchor[slot] = (rest, line)

    def _relationship(self, anchor, line, label, target_text):
        """Append a relationship from this anchor. target_key stays None for now.

        An empty target is stored and not added to self.unresolved, so _resolve
        leaves target_key None. Any other target is deferred as
        (record, name, script id or None, line) so the target anchor may be
        declared later in the file.
        """
        rel = {
            "source_key": anchor["key"],
            "label": label,
            "target_key": None,
            "line": line,
        }
        self.relationships.append(rel)
        if target_text == "":
            return
        name, script_id = self._split_name_id(line, target_text)
        self.unresolved.append((rel, name, script_id, line))

    def _resolve(self):
        """Finish references, then avatar requests. Called once, after the Account block.

        Phase 1, relationships. A deferred target with a script id must name
        that anchor. A target with only a name uses anchor_names. Either miss
        is an error. The match writes the anchor's internal key into target_key.
        An empty target never enters this loop.

        Phase 2, id-only refs. Anchor field_refs, anchor note_refs, member
        field_refs, member note_refs, member buckets, and friend buckets are
        lists of (script id, line) at this point. Each id must exist in the
        catalog collected from the whole file. The list becomes script ids in
        first-seen order. A repeated id is dropped. Source lines are not kept.
        Anchor note_refs and member note_refs are resolved separately. A note
        cited by an anchor is not added to a member, and the reverse is also
        true. A Notes block may follow the anchor that cites it.

        Phase 3, values that stay tuples. Member field_values remain
        (script id, value, line) after the field is known to exist. They are
        not deduplicated here; _apply_bag already kept one value per field.
        Anchor field_values are checked and left unchanged, including repeats.
        Friend trusted, when set, becomes the bool. None stays None.

        Phase 4, _resolve_avatars. Definitions can legally follow their uses,
        which is why none of this runs during the scan.
        """
        # Phase 1. Relationship targets become internal anchor keys.
        for rel, name, script_id, line in self.unresolved:
            if script_id is not None:
                anchor = self.anchor_script_ids.get(script_id)
                if anchor is None:
                    self.error(line, f"undefined anchor script id {script_id!r}")
                if anchor["name"] != name:
                    self.error(
                        line,
                        f"target name {name!r} does not match {script_id!r} "
                        f"({anchor['name']!r} on line {anchor['line']})",
                    )
            else:
                anchor = self.anchor_names.get(name)
                if anchor is None:
                    self.error(line, f"undefined anchor {name!r}")
            rel["target_key"] = anchor["key"]
        # Phase 2. (script id, line) lists become ordered script ids.
        known_fields = {field["script_id"] for field in self.fields}
        known_notes = {note["script_id"] for note in self.notes}
        known_buckets = {bucket["script_id"] for bucket in self.buckets}
        for anchor in self.anchors:
            resolved = []
            for script_id, line in anchor["field_refs"]:
                if script_id not in known_fields:
                    self.error(line, f"undefined field {script_id!r}")
                if script_id not in resolved:
                    resolved.append(script_id)
            anchor["field_refs"] = resolved
            notes = []
            for script_id, line in anchor["note_refs"]:
                if script_id not in known_notes:
                    self.error(line, f"undefined note {script_id!r}")
                if script_id not in notes:
                    notes.append(script_id)
            anchor["note_refs"] = notes
        for member in self.members:
            fields = []
            for script_id, line in member["field_refs"]:
                if script_id not in known_fields:
                    self.error(line, f"undefined field {script_id!r}")
                if script_id not in fields:
                    fields.append(script_id)
            notes = []
            for script_id, line in member["note_refs"]:
                if script_id not in known_notes:
                    self.error(line, f"undefined note {script_id!r}")
                if script_id not in notes:
                    notes.append(script_id)
            member["field_refs"] = fields
            member["note_refs"] = notes
            # Phase 3. Values keep their source lines. trusted becomes a bool.
            values = []
            for script_id, value, line in member["field_values"]:
                if script_id not in known_fields:
                    self.error(line, f"undefined field {script_id!r}")
                values.append((script_id, value, line))
            member["field_values"] = values
            buckets = []
            for script_id, line in member["buckets"]:
                if script_id not in known_buckets:
                    self.error(line, f"undefined bucket {script_id!r}")
                if script_id not in buckets:
                    buckets.append(script_id)
            member["buckets"] = buckets
        # Friend bucket ids follow the same first-seen rule. trusted drops its line.
        for friend in self.friends:
            buckets = []
            for script_id, line in friend["buckets"]:
                if script_id not in known_buckets:
                    self.error(line, f"undefined bucket {script_id!r}")
                if script_id not in buckets:
                    buckets.append(script_id)
            friend["buckets"] = buckets
            if friend["trusted"] is not None:
                friend["trusted"] = friend["trusted"][0]
        # Anchor field values are validated and not rewritten.
        for anchor in self.anchors:
            for script_id, _value, line in anchor["field_values"]:
                if script_id not in known_fields:
                    self.error(line, f"undefined field {script_id!r}")
        # Phase 4. One avatar request per shared member.
        self._resolve_avatars()

    def _parse_config(self, header_line):
        """Read the optional Config block and consume its ']'.

        Only avatar attributes are legal. Each is stored as (value, line) in
        config_avatar. A repeated attribute must carry the same value. This
        method does not apply the values to members. _resolve_avatars does.
        """
        self._expect_open(header_line)
        while True:
            item = self.peek()
            if item is None:
                self.error(header_line, "unclosed '['")
            line, text = item
            if text == "]":
                self.pop()
                return
            self.pop()
            header = HEADER_RE.match(text)
            if not header:
                self.error(line, f"unrecognized Config statement {text!r}")
            keyword, rest = header.group(1), header.group(2).strip()
            if keyword not in AVATAR_ATTRS:
                self.error(line, f"{keyword} is not allowed in Config")
            self._set_avatar(
                self.config_avatar, keyword, line, self._avatar_value(keyword, line, rest),
            )

    def _avatar_value(self, keyword, line, rest):
        """Return an int dimension, a style string, or a lowercase #rrggbb color.

        Dimensions must be positive integers. A leading zero is rejected.
        Style must be none, solid, or crosshatch. Color must be #RRGGBB and is
        stored lowercase, still including the leading #.
        """
        if keyword in ("avatar-width", "avatar-height"):
            if not re.fullmatch(r"[1-9]\d*", rest or ""):
                self.error(line, f"{keyword} must be a positive integer; got {rest!r}")
            return int(rest)
        if keyword == "avatar":
            if rest not in AVATAR_STYLES:
                self.error(line, f"avatar must be none, solid, or crosshatch; got {rest!r}")
            return rest
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", rest or ""):
            self.error(line, f"color must be #RRGGBB; got {rest!r}")
        return rest.lower()

    def _set_avatar(self, bucket, keyword, line, value):
        """Store (value, line) on a config, anchor, or member-bag avatar dict.

        Repeating an attribute with the same value updates its stored source
        line to the latest assignment. A different value raises FeedError.
        """
        current = bucket.get(keyword)
        if current is not None and current[0] != value:
            self.error(line, f"{keyword} conflicts with line {current[1]}")
        bucket[keyword] = (value, line)

    def _avatar_object(self, explicit):
        """Copy only the keys present in explicit, in AVATAR_ATTRS order.

        explicit values may be (value, line) or a bare value. The returned
        dict is what adapters can serialize. An empty result is falsy, and
        callers store None instead of {}.
        """
        obj = {}
        for key in AVATAR_ATTRS:
            if key in explicit:
                obj[key] = explicit[key][0] if isinstance(explicit[key], tuple) else explicit[key]
        return obj

    def _resolve_avatars(self):
        """Config, then outer anchors, then the member block. One request per shared member.

        A setting anywhere in a bracket applies to that whole scope. Position
        relative to a Member line does not matter. An explicit member-block
        attribute applies to every placement of that shared member. A later
        placement that omits the attribute does not reset it. Placements
        conflict when they set different explicit values, or when the member
        never sets an attribute and the enclosing scopes disagree. An explicit
        avatar conflict cites the previously stored attribute-setting line,
        rather than the Member declaration line. A generated member's name is
        None, so that message quotes None. Comments in the body mark each stage.
        """
        anchors = {anchor["key"]: anchor for anchor in self.anchors}
        # Account-level result: built-in defaults, then Config. Color is included
        # only when Config set it. This dict is what _model exposes as account_config.
        account_config = dict(AVATAR_DEFAULTS)
        for key in ("avatar-width", "avatar-height", "avatar"):
            if key in self.config_avatar:
                account_config[key] = self.config_avatar[key][0]
        if "color" in self.config_avatar:
            account_config["color"] = self.config_avatar["color"][0]
        self.account_config = account_config

        # Placements in declaration order, grouped by shared member.
        by_member = {}
        for occ in self.occurrences:
            by_member.setdefault(occ["member_key"], []).append(occ)

        for member in self.members:
            resolved_rows = []
            for occ in by_member.get(member["key"], []):
                # Start from defaults and Config, then apply ancestors from the
                # outside inward. The occurrence's own avatar dict is last, so
                # an explicit member-block value overrides the chain for this
                # placement only at this stage.
                values = dict(AVATAR_DEFAULTS)
                sources = {key: None for key in AVATAR_ATTRS}
                if "color" in self.config_avatar:
                    values["color"] = self.config_avatar["color"][0]
                    sources["color"] = self.config_avatar["color"][1]
                for key in ("avatar-width", "avatar-height", "avatar"):
                    if key in self.config_avatar:
                        values[key] = self.config_avatar[key][0]
                        sources[key] = self.config_avatar[key][1]
                chain = []
                anchor = anchors[occ["anchor_key"]]
                seen = set()
                # chain[0] is the placement's anchor. The last item is the outermost.
                while anchor is not None:
                    if anchor["key"] in seen:
                        self.error(anchor["line"], "anchor containment cycle")
                    seen.add(anchor["key"])
                    chain.append(anchor)
                    parent = anchor["parent_key"]
                    anchor = anchors.get(parent) if parent else None
                for scope in reversed(chain):
                    for key, (value, line) in scope["avatar"].items():
                        values[key] = value
                        sources[key] = line
                for key, (value, line) in occ["avatar"].items():
                    values[key] = value
                    sources[key] = line
                resolved_rows.append((occ, values, sources))
            # Explicit member-block keys, gathered across every placement.
            # The first placement that sets a key supplies the member-wide value.
            explicit = {}
            explicit_lines = {}
            for occ, _values, _sources in resolved_rows:
                for key, (value, line) in occ["avatar"].items():
                    previous = explicit.get(key)
                    if previous is not None and previous != value:
                        self.error(
                            explicit_lines[key],
                            f"member {member['name']!r} {key} conflicts with line {line}",
                        )
                    explicit[key] = value
                    explicit_lines[key] = line
            # Per attribute: an explicit member value wins. Otherwise every
            # placement's inherited value must be the same, including a color
            # that nobody set (None).
            chosen = {}
            chosen_sources = {}
            for key in AVATAR_ATTRS:
                if key in explicit:
                    chosen[key] = explicit[key]
                    chosen_sources[key] = explicit_lines[key]
                    continue
                inherited = []
                for occ, values, sources in resolved_rows:
                    inherited.append((values.get(key), sources.get(key), occ["line"]))
                distinct = {item[0] for item in inherited}
                if len(distinct) > 1:
                    first = inherited[0]
                    other = next(item for item in inherited if item[0] != first[0])
                    self.error(
                        first[2],
                        f"member {member['name']!r} avatar conflicts with line {other[2]}: "
                        f"{key} {first[0]!r} from "
                        f"{'default' if first[1] is None else 'line ' + str(first[1])} vs "
                        f"{other[0]!r} from "
                        f"{'default' if other[1] is None else 'line ' + str(other[1])}",
                    )
                chosen[key] = inherited[0][0]
                chosen_sources[key] = inherited[0][1]
            # avatar_request is the member-wide result. color is None when unset.
            # avatar_config is only the keys the member blocks set, or None.
            member["avatar_request"] = {
                "style": chosen["avatar"],
                "width": chosen["avatar-width"],
                "height": chosen["avatar-height"],
                "color": chosen.get("color"),
            }
            member["avatar_config"] = self._avatar_object(explicit) or None
        # An anchor config is that anchor's own explicit keys, not the inherited chain.
        for anchor in self.anchors:
            anchor["avatar_config"] = self._avatar_object(anchor["avatar"]) or None

    def _avatar_conflict_text(self, values, sources):
        """Format one resolved avatar. The current conflict path does not call this.

        _resolve_avatars builds its own message and names the two disagreeing
        lines. This helper remains available and is not part of that message.
        """
        def locate(key):
            """Say default when that attribute was never set on a source line."""
            line = sources.get(key)
            return "default" if line is None else f"line {line}"

        color = values.get("color") or "derived"
        return (
            f"{values['avatar']} {values['avatar-width']}x{values['avatar-height']} color {color} "
            f"(width {locate('avatar-width')}, height {locate('avatar-height')}, "
            f"avatar {locate('avatar')}, color {locate('color')})"
        )

    def _model(self):
        """Return the shared model. Lists and dicts are the parser's own objects.

        Guarantees after _resolve:

        - path is the feed path as text. stem is its filename without the suffix.
        - account_name and account_email are strings. account_permission is a
          list of type strings or None. account_visibility is a token or None.
        - account_config always has avatar-width, avatar-height, and avatar.
          color is present only when Config set it.
        - notices is a new list. The only notice this parser appends is for
          visibility "self".
        - anchors, members, and occurrences are in declaration order. Members
          have avatar_request and avatar_config. They do not have json_id.
        - anchor field_refs, anchor note_refs, member field_refs, member
          note_refs, and member and friend buckets are lists of script-id
          strings. Anchor note_refs are that anchor's own associations.
          Member note_refs are that member's own associations.
          Member field_values and anchor field_values are still
          (script id, value, line).
        - friend trusted is a bool or None. relationship target_key is an
          internal anchor key, or None when the feed target was empty.
        - anchor permission and visibility are still (raw text, line) or None.
        - occurrence visibility is a token or None. occurrence permission is
          a list of types or None.
        - custom fronts are not members. notes, fields, and buckets are the
          catalog records from the scan.

        Adapters may add json_id and other keys onto these dicts while rendering.
        """
        return {
            "path": self.path,
            "stem": Path(self.path).stem,
            "account_name": self.account_name,
            "account_email": self.account_email,
            "account_permission": self.account_permission,
            "account_visibility": self.account_visibility,
            "account_config": self.account_config,
            "notices": list(self.notices),
            "anchors": self.anchors,
            "members": self.members,
            "occurrences": self.occurrences,
            "notes": self.notes,
            "fields": self.fields,
            "buckets": self.buckets,
            "friends": self.friends,
            "custom_fronts": self.custom_fronts,
            "relationships": self.relationships,
        }


def parse_feed(path):
    """Read one UTF-8 feed and return the model from _model.

    A missing path raises FeedError with no line number. An empty file, a
    syntax error, an unresolved reference, or an avatar conflict also raises
    FeedError. The returned members have no json_id. This function does not
    write and does not load a target adapter.
    """
    path = Path(path)
    if not path.is_file():
        raise FeedError(f"{path}: file not found")
    text = path.read_text(encoding="utf-8")
    return _Parser(path, text).parse()


def _output_path(stem, imports_root=None):
    """PluralBridge JSON path under the imports root.

    imports_root None uses out/imports, relative to the cwd. Tests pass a
    temporary directory and do not write the repository out/ tree.
    """
    root = Path("out") / "imports" if imports_root is None else Path(imports_root)
    return root / "pluralbridge" / f"{stem}.json"


def _target_path(target, stem, imports_root=None):
    """JSON path out/imports/<target>/<stem>.json, or under imports_root."""
    root = Path("out") / "imports" if imports_root is None else Path(imports_root)
    return root / target / f"{stem}.json"


def _avatar_pngs(model):
    """One PNG per shared member whose resolved style is not none.

    Keys are member["json_id"]. Accessing a missing member["json_id"] raises
    KeyError before generate_avatar is called. ValueError raised by
    generate_avatar is converted to FeedError. Style none is skipped and
    contributes no key. This function does not write the PNG files.
    PluralPort does not call it.
    """
    avatars = _load_sibling("gen-avatars.py", "gen_avatars")
    pngs = {}
    for member in model["members"]:
        request = member["avatar_request"]
        try:
            result = avatars.generate_avatar(
                request["style"],
                member["json_id"],
                width=request["width"],
                height=request["height"],
                color=request["color"],
            )
        except ValueError as exc:
            raise FeedError(f"{model['path']}:{member['line']}: {exc}") from exc
        if request["style"] == "none":
            continue
        pngs[member["json_id"]] = result.png
    return pngs


def _run_pluralbridge(feed_path, imports_root=None):
    """Parse, render, build PNGs, then write.

    render_import_model returns (export, gaps) and assigns member json_id
    values before _avatar_pngs. write_import_export receives the PNG dict,
    including an empty dict when every style is none. ImportRenderError is
    printed and returns 1. FeedError is not caught here. On success, stderr
    gets parser notices and one "gap:" line per gap. stdout is the posix path
    and a count line. The path is out/imports/pluralbridge/<stem>.json unless
    imports_root is set.
    """
    model = parse_feed(feed_path)
    pluralbridge = _load_sibling("gen-pluralbridge.py", "gen_pluralbridge")
    try:
        export, gaps = pluralbridge.render_import_model(model)
        pngs = _avatar_pngs(model)
        destination = _output_path(model["stem"], imports_root)
        pluralbridge.write_import_export(destination, export, pngs)
    except pluralbridge.ImportRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for notice in model["notices"]:
        print(f"notice: {notice}", file=sys.stderr)
    for gap in gaps:
        print(f"gap: {gap}", file=sys.stderr)
    account = export["account"]
    print(destination.as_posix())
    print(
        "members={members} anchors={anchors} relationships={relationships} avatars={avatars}".format(
            members=len(account["members"]),
            anchors=len(account["anchors"]),
            relationships=len(account.get("relationships") or []),
            avatars=len(pngs),
        )
    )
    return 0


def _run_simplyplural(feed_path, imports_root=None):
    """Parse, render, build PNGs, then write.

    render_import_model returns (export, notices) and assigns member json_id
    values first. SimplyPluralError is printed and returns 1. FeedError is
    not caught here. Parser notices and adapter notices both use the "notice:"
    prefix. The path is out/imports/simplyplural/<stem>.json unless
    imports_root is set. PNG names are the member ids the adapter stored.
    """
    model = parse_feed(feed_path)
    simplyplural = _load_sibling("gen-simplyplural.py", "gen_simplyplural")
    try:
        export, notices = simplyplural.render_import_model(model)
        pngs = _avatar_pngs(model)
        destination = _target_path("simplyplural", model["stem"], imports_root)
        simplyplural.write_import_export(destination, export, pngs)
    except simplyplural.SimplyPluralError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for notice in model["notices"]:
        print(f"notice: {notice}", file=sys.stderr)
    for notice in notices:
        print(f"notice: {notice}", file=sys.stderr)
    account_members = export["members"]
    print(destination.as_posix())
    print(
        "users={users} members={members} groups={groups} notes={notes} "
        "fields={fields} buckets={buckets} friends={friends} "
        "customFronts={fronts} frontHistory={history} avatars={avatars}".format(
            users=len(export["users"]),
            members=len(account_members),
            groups=len(export.get("groups") or []),
            notes=len(export.get("notes") or []),
            fields=len(export.get("customFields") or []),
            buckets=len(export.get("privacyBuckets") or []),
            friends=len(export.get("friends") or []),
            fronts=len(export.get("frontStatuses") or []),
            history=len(export.get("frontHistory") or []),
            avatars=len(pngs),
        )
    )
    return 0


def _run_pluralport(feed_path, imports_root=None):
    """Parse, render, then write JSON. This runner does not call _avatar_pngs.

    The PluralPort renderer loads gen-avatars itself while building Asset
    records. It returns (export, warnings). PluralPortError is printed and
    returns 1. Parser notices use "notice:". Each warning's message is printed
    with "warning:". The path is out/imports/pluralport/<stem>.json unless
    imports_root is set.
    """
    model = parse_feed(feed_path)
    pluralport = _load_sibling("gen-pluralport.py", "gen_pluralport")
    try:
        export, warnings = pluralport.render_import_model(model)
        destination = _target_path("pluralport", model["stem"], imports_root)
        pluralport.write_import_export(destination, export)
    except pluralport.PluralPortError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for notice in model["notices"]:
        print(f"notice: {notice}", file=sys.stderr)
    for warning in warnings:
        print(f"warning: {warning['message']}", file=sys.stderr)
    print(destination.as_posix())
    print(
        "systems={systems} members={members} groups={groups} "
        "group_memberships={memberships} custom_fields={fields} "
        "custom_field_values={values} notes={notes} front_periods={periods} "
        "assets={assets}".format(
            systems=len(export["systems"]),
            members=len(export["members"]),
            groups=len(export.get("groups") or []),
            memberships=len(export.get("group_memberships") or []),
            fields=len(export.get("custom_fields") or []),
            values=len(export.get("custom_field_values") or []),
            notes=len(export.get("notes") or []),
            periods=len(export.get("front_periods") or []),
            assets=len(export.get("assets") or []),
        )
    )
    return 0


def _run_pluralkit(feed_path, imports_root=None):
    """Parse, render, build PNGs, then write.

    render_import_model returns (export, notices) and sets json_id to the
    member short id before _avatar_pngs. Those ids are the PNG filenames.
    PluralKitError is printed and returns 1. FeedError is not caught here.
    Parser notices and adapter notices both use "notice:". The path is
    out/imports/pluralkit/<stem>.json unless imports_root is set.
    """
    model = parse_feed(feed_path)
    pluralkit = _load_sibling("gen-pluralkit.py", "gen_pluralkit")
    try:
        export, notices = pluralkit.render_import_model(model)
        pngs = _avatar_pngs(model)
        destination = _target_path("pluralkit", model["stem"], imports_root)
        pluralkit.write_import_export(destination, export, pngs)
    except pluralkit.PluralKitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for notice in model["notices"]:
        print(f"notice: {notice}", file=sys.stderr)
    for notice in notices:
        print(f"notice: {notice}", file=sys.stderr)
    print(destination.as_posix())
    print(
        "members={members} groups={groups} switches={switches} "
        "accounts={accounts} avatars={avatars}".format(
            members=len(export["members"]),
            groups=len(export["groups"]),
            switches=len(export["switches"]),
            accounts=len(export["accounts"]),
            avatars=len(pngs),
        )
    )
    return 0


def _run_stub(filename, module_name):
    """Call run() on a sibling and return 0. main does not use this for the four targets."""
    module = _load_sibling(filename, module_name)
    module.run()
    return 0


def main(argv=None, imports_root=None):
    """Dispatch --model. The description string is the help text, not this docstring.

    lighthouse prints to stderr and returns 2. An unknown model returns 2.
    simplyplural, pluralport, pluralkit, and pluralbridge catch FeedError,
    print it, and return 1. Each runner catches only its own target exception.
    Other exceptions, including an error raised after a replace, propagate.
    argv None reads the process arguments. imports_root None writes under
    out/imports. A caller may pass another directory; the command line does not.
    """
    parser = argparse.ArgumentParser(
        description="Proof-of-concept model-feed importer.",
    )
    parser.add_argument(
        "--model", required=True,
        help="pluralbridge, simplyplural, pluralport, pluralkit, or lighthouse",
    )
    parser.add_argument("--scriptfspec", required=True, help="Path to a model-feed text file")
    args = parser.parse_args(argv)
    model = args.model.strip().lower()
    if model == "lighthouse":
        print("Lighthouse is not implemented", file=sys.stderr)
        return 2
    if model == "simplyplural":
        try:
            return _run_simplyplural(args.scriptfspec, imports_root)
        except FeedError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if model == "pluralport":
        try:
            return _run_pluralport(args.scriptfspec, imports_root)
        except FeedError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if model == "pluralkit":
        try:
            return _run_pluralkit(args.scriptfspec, imports_root)
        except FeedError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if model != "pluralbridge":
        print(f"unknown model {args.model!r}", file=sys.stderr)
        return 2
    try:
        return _run_pluralbridge(args.scriptfspec, imports_root)
    except FeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
