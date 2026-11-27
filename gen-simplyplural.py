#!/usr/bin/env python3
"""Proof-of-concept Simply Plural export from the shared model feed.

Named gen-simplyplural.py (hyphen). gen-import-engine.py loads it. This
module does not parse the feed, does not import generate.py, and does not
write on import.

The JSON is the observed direct-export shape: one root object of collection
arrays, records carrying _id. It is not a PluralBridge account. Only the
collections this cut can fill are written.

Privacy flags follow the public Apparyllis API (SimplyPluralApi release):

- src/api/v1/member.ts getMembers, accounts at version 1.11 or later: a
  friend sees members whose buckets overlap that friend's buckets. The
  private and preventTrusted flags are not part of that query.
- The same file's pre-1.11 filterFieldsForPrivacy shows a custom field to a
  trusted friend only when private is true and preventTrusted is false, and
  to a friend when both are false. preventTrusted true matches neither branch.

self and only you therefore set private true and preventTrusted true, with
no invented bucket. trusted friends sets private true and preventTrusted
false and keeps buckets the feed assigned. A bucket name is not an access
rule. Operation permissions are not written.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


class SimplyPluralError(Exception):
    """The shared model cannot be written as this Simply Plural cut."""


SYSTEM_ID = "synthetic-system-0001"
# 2026-01-01T00:00:00Z. The same instant as the PluralBridge fixed audit.
FIXED_MS = 1767225600000


def _location(model, line, message):
    raise SimplyPluralError(f"{model['path']}:{line}: {message}")


def _privacy_flags(visibility):
    """Legacy SP flags for one resolved feed visibility. None stays private."""
    if visibility in (None, "self", "only you", "inherit", "selected people"):
        return True, True
    if visibility == "trusted friends":
        return True, False
    if visibility == "all friends":
        return False, False
    raise SimplyPluralError(f"unsupported visibility {visibility!r}")


def _member_visibility(model, member):
    found = []
    for occ in model["occurrences"]:
        if occ["member_key"] != member["key"]:
            continue
        if occ["visibility"] is not None:
            found.append((occ["visibility"], occ["visibility_line"] or occ["line"]))
        else:
            found.append((model.get("account_visibility"), occ["line"]))
    if not found:
        _location(model, member["line"], "member has no occurrence")
    values = {item[0] for item in found}
    if len(values) > 1:
        lines = ", ".join(str(item[1]) for item in found)
        _location(model, member["line"], f"member visibility conflicts across lines {lines}")
    return found[0][0]


def _ancestors(model, anchor):
    by_key = {item["key"]: item for item in model["anchors"]}
    chain = []
    seen = set()
    current = anchor
    while current is not None:
        if current["key"] in seen:
            _location(model, current["line"], "anchor containment cycle")
        seen.add(current["key"])
        chain.append(current)
        parent = current["parent_key"]
        current = by_key.get(parent) if parent else None
    return chain


def _require_supported_shape(model):
    """This cut is one top-level System, its Groups, and member records."""
    systems = [anchor for anchor in model["anchors"] if anchor["kind"] == "system"]
    if len(systems) != 1:
        line = systems[1]["line"] if len(systems) > 1 else 1
        _location(model, line, "this Simply Plural cut requires exactly one System")
    system = systems[0]
    if system["parent_key"] is not None:
        _location(model, system["line"], "a nested System is not supported")
    for anchor in model["anchors"]:
        if anchor["kind"] == "place":
            _location(model, anchor["line"], "Place anchors are not supported in this Simply Plural cut")
        if anchor["kind"] == "group" and (anchor.get("field_refs") or anchor.get("field_values")):
            _location(model, anchor["line"], "Group custom-field associations are not supported")
        if anchor["kind"] == "group":
            for ancestor in _ancestors(model, anchor)[1:]:
                if ancestor["kind"] == "place" or (
                    ancestor["kind"] == "system" and ancestor["key"] != system["key"]
                ):
                    _location(model, anchor["line"], "this Group is not inside the single System")
    if model["relationships"]:
        _location(
            model, model["relationships"][0]["line"],
            "anchor relationships are not supported in this Simply Plural cut",
        )


def _assign_ids(model):
    """Stable SP ids. Named and range members keep the parse order, one id each."""
    for index, member in enumerate(model["members"], 1):
        member["json_id"] = f"synthetic-member-{index:04d}"
        if member["generated"]:
            member["display_name"] = member["json_id"]
        else:
            member["display_name"] = member["name"]
        if member["avatar_request"]["style"] == "none":
            member["avatar_uuid"] = None
        else:
            member["avatar_uuid"] = f"synthetic-avatar-{index:04d}"
    groups = [anchor for anchor in model["anchors"] if anchor["kind"] == "group"]
    for index, group in enumerate(groups, 1):
        group["json_id"] = f"synthetic-group-{index:04d}"


def _note_owners(model):
    owners = {}
    for member in model["members"]:
        for script_id in member["note_refs"]:
            if script_id in owners:
                _location(model, member["line"], f"note {script_id!r} already belongs to another member")
            owners[script_id] = member
    for note in model["notes"]:
        if note["script_id"] not in owners:
            _location(model, note["line"], f"note {note['script_id']!r} has no member owner")
    return owners


def _group_parent(model, group, system):
    by_key = {anchor["key"]: anchor for anchor in model["anchors"]}
    parent = by_key.get(group["parent_key"]) if group["parent_key"] else None
    if parent is None or parent["key"] == system["key"]:
        return "root"
    if parent["kind"] != "group":
        _location(model, group["line"], "this Group parent cannot be represented as an SP group")
    return parent["json_id"]


def _group_members(model, group):
    ids = []
    for occ in model["occurrences"]:
        if occ["anchor_key"] != group["key"]:
            continue
        member = next(item for item in model["members"] if item["key"] == occ["member_key"])
        if member["json_id"] not in ids:
            ids.append(member["json_id"])
    return ids


def render_import_model(model):
    """Map the shared model to Simply Plural collections and console notices."""
    _require_supported_shape(model)
    _assign_ids(model)
    owners = _note_owners(model)
    system = next(anchor for anchor in model["anchors"] if anchor["kind"] == "system")
    notices = []
    if model.get("account_permission"):
        rendered = ",".join(model["account_permission"])
        notices.append(
            f"{model['path']}: account Permission {rendered} has no Simply Plural field "
            "and was not written. It was not mapped to a privacy bucket, role, or token permission."
        )
    if model.get("account_email"):
        notices.append(
            f"{model['path']}: account email has no users[] field in the observed direct export "
            "and was not written."
        )
    notices.append(
        f"{model['path']}: visibility self and only you are private:true and preventTrusted:true. "
        "trusted friends is private:true and preventTrusted:false. "
        "Current Simply Plural friend listing (API 1.11+) still shows a member only when a "
        "friend's buckets overlap the member's buckets. No bucket was invented from a name."
    )

    users = [{
        "_id": SYSTEM_ID,
        "uid": SYSTEM_ID,
        "username": model["account_name"],
        "desc": system["name"],
        "isAsystem": True,
    }]

    members = []
    for member in model["members"]:
        private, prevent_trusted = _privacy_flags(_member_visibility(model, member))
        if _member_visibility(model, member) == "all friends":
            notices.append(
                f"{model['path']}:{member['line']}: all friends sets the legacy flags public, "
                "but API 1.11+ friend listing still requires a shared bucket."
            )
        record = {
            "_id": member["json_id"],
            "uid": SYSTEM_ID,
            "name": member["display_name"],
            "private": private,
            "preventTrusted": prevent_trusted,
        }
        if member.get("description"):
            record["desc"] = member["description"]
        if member["avatar_request"].get("color"):
            record["color"] = member["avatar_request"]["color"]
        if member["avatar_uuid"]:
            record["avatarUuid"] = member["avatar_uuid"]
        if member["buckets"]:
            record["buckets"] = list(member["buckets"])
        if member["field_values"]:
            record["info"] = {script_id: value for script_id, value, _line in member["field_values"]}
        if member.get("archived"):
            record["archived"] = True
            if member.get("archived_reason"):
                record["archivedReason"] = member["archived_reason"]
        members.append(record)

    groups = []
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        groups.append({
            "_id": anchor["json_id"],
            "uid": SYSTEM_ID,
            "name": anchor["name"],
            "parent": _group_parent(model, anchor, system),
            "members": _group_members(model, anchor),
        })

    notes = []
    for note in model["notes"]:
        owner = owners[note["script_id"]]
        notes.append({
            "_id": note["script_id"],
            "uid": SYSTEM_ID,
            "member": owner["json_id"],
            "title": "",
            "note": note["body"],
            "date": FIXED_MS,
            "supportMarkdown": False,
        })

    fields = []
    for index, field in enumerate(model["fields"]):
        fields.append({
            "_id": field["script_id"],
            "uid": SYSTEM_ID,
            "name": field["label"],
            "order": index,
            "type": 0,
            "private": True,
            "preventTrusted": True,
        })

    buckets = []
    for bucket in model["buckets"]:
        buckets.append({
            "_id": bucket["script_id"],
            "uid": SYSTEM_ID,
            "name": bucket["name"],
        })

    friends = []
    for index, friend in enumerate(model["friends"], 1):
        frienduid = f"synthetic-frienduid-{index:04d}"
        record = {
            "_id": f"synthetic-friend-{index:04d}",
            "uid": SYSTEM_ID,
            "frienduid": frienduid,
            "username": friend["name"],
            "buckets": list(friend["buckets"]),
        }
        if friend["trusted"] is not None:
            record["trusted"] = friend["trusted"]
        friends.append(record)
        notices.append(
            f"{model['path']}:{friend['line']}: friend {friend['name']} is an external account, "
            f"not a member. friends[]._id is {record['_id']}; frienduid is {frienduid}."
        )
        notices.append(
            f"{model['path']}:{friend['line']}: seeMembers and seeFront were not in the feed "
            "and were not given defaults."
        )

    statuses = []
    history = []
    history_index = 1
    for member in model["members"]:
        if member.get("fronting") is not True:
            continue
        history.append({
            "_id": f"synthetic-fh-{history_index:04d}",
            "uid": SYSTEM_ID,
            "member": member["json_id"],
            "custom": False,
            "live": True,
            "startTime": FIXED_MS,
        })
        history_index += 1
    for front in model["custom_fronts"]:
        record = {
            "_id": front["script_id"],
            "uid": SYSTEM_ID,
            "name": front["name"],
            "private": True,
            "preventTrusted": True,
        }
        if front.get("description"):
            record["desc"] = front["description"]
        statuses.append(record)
        if front.get("fronting") is True:
            history.append({
                "_id": f"synthetic-fh-{history_index:04d}",
                "uid": SYSTEM_ID,
                "member": front["script_id"],
                "custom": True,
                "live": True,
                "startTime": FIXED_MS,
            })
            history_index += 1

    export = {"users": users, "members": members}
    if groups:
        export["groups"] = groups
    if notes:
        export["notes"] = notes
    if fields:
        export["customFields"] = fields
    if buckets:
        export["privacyBuckets"] = buckets
    if friends:
        export["friends"] = friends
    if statuses:
        export["frontStatuses"] = statuses
    if history:
        export["frontHistory"] = history
    _validate(model, export)
    return export, notices


def _validate(model, export):
    """References that must resolve before any output file is replaced."""
    member_ids = [record["_id"] for record in export["members"]]
    if len(member_ids) != len(set(member_ids)):
        raise SimplyPluralError(f"{model['path']}: duplicate member id")
    if len(export["users"]) != 1 or export["users"][0]["_id"] != SYSTEM_ID:
        raise SimplyPluralError(f"{model['path']}: expected one owning user")
    known_members = set(member_ids)
    group_ids = {record["_id"] for record in export.get("groups") or []}
    for group in export.get("groups") or []:
        if group["parent"] != "root" and group["parent"] not in group_ids:
            raise SimplyPluralError(f"{model['path']}: group parent {group['parent']!r} is missing")
        for member_id in group["members"]:
            if member_id not in known_members:
                raise SimplyPluralError(f"{model['path']}: group member {member_id!r} is missing")
    field_ids = {record["_id"] for record in export.get("customFields") or []}
    for member in export["members"]:
        for field_id in member.get("info") or {}:
            if field_id not in field_ids:
                raise SimplyPluralError(f"{model['path']}: field value {field_id!r} has no definition")
    bucket_ids = {record["_id"] for record in export.get("privacyBuckets") or []}
    for member in export["members"]:
        for bucket_id in member.get("buckets") or []:
            if bucket_id not in bucket_ids:
                raise SimplyPluralError(f"{model['path']}: bucket {bucket_id!r} is missing")
    status_ids = {record["_id"] for record in export.get("frontStatuses") or []}
    for friend in export.get("friends") or []:
        if friend["frienduid"] == friend["_id"] or friend["frienduid"] == SYSTEM_ID:
            raise SimplyPluralError(f"{model['path']}: frienduid must be distinct")
        for bucket_id in friend.get("buckets") or []:
            if bucket_id not in bucket_ids:
                raise SimplyPluralError(f"{model['path']}: friend bucket {bucket_id!r} is missing")
    for note in export.get("notes") or []:
        if note["member"] not in known_members:
            raise SimplyPluralError(f"{model['path']}: note owner {note['member']!r} is missing")
    for row in export.get("frontHistory") or []:
        if row["custom"]:
            if row["member"] not in status_ids:
                raise SimplyPluralError(f"{model['path']}: custom front row {row['member']!r} is missing")
        elif row["member"] not in known_members:
            raise SimplyPluralError(f"{model['path']}: front row {row['member']!r} is missing")
        if "endTime" in row or row["live"] is not True:
            raise SimplyPluralError(f"{model['path']}: current front rows omit endTime and set live true")


def _replace_avatar_dir(parent, stem, staged_dir):
    dest = parent / f"{stem}-avatars"
    backup = parent / f".{stem}-avatars.previous"
    if backup.exists() and not dest.exists():
        os.replace(backup, dest)
    elif backup.exists():
        shutil.rmtree(backup)
    moved = False
    if dest.exists():
        os.replace(dest, backup)
        moved = True
    try:
        if staged_dir is not None:
            os.replace(staged_dir, dest)
    except Exception:
        if moved and not dest.exists() and backup.exists():
            os.replace(backup, dest)
        raise
    return backup if backup.exists() else None


def write_import_export(path, export, avatar_pngs):
    """Validate avatar file names, then replace this feed's JSON and PNG directory."""
    path = Path(path)
    expected = {record["_id"] for record in export["members"] if record.get("avatarUuid")}
    if set(avatar_pngs) != expected:
        raise SimplyPluralError(
            f"{path}: avatar files {sorted(avatar_pngs)} do not match members {sorted(expected)}"
        )
    text = json.dumps(export, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    staging = Path(tempfile.mkdtemp(prefix=f".{stem}-", dir=path.parent))
    try:
        staged_json = staging / path.name
        with open(staged_json, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        staged_avatars = None
        if avatar_pngs:
            staged_avatars = staging / f"{stem}-avatars"
            staged_avatars.mkdir()
            for member_id in sorted(avatar_pngs):
                (staged_avatars / f"{member_id}.png").write_bytes(avatar_pngs[member_id])
        backup = _replace_avatar_dir(path.parent, stem, staged_avatars)
        try:
            os.replace(staged_json, path)
        except Exception:
            dest = path.parent / f"{stem}-avatars"
            if backup is not None and backup.exists():
                if dest.exists():
                    shutil.rmtree(dest)
                os.replace(backup, dest)
            elif dest.exists():
                shutil.rmtree(dest)
            raise
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return path


def run():
    """Direct execution is not the importer. The engine owns the feed path."""
    print(
        "Use: python gen-import-engine.py --model simplyplural --scriptfspec <path>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(run())
