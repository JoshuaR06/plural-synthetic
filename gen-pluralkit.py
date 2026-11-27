#!/usr/bin/env python3
"""Proof-of-concept PluralKit export from the shared model feed.

Named gen-pluralkit.py (hyphen). gen-import-engine.py loads it. This module
does not parse the feed and does not write on import. The JSON is the native
version-2 owner export from PluralKit commit 22fa0682, not an API response.
There is no official JSON Schema for that export.

Short ids are five lowercase letters. UUIDs are RFC 4122 version 4 strings
from SHA-256 of a stable key. Timestamps are 2026-01-01T00:00:00Z. The clock
is not used.

Avatar URL fields stay null. gen-import-engine.py writes the PNG bytes beside
the JSON, named by member short id.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

FIXED_TIMESTAMP = "2026-01-01T00:00:00Z"
_ALPHABET = "abcdefghijklmnopqrstuvwxyz"

SYSTEM_PRIVACY = (
    "name_privacy",
    "avatar_privacy",
    "description_privacy",
    "banner_privacy",
    "pronoun_privacy",
    "member_list_privacy",
    "group_list_privacy",
    "front_privacy",
    "front_history_privacy",
)
MEMBER_PRIVACY = (
    "visibility",
    "name_privacy",
    "description_privacy",
    "banner_privacy",
    "birthday_privacy",
    "pronoun_privacy",
    "avatar_privacy",
    "metadata_privacy",
    "proxy_privacy",
    "alias_privacy",
)
GROUP_PRIVACY = (
    "name_privacy",
    "description_privacy",
    "banner_privacy",
    "icon_privacy",
    "list_privacy",
    "metadata_privacy",
    "visibility",
)


class PluralKitError(Exception):
    """The shared model cannot be written as this PluralKit cut."""


def _location(model, line, message):
    raise PluralKitError(f"{model['path']}:{line}: {message}")


def _uuid(key):
    raw = bytearray(hashlib.sha256(key.encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(raw)))


def _hid(key, used):
    """Five lowercase letters from SHA-256. The next salt is used when that id is already taken."""
    start = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    for salt in range(64):
        value = start + salt
        chars = []
        for _ in range(5):
            chars.append(_ALPHABET[value % 26])
            value //= 26
        hid = "".join(chars)
        if hid not in used:
            used.add(hid)
            return hid
    raise PluralKitError(f"no free short id for {key}")


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
    """One top-level System. Places and extra systems are rejected."""
    for anchor in model["anchors"]:
        if anchor["kind"] == "place":
            _location(model, anchor["line"], "Place anchors are not supported in this PluralKit cut")
    systems = [anchor for anchor in model["anchors"] if anchor["kind"] == "system"]
    if len(systems) != 1:
        line = systems[1]["line"] if len(systems) > 1 else 1
        _location(model, line, "this PluralKit cut requires exactly one System")
    system = systems[0]
    if system["parent_key"] is not None:
        _location(model, system["line"], "a nested System is not supported")
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        for ancestor in _ancestors(model, anchor)[1:]:
            if ancestor["kind"] != "group" and ancestor["key"] != system["key"]:
                _location(model, anchor["line"], "this Group is not inside the single System")
    return system


def _member_name(member):
    if member["generated"]:
        return f"L{member['line']}:{member['number']}"
    return member["name"]


def _resolved_visibility(model, member):
    found = []
    for occ in model["occurrences"]:
        if occ["member_key"] != member["key"]:
            continue
        if occ["visibility"] is not None:
            found.append(occ["visibility"])
        else:
            found.append(model.get("account_visibility"))
    if not found:
        _location(model, member["line"], "member has no occurrence")
    if len(set(found)) > 1:
        _location(model, member["line"], "member visibility conflicts across placements")
    return found[0]


def _pk_private(token):
    """Every supported feed audience becomes PluralKit private. Unknown tokens raise."""
    if token in (None, "self", "only you", "inherit", "trusted friends", "all friends", "selected people"):
        return "private"
    raise PluralKitError(f"unsupported visibility {token!r}")


def _privacy(keys):
    return {key: "private" for key in keys}


def _color(request):
    """Feed #RRGGBB becomes six lowercase hex digits. No color stays null. A leading # is not written."""
    color = request.get("color")
    if not color:
        return None
    if len(color) == 7 and color[0] == "#":
        return color[1:]
    raise PluralKitError(f"avatar color {color!r} is not #RRGGBB")


def _notices(model, system, member_by_key):
    """Supplied data this native export does not store. Members are still written."""
    notices = []
    account_name = model.get("account_name")
    if account_name and account_name != system["name"]:
        notices.append(
            f"account name {account_name!r} has no PluralKit field; "
            f"the system name is {system['name']!r}"
        )
    if model.get("account_email"):
        notices.append(
            f"account email {model['account_email']!r} has no PluralKit field"
        )
    if model.get("account_permission"):
        rendered = ",".join(model["account_permission"])
        notices.append(
            f"account permission {rendered} was not mapped to privacy or a role"
        )
    account_visibility = model.get("account_visibility")
    if account_visibility is not None:
        notices.append(
            f"account visibility {account_visibility!r} is exported as private"
        )
    for member in model["members"]:
        token = _resolved_visibility(model, member)
        if token == "trusted friends":
            notices.append(
                f"member {_member_name(member)!r} visibility 'trusted friends' "
                "is exported as private, which is narrower than trusted friends"
            )
        elif token not in (None, "self", "only you", "inherit") and token != account_visibility:
            notices.append(
                f"member {_member_name(member)!r} visibility {token!r} "
                "is exported as private"
            )
    by_key = {anchor["key"]: anchor for anchor in model["anchors"]}
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        parent = by_key.get(anchor["parent_key"])
        if parent and parent["kind"] == "group":
            notices.append(
                f"group {anchor['name']!r} is nested under {parent['name']!r}; "
                "PluralKit groups are flat, so that parent is not written"
            )
        if anchor.get("field_refs") or anchor.get("field_values"):
            notices.append(
                f"group {anchor['name']!r} custom-field associations have no PluralKit field"
            )
    for anchor in model["anchors"]:
        if anchor.get("note_refs"):
            rendered = ", ".join(anchor["note_refs"])
            kind = anchor["kind"]
            notices.append(
                f"{kind} {anchor['name']!r} note association {rendered} has no PluralKit field"
            )
    if model["notes"]:
        rendered = ", ".join(note["script_id"] for note in model["notes"])
        notices.append(f"notes have no PluralKit field: {rendered}")
    if model["fields"]:
        rendered = ", ".join(
            f"{field['script_id']} {field['label']!r}" for field in model["fields"]
        )
        notices.append(f"custom fields have no PluralKit field: {rendered}")
    for member in model["members"]:
        for script_id, value, _line in member.get("field_values") or []:
            notices.append(
                f"member {_member_name(member)!r} custom field {script_id} "
                f"value {value!r} has no PluralKit field"
            )
    for bucket in model["buckets"]:
        notices.append(
            f"privacy bucket {bucket['script_id']} {bucket['name']!r} has no PluralKit field"
        )
    for friend in model["friends"]:
        notices.append(
            f"friend {friend['script_id']} {friend['name']!r} has no PluralKit field"
        )
    for member in model["members"]:
        if member.get("buckets"):
            rendered = ", ".join(member["buckets"])
            notices.append(
                f"member {_member_name(member)!r} bucket assignment {rendered} "
                "has no PluralKit field"
            )
        if member.get("archived") or member.get("archived_reason"):
            reason = member.get("archived_reason")
            notices.append(
                f"member {_member_name(member)!r} archived "
                f"{str(bool(member.get('archived'))).lower()} reason {reason!r} "
                "has no PluralKit field"
            )
    for front in model["custom_fronts"]:
        notices.append(
            f"custom front {front['script_id']} {front['name']!r} is not a PluralKit member"
        )
    if model["relationships"]:
        notices.append("anchor relationships have no PluralKit field")
    imaged = [
        _member_name(member)
        for member in model["members"]
        if member["avatar_request"]["style"] != "none"
    ]
    if imaged:
        names = ", ".join(
            f"{_member_name(member)} ({member_by_key[member['key']]})"
            for member in model["members"]
            if member["avatar_request"]["style"] != "none"
        )
        notices.append(
            "native avatar_url fields are null; generated images are local sidecars "
            f"named by member short id, with no hosted URL: {names}"
        )
    return notices


def render_import_model(model):
    """Map the shared model to one version-2 export and console notices."""
    system = _require_supported_shape(model)
    used = set()
    system_hid = _hid(f"system:{system['key']}", used)
    member_hids = {}
    for member in model["members"]:
        hid = _hid(f"member:{member['key']}", used)
        member["json_id"] = hid
        member_hids[member["key"]] = hid
    group_hids = {}
    for anchor in model["anchors"]:
        if anchor["kind"] == "group":
            group_hids[anchor["key"]] = _hid(f"group:{anchor['key']}", used)

    members = []
    fronting = []
    for member in model["members"]:
        hid = member_hids[member["key"]]
        record = {
            "id": hid,
            "uuid": _uuid(f"pluralkit:member:{member['key']}"),
            "name": _member_name(member),
            "display_name": None,
            "color": _color(member["avatar_request"]),
            "birthday": None,
            "pronouns": None,
            "avatar_url": None,
            "webhook_avatar_url": None,
            "banner": None,
            "description": None,
            "created": FIXED_TIMESTAMP,
            "keep_proxy": False,
            "tts": False,
            "autoproxy_enabled": False,
            "message_count": 0,
            "last_message_timestamp": None,
            "proxy_tags": [],
            "aliases": [],
            "privacy": _privacy(MEMBER_PRIVACY),
        }
        _pk_private(_resolved_visibility(model, member))
        members.append(record)
        if member.get("fronting") is True:
            fronting.append(hid)

    groups = []
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        member_ids = []
        for occ in model["occurrences"]:
            if occ["anchor_key"] != anchor["key"]:
                continue
            member_ids.append(member_hids[occ["member_key"]])
        groups.append({
            "id": group_hids[anchor["key"]],
            "uuid": _uuid(f"pluralkit:group:{anchor['key']}"),
            "name": anchor["name"],
            "display_name": None,
            "description": None,
            "icon": None,
            "banner": None,
            "color": None,
            "created": FIXED_TIMESTAMP,
            "members": member_ids,
            "privacy": _privacy(GROUP_PRIVACY),
        })

    switches = []
    if fronting:
        switches.append({
            "timestamp": FIXED_TIMESTAMP,
            "members": fronting,
        })

    export = {
        "version": 2,
        "id": system_hid,
        "uuid": _uuid(f"pluralkit:system:{system['key']}"),
        "name": system["name"],
        "description": None,
        "tag": None,
        "pronouns": None,
        "avatar_url": None,
        "banner": None,
        "color": None,
        "created": FIXED_TIMESTAMP,
        "webhook_url": None,
        "privacy": _privacy(SYSTEM_PRIVACY),
        "config": {
            "timezone": "UTC",
            "pings_enabled": False,
            "latch_timeout": None,
            "member_default_private": True,
            "group_default_private": True,
            "show_private_info": False,
            "member_limit": 1000,
            "group_limit": 250,
            "case_sensitive_proxy_tags": False,
            "proxy_error_message_enabled": False,
            "hid_display_split": False,
            "hid_display_caps": False,
            "hid_list_padding": "off",
            "card_show_color_hex": False,
            "proxy_switch": "off",
            "name_format": "{name} {tag}",
            "description_templates": [],
        },
        "accounts": [],
        "members": members,
        "groups": groups,
        "switches": switches,
    }
    _validate(model, export)
    return export, _notices(model, system, member_hids)


def _validate(model, export):
    if export["version"] != 2:
        raise PluralKitError(f"{model['path']}: version must be 2")
    if export["accounts"] != []:
        raise PluralKitError(f"{model['path']}: this feed has no Discord accounts")
    member_ids = [row["id"] for row in export["members"]]
    if len(member_ids) != len(set(member_ids)):
        raise PluralKitError(f"{model['path']}: member short ids are not unique")
    known = set(member_ids)
    for row in export["groups"]:
        if len(row["members"]) != len(set(row["members"])):
            raise PluralKitError(f"{model['path']}: group {row['name']!r} repeats a member")
        missing = [hid for hid in row["members"] if hid not in known]
        if missing:
            raise PluralKitError(f"{model['path']}: group member {missing[0]} is missing")
    if len(export["switches"]) > 1:
        raise PluralKitError(f"{model['path']}: current fronters share one switch")
    for row in export["switches"]:
        missing = [hid for hid in row["members"] if hid not in known]
        if missing:
            raise PluralKitError(f"{model['path']}: switch member {missing[0]} is missing")
    for row in export["members"]:
        for key in ("avatar_url", "webhook_avatar_url", "banner"):
            if row[key] is not None:
                raise PluralKitError(f"{model['path']}: {key} must stay null in this cut")
    if export["avatar_url"] is not None or export["banner"] is not None or export["webhook_url"] is not None:
        raise PluralKitError(f"{model['path']}: system image and webhook fields must stay null")


def write_import_export(path, export, avatar_pngs):
    """Replace this feed's JSON and short-id PNG directory, or leave both in place."""
    path = Path(path)
    text = json.dumps(export, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    staging = Path(tempfile.mkdtemp(prefix=f".{stem}-", dir=path.parent))
    try:
        staged_json = staging / path.name
        with open(staged_json, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        staged_avatars = None
        if avatar_pngs is not None:
            known = {row["id"] for row in export["members"]}
            unknown = [key for key in avatar_pngs if key not in known]
            if unknown:
                raise PluralKitError(f"{path}: avatar {unknown[0]} is not a member short id")
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
            elif dest.exists() and staged_avatars is not None:
                shutil.rmtree(dest)
            raise
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return path


def _replace_avatar_dir(parent, stem, staged_dir):
    """Swap this feed's short-id PNG directory. Another target's directory is not in this parent."""
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


def run():
    print(
        "Use: python gen-import-engine.py --model pluralkit --scriptfspec <path>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(run())
