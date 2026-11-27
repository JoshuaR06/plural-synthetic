#!/usr/bin/env python3
"""Proof-of-concept model-feed import engine.

Parses templates/model-feed.txt syntax, builds a target-independent model,
and dispatches to a generator. PluralBridge mapping and JSON writing live in
gen-pluralbridge.py. This module does not import generate.py. Importing it
does not write files.

Accepted syntax is documented in templates/model-feed-usage.md.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path


class FeedError(Exception):
    """The feed is not usable. No output file should be written."""


HEADER_RE = re.compile(
    r"^(Account|Permission|Visibility|Place|System|Group|Member|Notes|CustomFields|"
    r"PrivacyBuckets|Friends|CustomFronts|Note|Field|Bucket|Friend|CustomFront|"
    r"name|email|visibility|permission|field|note|front|archivedReason|archived|"
    r"bucket|description|trusted|avatar-width|avatar-height|avatar|color)\s*:\s*(.*)$"
)
ACCOUNT_BLOCKS = ("Notes", "CustomFields", "PrivacyBuckets", "Friends", "CustomFronts")
AVATAR_ATTRS = ("avatar-width", "avatar-height", "avatar", "color")
AVATAR_STYLES = ("none", "solid", "crosshatch")
AVATAR_DEFAULTS = {"avatar-width": 64, "avatar-height": 64, "avatar": "none"}
PERMISSION_TYPES = ("read", "write", "create", "delete", "inherit", "all")
VISIBILITY_TYPES = ("only you", "trusted friends", "all friends", "selected people", "inherit")
RELATION_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*->\s*(.*)$")
SCRIPT_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
RANGE_RE = re.compile(r"^(\d+)-(\d+)$")
ANCHOR_KINDS = {"Place": "place", "System": "system", "Group": "group"}


def _load_sibling(filename, module_name):
    """Load a hyphen-named generator beside this file. Loading must not emit output."""
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Parser:
    def __init__(self, path, text):
        self.path = str(path)
        self.lines = []
        for number, raw in enumerate(text.splitlines(), 1):
            stripped = raw.strip()
            if stripped:
                self.lines.append((number, stripped))
        self.index = 0
        self.anchors = []
        self.members = []
        self.member_by_key = {}
        self.occurrences = []
        self.occurrence_keys = set()
        self.notes = []
        self.fields = []
        self.buckets = []
        self.friends = []
        self.custom_fronts = []
        self.relationships = []
        self.account_name = None
        self.account_email = None
        self.account_permission = None
        self.account_visibility = None
        self.config_avatar = {}
        self.notices = []
        self.anchor_script_ids = {}
        self.anchor_names = {}
        self.note_ids = set()
        self.field_ids = set()
        self.generated_ordinal = {"place": 0, "system": 0, "group": 0}
        self.unresolved = []

    def error(self, line, message):
        raise FeedError(f"{self.path}:{line}: {message}")

    def peek(self):
        if self.index >= len(self.lines):
            return None
        return self.lines[self.index]

    def pop(self):
        item = self.peek()
        if item is None:
            raise FeedError(f"{self.path}: unexpected end of file")
        self.index += 1
        return item

    def parse(self):
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
        item = self.peek()
        if item is None or item[1] != "[":
            self.error(header_line, "expected '[' to open this block")
        self.pop()

    def _parse_body(self, scope, owner):
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
        if scope == "anchor" and keyword in ("visibility", "permission"):
            self._anchor_setting(owner, number, keyword, rest)
            return
        self.error(number, f"{keyword} is not allowed in this scope")

    def _account_identity(self, keyword, line, rest):
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
                key = ("range", anchor["key"], line, number)
                member = self._new_member(key, line, generated=True, anchor_key=anchor["key"], number=number)
                created.append(member)
                self._add_occurrence(anchor, member, line)
        else:
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
        if not rest:
            self.error(line, f"{label} requires a value")
        if bag[key] is not None and bag[key][0] != rest:
            self.error(line, f"{label} conflicts with line {bag[key][1]}")
        bag[key] = (rest, line)

    def _apply_bag(self, member, anchor, bag):
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
        match = re.fullmatch(r"'([^']*)'", rest or "")
        if not match:
            self.error(line, f"{label} requires single-quoted text")
        return match.group(1)

    def _field_ref(self, line, rest):
        """field: scriptId, or field: scriptId 'value'."""
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*)(?:\s+'([^']*)')?", rest or "")
        if not match:
            self.error(line, "field reference must be a script id, optionally followed by single-quoted text")
        return match.group(1), match.group(2)

    def _catalog_block(self, header_line, expected, store):
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
        if not rest:
            self.error(line, f"{label} requires a name and script id")
        name, script_id = self._split_name_id(line, rest)
        if script_id is None:
            self.error(line, f"{label} requires a script id")
        return name, script_id

    def _bucket_definition(self, line, rest):
        name, script_id = self._named_script(line, rest, "Bucket")
        if any(bucket["script_id"] == script_id for bucket in self.buckets):
            self.error(line, f"bucket {script_id!r} is already defined")
        self.buckets.append({"script_id": script_id, "name": name, "line": line})

    def _friend_definition(self, line, rest):
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
        if not SCRIPT_ID_RE.match(rest):
            self.error(line, f"{label} reference must be a script id")
        bucket.append((rest, line))

    def _anchor_setting(self, anchor, line, keyword, rest):
        if not rest:
            self.error(line, f"{keyword} requires a value")
        slot = "visibility" if keyword == "visibility" else "permission"
        current = anchor[slot]
        if current is not None and current[0] != rest:
            self.error(line, f"{keyword} conflicts with line {current[1]}")
        anchor[slot] = (rest, line)

    def _relationship(self, anchor, line, label, target_text):
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
        for anchor in self.anchors:
            for script_id, _value, line in anchor["field_values"]:
                if script_id not in known_fields:
                    self.error(line, f"undefined field {script_id!r}")
        self._resolve_avatars()

    def _parse_config(self, header_line):
        """One top-level Config block. Its avatar attributes are the global defaults."""
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
        current = bucket.get(keyword)
        if current is not None and current[0] != value:
            self.error(line, f"{keyword} conflicts with line {current[1]}")
        bucket[keyword] = (value, line)

    def _avatar_object(self, explicit):
        """JSON config for attributes set in one scope, in canonical key order."""
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
        never sets an attribute and the enclosing scopes disagree.
        """
        anchors = {anchor["key"]: anchor for anchor in self.anchors}
        account_config = dict(AVATAR_DEFAULTS)
        for key in ("avatar-width", "avatar-height", "avatar"):
            if key in self.config_avatar:
                account_config[key] = self.config_avatar[key][0]
        if "color" in self.config_avatar:
            account_config["color"] = self.config_avatar["color"][0]
        self.account_config = account_config

        by_member = {}
        for occ in self.occurrences:
            by_member.setdefault(occ["member_key"], []).append(occ)

        for member in self.members:
            resolved_rows = []
            for occ in by_member.get(member["key"], []):
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
            member["avatar_request"] = {
                "style": chosen["avatar"],
                "width": chosen["avatar-width"],
                "height": chosen["avatar-height"],
                "color": chosen.get("color"),
            }
            member["avatar_config"] = self._avatar_object(explicit) or None
        for anchor in self.anchors:
            anchor["avatar_config"] = self._avatar_object(anchor["avatar"]) or None

    def _avatar_conflict_text(self, values, sources):
        def locate(key):
            line = sources.get(key)
            return "default" if line is None else f"line {line}"

        color = values.get("color") or "derived"
        return (
            f"{values['avatar']} {values['avatar-width']}x{values['avatar-height']} color {color} "
            f"(width {locate('avatar-width')}, height {locate('avatar-height')}, "
            f"avatar {locate('avatar')}, color {locate('color')})"
        )

    def _model(self):
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
    """Read one feed file into a target-independent model."""
    path = Path(path)
    if not path.is_file():
        raise FeedError(f"{path}: file not found")
    text = path.read_text(encoding="utf-8")
    return _Parser(path, text).parse()


def _output_path(stem):
    return Path("out") / "imports" / "pluralbridge" / f"{stem}.json"


def _avatar_pngs(model):
    """Ask gen-avatars for one image per shared member. none contributes no file."""
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


def _run_pluralbridge(feed_path):
    model = parse_feed(feed_path)
    pluralbridge = _load_sibling("gen-pluralbridge.py", "gen_pluralbridge")
    try:
        export, gaps = pluralbridge.render_import_model(model)
        pngs = _avatar_pngs(model)
        destination = _output_path(model["stem"])
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


def _run_simplyplural(feed_path):
    """Parse with the shared engine, then let gen-simplyplural.py map and write."""
    model = parse_feed(feed_path)
    simplyplural = _load_sibling("gen-simplyplural.py", "gen_simplyplural")
    try:
        export, notices = simplyplural.render_import_model(model)
        pngs = _avatar_pngs(model)
        destination = Path("out") / "imports" / "simplyplural" / f"{model['stem']}.json"
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


def _run_pluralport(feed_path):
    """Parse with the shared engine, then let gen-pluralport.py map and write."""
    model = parse_feed(feed_path)
    pluralport = _load_sibling("gen-pluralport.py", "gen_pluralport")
    try:
        export, warnings = pluralport.render_import_model(model)
        destination = Path("out") / "imports" / "pluralport" / f"{model['stem']}.json"
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


def _run_stub(filename, module_name):
    module = _load_sibling(filename, module_name)
    module.run()
    return 0


def main(argv=None):
    """Command line for the proof-of-concept importer."""
    parser = argparse.ArgumentParser(
        description="Proof-of-concept model-feed importer.",
    )
    parser.add_argument("--model", required=True, help="pluralbridge, simplyplural, pluralport, or lighthouse")
    parser.add_argument("--scriptfspec", required=True, help="Path to a model-feed text file")
    args = parser.parse_args(argv)
    model = args.model.strip().lower()
    if model == "lighthouse":
        print("Lighthouse is not implemented", file=sys.stderr)
        return 2
    if model == "simplyplural":
        try:
            return _run_simplyplural(args.scriptfspec)
        except FeedError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if model == "pluralport":
        try:
            return _run_pluralport(args.scriptfspec)
        except FeedError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if model != "pluralbridge":
        print(f"unknown model {args.model!r}", file=sys.stderr)
        return 2
    try:
        return _run_pluralbridge(args.scriptfspec)
    except FeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
