#!/usr/bin/env python3
"""PluralBridge canonical-model topologies and export builder.

Each of the twelve canonical configurations is a compact Python spec
(`spec_001` … `spec_012`). `assemble` expands a spec into one hierarchical
account: shared members/notes/fields/anchors, a containment `tree`, optional
field-based `relationships`, and optional `frontHistory`.

Spec tuples such as `system_links`, `system_placements`, `group_memberships`,
and `account_placements` are generation input. They are not copied into the
serialized JSON. The tree is nesting; graph relationships are a separate
account-level collection whose labels come from custom fields.

This is generation, not JSON embedding: anchors, tree nodes, identifier
references, inherit settings, and member-wide fronting are created
programmatically from the topology. Aurora/Simply Plural emission lives in
generate.py and must not be mixed with this schema. Feed imports do not call
assemble. gen-pluralbridge.render_import_model builds their account directly.
"""
from collections import OrderedDict, defaultdict

EXPORT_VERSION = "0.1-draft"
EXPORT_KIND = "self-contained-pluralbridge-example"
SOURCE_GENERATOR = "plural-synthetic"
NOTE_ASSIGNEE = "member-001"  # every noteId in an example is assigned to this shared member

# Roles that describe topology structure. Any other linkRole becomes a tag on
# the corresponding serialized record (member occurrence, group, note, or front).
STRUCTURAL_LINK_ROLES = {
    "scoped-to-system",
    "scoped-to-account",
    "account-structure-root",
    "account-note",
    "fronting-context",
    "defined-in-system",
    "container-child",
}

REQUIRED_TOP_LEVEL = ("account", "audit", "pluralBridgeExport", "provenance")
REQUIRED_ACCOUNT_FIELDS = (
    "accountId", "displayName", "email", "status", "username",
    "members", "anchors", "tree",
)
OPTIONAL_ACCOUNT_ARRAYS = (
    "notes", "customFields", "relationships", "frontHistory",
)
# Present in some specs as unused generation input; assemble must not emit them.
REMOVED_ACCOUNT_COLLECTIONS = (
    "privacyBuckets", "visibilityScopes", "memberships",
)
ACCOUNT_COLLECTION_ORDER = (
    "members", "notes", "customFields",
    "anchors", "tree", "relationships", "frontHistory",
)
INHERIT_SETTING = {"mode": "inherit"}
# First account property on every canonical example. Feed imports do not use this.
CANONICAL_AVATAR_CONFIG = {
    "avatar-width": 64,
    "avatar-height": 64,
    "avatar": "solid",
}
ANCHOR_ID_FIELDS = {"system": "systemId", "group": "groupId", "place": "placeId"}

FIXED_AUDIT = {"createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"}
# Both stamps are this constant. assemble does not read the clock.


def account(n):
    """Compact account identity for example n. assemble adds config, members, and anchors."""
    return {
        "accountId": f"account-{n:03d}",
        "displayName": f"Example {n}",
        "username": f"example-{n}",
        "email": f"example-{n}@pluralbridge.org",
        "status": "Active",
    }


def system_rec(system_id, name, description, color, **extra):
    """One System row in a spec. extra holds archived state or other anchor fields."""
    rec = {"systemId": system_id, "name": name, "description": description, "color": color}
    rec.update(extra)
    return rec


def member_rec(member_id, display_name, pronouns, description, color, archived=False, reason=None):
    """One shared member in a spec. Placements are added later from links, not from this row."""
    rec = {
        "memberId": member_id,
        "displayName": display_name,
        "pronouns": pronouns,
        "description": description,
        "color": color,
        "isArchived": archived,
    }
    if reason is not None:
        rec["archivedReason"] = reason
    return rec


def group_rec(group_id, name, description, color, archived=None):
    rec = {"groupId": group_id, "name": name, "description": description, "color": color}
    if archived is not None:
        rec["isArchived"] = archived
    return rec


def place_rec(place_id, name, description, color):
    return {"placeId": place_id, "name": name, "description": description, "color": color}


def note_rec(note_id, title, body, archived=None):
    rec = {"noteId": note_id, "title": title, "body": body, "supportsMarkdown": True}
    if archived is not None:
        rec["isArchived"] = archived
    return rec


def front_rec(front_id, member_ids, started, ended, live, status, archived=None):
    rec = {
        "frontHistoryId": front_id,
        "memberIds": list(member_ids),
        "startedAt": started,
        "endedAt": ended,
        "isLive": live,
        "status": status,
    }
    if archived is not None:
        rec["isArchived"] = archived
    return rec


def field_rec(field_id, name, description):
    """Payload-bearing field. Uses customFieldId until _shape_custom_field normalizes to fieldId."""
    return {
        "customFieldId": field_id,
        "fieldName": name,
        "fieldType": "text",
        "description": description,
        "supportsMarkdown": False,
    }


def relationship_field_rec(field_id, field_name):
    """Account-owned label field referenced by relationship rows.

    These ids must not be copied onto `anchor.fieldIds` merely to display a
    relationship label. `field_rec` is the unrelated payload-bearing field.
    """
    return {
        "fieldId": field_id,
        "fieldName": field_name,
        "visibility": {"mode": "inherit"},
        "permissions": {"mode": "inherit"},
    }


def bucket_rec(bucket_id, name, description, color="#1998a8"):
    """Spec-only privacy bucket. Not serialized into the canonical JSON account."""
    return {
        "privacyBucketId": bucket_id,
        "name": name,
        "description": description,
        "color": color,
    }


def scope_rec(scope_id, member_ids, name="Private"):
    """Spec-only visibility scope. Not serialized into the canonical JSON account."""
    return {
        "visibilityScopeId": scope_id,
        "name": name,
        "description": "Visible only through explicit private visibility rules.",
        "isSystemDefault": False,
        "isActive": True,
        "memberIds": list(member_ids),
    }


def _ensure_inherit_settings(rec):
    """Add approved inherit visibility/permissions without overwriting explicit values.

    Applied to notes, custom fields, and tree occurrences. Shared members do not
    receive these keys; do not derive them from the omitted privacy collections.
    """
    if "visibility" not in rec:
        rec["visibility"] = dict(INHERIT_SETTING)
    if "permissions" not in rec:
        rec["permissions"] = dict(INHERIT_SETTING)
    return rec


def _id_first(rec, id_field, extra_last=()):
    """Keep the identifier first, sort remaining payload keys, then extras."""
    rest = {k: rec[k] for k in rec if k != id_field and k not in extra_last}
    out = {id_field: rec[id_field]}
    for key in sorted(rest):
        out[key] = rest[key]
    for key in extra_last:
        if key in rec:
            out[key] = rec[key]
    return out


def _sorted_keys(rec, extra_last=()):
    rest = {k: rec[k] for k in rec if k not in extra_last}
    out = {key: rest[key] for key in sorted(rest)}
    for key in extra_last:
        if key in rec:
            out[key] = rec[key]
    return out


def _tag_for_role(role):
    if role in STRUCTURAL_LINK_ROLES:
        return None
    return role


def _current_fronting_ids(front_history):
    """Members listed on a current event: endedAt is null and isLive is true."""
    current = set()
    for rec in front_history:
        if rec.get("endedAt") is None and rec.get("isLive") is True:
            current.update(rec.get("memberIds") or [])
    return current


def _placements(spec):
    """Flatten system and account placement tuples. The owner id is generation input only."""
    rows = []
    for item in list(spec.get("system_placements", [])) + list(spec.get("account_placements", [])):
        _owner, object_type, object_id, parent_type, parent_id, rank = item[:6]
        rows.append((object_type, object_id, parent_type, parent_id, rank))
    return rows


def _shape_anchor(rec, object_type, field_ids=None, tags=None, note_ids=None):
    """Shared account.anchors[] record. Empty fieldIds, noteIds, and tags are omitted."""
    id_field = ANCHOR_ID_FIELDS[object_type]
    payload = {k: v for k, v in rec.items() if k != id_field}
    out = {"anchorId": rec[id_field], "objectType": object_type}
    for key in sorted(payload):
        out[key] = payload[key]
    if field_ids:
        out["fieldIds"] = list(field_ids)
    if note_ids:
        out["noteIds"] = list(note_ids)
    if tags:
        out["tags"] = list(tags)
    return out


def _shape_member(rec, field_ids, note_ids, fronting):
    """Shared account.members[] payload. Fronting is member-wide, never copied onto tree occurrences."""
    shaped = _id_first(rec, "memberId")
    shaped["fieldIds"] = list(field_ids)
    shaped["noteIds"] = list(note_ids)
    shaped["fronting"] = fronting
    return shaped


def _member_occ(member_id, tags=None):
    """Tree occurrence of a shared member. Settings belong here; identity stays on account.members."""
    occ = {"memberId": member_id}
    if tags:
        occ["tags"] = list(tags)
    return _ensure_inherit_settings(occ)


def _shape_relationship(rel, index):
    """One directed row. Label is customFields.fieldName for fieldId; targetAnchorId may be JSON null."""
    rec = {
        "relationshipId": rel.get("relationshipId", f"relationship-{index:03d}"),
        "sourceAnchorId": rel["sourceAnchorId"],
        "fieldId": rel["fieldId"],
        "targetAnchorId": rel.get("targetAnchorId"),
    }
    return rec


def _shape_custom_field(rec):
    """Normalize field_rec (customFieldId) and relationship_field_rec (fieldId) to one shape."""
    payload = dict(rec)
    if "customFieldId" in payload:
        payload["fieldId"] = payload.pop("customFieldId")
    shaped = _id_first(payload, "fieldId", extra_last=("visibility", "permissions"))
    return _ensure_inherit_settings(shaped)


def _shape_membership(system_id, index, override):
    """Leftover access-membership builder. Canonical exports omit memberships."""
    return {
        "membershipId": f"membership-{index:03d}",
        "anchorId": system_id,
        "roles": list(override.get("roles", ["Owner"])),
        "status": override.get("status", "Active"),
    }


def _tree_node(anchor_id, children_by_parent, members_by_anchor):
    """One tree node: anchor reference, occurrence list, children in rank order."""
    child_rows = sorted(children_by_parent.get(anchor_id, []), key=lambda row: row[0])
    return {
        "anchorId": anchor_id,
        "members": list(members_by_anchor.get(anchor_id, [])),
        "children": [
            _tree_node(child_id, children_by_parent, members_by_anchor)
            for _rank, _ctype, child_id in child_rows
        ],
    }


def _provenance(spec):
    rec = {
        "lossyMappings": [],
        "source": "synthetic",
        "sourceGenerator": SOURCE_GENERATOR,
        "sourceIdsPreserved": True,
    }
    rec.update(spec.get("provenance") or {})
    return {key: rec[key] for key in sorted(rec)}


def assemble(spec):
    """Expand a compact topology into a hierarchical single-account export.

    Member order on a System comes from `system_links` of type member.
    Group/place occurrence order comes from ranked membership tuples.
    Tree shape comes from placements: account-parented rows are roots; otherwise
    unplaced systems become top-level roots. Custom fields listed as
    defined-in-system are the only fields copied onto `anchor.fieldIds`.

    Shared members currently receive empty fieldIds. All notes in a spec are
    assigned to NOTE_ASSIGNEE. Fronting is derived from current front-history
    events unless `explicit_fronting` is present (Example 12). Empty optional
    collections are omitted; members, anchors, and tree are always emitted.
    """
    account_rec = spec["account"]
    systems = list(spec.get("systems", []))
    groups = list(spec.get("groups", []))
    places = list(spec.get("places", []))
    notes = list(spec.get("notes", []))
    fields = list(spec.get("custom_fields", []))
    front_history = list(spec.get("front_history", []))
    system_links = list(spec.get("system_links", []))

    field_ids_by_anchor = defaultdict(list)
    tags_by_group = defaultdict(list)
    tags_by_note = defaultdict(list)
    tags_by_front = defaultdict(list)
    member_tags_by_system = defaultdict(dict)
    system_member_order = defaultdict(list)
    # account_links, if present on a spec, are unused; tree roots come from placements.
    for owner_id, object_type, object_id, link_role in system_links:
        if object_type == "customField" and link_role == "defined-in-system":
            field_ids_by_anchor[owner_id].append(object_id)
        tag = _tag_for_role(link_role)
        if object_type == "member":
            if object_id not in system_member_order[owner_id]:
                system_member_order[owner_id].append(object_id)
            if tag:
                member_tags_by_system[owner_id][object_id] = [tag]
        elif tag and object_type == "group":
            tags_by_group[object_id].append(tag)
        elif tag and object_type == "note":
            tags_by_note[object_id].append(tag)
        elif tag and object_type == "frontHistory":
            tags_by_front[object_id].append(tag)

    # Same memberId may appear under several anchors; identity stays on account.members.
    members_by_anchor = {}
    for system_id, member_ids in system_member_order.items():
        members_by_anchor[system_id] = [
            _member_occ(mid, member_tags_by_system.get(system_id, {}).get(mid))
            for mid in member_ids
        ]
    group_rows = defaultdict(list)
    for group_id, member_id, rank in spec.get("group_memberships", []):
        group_rows[group_id].append((rank, _member_occ(member_id)))
    for group_id, rows in group_rows.items():
        members_by_anchor[group_id] = [occ for _rank, occ in sorted(rows)]
    place_rows = defaultdict(list)
    for place_id, member_id, rank in spec.get("place_memberships", []):
        place_rows[place_id].append((rank, _member_occ(member_id)))
    for place_id, rows in place_rows.items():
        members_by_anchor[place_id] = [occ for _rank, occ in sorted(rows)]

    placements = _placements(spec)
    children_by_parent = defaultdict(list)
    child_ids = set()
    account_roots = []
    account_id = account_rec["accountId"]
    for object_type, object_id, parent_type, parent_id, rank in placements:
        child_ids.add(object_id)
        if parent_type == "account" and parent_id == account_id:
            account_roots.append((rank, object_type, object_id))
        else:
            children_by_parent[parent_id].append((rank, object_type, object_id))
    if account_roots:
        root_ids = [oid for _rank, _otype, oid in sorted(account_roots)]
    else:
        # Examples 1–9: any system not placed under another anchor is a tree root.
        root_ids = [row["systemId"] for row in systems if row["systemId"] not in child_ids]

    tree = [_tree_node(root_id, children_by_parent, members_by_anchor) for root_id in root_ids]

    anchors = []
    for rec in systems:
        anchors.append(_shape_anchor(
            rec, "system",
            field_ids=field_ids_by_anchor.get(rec["systemId"]),
            tags=None,
        ))
    for rec in groups:
        anchors.append(_shape_anchor(
            rec, "group",
            tags=tags_by_group.get(rec["groupId"]),
        ))
    for rec in places:
        anchors.append(_shape_anchor(rec, "place"))

    explicit_fronting = spec.get("explicit_fronting")
    derived_fronting = _current_fronting_ids(front_history)
    note_ids = [rec["noteId"] for rec in notes]
    shared_members = []
    for rec in spec.get("members", []):
        mid = rec["memberId"]
        if explicit_fronting is not None:
            # Presence of the map is the override. Every member must be listed, including False.
            assert mid in explicit_fronting, f"{spec['example_id']}: explicit_fronting missing {mid}"
            fronting = explicit_fronting[mid]
        else:
            fronting = mid in derived_fronting
        assigned_notes = note_ids if mid == NOTE_ASSIGNEE else []
        # Shared members keep empty fieldIds; inherit settings are not applied here.
        shared_members.append(_shape_member(rec, [], assigned_notes, fronting))

    shaped_notes = []
    for rec in notes:
        shaped = _id_first(rec, "noteId", extra_last=("visibility", "permissions"))
        _ensure_inherit_settings(shaped)
        if tags_by_note.get(rec["noteId"]):
            shaped["tags"] = list(tags_by_note[rec["noteId"]])
        shaped_notes.append(shaped)

    shaped_fields = [_shape_custom_field(rec) for rec in fields]

    shaped_fronts = []
    for rec in front_history:
        shaped = _sorted_keys(rec)
        if tags_by_front.get(rec["frontHistoryId"]):
            shaped["tags"] = list(tags_by_front[rec["frontHistoryId"]])
        shaped_fronts.append(shaped)

    relationships = [
        _shape_relationship(rel, i) for i, rel in enumerate(spec.get("relationships", []), 1)
    ]

    account_obj = {
        "config": dict(CANONICAL_AVATAR_CONFIG),
        "accountId": account_rec["accountId"],
        "displayName": account_rec["displayName"],
        "email": account_rec["email"],
        "status": account_rec["status"],
        "username": account_rec["username"],
    }
    collections = {
        "members": shared_members,
        "notes": shaped_notes,
        "customFields": shaped_fields,
        "anchors": anchors,
        "tree": tree,
        "relationships": relationships,
        "frontHistory": shaped_fronts,
    }
    # Omit empty optional arrays. privacyBuckets/visibilityScopes/memberships are never copied.
    for key in ACCOUNT_COLLECTION_ORDER:
        if key in ("members", "anchors", "tree") or collections[key]:
            account_obj[key] = collections[key]

    header = {
        "exampleId": spec["example_id"],
        "exampleName": spec["example_name"],
        "exportKind": EXPORT_KIND,
        "exportVersion": EXPORT_VERSION,
        "modelingNote": spec["modeling_note"],
    }
    return {
        "account": account_obj,
        "audit": dict(FIXED_AUDIT),
        "pluralBridgeExport": header,
        "provenance": _provenance(spec),
    }


# ---------------------------------------------------------------- topologies
# Compact generation input. Filenames are stable, including example-006-subsystem.json
# whose exampleName is Nested Structure Model. Do not emit spec tuples into JSON.


def spec_001():
    """One System. Member A occurs on The Harbor, Musicians, and Ballet."""
    harbor = "system-001"
    return {
        "filename": "example-001-simple-single-system.json",
        "example_id": "example-001",
        "example_name": "Simple Single-System Model",
        "modeling_note": (
            "Synthetic PluralBridge example with one account and one System. "
            "Groups nest under The Harbor in the tree so they can be placed anywhere within that System."
        ),
        "account": account(1),
        "systems": [system_rec(harbor, "The Harbor",
                               "A simple single-system example with one shared System context.", "#8367ea")],
        "relationships": [],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B.", "#4a90e2"),
            member_rec("member-003", "C", "he/him", "Synthetic member C.", "#f5a623"),
        ],
        "groups": [
            group_rec("group-001", "Musicians", "Synthetic group for members A and C.", "#cccccc"),
            group_rec("group-002", "Dancers", "Synthetic group for member B.", "#b4d8ff"),
            group_rec("group-003", "Ballet", "Synthetic nested group under Dancers for member A.", "#ffd1dc"),
        ],
        "group_memberships": [
            ("group-001", "member-001", 1),
            ("group-001", "member-003", 2),
            ("group-002", "member-002", 1),
            ("group-003", "member-001", 1),
        ],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (harbor, "member", "member-003", "scoped-to-system"),
            (harbor, "group", "group-001", "scoped-to-system"),
            (harbor, "group", "group-002", "scoped-to-system"),
            (harbor, "group", "group-003", "scoped-to-system"),
            (harbor, "note", "note-001", "scoped-to-system"),
            (harbor, "frontHistory", "front-001", "fronting-context"),
            (harbor, "frontHistory", "front-002", "fronting-context"),
            (harbor, "customField", "custom-field-001", "defined-in-system"),
            (harbor, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (harbor, "visibilityScope", "visibility-scope-001", "defined-in-system"),
        ],
        "system_placements": [
            (harbor, "group", "group-001", "system", harbor, 1),
            (harbor, "group", "group-002", "system", harbor, 2),
            (harbor, "group", "group-003", "group", "group-002", 1),
        ],
        "notes": [note_rec("note-001", "System note",
                           "Synthetic note attached to the single System context.")],
        "front_history": [
            front_rec("front-001", ["member-001"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, None),
            front_rec("front-002", ["member-001", "member-002"], "2026-01-01T13:00:00Z",
                      None, True, "co-fronting"),
        ],
        "custom_fields": [field_rec("custom-field-001", "System Role", "Synthetic custom field example.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted", "Synthetic privacy bucket.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_002():
    """Two root Systems. Sibling containment is not implied; no relationship rows."""
    harbor, observatory = "system-001", "system-002"
    return {
        "filename": "example-002-multiple-top-level-systems.json",
        "example_id": "example-002",
        "example_name": "Multiple Top-Level Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example with two top-level Systems. "
            "Neither System owns or contains the other. This example has no relationship rows."
        ),
        "account": account(2),
        "systems": [
            system_rec(harbor, "The Harbor", "Primary root-level System.", "#8367ea"),
            system_rec(observatory, "The Observatory",
                       "Second root-level System. Neither root owns the other.", "#4f8fcf"),
        ],
        "relationships": [],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A in The Harbor.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B in The Harbor.", "#4a90e2"),
            member_rec("member-003", "C", "she/they", "Synthetic member C in The Observatory.", "#f5a623"),
        ],
        "groups": [group_rec("group-001", "Harbor Group", "Synthetic group scoped to The Harbor.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (harbor, "group", "group-001", "scoped-to-system"),
            (harbor, "frontHistory", "front-001", "fronting-context"),
            (harbor, "customField", "custom-field-001", "defined-in-system"),
            (harbor, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (harbor, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (observatory, "member", "member-003", "scoped-to-system"),
            (observatory, "note", "note-001", "scoped-to-system"),
            (observatory, "customField", "custom-field-002", "defined-in-system"),
        ],
        "system_placements": [
            (harbor, "group", "group-001", "system", harbor, 1),
        ],
        "notes": [note_rec(
            "note-001", "Observatory orientation note",
            "The Observatory is a separate top-level System. It has no parent System and does not own The Harbor.")],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "Harbor Role", "Synthetic custom field scoped to The Harbor."),
            field_rec("custom-field-002", "Observatory Role", "Synthetic custom field scoped to The Observatory."),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket scoped to The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_003():
    """The Workshop is nested under Main House. No relationship rows; containment is the tree."""
    main, workshop = "system-001", "system-002"
    return {
        "filename": "example-003-parent-child-system.json",
        "example_id": "example-003",
        "example_name": "Parent / Child System Model",
        "modeling_note": (
            "Synthetic PluralBridge example with The Workshop nested beneath Main House. "
            "The parent/child structure is tree containment; it does not grant access or "
            "inherited ownership. This example has no relationship rows."
        ),
        "account": account(3),
        "systems": [
            system_rec(main, "Main House", "Root-level System.", "#8367ea"),
            system_rec(workshop, "The Workshop",
                       "Child System structurally related to Main House. Access and privacy remain "
                       "governed by membership, consent, and policy.", "#4f8fcf"),
        ],
        "relationships": [],
        "members": [
            member_rec("member-001", "Rowan", "she/her", "Synthetic member in Main House.", "#69d563"),
            member_rec("member-002", "Tess", "they/them", "Synthetic member in Main House.", "#4a90e2"),
            member_rec("member-003", "Kit", "they/them", "Synthetic member in The Workshop.", "#f5a623"),
            member_rec("member-004", "Lark", "she/her", "Synthetic member in The Workshop.", "#7ed321"),
        ],
        "groups": [group_rec("group-001", "Main House Group",
                             "Synthetic group scoped to Main House.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (main, "member", "member-001", "scoped-to-system"),
            (main, "member", "member-002", "scoped-to-system"),
            (main, "group", "group-001", "scoped-to-system"),
            (main, "note", "note-001", "scoped-to-system"),
            (main, "frontHistory", "front-001", "fronting-context"),
            (main, "customField", "custom-field-001", "defined-in-system"),
            (main, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (main, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (workshop, "member", "member-003", "scoped-to-system"),
            (workshop, "member", "member-004", "scoped-to-system"),
            (workshop, "note", "note-002", "scoped-to-system"),
            (workshop, "frontHistory", "front-002", "fronting-context"),
        ],
        "system_placements": [
            (main, "group", "group-001", "system", main, 1),
            (main, "system", workshop, "system", main, 2),
        ],
        "notes": [
            note_rec("note-001", "Main House note", "Synthetic note attached to the parent System context."),
            note_rec("note-002", "Workshop note", "Synthetic note attached to the child System context."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, None),
            front_rec("front-002", ["member-003", "member-004"], "2026-01-01T13:00:00Z",
                      None, True, "co-fronting"),
        ],
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in Main House.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in Main House.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_004():
    """Peer Systems. Reciprocity is two directed rows sharing the sibling field."""
    day, night = "system-001", "system-002"
    return {
        "filename": "example-004-sibling-systems.json",
        "example_id": "example-004",
        "example_name": "Sibling Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example with two sibling Systems and two reciprocal "
            "sibling relationship rows. Neither System owns, contains, or controls the other."
        ),
        "account": account(4),
        "systems": [
            system_rec(day, "Day Team", "Root-level System operating in parallel with Night Team.", "#8367ea"),
            system_rec(night, "Night Team", "Root-level System operating in parallel with Day Team.", "#4f8fcf"),
        ],
        "relationships": [
            {"relationshipId": "relationship-003", "sourceAnchorId": day,
             "fieldId": "custom-field-sibling", "targetAnchorId": night},
            {"relationshipId": "relationship-004", "sourceAnchorId": night,
             "fieldId": "custom-field-sibling", "targetAnchorId": day},
        ],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A in Day Team.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B in Day Team.", "#4a90e2"),
            member_rec("member-003", "C", "she/they", "Synthetic member C in Night Team.", "#f5a623"),
            member_rec("member-004", "D", "he/they", "Synthetic member D in Night Team.", "#7ed321"),
        ],
        "groups": [group_rec("group-001", "Day Team Group", "Synthetic group scoped to Day Team.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (day, "member", "member-001", "scoped-to-system"),
            (day, "member", "member-002", "scoped-to-system"),
            (day, "group", "group-001", "scoped-to-system"),
            (day, "note", "note-001", "scoped-to-system"),
            (day, "frontHistory", "front-001", "fronting-context"),
            (day, "customField", "custom-field-001", "defined-in-system"),
            (day, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (day, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (night, "member", "member-003", "scoped-to-system"),
            (night, "member", "member-004", "scoped-to-system"),
            (night, "note", "note-002", "scoped-to-system"),
            (night, "frontHistory", "front-002", "fronting-context"),
        ],
        "system_placements": [
            (day, "group", "group-001", "system", day, 1),
        ],
        "notes": [
            note_rec("note-001", "Day Team note", "Synthetic note attached to the Day Team System context."),
            note_rec("note-002", "Night Team note", "Synthetic note attached to the Night Team System context."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
            front_rec("front-002", ["member-003", "member-004"], "2026-01-01T22:00:00Z",
                      None, True, "co-fronting"),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "System Role",
                      "Synthetic custom field defined in Day Team."),
            relationship_field_rec("custom-field-sibling", "sibling"),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in Day Team.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_005():
    """Peer Systems. Reciprocity is two directed rows sharing the related field."""
    harbor, archive = "system-001", "system-002"
    return {
        "filename": "example-005-related-systems.json",
        "example_id": "example-005",
        "example_name": "Related Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example with two Systems associated by reciprocal related "
            "records. Each System is labeled related with no arrow, so both directions are "
            "encoded. The records describe association without parentage, containment, "
            "ownership, or automatic authority."
        ),
        "account": account(5),
        "systems": [
            system_rec(harbor, "The Harbor",
                       "Root-level System with a related association to The Archive.", "#8367ea"),
            system_rec(archive, "The Archive",
                       "Root-level System associated with The Harbor through shared history, "
                       "partial overlap, or a loosely connected internal organization.", "#4f8fcf"),
        ],
        "relationships": [
            {"relationshipId": "relationship-004", "sourceAnchorId": harbor,
             "fieldId": "custom-field-related", "targetAnchorId": archive},
            {"relationshipId": "relationship-003", "sourceAnchorId": archive,
             "fieldId": "custom-field-related", "targetAnchorId": harbor},
        ],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A in The Harbor.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B in The Harbor.", "#4a90e2"),
            member_rec("member-003", "C", "she/they", "Synthetic member C in The Archive.", "#f5a623"),
        ],
        "groups": [group_rec("group-001", "Harbor Group", "Synthetic group scoped to The Harbor.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (harbor, "group", "group-001", "scoped-to-system"),
            (harbor, "note", "note-001", "scoped-to-system"),
            (harbor, "frontHistory", "front-001", "fronting-context"),
            (harbor, "customField", "custom-field-001", "defined-in-system"),
            (harbor, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (harbor, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (archive, "member", "member-003", "scoped-to-system"),
            (archive, "note", "note-002", "scoped-to-system"),
            (archive, "customField", "custom-field-002", "defined-in-system"),
            (archive, "frontHistory", "front-002", "fronting-context"),
        ],
        "system_placements": [
            (harbor, "group", "group-001", "system", harbor, 1),
        ],
        "notes": [
            note_rec("note-001", "Harbor note", "Synthetic note attached to The Harbor."),
            note_rec("note-002", "Archive note",
                     "Synthetic note attached to The Archive. This note records that The Archive "
                     "is related to The Harbor without being its parent or child."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
            front_rec("front-002", ["member-003"], "2026-01-01T14:00:00Z", None, True, None),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "System Role", "Synthetic custom field defined in The Harbor."),
            field_rec("custom-field-002", "Archive Context", "Synthetic custom field defined in The Archive."),
            relationship_field_rec("custom-field-related", "related"),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_006():
    """Place nested in one System. Filename keeps -subsystem; exampleName is Nested Structure Model."""
    harbor = "system-001"
    return {
        "filename": "example-006-subsystem.json",
        "example_id": "example-006",
        "example_name": "Nested Structure Model",
        "modeling_note": (
            "Synthetic PluralBridge Nested Structure Model. Morgan's Room is a Place inside "
            "The Harbor, not a second System. M1 and M2 belong to the Place rather than to "
            "The Harbor member list. This example has no relationship rows."
        ),
        "account": account(6),
        "systems": [system_rec(harbor, "The Harbor",
                               "Root-level System containing members, a group, and a Place.", "#8367ea")],
        "relationships": [],
        "members": [
            member_rec("member-001", "Alex", "she/her", "Synthetic member in The Harbor.", "#69d563"),
            member_rec("member-002", "Morgan", "they/them",
                       "Synthetic member in The Harbor. Morgan's Room is a Place in the same System.",
                       "#4a90e2"),
            member_rec("member-003", "Rae", "she/they", "Synthetic member in The Harbor.", "#f5a623"),
            member_rec("member-004", "M1", "they/them", "Synthetic member inside Morgan's Room.", "#7ed321"),
            member_rec("member-005", "M2", "he/they", "Synthetic member inside Morgan's Room.", "#bd10e0"),
        ],
        "groups": [group_rec("group-001", "Harbor Group", "Synthetic group scoped to The Harbor.", "#cccccc")],
        "group_memberships": [
            ("group-001", "member-001", 1),
            ("group-001", "member-002", 2),
            ("group-001", "member-003", 3),
        ],
        "places": [place_rec("place-001", "Morgan's Room",
                             "Place inside The Harbor with its own member structure.", "#4f8fcf")],
        "place_memberships": [
            ("place-001", "member-004", 1),
            ("place-001", "member-005", 2),
        ],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (harbor, "member", "member-003", "scoped-to-system"),
            (harbor, "group", "group-001", "scoped-to-system"),
            (harbor, "place", "place-001", "scoped-to-system"),
            (harbor, "note", "note-001", "scoped-to-system"),
            (harbor, "note", "note-002", "scoped-to-system"),
            (harbor, "frontHistory", "front-001", "fronting-context"),
            (harbor, "customField", "custom-field-001", "defined-in-system"),
            (harbor, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (harbor, "visibilityScope", "visibility-scope-001", "defined-in-system"),
        ],
        "system_placements": [
            (harbor, "group", "group-001", "system", harbor, 1),
            (harbor, "place", "place-001", "system", harbor, 2),
        ],
        "notes": [
            note_rec("note-001", "Harbor note", "Synthetic note attached to The Harbor."),
            note_rec("note-002", "Place note",
                     "Morgan's Room is modeled as a Place inside The Harbor, with its own members."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
        ],
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in The Harbor.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-002"])],
    }


def spec_007():
    """Two independent null-target labels on North Wing: evolving and unknown."""
    harbor, north = "system-001", "system-002"
    return {
        "filename": "example-007-evolving-uncertain-relationship.json",
        "example_id": "example-007",
        "example_name": "Evolving / Uncertain Relationship Model",
        "modeling_note": (
            "Synthetic PluralBridge example that preserves a real but unresolved relationship "
            "between two Systems. North Wing has evolving and unknown as separate null-target "
            "rows, without naming the connection as parent, child, sibling, related, subsystem, "
            "or ownership."
        ),
        "account": account(7),
        "systems": [
            system_rec(harbor, "The Harbor",
                       "Root-level System with an unresolved relationship to North Wing.", "#8367ea"),
            system_rec(north, "North Wing",
                       "System connected to The Harbor. The exact relationship is still forming.", "#4f8fcf"),
        ],
        "relationships": [
            {"relationshipId": "relationship-003", "sourceAnchorId": north,
             "fieldId": "custom-field-evolving", "targetAnchorId": None},
            {"relationshipId": "relationship-004", "sourceAnchorId": north,
             "fieldId": "custom-field-unknown", "targetAnchorId": None},
        ],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A in The Harbor.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B in The Harbor.", "#4a90e2"),
            member_rec("member-003", "C", "she/they", "Synthetic member C in North Wing.", "#f5a623"),
            member_rec("member-004", "D", "he/they", "Synthetic member D in North Wing.", "#7ed321"),
        ],
        "groups": [group_rec("group-001", "Harbor Group", "Synthetic group scoped to The Harbor.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (harbor, "group", "group-001", "scoped-to-system"),
            (harbor, "note", "note-001", "scoped-to-system"),
            (harbor, "frontHistory", "front-001", "fronting-context"),
            (harbor, "customField", "custom-field-001", "defined-in-system"),
            (harbor, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (harbor, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (north, "member", "member-003", "scoped-to-system"),
            (north, "member", "member-004", "scoped-to-system"),
            (north, "note", "note-002", "scoped-to-system"),
            (north, "frontHistory", "front-002", "fronting-context"),
        ],
        "system_placements": [
            (harbor, "group", "group-001", "system", harbor, 1),
        ],
        "notes": [
            note_rec("note-001", "Harbor note", "Synthetic note attached to The Harbor."),
            note_rec("note-002", "North Wing relationship note",
                     "North Wing is connected to The Harbor, but the exact relationship is still forming."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
            front_rec("front-002", ["member-003"], "2026-01-01T14:00:00Z", None, True, None),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "System Role",
                      "Synthetic custom field defined in The Harbor."),
            relationship_field_rec("custom-field-evolving", "evolving"),
            relationship_field_rec("custom-field-unknown", "unknown"),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_008():
    """Archived relationship label does not cascade isArchived/status on Old Map or its records."""
    current, old = "system-001", "system-002"
    return {
        "filename": "example-008-archived-system.json",
        "example_id": "example-008",
        "example_name": "Archived System Model",
        "modeling_note": (
            "Synthetic PluralBridge example that preserves an archived System as historically "
            "meaningful data. Old Map has an archived null-target relationship label. Archive "
            "flags remain independent lifecycle data; the label does not change or cascade those "
            "flags. Old Map and its existing members, groups, notes, front history, and "
            "associations are retained."
        ),
        "account": account(8),
        "systems": [
            system_rec(current, "Current System", "Active root-level System.", "#8367ea",
                       status="active", isArchived=False),
            system_rec(old, "Old Map",
                       "Archived System retained for historical organization, old notes, "
                       "migration meaning, and past fronting records.", "#808080",
                       status="archived", isArchived=True, archivedAt="2026-01-01T00:00:00Z",
                       archivedReason="Superseded by Current System during migration."),
        ],
        # Leftover access-membership input. assemble does not emit memberships.
        "membership_overrides": {old: {"status": "Historical"}},
        "relationships": [
            {"relationshipId": "relationship-001", "sourceAnchorId": old,
             "fieldId": "custom-field-archived", "targetAnchorId": None},
        ],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic member A in Current System.", "#69d563"),
            member_rec("member-002", "B", "they/them", "Synthetic member B in Current System.", "#4a90e2"),
            member_rec("member-003", "Archive A", "she/her",
                       "Synthetic historical member record from Old Map.", "#999999",
                       archived=True, reason="Historical member record retained from archived structure."),
            member_rec("member-004", "Archive B", "they/them",
                       "Synthetic historical member record from Old Map.", "#777777",
                       archived=True, reason="Historical member record retained from archived structure."),
        ],
        "groups": [
            group_rec("group-001", "Current Group", "Synthetic group scoped to Current System.",
                      "#cccccc", archived=False),
            group_rec("group-002", "Old Map Group", "Synthetic archived group retained from Old Map.",
                      "#999999", archived=True),
        ],
        "group_memberships": [
            ("group-001", "member-001", 1),
            ("group-001", "member-002", 2),
            ("group-002", "member-003", 1),
            ("group-002", "member-004", 2),
        ],
        "system_links": [
            (current, "member", "member-001", "scoped-to-system"),
            (current, "member", "member-002", "scoped-to-system"),
            (current, "group", "group-001", "scoped-to-system"),
            (current, "note", "note-001", "scoped-to-system"),
            (current, "frontHistory", "front-001", "fronting-context"),
            (current, "customField", "custom-field-001", "defined-in-system"),
            (current, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (current, "visibilityScope", "visibility-scope-001", "defined-in-system"),
            (old, "member", "member-003", "historical-system-member"),
            (old, "member", "member-004", "historical-system-member"),
            (old, "group", "group-002", "historical-organization"),
            (old, "note", "note-002", "historical-note"),
            (old, "frontHistory", "front-002", "historical-fronting-context"),
        ],
        "system_placements": [
            (current, "group", "group-001", "system", current, 1),
            (old, "group", "group-002", "system", old, 1),
        ],
        "notes": [
            note_rec("note-001", "Current System note",
                     "Synthetic note attached to the active Current System.", archived=False),
            note_rec("note-002", "Old Map migration note",
                     "Synthetic archived note preserving the meaning of the old structure after migration.",
                     archived=True),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting", archived=False),
            front_rec("front-002", ["member-003"], "2025-06-01T12:00:00Z",
                      "2025-06-01T13:00:00Z", False, "historical", archived=True),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "System Role",
                      "Synthetic custom field defined in Current System."),
            relationship_field_rec("custom-field-archived", "archived"),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in Current System.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_009():
    """Three directed edges. Graph rows are not tree containment; all three Systems remain roots."""
    a, b, c = "system-001", "system-002", "system-003"
    return {
        "filename": "example-009-non-tree-graph.json",
        "example_id": "example-009",
        "example_name": "Non-Tree / Graph Model",
        "modeling_note": (
            "Synthetic PluralBridge example that breaks the ordinary tree assumption by "
            "representing Systems as graph nodes: A related to B, B sibling of C, and C "
            "associated with A. No single trunk, root hierarchy, or forced parentage is required."
        ),
        "account": account(9),
        "systems": [
            system_rec(a, "A", "Graph node System A.", "#8367ea"),
            system_rec(b, "B", "Graph node System B.", "#4f8fcf"),
            system_rec(c, "C", "Graph node System C.", "#f5a623"),
        ],
        "relationships": [
            {"relationshipId": "relationship-004", "sourceAnchorId": a,
             "fieldId": "custom-field-related", "targetAnchorId": b},
            {"relationshipId": "relationship-005", "sourceAnchorId": b,
             "fieldId": "custom-field-sibling", "targetAnchorId": c},
            {"relationshipId": "relationship-006", "sourceAnchorId": c,
             "fieldId": "custom-field-associated", "targetAnchorId": a},
        ],
        "members": [
            member_rec("member-001", "A1", "she/her", "Synthetic member in System A.", "#69d563"),
            member_rec("member-002", "A2", "they/them", "Synthetic member in System A.", "#4a90e2"),
            member_rec("member-003", "B1", "she/they", "Synthetic member in System B.", "#f5a623"),
            member_rec("member-004", "C1", "he/they", "Synthetic member in System C.", "#7ed321"),
        ],
        "groups": [group_rec("group-001", "A Group", "Synthetic group scoped to System A.", "#cccccc")],
        "group_memberships": [("group-001", "member-001", 1), ("group-001", "member-002", 2)],
        "system_links": [
            (a, "member", "member-001", "scoped-to-system"),
            (a, "member", "member-002", "scoped-to-system"),
            (b, "member", "member-003", "scoped-to-system"),
            (c, "member", "member-004", "scoped-to-system"),
            (a, "group", "group-001", "scoped-to-system"),
            (a, "note", "note-001", "scoped-to-system"),
            (b, "note", "note-002", "scoped-to-system"),
            (c, "note", "note-003", "scoped-to-system"),
            (a, "frontHistory", "front-001", "fronting-context"),
            (b, "frontHistory", "front-002", "fronting-context"),
            (c, "frontHistory", "front-003", "fronting-context"),
            (a, "customField", "custom-field-001", "defined-in-system"),
            (a, "privacyBucket", "privacy-bucket-001", "defined-in-system"),
            (a, "visibilityScope", "visibility-scope-001", "defined-in-system"),
        ],
        "system_placements": [
            (a, "group", "group-001", "system", a, 1),
        ],
        "notes": [
            note_rec("note-001", "System A note", "Synthetic note attached to System A."),
            note_rec("note-002", "System B note", "Synthetic note attached to System B."),
            note_rec("note-003", "System C graph note",
                     "This example uses graph relationships: A related to B, B sibling of C, "
                     "and C associated with A."),
        ],
        "front_history": [
            front_rec("front-001", ["member-001", "member-002"], "2026-01-01T12:00:00Z",
                      "2026-01-01T13:00:00Z", False, "co-fronting"),
            front_rec("front-002", ["member-003"], "2026-01-01T14:00:00Z",
                      "2026-01-01T15:00:00Z", False, None),
            front_rec("front-003", ["member-004"], "2026-01-01T16:00:00Z", None, True, None),
        ],
        "custom_fields": [
            field_rec("custom-field-001", "System Role",
                      "Synthetic custom field defined in System A."),
            relationship_field_rec("custom-field-related", "related"),
            relationship_field_rec("custom-field-sibling", "sibling"),
            relationship_field_rec("custom-field-associated", "associated"),
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in System A.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_010():
    """Account placements make Household the tree root. Empty relationships[] is omitted."""
    harbor, house = "system-001", "system-002"
    acct = account(10)
    aid = acct["accountId"]
    return {
        "filename": "example-010-top-level-group-containing-systems.json",
        "example_id": "example-010",
        "example_name": "Top-Level Group Containing Systems",
        "modeling_note": (
            "Synthetic PluralBridge example where the Household Group is the tree root and "
            "contains two Systems. This example has no relationship rows."
        ),
        "account": acct,
        "systems": [
            system_rec(harbor, "The Harbor",
                       "Synthetic system contained within the Household group.", "#8367ea"),
            system_rec(house, "Main House",
                       "Second synthetic system contained within the Household group.", "#4a90e2"),
        ],
        "relationships": [],
        "members": [
            member_rec("member-001", "A", "she/her", "Synthetic household member A.", "#69d563"),
            member_rec("member-002", "E", "they/them", "Synthetic household member E.", "#4a90e2"),
            member_rec("member-003", "I", "she/they", "Synthetic household member I.", "#f5a623"),
            member_rec("member-004", "O", "he/they", "Synthetic household member O.", "#7ed321"),
            member_rec("member-005", "W", "they/them", "Synthetic member in The Harbor.", "#bd10e0"),
            member_rec("member-006", "X", "she/her", "Synthetic member in Main House.", "#50e3c2"),
            member_rec("member-007", "Y", "he/him", "Synthetic member in The Harbor.", "#b8e986"),
            member_rec("member-008", "Z", "they/them", "Synthetic member in Main House.", "#9013fe"),
        ],
        "groups": [group_rec("group-001", "Household",
                             "Top-level account group containing two systems.", "#cccccc")],
        "group_memberships": [
            ("group-001", "member-001", 1),
            ("group-001", "member-002", 2),
            ("group-001", "member-003", 3),
            ("group-001", "member-004", 4),
        ],
        "account_links": [
            (aid, "group", "group-001", "account-structure-root"),
            (aid, "system", harbor, "scoped-to-account"),
            (aid, "system", house, "scoped-to-account"),
            (aid, "note", "note-001", "account-note"),
            (aid, "frontHistory", "front-001", "fronting-context"),
        ],
        "account_placements": [
            (aid, "group", "group-001", "account", aid, 1),
            (aid, "system", harbor, "group", "group-001", 1),
            (aid, "system", house, "group", "group-001", 2),
        ],
        "system_links": [
            (harbor, "member", "member-005", "scoped-to-system"),
            (harbor, "member", "member-007", "scoped-to-system"),
            (house, "member", "member-006", "scoped-to-system"),
            (house, "member", "member-008", "scoped-to-system"),
        ],
        "notes": [note_rec("note-001", "Example 10 note",
                           "Synthetic account-level note for Group Collection of Systems.")],
        "front_history": [
            front_rec("front-001", ["member-001"], "2026-01-01T12:00:00Z", None, True, None),
        ],
    }


def spec_011():
    """Account placements make Central Hub the tree root. Main House members live on Waiting Room."""
    harbor, house = "system-001", "system-002"
    acct = account(11)
    aid = acct["accountId"]
    return {
        "filename": "example-011-top-level-place-containing-systems.json",
        "example_id": "example-011",
        "example_name": "Place Collection of Systems",
        "modeling_note": (
            "Synthetic PluralBridge example where Central Hub is the tree root and contains "
            "two Systems. Waiting Room is a Place nested inside Main House. This example has "
            "no relationship rows."
        ),
        "account": acct,
        "systems": [
            system_rec(harbor, "The Harbor", "System under Central Hub place.", "#8367ea"),
            system_rec(house, "Main House",
                       "System under Central Hub place containing nested Waiting Room place.", "#4a90e2"),
        ],
        "relationships": [],
        "members": [
            member_rec("member-001", "Popeye", "he/him", "Synthetic member in The Harbor.", "#69d563"),
            member_rec("member-002", "Gilligan", "he/him", "Synthetic member in The Harbor.", "#4a90e2"),
            member_rec("member-003", "Mickey", "he/him", "Synthetic member in Waiting Room place.", "#f5a623"),
            member_rec("member-004", "Minnie", "she/her", "Synthetic member in Waiting Room place.", "#bd10e0"),
        ],
        "places": [
            place_rec("place-001", "Central Hub", "Top-level place containing two systems.", "#cccccc"),
            place_rec("place-002", "Waiting Room", "Nested place under Main House.", "#b8e986"),
        ],
        "place_memberships": [
            ("place-002", "member-003", 1),
            ("place-002", "member-004", 2),
        ],
        "account_links": [
            (aid, "place", "place-001", "account-structure-root"),
            (aid, "system", harbor, "scoped-to-account"),
            (aid, "system", house, "scoped-to-account"),
            (aid, "note", "note-001", "account-note"),
            (aid, "frontHistory", "front-001", "fronting-context"),
        ],
        "account_placements": [
            (aid, "place", "place-001", "account", aid, 1),
            (aid, "system", harbor, "place", "place-001", 1),
            (aid, "system", house, "place", "place-001", 2),
        ],
        "system_links": [
            (harbor, "member", "member-001", "scoped-to-system"),
            (harbor, "member", "member-002", "scoped-to-system"),
            (house, "place", "place-002", "scoped-to-system"),
        ],
        "system_placements": [
            (house, "place", "place-002", "system", house, 1),
        ],
        "notes": [note_rec("note-001", "Example 11 note",
                           "Synthetic account-level note for Place Collection of Systems.")],
        "front_history": [
            front_rec("front-001", ["member-001"], "2026-01-01T12:00:00Z", None, True, None),
        ],
    }


def spec_012():
    """Non-System anchors. Tree from account_placements; account_links are unused by assemble."""
    aid = "account-012"
    return {
        "filename": "example-012-non-system-anchors.json",
        "example_id": "example-012",
        "example_name": "Non-System Anchors Plural Map",
        "modeling_note": (
            "Synthetic PluralBridge example following Example 12. Central Hub is a root Place "
            "containing The Harbor and Main House Groups. Main House contains Waiting Room Place. "
            "No System entities or System references exist. Tree nesting and member occurrences "
            "do not grant access. Access grants, focus, note contents, and fronting events are not "
            "specified by the source and are not fabricated."
        ),
        "account": account(12),
        "systems": [],
        "memberships": [],
        "members": [
            {"memberId": f"member-{i:03d}", "displayName": name, "isArchived": False}
            for i, name in enumerate(("Popeye", "Gilligan", "Mickey", "Minnie"), 1)
        ],
        "groups": [
            {"groupId": "group-001", "name": "The Harbor"},
            {"groupId": "group-002", "name": "Main House"},
        ],
        "places": [
            {"placeId": "place-001", "name": "Central Hub"},
            {"placeId": "place-002", "name": "Waiting Room"},
        ],
        "account_links": [
            (aid, "place", "place-001", "account-structure-root"),
            (aid, "group", "group-001", "scoped-to-account"),
            (aid, "group", "group-002", "scoped-to-account"),
            (aid, "place", "place-002", "scoped-to-account"),
        ],
        "account_placements": [
            (aid, "place", "place-001", "account", aid, 1),
            (aid, "group", "group-001", "place", "place-001", 1),
            (aid, "group", "group-002", "place", "place-001", 2),
            (aid, "place", "place-002", "group", "group-002", 1),
        ],
        "group_memberships": [
            ("group-001", "member-001", 1),
            ("group-001", "member-002", 2),
        ],
        "place_memberships": [
            ("place-002", "member-003", 1),
            ("place-002", "member-004", 2),
        ],
        # Explicit fixture decision for Example 12, not a missing-history default.
        # There is no frontHistory collection; do not derive False from empty history.
        "explicit_fronting": {
            "member-001": False,
            "member-002": False,
            "member-003": False,
            "member-004": False,
        },
        # Historical transcription provenance; the live spec filename may differ.
        "provenance": {
            "sourceDocument": "PluralBridge-Plural-Maps-and-Design-Rules.txt",
            "sourceExample": 12,
            "sourceGenerator": "example-012-document-transcription",
            "sourceIdsPreserved": False,
        },
    }


SPECS = [
    spec_001, spec_002, spec_003, spec_004, spec_005, spec_006,
    spec_007, spec_008, spec_009, spec_010, spec_011, spec_012,
]


def build_all():
    """Return {filename: export} for all twelve canonical configurations, in SPECS order."""
    out = OrderedDict()
    for spec_fn in SPECS:
        spec = spec_fn()
        export = assemble(spec)
        out[spec["filename"]] = export
    return dict(out)


# Fixture contract: order and names must match generate.py's expected file set.
SYSTEM_MODEL_FILENAMES = [
    "example-001-simple-single-system.json",
    "example-002-multiple-top-level-systems.json",
    "example-003-parent-child-system.json",
    "example-004-sibling-systems.json",
    "example-005-related-systems.json",
    "example-006-subsystem.json",
    "example-007-evolving-uncertain-relationship.json",
    "example-008-archived-system.json",
    "example-009-non-tree-graph.json",
    "example-010-top-level-group-containing-systems.json",
    "example-011-top-level-place-containing-systems.json",
    "example-012-non-system-anchors.json",
]


# ---------------------------------------------------------------- validation


def ids_in(collection, id_field):
    """Set of one id field. Used to reject duplicate ids and dangling references."""
    return {row[id_field] for row in collection}


def _assert_inherit_settings(rec, name, where):
    """Every serialized record carries visibility and permissions, each with a mode."""
    for key in ("visibility", "permissions"):
        assert key in rec, f"{name}: {where} missing {key}"
        setting = rec[key]
        assert isinstance(setting, dict), f"{name}: {where}.{key} must be an object"
        assert "mode" in setting, f"{name}: {where}.{key} missing mode"
        if setting["mode"] == "inherit":
            assert setting == INHERIT_SETTING, f"{name}: {where}.{key} inherit syntax"


def _acct(export):
    """The single account object. Canonical exports are not a list of accounts."""
    return export["account"]


def walk_tree(nodes):
    """Depth-first tree nodes. Order follows the serialized children arrays."""
    for node in nodes or []:
        yield node
        yield from walk_tree(node.get("children"))


def _tree_index(export):
    return {node["anchorId"]: node for node in walk_tree(_acct(export).get("tree"))}


def _child_ids(node):
    return [child["anchorId"] for child in node.get("children") or []]


def _tree_member_ids(node):
    return [occ["memberId"] for occ in node.get("members") or []]


def _anchors_of_type(export, object_type):
    return [a for a in _acct(export)["anchors"] if a["objectType"] == object_type]


def _anchor_names(export, object_type):
    return {a["anchorId"]: a["name"] for a in _anchors_of_type(export, object_type)}


def _rel_labels(export):
    """Compare relationships by (source, fieldName, target). Target None is JSON null."""
    names = {f["fieldId"]: f["fieldName"] for f in _acct(export).get("customFields") or []}
    return {(r["sourceAnchorId"], names[r["fieldId"]], r["targetAnchorId"])
            for r in _acct(export).get("relationships") or []}


def _system_members(export, system_id):
    node = _tree_index(export).get(system_id)
    names = {m["memberId"]: m["displayName"] for m in _acct(export)["members"]}
    if node is None:
        return set()
    return {names[mid] for mid in _tree_member_ids(node)}


def validate_schema(export, name="export"):
    """Envelope, required collections, omitted empty arrays, and forbidden legacy collections."""
    extra = [key for key in export if key not in REQUIRED_TOP_LEVEL]
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in export]
    assert not missing, f"{name}: missing top-level keys {missing}"
    assert not extra, f"{name}: unexpected top-level keys {extra}"
    for key in ("audit", "pluralBridgeExport", "provenance"):
        assert isinstance(export[key], dict), f"{name}: {key} must be an object"
    account = export["account"]
    assert isinstance(account, dict), f"{name}: account must be an object"
    for key in REQUIRED_ACCOUNT_FIELDS:
        assert key in account, f"{name}: account missing {key}"
    for key in ("members", "anchors", "tree"):
        assert isinstance(account[key], list), f"{name}: account.{key} must be an array"
    for key in OPTIONAL_ACCOUNT_ARRAYS:
        if key in account:
            assert isinstance(account[key], list), f"{name}: account.{key} must be an array"
            assert account[key], f"{name}: omit empty account.{key}"
    for key in REMOVED_ACCOUNT_COLLECTIONS:
        assert key not in account, f"{name}: account.{key} was removed"
    assert "permissionIds" not in str(account.get("anchors")), f"{name}: permissionIds are not in this format"
    for anchor in account["anchors"]:
        assert "permissionIds" not in anchor and "visibilityIds" not in anchor, (
            f"{name}: anchors must not carry permissionIds/visibilityIds")


def validate_unique_memberships(export, name="export"):
    """Name kept for callers. Access memberships are omitted from this format."""
    assert "memberships" not in _acct(export), f"{name}: memberships collection was removed"


def validate_references(export, name="export"):
    """IDs unique, every reference in-account, relationship rows use the approved fields only.

    Member noteIds and anchor noteIds must name a note in this account.
    The twelve canonical examples do not set anchor noteIds.
    """
    account = _acct(export)
    member_ids = ids_in(account["members"], "memberId")
    assert len(member_ids) == len(account["members"]), f"{name}: duplicate memberId"
    anchor_ids = ids_in(account["anchors"], "anchorId")
    assert len(anchor_ids) == len(account["anchors"]), f"{name}: duplicate anchorId"
    # Anchor names are unique across the account, including mixed object types.
    seen_anchor_names = []
    for anchor in account["anchors"]:
        anchor_name = anchor["name"]
        assert anchor_name not in seen_anchor_names, f"{name}: duplicate anchor name {anchor_name!r}"
        seen_anchor_names.append(anchor_name)
    notes = account.get("notes") or []
    note_ids = ids_in(notes, "noteId")
    assert len(note_ids) == len(notes), f"{name}: duplicate noteId"
    field_ids = ids_in(account.get("customFields") or [], "fieldId")

    for member in account["members"]:
        assert isinstance(member.get("fronting"), bool), (
            f"{name}: member {member.get('memberId')} fronting must be a boolean")
        for nid in member.get("noteIds") or []:
            assert nid in note_ids, f"{name}: member {member['memberId']} note {nid} missing"
        for fid in member.get("fieldIds") or []:
            assert fid in field_ids, f"{name}: member {member['memberId']} field {fid} missing"

    for rec in account.get("notes") or []:
        _assert_inherit_settings(rec, name, f"note {rec.get('noteId')}")
        for tag in rec.get("tags") or []:
            assert tag, f"{name}: empty note tag"

    for rec in account.get("customFields") or []:
        assert rec["fieldId"] in field_ids
        _assert_inherit_settings(rec, name, f"custom field {rec['fieldId']}")
    seen_rel_ids = []
    for rec in account.get("relationships") or []:
        rid = rec.get("relationshipId")
        assert rid, f"{name}: relationship missing relationshipId"
        assert rid not in seen_rel_ids, f"{name}: duplicate relationshipId {rid}"
        seen_rel_ids.append(rid)
        for key in ("relationshipType", "relationshipStatus", "parentAnchorId", "anchorId"):
            assert key not in rec, f"{name}: relationship {rid} still has {key}"
        source = rec.get("sourceAnchorId")
        field_id = rec.get("fieldId")
        assert source, f"{name}: relationship {rid} sourceAnchorId is required"
        assert field_id, f"{name}: relationship {rid} fieldId is required"
        assert source in anchor_ids, f"{name}: relationship {rid} source {source} missing"
        assert field_id in field_ids, f"{name}: relationship {rid} field {field_id} missing"
        assert "targetAnchorId" in rec, f"{name}: relationship {rid} targetAnchorId is required"
        target = rec["targetAnchorId"]
        assert target not in (0, "", "null"), f"{name}: relationship {rid} targetAnchorId must be an id or JSON null"
        if target is not None:
            assert target in anchor_ids, f"{name}: relationship {rid} target {target} missing"
    for rec in account.get("frontHistory") or []:
        for mid in rec["memberIds"]:
            assert mid in member_ids, f"{name}: frontHistory {rec['frontHistoryId']} member {mid}"

    for anchor in account["anchors"]:
        for fid in anchor.get("fieldIds") or []:
            assert fid in field_ids, f"{name}: anchor {anchor['anchorId']} field {fid} missing"
        for nid in anchor.get("noteIds") or []:
            assert nid in note_ids, f"{name}: anchor {anchor['anchorId']} note {nid} missing"

    seen_tree = []
    for node in walk_tree(account["tree"]):
        assert node["anchorId"] in anchor_ids, f"{name}: tree anchor {node['anchorId']} missing"
        assert node["anchorId"] not in seen_tree, f"{name}: tree repeats anchor {node['anchorId']}"
        seen_tree.append(node["anchorId"])
        for occ in node.get("members") or []:
            assert occ["memberId"] in member_ids, (
                f"{name}: tree member {occ['memberId']} missing from shared members")
            assert "fronting" not in occ, f"{name}: fronting belongs on shared members, not tree occurrences"
            _assert_inherit_settings(occ, name, f"tree occurrence {occ['memberId']} under {node['anchorId']}")


def validate_topology(export, name="export"):
    """Per-example structural contract: names, tree order, relationship labels, fronting, archives."""
    example_id = export["pluralBridgeExport"]["exampleId"]
    account = _acct(export)
    names = _anchor_names(export, "system")
    member_names = {m["memberId"]: m["displayName"] for m in account["members"]}
    group_names = _anchor_names(export, "group")
    place_names = _anchor_names(export, "place")
    tree = _tree_index(export)
    relationships = account.get("relationships") or []

    if example_id == "example-001":
        assert names == {"system-001": "The Harbor"}
        assert set(member_names.values()) == {"A", "B", "C"}
        assert set(group_names.values()) == {"Musicians", "Dancers", "Ballet"}
        assert _child_ids(tree["group-002"]) == ["group-003"]
        assert "group-003" in tree
        assert _tree_member_ids(tree["system-001"]) == ["member-001", "member-002", "member-003"]
        assert _tree_member_ids(tree["group-001"]) == ["member-001", "member-003"]
        assert _tree_member_ids(tree["group-003"]) == ["member-001"]
        assert place_names == {}
        assert "relationships" not in account
        assert [m["displayName"] for m in account["members"] if m["fronting"]] == ["A", "B"]
    elif example_id == "example-002":
        assert set(names.values()) == {"The Harbor", "The Observatory"}
        assert "relationships" not in account
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert [node["anchorId"] for node in account["tree"]] == ["system-001", "system-002"]
        assert _system_members(export, "system-002") == {"C"}
        assert not any(m["fronting"] for m in account["members"])
    elif example_id == "example-003":
        assert "relationships" not in account
        assert [node["anchorId"] for node in account["tree"]] == ["system-001"]
        assert _child_ids(tree["system-001"]) == ["group-001", "system-002"]
        assert _tree_member_ids(tree["system-002"]) == ["member-003", "member-004"]
        assert _child_ids(tree["system-002"]) == []
        assert _system_members(export, "system-002") == {"Kit", "Lark"}
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"Kit", "Lark"}
    elif example_id == "example-004":
        assert _rel_labels(export) == {
            ("system-001", "sibling", "system-002"),
            ("system-002", "sibling", "system-001"),
        }
        assert len({r["fieldId"] for r in relationships}) == 1
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"C", "D"}
    elif example_id == "example-005":
        assert _rel_labels(export) == {
            ("system-001", "related", "system-002"),
            ("system-002", "related", "system-001"),
        }
        assert len({r["fieldId"] for r in relationships}) == 1
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"C"}
    elif example_id == "example-006":
        assert names == {"system-001": "The Harbor"}
        assert export["pluralBridgeExport"]["exampleName"] == "Nested Structure Model"
        assert set(place_names.values()) == {"Morgan's Room"}
        assert _child_ids(tree["system-001"]) == ["group-001", "place-001"]
        assert _system_members(export, "system-001") == {"Alex", "Morgan", "Rae"}
        assert _tree_member_ids(tree["place-001"]) == ["member-004", "member-005"]
        assert {member_names[mid] for mid in _tree_member_ids(tree["place-001"])} == {"M1", "M2"}
        assert "relationships" not in account
        assert len(_anchors_of_type(export, "system")) == 1
        assert not any(m["fronting"] for m in account["members"])
    elif example_id == "example-007":
        # evolving and unknown are separate rows; neither is copied onto anchor.fieldIds.
        assert len(relationships) == 2
        evolving = relationships[0]
        unknown = relationships[1]
        assert evolving["relationshipId"] == "relationship-003"
        assert evolving["sourceAnchorId"] == "system-002"
        assert evolving["fieldId"] == "custom-field-evolving"
        assert evolving["targetAnchorId"] is None
        assert unknown["relationshipId"] == "relationship-004"
        assert unknown["sourceAnchorId"] == "system-002"
        assert unknown["fieldId"] == "custom-field-unknown"
        assert unknown["targetAnchorId"] is None
        assert _rel_labels(export) == {
            ("system-002", "evolving", None),
            ("system-002", "unknown", None),
        }
        harbor_fields = next(a for a in account["anchors"] if a["anchorId"] == "system-001").get("fieldIds") or []
        north_fields = next(a for a in account["anchors"] if a["anchorId"] == "system-002").get("fieldIds") or []
        assert "custom-field-evolving" not in harbor_fields
        assert "custom-field-evolving" not in north_fields
        assert "custom-field-unknown" not in harbor_fields
        assert "custom-field-unknown" not in north_fields
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"C"}
    elif example_id == "example-008":
        # Archive flags on systems, members, groups, notes, and fronts are independent of the label.
        assert len(relationships) == 1
        archived = relationships[0]
        assert archived["relationshipId"] == "relationship-001"
        assert archived["sourceAnchorId"] == "system-002"
        assert archived["fieldId"] == "custom-field-archived"
        assert archived["targetAnchorId"] is None
        assert _rel_labels(export) == {("system-002", "archived", None)}
        old = next(a for a in account["anchors"] if a["anchorId"] == "system-002")
        assert "custom-field-archived" not in (old.get("fieldIds") or [])
        assert "custom-field-archived" not in (
            next(a for a in account["anchors"] if a["anchorId"] == "system-001").get("fieldIds") or [])
        current = next(a for a in account["anchors"] if a["anchorId"] == "system-001")
        assert old["isArchived"] is True and old["status"] == "archived"
        assert current["isArchived"] is False and current["status"] == "active"
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert _child_ids(tree["system-002"]) == ["group-002"]
        archive_members = [m for m in account["members"] if m["memberId"] in ("member-003", "member-004")]
        assert all(m["isArchived"] is True for m in archive_members)
        old_group = next(a for a in account["anchors"] if a["anchorId"] == "group-002")
        assert old_group["isArchived"] is True
        assert old_group.get("tags") == ["historical-organization"]
        old_note = next(n for n in account["notes"] if n["noteId"] == "note-002")
        assert old_note["isArchived"] is True
        assert old_note.get("tags") == ["historical-note"]
        old_front = next(f for f in account["frontHistory"] if f["frontHistoryId"] == "front-002")
        assert old_front["isArchived"] is True
        assert old_front.get("tags") == ["historical-fronting-context"]
        assert all(occ.get("tags") == ["historical-system-member"] for occ in tree["system-002"]["members"])
        assert not any(m["fronting"] for m in account["members"])
    elif example_id == "example-009":
        assert _rel_labels(export) == {
            ("system-001", "related", "system-002"),
            ("system-002", "sibling", "system-003"),
            ("system-003", "associated", "system-001"),
        }
        assert _child_ids(tree["system-001"]) == ["group-001"]
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"C1"}
    elif example_id == "example-010":
        assert group_names["group-001"] == "Household"
        assert [node["anchorId"] for node in account["tree"]] == ["group-001"]
        assert _child_ids(tree["group-001"]) == ["system-001", "system-002"]
        assert "relationships" not in account
        assert _system_members(export, "system-001") == {"W", "Y"}
        assert _system_members(export, "system-002") == {"X", "Z"}
        assert {member_names[mid] for mid in _tree_member_ids(tree["group-001"])} == {"A", "E", "I", "O"}
        assert place_names == {}
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"A"}
    elif example_id == "example-011":
        assert set(place_names.values()) == {"Central Hub", "Waiting Room"}
        assert [node["anchorId"] for node in account["tree"]] == ["place-001"]
        assert _child_ids(tree["place-001"]) == ["system-001", "system-002"]
        assert "place-002" not in _child_ids(tree["place-001"])
        assert _child_ids(tree["system-002"]) == ["place-002"]
        assert _system_members(export, "system-001") == {"Popeye", "Gilligan"}
        assert _system_members(export, "system-002") == set()
        assert {member_names[mid] for mid in _tree_member_ids(tree["place-002"])} == {"Mickey", "Minnie"}
        assert _anchors_of_type(export, "group") == []
        assert "relationships" not in account
        assert {m["displayName"] for m in account["members"] if m["fronting"]} == {"Popeye"}
    elif example_id == "example-012":
        # Keep the historical provenance filename even if the live spec was renamed.
        assert account["accountId"] == "account-012"
        assert _anchors_of_type(export, "system") == []
        for key in ("memberships", "relationships", "notes", "frontHistory",
                    "customFields", "privacyBuckets", "visibilityScopes"):
            assert key not in account, f"{name}: {key} must be omitted"
        assert group_names == {"group-001": "The Harbor", "group-002": "Main House"}
        assert place_names == {"place-001": "Central Hub", "place-002": "Waiting Room"}
        assert member_names == {
            "member-001": "Popeye", "member-002": "Gilligan",
            "member-003": "Mickey", "member-004": "Minnie",
        }
        assert len(account["anchors"]) == 4
        assert len(account["members"]) == 4
        assert [node["anchorId"] for node in account["tree"]] == ["place-001"]
        assert _child_ids(tree["place-001"]) == ["group-001", "group-002"]
        assert _child_ids(tree["group-002"]) == ["place-002"]
        assert _tree_member_ids(tree["group-001"]) == ["member-001", "member-002"]
        assert _tree_member_ids(tree["group-002"]) == []
        assert _tree_member_ids(tree["place-002"]) == ["member-003", "member-004"]
        assert _tree_member_ids(tree["place-001"]) == []
        assert "member-004" not in _tree_member_ids(tree["group-001"])
        assert all(m["fronting"] is False for m in account["members"])
        prov = export["provenance"]
        assert prov["sourceGenerator"] == "example-012-document-transcription"
        assert prov["sourceIdsPreserved"] is False
        assert prov["sourceDocument"] == "PluralBridge-Plural-Maps-and-Design-Rules.txt"
        assert prov["sourceExample"] == 12
    else:
        raise AssertionError(f"{name}: unknown exampleId {example_id}")


def validate_export(export, name="export"):
    """Synthetic header plus schema, reference, and topology checks used by generate.py."""
    header = export["pluralBridgeExport"]
    assert header.get("exportKind") == EXPORT_KIND, f"{name}: exportKind"
    assert str(header.get("modelingNote", "")).startswith("Synthetic"), f"{name}: modelingNote"
    validate_schema(export, name)
    validate_unique_memberships(export, name)
    validate_references(export, name)
    validate_topology(export, name)


def structural_facts(export):
    """Order-independent facts used as a secondary summary of a hierarchical export."""
    account = _acct(export)
    tree = [
        (node["anchorId"], tuple(_tree_member_ids(node)), tuple(_child_ids(node)))
        for node in walk_tree(account.get("tree"))
    ]
    return {
        "example_id": export["pluralBridgeExport"]["exampleId"],
        "account_id": account["accountId"],
        "anchor_names": sorted((a["anchorId"], a["objectType"], a["name"]) for a in account["anchors"]),
        "member_names": sorted((m["memberId"], m["displayName"], m["fronting"]) for m in account["members"]),
        "relationships": sorted(
            (r["sourceAnchorId"], r["fieldId"], r.get("targetAnchorId"))
            for r in account.get("relationships") or []),
        "tree": tree,
    }
