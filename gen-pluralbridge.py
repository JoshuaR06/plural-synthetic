#!/usr/bin/env python3
"""Canonical PluralBridge system-model serialization, writing, and fixture checks.

This file is named gen-pluralbridge.py (hyphen). It is not a valid import
identifier; generate.py loads it with importlib.util.spec_from_file_location.
Importing this module does not write files or start generation.

Model construction and topology validation for the twelve examples stay in
system_models.py. This module serializes those exports (insertion-order JSON,
LF), writes the --out copy and optional sample-output sync, and compares them
to committed fixtures. example-shape.json is never written.

Proof-of-concept feed imports are a separate entry point (render_import_model,
write_import_export). They reuse serialization and reference checks. They do
not parse the feed and do not require one of the twelve topologies.
gen-import-engine.py owns parsing and dispatch. Do not import it here.

Do not import generate.py from here: Aurora and Simply Plural emission live
there and must not mix dump() key-sorting into canonical models.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

import system_models

# Twelve example filenames. Never includes example-shape.json.
SYSTEM_MODEL_FIXTURE_NAMES = system_models.SYSTEM_MODEL_FILENAMES
SYSTEM_MODEL_EXPORT_KIND = system_models.EXPORT_KIND
SYSTEM_MODEL_OUT_DIRNAME = "pluralbridge-system-models"
SYSTEM_MODEL_SAMPLE_OUTPUT_DIR = Path("sample-output") / SYSTEM_MODEL_OUT_DIRNAME
SYSTEM_MODEL_FIXTURES_DIR = Path("fixtures") / SYSTEM_MODEL_OUT_DIRNAME
EXAMPLE_SHAPE_FILENAME = "example-shape.json"
FIXTURE_DOC_NAMES = {"README.md", "Canonical Model Minimum Base.txt"}


def dump_system_model(obj):
    """Insertion-order JSON for canonical models. Aurora/edge output still uses generate.dump()."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def write_json(path, text):
    """Write UTF-8 text with LF newlines so Windows checkout does not scramble fixtures."""
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def generate_system_models():
    """Build and validate the twelve canonical models from Python topologies.

    Filename order is part of the fixture contract. exampleId is derived from the
    filename prefix (example-001-...), not from the topology's display name.
    """
    built = system_models.build_all()
    assert list(built) == SYSTEM_MODEL_FIXTURE_NAMES, list(built)
    for name, obj in built.items():
        expected_example_id = name.split("-", 2)[0] + "-" + name.split("-", 2)[1]
        assert obj["pluralBridgeExport"]["exampleId"] == expected_example_id, name
        system_models.validate_export(obj, name)
    return built


def write_system_model_exports(target, exports):
    """Write the twelve generated example JSON files under target/.

    Only names in SYSTEM_MODEL_FIXTURE_NAMES are written. example-shape.json is
    illustrative and is never generated or overwritten, including during sample-output sync.
    """
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for name, obj in exports.items():
        write_json(target / name, dump_system_model(obj))


def load_canonical_system_models(repo_root):
    """Load committed canonical JSON for complete comparison with generated output."""
    fixtures_root = Path(repo_root) / SYSTEM_MODEL_FIXTURES_DIR
    loaded = {}
    for name in SYSTEM_MODEL_FIXTURE_NAMES:
        obj = json.loads((fixtures_root / name).read_text(encoding="utf-8"))
        loaded[name] = obj
    return loaded


def write_system_model_fixtures(out, exports):
    """Write generated system-model JSON under <out>/pluralbridge-system-models/.

    This is the --out copy used for comparison. It does not update committed fixtures.
    """
    write_system_model_exports(Path(out) / SYSTEM_MODEL_OUT_DIRNAME, exports)


def sync_system_model_sample_output(repo_root, exports):
    """Refresh sample-output/pluralbridge-system-models from generated exports.

    Opt-in via --sync-system-model-sample-output. Committed fixtures/ are updated
    separately; this flag must not be pointed at fixtures or used to rewrite example-shape.json.
    """
    write_system_model_exports(Path(repo_root) / SYSTEM_MODEL_SAMPLE_OUTPUT_DIR, exports)


def check_system_model_fixtures(repo_root, out, generated_exports):
    """Generated canonical models must match committed fixtures completely (objects and
    serialized text), keep independent topology checks, and leave example-shape.json alone.

    Fixtures/ is an exact file set: the twelve examples plus README and Canonical Model
    Minimum Base.txt. Sample-output may also contain example-shape.json, which is compared
    against nothing and must not be treated as a thirteenth model. Object equality and
    LF-serialized text must both match; dumping with sort_keys would fail this check.
    """
    src = Path(repo_root) / SYSTEM_MODEL_FIXTURES_DIR
    mirror = Path(repo_root) / SYSTEM_MODEL_SAMPLE_OUTPUT_DIR
    expected = set(SYSTEM_MODEL_FIXTURE_NAMES)
    fixture_allowed = expected | FIXTURE_DOC_NAMES
    found_src = {p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file()}
    assert found_src == fixture_allowed, (
        f"fixtures/pluralbridge-system-models: unexpected {sorted(found_src - fixture_allowed)}, "
        f"missing {sorted(fixture_allowed - found_src)}")
    found_mirror = {p.relative_to(mirror).as_posix() for p in mirror.rglob("*") if p.is_file()}
    missing_mirror = expected - found_mirror
    assert not missing_mirror, f"sample-output/pluralbridge-system-models missing {sorted(missing_mirror)}"
    extra_examples = sorted(
        name for name in found_mirror
        if name.startswith("example-") and name.endswith(".json")
        and name not in expected and name != EXAMPLE_SHAPE_FILENAME
    )
    assert not extra_examples, f"sample-output has unexpected canonical JSON {extra_examples}"
    canonical = load_canonical_system_models(repo_root)
    for name in SYSTEM_MODEL_FIXTURE_NAMES:
        generated_obj = generated_exports[name]
        generated_text = (Path(out) / SYSTEM_MODEL_OUT_DIRNAME / name).read_text(encoding="utf-8")
        fixture_text = (src / name).read_text(encoding="utf-8")
        assert dump_system_model(generated_obj) == generated_text, (
            f"{name}: written output drifted from generated object")
        assert generated_obj == canonical[name], f"{name}: generated object diverged from canonical fixture"
        assert generated_text == fixture_text, f"{name}: generated text diverged from canonical fixture"
        header = generated_obj["pluralBridgeExport"]
        assert header.get("exportKind") == SYSTEM_MODEL_EXPORT_KIND, f"{name}: exportKind must be {SYSTEM_MODEL_EXPORT_KIND!r}"
        assert str(header.get("modelingNote", "")).startswith("Synthetic"), f"{name}: modelingNote must start with 'Synthetic'"
        system_models.validate_export(canonical[name], f"fixture {name}")
        committed = mirror / name
        assert committed.exists() and committed.read_text(encoding="utf-8") == generated_text, (
            f"sample-output/pluralbridge-system-models/{name} is stale: run generate.py --sync-system-model-sample-output")


def emit_system_models(repo_root, out, sync_sample_output=False):
    """Build and write the twelve canonical models under --out; optionally sync sample-output.

    Called from generate.py after Aurora/edge emission. Does not wipe --out.
    Fixture comparison is a separate call so Aurora check() still runs first.
    """
    exports = generate_system_models()
    write_system_model_fixtures(out, exports)
    if sync_sample_output:
        sync_system_model_sample_output(repo_root, exports)
    return exports


class ImportRenderError(Exception):
    """A parsed feed cannot be written as PluralBridge JSON without inventing fields."""


def _explicit_or_inherit(value):
    """None means the feed omitted the setting. Permission values are arrays.

    An explicit permission type named inherit stays in the array. It is not
    rewritten to mode inherit. The permission type all is not expanded.
    """
    if value is None:
        return dict(system_models.INHERIT_SETTING)
    if isinstance(value, (list, tuple)):
        return {"mode": "explicit", "value": list(value)}
    return {"mode": "explicit", "value": value}


def _gap(model, line, message):
    return f"{model['path']}:{line}: {message}"


def render_import_model(model):
    """Map a target-independent feed model to one PluralBridge account document.

    Does not parse text and does not call assemble(). Empty notes, custom fields,
    relationships, and front history are omitted. Account name, email, permission,
    and visibility are serialized. Anchor-level permission and visibility still
    have no JSON field and are reported as gaps. Username is not invented.
    """
    gaps = []

    used_ids = set()
    anchor_json_id = {}
    counters = {"system": 0, "group": 0, "place": 0}
    for anchor in model["anchors"]:
        if anchor["script_id"]:
            json_id = anchor["script_id"]
        else:
            counters[anchor["kind"]] += 1
            json_id = f"{anchor['kind']}-{counters[anchor['kind']]:03d}"
        if json_id in used_ids:
            raise ImportRenderError(
                f"{model['path']}:{anchor['line']}: anchor id {json_id!r} collides with another id"
            )
        used_ids.add(json_id)
        anchor_json_id[anchor["key"]] = json_id
        for setting_name, stored in (
            ("Permission", anchor.get("permission")),
            ("Visibility", anchor.get("visibility")),
        ):
            if stored is not None:
                value, line = stored
                gaps.append(_gap(
                    model, line,
                    f"Anchor {setting_name} {value!r} has no approved JSON field and was not serialized.",
                ))
        if anchor.get("field_values"):
            gaps.append(_gap(
                model, anchor["field_values"][0][2],
                "Anchor field values have no PluralBridge field and were not serialized.",
            ))

    for member in model["members"]:
        if member.get("archived") is not None or member.get("archived_reason"):
            gaps.append(_gap(
                model, member.get("archived_line") or member["line"],
                f"Member archive state for {member.get('name') or member.get('number')} "
                "has no PluralBridge mapping in this proof of concept and was not serialized.",
            ))
        if member.get("field_values"):
            gaps.append(_gap(
                model, member["field_values"][0][2],
                "Member field values have no PluralBridge mapping in this proof of concept "
                "and were not serialized.",
            ))
        if member.get("buckets"):
            gaps.append(_gap(
                model, member["line"],
                "Member privacy buckets have no PluralBridge mapping in this proof of concept "
                "and were not serialized.",
            ))
        if member.get("description"):
            gaps.append(_gap(
                model, member["line"],
                "Member description has no PluralBridge mapping in this proof of concept "
                "and was not serialized.",
            ))
    for bucket in model.get("buckets") or []:
        gaps.append(_gap(
            model, bucket["line"],
            f"Privacy bucket {bucket['name']!r} has no PluralBridge mapping in this proof of concept "
            "and was not serialized.",
        ))
    for friend in model.get("friends") or []:
        gaps.append(_gap(
            model, friend["line"],
            f"Friend {friend['name']!r} has no PluralBridge mapping in this proof of concept "
            "and was not serialized.",
        ))
    for front in model.get("custom_fronts") or []:
        gaps.append(_gap(
            model, front["line"],
            f"Custom front {front['name']!r} has no PluralBridge mapping in this proof of concept "
            "and was not serialized.",
        ))

    member_json_id = {}
    display_names = {}
    named_index = 0
    for member in model["members"]:
        if member["generated"]:
            anchor_id = anchor_json_id[member["anchor_key"]]
            number = member["number"]
            line = member["line"]
            member_id = f"member-{anchor_id}-L{line}-{number}"
            display_name = f"{anchor_id}:L{line}:{number}"
        else:
            named_index += 1
            member_id = f"member-{named_index:03d}"
            display_name = member["name"]
        if member_id in used_ids:
            raise ImportRenderError(
                f"{model['path']}:{member['line']}: member id {member_id!r} collides with another id"
            )
        if display_name in display_names:
            previous = display_names[display_name]
            raise ImportRenderError(
                f"{model['path']}:{member['line']}: display name {display_name!r} "
                f"collides with {model['path']}:{previous}"
            )
        used_ids.add(member_id)
        display_names[display_name] = member["line"]
        member_json_id[member["key"]] = member_id
        member["json_id"] = member_id
        member["display_name"] = display_name

    field_json_id = {field["script_id"]: field["script_id"] for field in model["fields"]}
    fields_by_name = {}
    for field in model["fields"]:
        fields_by_name.setdefault(field["label"], []).append(field)
    for label, rows in fields_by_name.items():
        if len(rows) > 1:
            lines = ", ".join(f"{model['path']}:{row['line']}" for row in rows)
            raise ImportRenderError(
                f"custom field label {label!r} is defined more than once ({lines})"
            )

    relationship_field_ids = {}
    for rel in model["relationships"]:
        label = rel["label"]
        if label in relationship_field_ids:
            continue
        existing = fields_by_name.get(label)
        if existing:
            relationship_field_ids[label] = existing[0]["script_id"]
            continue
        json_id = f"field-{label}"
        suffix = 2
        while json_id in used_ids or json_id in field_json_id:
            json_id = f"field-{label}-{suffix}"
            suffix += 1
        relationship_field_ids[label] = json_id
        field_json_id[json_id] = json_id
        used_ids.add(json_id)

    shared_members = []
    for member in model["members"]:
        fronting = member["fronting"]
        if fronting is None:
            fronting = False
        member_rec = {
            "memberId": member["json_id"],
            "displayName": member["display_name"],
            "isArchived": False,
        }
        if member.get("avatar_config"):
            member_rec["config"] = member["avatar_config"]
        shared_members.append(system_models._shape_member(
            member_rec,
            member["field_refs"],
            member["note_refs"],
            fronting,
        ))

    shaped_notes = []
    for note in model["notes"]:
        shaped = system_models._id_first(
            {"noteId": note["script_id"], "body": note["body"]},
            "noteId",
            extra_last=("visibility", "permissions"),
        )
        system_models._ensure_inherit_settings(shaped)
        shaped_notes.append(shaped)

    shaped_fields = []
    for field in model["fields"]:
        shaped_fields.append(system_models._shape_custom_field(
            {"fieldId": field["script_id"], "fieldName": field["label"]}
        ))
    for rel in model["relationships"]:
        json_id = relationship_field_ids[rel["label"]]
        if any(field["fieldId"] == json_id for field in shaped_fields):
            continue
        shaped_fields.append(system_models._shape_custom_field(
            {"fieldId": json_id, "fieldName": rel["label"]}
        ))

    shaped_anchors = []
    for anchor in model["anchors"]:
        kind = anchor["kind"]
        id_field = system_models.ANCHOR_ID_FIELDS[kind]
        rec = {id_field: anchor_json_id[anchor["key"]], "name": anchor["name"]}
        if anchor.get("avatar_config"):
            rec["config"] = anchor["avatar_config"]
        shaped_anchors.append(system_models._shape_anchor(
            rec, kind, field_ids=anchor["field_refs"] or None,
        ))

    occurrences = {}
    for occ in model["occurrences"]:
        occurrences.setdefault(occ["anchor_key"], []).append({
            "memberId": member_json_id[occ["member_key"]],
            "visibility": _explicit_or_inherit(occ["visibility"]),
            "permissions": _explicit_or_inherit(occ["permission"]),
        })

    children = {}
    roots = []
    for anchor in model["anchors"]:
        parent = anchor["parent_key"]
        if parent is None:
            roots.append(anchor["key"])
        else:
            children.setdefault(parent, []).append(anchor["key"])

    def tree_node(key):
        return {
            "anchorId": anchor_json_id[key],
            "members": list(occurrences.get(key, [])),
            "children": [tree_node(child) for child in children.get(key, [])],
        }

    relationships = []
    for index, rel in enumerate(model["relationships"], 1):
        target = None if rel["target_key"] is None else anchor_json_id[rel["target_key"]]
        relationships.append(system_models._shape_relationship(
            {
                "sourceAnchorId": anchor_json_id[rel["source_key"]],
                "fieldId": relationship_field_ids[rel["label"]],
                "targetAnchorId": target,
            },
            index,
        ))

    stem = model["stem"]
    account_obj = {
        "config": _account_avatar_config(model),
        "accountId": "account-001",
        "displayName": model["account_name"],
        "email": model["account_email"],
        "status": "Active",
        "permissions": _explicit_or_inherit(model.get("account_permission")),
        "visibility": _explicit_or_inherit(model.get("account_visibility")),
    }
    collections = {
        "members": shared_members,
        "notes": shaped_notes,
        "customFields": shaped_fields,
        "anchors": shaped_anchors,
        "tree": [tree_node(key) for key in roots],
        "relationships": relationships,
        "frontHistory": [],
    }
    for key in system_models.ACCOUNT_COLLECTION_ORDER:
        if key in ("members", "anchors", "tree") or collections[key]:
            account_obj[key] = collections[key]

    export = {
        "account": account_obj,
        "audit": dict(system_models.FIXED_AUDIT),
        "pluralBridgeExport": {
            "exampleId": f"import-{stem}",
            "exampleName": f"Import of {stem}",
            "exportKind": system_models.EXPORT_KIND,
            "exportVersion": system_models.EXPORT_VERSION,
            "modelingNote": (
                "Synthetic proof-of-concept import from a model feed. "
                "Not one of the twelve canonical examples."
            ),
        },
        "provenance": {
            "lossyMappings": [],
            "source": "synthetic",
            "sourceGenerator": "plural-synthetic-import-poc",
            "sourceIdsPreserved": True,
        },
    }
    return export, gaps


def _account_avatar_config(model):
    """Global defaults only. Anchor and member overrides stay on those records."""
    source = model.get("account_config") or {
        "avatar-width": 64, "avatar-height": 64, "avatar": "none",
    }
    config = {
        "avatar-width": source["avatar-width"],
        "avatar-height": source["avatar-height"],
        "avatar": source["avatar"],
    }
    if "color" in source:
        config["color"] = source["color"]
    return config


def _reject_occurrence_config(nodes, name):
    for node in nodes:
        for occ in node.get("members") or []:
            if "config" in occ:
                raise ImportRenderError(f"{name}: member occurrence must not carry avatar config")
        _reject_occurrence_config(node.get("children") or [], name)


def check_import_export(export, name="import"):
    """Schema and reference checks for a feed import.

    Does not call validate_topology: that function only accepts the twelve
    canonical exampleId values. Feed imports omit username; the twelve-example
    schema check still requires it, so that check sees a copy.
    """
    account = export["account"]
    if "username" in account:
        raise ImportRenderError(f"{name}: feed import must not invent username")
    schema_export = dict(export)
    schema_account = dict(account)
    schema_account["username"] = "not-part-of-feed-import"
    schema_export["account"] = schema_account
    system_models.validate_schema(schema_export, name)
    system_models.validate_unique_memberships(export, name)
    system_models.validate_references(export, name)
    for key in ("permissions", "visibility"):
        setting = account.get(key)
        if not isinstance(setting, dict) or "mode" not in setting:
            raise ImportRenderError(f"{name}: account.{key} must be a setting object")
        if setting["mode"] == "explicit" and key == "permissions" and not isinstance(setting.get("value"), list):
            raise ImportRenderError(f"{name}: explicit account permissions must be an array")
        if setting["mode"] == "inherit" and setting != system_models.INHERIT_SETTING:
            raise ImportRenderError(f"{name}: account.{key} inherit syntax")
    account = export["account"]
    for forbidden in ("privacyBuckets", "visibilityScopes", "memberships"):
        if forbidden in account:
            raise ImportRenderError(f"{name}: {forbidden} is not an export collection")
    if "frontHistory" in account:
        raise ImportRenderError(f"{name}: this proof of concept does not emit frontHistory")
    config = account.get("config")
    if not isinstance(config, dict):
        raise ImportRenderError(f"{name}: account.config is required")
    for key in ("avatar-width", "avatar-height", "avatar"):
        if key not in config:
            raise ImportRenderError(f"{name}: account.config missing {key}")
    if config["avatar"] not in ("none", "solid", "crosshatch"):
        raise ImportRenderError(f"{name}: account.config avatar is invalid")
    for key in ("avatar-width", "avatar-height"):
        if type(config[key]) is not int or config[key] < 1:
            raise ImportRenderError(f"{name}: account.config {key} must be a positive integer")
    _reject_occurrence_config(account.get("tree") or [], name)


def _replace_avatar_dir(parent, stem, staged_dir):
    """Swap this feed's avatar directory. Another feed's directory is not touched.

    staged_dir None removes the directory. A failure restores the previous one.
    """
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


def write_import_export(path, export, avatar_pngs=None):
    """Validate, then replace the JSON and this feed's avatar directory.

    avatar_pngs maps memberId to PNG bytes. An empty dict removes a previous
    avatar directory for this stem. None leaves any existing avatar directory
    alone. Files are staged before the previous output is replaced.
    """
    check_import_export(export, name=str(path))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dump_system_model(export)
    if avatar_pngs is None:
        temporary = path.with_name(path.name + ".partial")
        try:
            write_json(temporary, text)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return path

    stem = path.stem
    for member_id in avatar_pngs:
        if not member_id or Path(member_id).name != member_id or member_id in (".", ".."):
            raise ImportRenderError(f"{path}: avatar filename {member_id!r} is not a member id")
    staging = Path(tempfile.mkdtemp(prefix=f".{stem}-", dir=path.parent))
    staged_avatars = None
    try:
        staged_json = staging / path.name
        write_json(staged_json, text)
        if avatar_pngs:
            staged_avatars = staging / f"{stem}-avatars"
            staged_avatars.mkdir()
            for member_id in sorted(avatar_pngs):
                (staged_avatars / f"{member_id}.png").write_bytes(avatar_pngs[member_id])
        backup = _replace_avatar_dir(path.parent, stem, staged_avatars)
        staged_avatars = None
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
