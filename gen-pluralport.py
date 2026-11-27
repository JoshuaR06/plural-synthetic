#!/usr/bin/env python3
"""Proof-of-concept PluralPort export from the shared model feed.

Named gen-pluralport.py (hyphen). gen-import-engine.py loads it. This module
does not parse the feed, does not read PB or SP JSON, and does not write on
import. There is no official JSON Schema in the captured specification; these
checks only enforce the shapes documented in docs/pluralport/.

File-local ids are RFC 4122 UUID version 4 strings derived from SHA-256 of a
stable key. The version nibble is set to 4 and the variant bits to RFC 4122.
The clock is not used. Timestamps are 2026-01-01T00:00:00Z.

Avatar PNG bytes come from gen-avatars.generate_avatar. They are stored on
Asset records as data_base64. No URL and no ZIP are written.
"""
import base64
import hashlib
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

FIXED_TIMESTAMP = "2026-01-01T00:00:00Z"
EXTENSION_NS = "org.thepluralbridge"


class PluralPortError(Exception):
    """The shared model cannot be written as this PluralPort cut."""


def _uuid(key):
    """Deterministic UUID version 4 for one stable key."""
    raw = bytearray(hashlib.sha256(key.encode("utf-8")).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(raw)))


def _location(model, line, message):
    raise PluralPortError(f"{model['path']}:{line}: {message}")


def _load_avatars():
    path = Path(__file__).resolve().parent / "gen-avatars.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_avatars", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    """One top-level System and its Groups. Places and relationships are rejected."""
    for anchor in model["anchors"]:
        if anchor["kind"] == "place":
            _location(model, anchor["line"], "Place anchors are not supported in this PluralPort cut")
    systems = [anchor for anchor in model["anchors"] if anchor["kind"] == "system"]
    if len(systems) != 1:
        line = systems[1]["line"] if len(systems) > 1 else 1
        _location(model, line, "this PluralPort cut requires exactly one System")
    system = systems[0]
    if system["parent_key"] is not None:
        _location(model, system["line"], "a nested System is not supported")
        if anchor["kind"] == "group" and (anchor.get("field_refs") or anchor.get("field_values")):
            _location(model, anchor["line"], "Group custom-field associations are not supported")
        if anchor["kind"] == "group":
            for ancestor in _ancestors(model, anchor)[1:]:
                if ancestor["kind"] != "group" and ancestor["key"] != system["key"]:
                    _location(model, anchor["line"], "this Group is not inside the single System")
    if model["relationships"]:
        _location(
            model, model["relationships"][0]["line"],
            "anchor relationships are not supported in this PluralPort cut",
        )


def _resolved_visibility(model, member):
    found = []
    for occ in model["occurrences"]:
        if occ["member_key"] != member["key"]:
            continue
        if occ["visibility"] is not None:
            found.append((occ["visibility"], "member"))
        else:
            found.append((model.get("account_visibility"), "account"))
    if not found:
        _location(model, member["line"], "member has no occurrence")
    if len({item[0] for item in found}) > 1:
        _location(model, member["line"], "member visibility conflicts across placements")
    return found[0]


def _privacy(feed_visibility, resolved_from):
    """Map a feed audience onto the spec's closed visibility set.

    self and only you are private. trusted friends is trusted. all friends
    is friends. selected people has no matching bucket, so visibility is
    unknown and the feed token stays in source. The original token is always
    kept in privacy.source.
    """
    token = feed_visibility
    if token in (None, "self", "only you", "inherit"):
        visibility = "private"
    elif token == "trusted friends":
        visibility = "trusted"
    elif token == "all friends":
        visibility = "friends"
    elif token == "selected people":
        visibility = "unknown"
    else:
        raise PluralPortError(f"unsupported visibility {token!r}")
    return {
        "visibility": visibility,
        "source": {"feed_visibility": token, "resolved_from": resolved_from},
    }


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


def _warning(code, message, record_type=None, record_id=None):
    return {
        "level": "warning",
        "code": code,
        "record_type": record_type,
        "record_id": record_id,
        "message": message,
        "count": 1,
    }


def _member_name(member):
    if member["generated"]:
        return f"L{member['line']}:{member['number']}"
    return member["name"]


def render_import_model(model):
    """Map the shared model to one OpenPlural 0.1 export and its warnings."""
    _require_supported_shape(model)
    owners = _note_owners(model)
    system = next(anchor for anchor in model["anchors"] if anchor["kind"] == "system")
    system_id = _uuid(f"system:{system['key']}")
    avatars = _load_avatars()
    warnings = []

    account_visibility = model.get("account_visibility")
    token, _origin = (account_visibility, "account")
    systems = [{
        "id": system_id,
        "name": system["name"],
        "display_name": None,
        "description": None,
        "parent_system_id": None,
        "archived": False,
        "privacy": _privacy(token, "account"),
        "settings": {},
        "extensions": {},
    }]

    members = []
    member_ids = {}
    assets = []
    periods = []
    for index, member in enumerate(model["members"]):
        member_id = _uuid(f"member:{member['key']}")
        member["json_id"] = member_id
        member_ids[member["key"]] = member_id
        feed_visibility, origin = _resolved_visibility(model, member)
        name = _member_name(member)
        record = {
            "id": member_id,
            "system_id": system_id,
            "name": name,
            "display_name": name,
            "is_custom_front": False,
            "archived": bool(member.get("archived")),
            "created_at": FIXED_TIMESTAMP,
            "sort_order": index,
            "privacy": _privacy(feed_visibility, origin),
            "extensions": {},
        }
        color = member["avatar_request"].get("color")
        if color:
            record["color"] = color
        if member.get("description"):
            record["description"] = member["description"]
        if member.get("archived_reason"):
            record["extensions"] = {
                EXTENSION_NS: {"archived_reason": member["archived_reason"]},
            }
            warnings.append(_warning(
                "archive_reason_preserved_in_extension",
                f"Archive reason for {name} has no core Member field and is in "
                f"extensions.{EXTENSION_NS}.archived_reason.",
                "Member",
                member_id,
            ))
        request = member["avatar_request"]
        if request["style"] != "none":
            result = avatars.generate_avatar(
                request["style"], member_id,
                width=request["width"], height=request["height"], color=request["color"],
            )
            asset_id = _uuid(f"asset:{member['key']}")
            encoded = base64.b64encode(result.png).decode("ascii")
            assets.append({
                "id": asset_id,
                "kind": "avatar",
                "mime_type": result.mime_type,
                "file_name": f"{name}.png",
                "uri": None,
                "data_base64": encoded,
                "data_uri": None,
                "size_bytes": len(result.png),
                "sha256": result.sha256,
                "width": result.width,
                "height": result.height,
            })
            record["avatar_asset_id"] = asset_id
        members.append(record)
        if member.get("fronting") is True:
            periods.append({
                "id": _uuid(f"front:{member['key']}"),
                "system_id": system_id,
                "started_at": FIXED_TIMESTAMP,
                "ended_at": None,
                "assignments": [{
                    "member_id": member_id,
                    "front_role": "member",
                }],
                "source_kind": "unknown",
            })

    for front in model["custom_fronts"]:
        front_id = _uuid(f"custom-front:{front['script_id']}")
        record = {
            "id": front_id,
            "system_id": system_id,
            "name": front["name"],
            "display_name": front["name"],
            "is_custom_front": True,
            "archived": False,
            "created_at": FIXED_TIMESTAMP,
            "sort_order": len(members),
            "privacy": _privacy(account_visibility, "account"),
            "extensions": {EXTENSION_NS: {"script_id": front["script_id"]}},
        }
        if front.get("description"):
            record["description"] = front["description"]
        members.append(record)
        if front.get("fronting") is True:
            periods.append({
                "id": _uuid(f"front:custom:{front['script_id']}"),
                "system_id": system_id,
                "started_at": FIXED_TIMESTAMP,
                "ended_at": None,
                "assignments": [{
                    "member_id": front_id,
                    "front_role": "custom_status",
                }],
                "source_kind": "unknown",
            })

    groups = []
    group_ids = {}
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        group_id = _uuid(f"group:{anchor['key']}")
        group_ids[anchor["key"]] = group_id
        anchor["json_id"] = group_id
    memberships = []
    for anchor in model["anchors"]:
        if anchor["kind"] != "group":
            continue
        parent = anchor["parent_key"]
        parent_id = group_ids.get(parent) if parent in group_ids else None
        groups.append({
            "id": group_ids[anchor["key"]],
            "system_id": system_id,
            "name": anchor["name"],
            "parent_group_id": parent_id,
            "sort_order": len(groups),
            "extensions": {EXTENSION_NS: {"script_id": anchor.get("script_id")}},
        })
        position = 0
        for occ in model["occurrences"]:
            if occ["anchor_key"] != anchor["key"]:
                continue
            memberships.append({
                "id": _uuid(f"membership:{anchor['key']}:{occ['member_key']}"),
                "group_id": group_ids[anchor["key"]],
                "member_id": member_ids[occ["member_key"]],
                "sort_order": position,
            })
            position += 1

    fields = []
    field_ids = {}
    for index, field in enumerate(model["fields"]):
        field_id = _uuid(f"field:{field['script_id']}")
        field_ids[field["script_id"]] = field_id
        fields.append({
            "id": field_id,
            "system_id": system_id,
            "name": field["label"],
            "field_type": "text",
            "supports_markdown": False,
            "sort_order": index,
            "privacy": _privacy(account_visibility, "account"),
            "extensions": {EXTENSION_NS: {"script_id": field["script_id"]}},
        })

    values = []
    for member in model["members"]:
        for script_id, value, _line in member.get("field_values") or []:
            values.append({
                "id": _uuid(f"value:{script_id}:{member['key']}"),
                "field_id": field_ids[script_id],
                "subject_type": "member",
                "subject_id": member_ids[member["key"]],
                "value": value,
            })

    notes = []
    for note in model["notes"]:
        owner = owners[note["script_id"]]
        notes.append({
            "id": _uuid(f"note:{note['script_id']}"),
            "system_id": system_id,
            "member_id": member_ids[owner["key"]],
            "title": None,
            "body": note["body"],
            "created_at": FIXED_TIMESTAMP,
            "extensions": {EXTENSION_NS: {"script_id": note["script_id"]}},
        })

    extension = {
        "account": {
            "name": model.get("account_name"),
            "email": model.get("account_email"),
            "permission": model.get("account_permission"),
            "visibility": account_visibility,
        },
        "system_script_id": system.get("script_id"),
    }
    if model.get("buckets"):
        extension["privacy_buckets"] = [
            {"script_id": bucket["script_id"], "name": bucket["name"]}
            for bucket in model["buckets"]
        ]
    if model.get("friends"):
        extension["friends"] = [
            {
                "script_id": friend["script_id"],
                "name": friend["name"],
                "trusted": friend.get("trusted"),
                "bucket_script_ids": list(friend.get("buckets") or []),
            }
            for friend in model["friends"]
        ]
    bucket_members = [
        {
            "member_id": member_ids[member["key"]],
            "member_name": _member_name(member),
            "bucket_script_ids": list(member["buckets"]),
        }
        for member in model["members"] if member.get("buckets")
    ]
    if bucket_members:
        extension["member_buckets"] = bucket_members

    warnings.append(_warning(
        "account_preserved_in_extension",
        "Account name and email have no core System field and are in "
        f"extensions.{EXTENSION_NS}.account.",
        "System",
        system_id,
    ))
    if model.get("account_permission"):
        rendered = ",".join(model["account_permission"])
        warnings.append(_warning(
            "permission_not_mapped",
            f"Account permission {rendered} was not mapped to a role or visibility. "
            f"It is in extensions.{EXTENSION_NS}.account.permission.",
            "System",
            system_id,
        ))
    if model.get("buckets") or model.get("friends") or bucket_members:
        warnings.append(_warning(
            "sharing_preserved_in_extension",
            "Friends and privacy buckets stay in "
            f"extensions.{EXTENSION_NS} because the captured sharing module has no record "
            "definition. The sharing module is not declared.",
            "System",
            system_id,
        ))

    modules = ["systems", "members"]
    export = {
        "openplural_version": "0.1",
        "exported_at": FIXED_TIMESTAMP,
        "producer": {
            "app": "plural-synthetic",
            "app_version": "0.0.0-poc",
            "exporter_version": "0.0.0-poc",
        },
        "systems": systems,
        "members": members,
    }
    if groups:
        modules.append("groups")
        export["groups"] = groups
        export["group_memberships"] = memberships
    if fields or values:
        modules.append("custom_fields")
        export["custom_fields"] = fields
        export["custom_field_values"] = values
    if notes:
        modules.append("notes")
        export["notes"] = notes
    if assets:
        modules.append("assets")
        export["assets"] = assets
    if periods:
        modules.append("front_periods")
        export["front_periods"] = periods
    export["capabilities"] = {"modules": modules}
    # capabilities is built last so the module list matches the keys written above.
    # Reorder the envelope to the documented key order.
    ordered = {
        "openplural_version": export["openplural_version"],
        "exported_at": export["exported_at"],
        "producer": export["producer"],
        "capabilities": export["capabilities"],
        "systems": export["systems"],
        "members": export["members"],
    }
    for key in (
        "groups", "group_memberships", "custom_fields", "custom_field_values",
        "notes", "assets", "front_periods",
    ):
        if key in export:
            ordered[key] = export[key]
    ordered["extensions"] = {EXTENSION_NS: extension}
    ordered["warnings"] = warnings
    _validate(model, ordered)
    return ordered, warnings


def _validate(model, export):
    """File-local references and asset bytes, before any output is replaced."""
    if export["openplural_version"] != "0.1":
        raise PluralPortError(f"{model['path']}: openplural_version must be 0.1")
    modules = export["capabilities"]["modules"]
    expected = []
    for name in ("systems", "members", "groups", "custom_fields", "notes", "assets", "front_periods"):
        if name == "groups" and export.get("groups"):
            expected.append(name)
        elif name != "groups" and export.get(name):
            expected.append(name)
    if modules != expected:
        raise PluralPortError(f"{model['path']}: capabilities.modules {modules} != {expected}")
    if "sharing" in modules or "sharing" in export:
        raise PluralPortError(f"{model['path']}: sharing module is not implemented")
    system_ids = {row["id"] for row in export["systems"]}
    member_ids = {row["id"] for row in export["members"]}
    group_ids = {row["id"] for row in export.get("groups") or []}
    field_ids = {row["id"] for row in export.get("custom_fields") or []}
    asset_ids = {row["id"] for row in export.get("assets") or []}
    for row in export["members"]:
        if row["system_id"] not in system_ids:
            raise PluralPortError(f"{model['path']}: member system {row['system_id']} is missing")
        avatar = row.get("avatar_asset_id")
        if avatar is not None and avatar not in asset_ids:
            raise PluralPortError(f"{model['path']}: avatar {avatar} is missing")
    for row in export.get("groups") or []:
        if row["system_id"] not in system_ids:
            raise PluralPortError(f"{model['path']}: group system is missing")
        parent = row.get("parent_group_id")
        if parent is not None and parent not in group_ids:
            raise PluralPortError(f"{model['path']}: parent group {parent} is missing")
    for row in export.get("group_memberships") or []:
        if row["group_id"] not in group_ids or row["member_id"] not in member_ids:
            raise PluralPortError(f"{model['path']}: group membership does not resolve")
    for row in export.get("custom_field_values") or []:
        if row["field_id"] not in field_ids:
            raise PluralPortError(f"{model['path']}: custom field value has no definition")
        if row["subject_type"] != "member" or row["subject_id"] not in member_ids:
            raise PluralPortError(f"{model['path']}: custom field subject does not resolve")
    for row in export.get("notes") or []:
        if row["member_id"] not in member_ids:
            raise PluralPortError(f"{model['path']}: note member does not resolve")
    for row in export.get("front_periods") or []:
        if row.get("ended_at") is not None:
            raise PluralPortError(f"{model['path']}: this cut only writes open front periods")
        if len(row["assignments"]) != 1:
            raise PluralPortError(f"{model['path']}: a front period needs one assignment")
        if row["assignments"][0]["member_id"] not in member_ids:
            raise PluralPortError(f"{model['path']}: front assignment does not resolve")
    for row in export.get("assets") or []:
        raw = base64.b64decode(row["data_base64"])
        if len(raw) != row["size_bytes"]:
            raise PluralPortError(f"{model['path']}: asset size does not match bytes")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise PluralPortError(f"{model['path']}: asset sha256 does not match bytes")
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise PluralPortError(f"{model['path']}: asset is not a PNG")
    for warning in export["warnings"]:
        record_id = warning.get("record_id")
        if record_id is not None and record_id not in system_ids | member_ids | asset_ids:
            raise PluralPortError(f"{model['path']}: warning record {record_id} is missing")


def write_import_export(path, export):
    """Validate, then replace only this feed's PluralPort JSON."""
    path = Path(path)
    text = json.dumps(export, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{path.stem}-", dir=path.parent))
    try:
        temporary = staging / path.name
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if staging.exists():
            import shutil
            shutil.rmtree(staging, ignore_errors=True)
    return path


def run():
    """Direct execution is not the importer."""
    print(
        "Use: python gen-import-engine.py --model pluralport --scriptfspec <path>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(run())
