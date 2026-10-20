#!/usr/bin/env python3
"""PluralBridge system-model topologies and export builder.

Each of the eleven canonical configurations is defined as a compact topology
(entities, graph relationships, containment placements, memberships). `assemble`
expands that topology into the flattened PluralBridge export shape, including
empty arrays for unused collections.

This is generation, not JSON embedding: link, placement, membership, lookup, and
wrapper records are created programmatically from the topology.
"""
from collections import OrderedDict

EXPORT_VERSION = "0.1-draft"
EXPORT_KIND = "self-contained-pluralbridge-example"
SOURCE_GENERATOR = "plural-synthetic"

REQUIRED_COLLECTIONS = (
    "pluralBridgeExport",
    "accounts",
    "memberships",
    "systems",
    "systemRelationships",
    "accountObjectLinks",
    "accountObjectPlacements",
    "systemObjectLinks",
    "systemObjectPlacements",
    "members",
    "groups",
    "groupMemberships",
    "places",
    "placeMemberships",
    "notes",
    "frontHistory",
    "customFields",
    "privacyBuckets",
    "visibilityScopes",
    "provenance",
    "audit",
    "lookups",
)

OBJECT_ID_FIELDS = {
    "member": ("members", "memberId"),
    "group": ("groups", "groupId"),
    "place": ("places", "placeId"),
    "note": ("notes", "noteId"),
    "frontHistory": ("frontHistory", "frontHistoryId"),
    "customField": ("customFields", "customFieldId"),
    "privacyBucket": ("privacyBuckets", "privacyBucketId"),
    "visibilityScope": ("visibilityScopes", "visibilityScopeId"),
    "system": ("systems", "systemId"),
    "account": ("accounts", "accountId"),
}

FIXED_AUDIT = {"createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"}

# ---------------------------------------------------------------- record builders


def account(n):
    return {
        "accountId": f"account-{n:03d}",
        "displayName": f"Example {n}",
        "username": f"example-{n}",
        "email": f"example-{n}@pluralbridge.org",
        "status": "Active",
    }


def system_rec(system_id, name, description, color, **extra):
    rec = {"systemId": system_id, "name": name, "description": description, "color": color}
    rec.update(extra)
    return rec


def member_rec(member_id, display_name, pronouns, description, color, archived=False, reason=None):
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
    return {
        "customFieldId": field_id,
        "fieldName": name,
        "fieldType": "text",
        "description": description,
        "supportsMarkdown": False,
    }


def bucket_rec(bucket_id, name, description, color="#1998a8"):
    return {
        "privacyBucketId": bucket_id,
        "name": name,
        "description": description,
        "color": color,
    }


def scope_rec(scope_id, member_ids, name="Private"):
    return {
        "visibilityScopeId": scope_id,
        "name": name,
        "description": "Visible only through explicit private visibility rules.",
        "isSystemDefault": False,
        "isActive": True,
        "memberIds": list(member_ids),
    }


def unique_append(seq, value):
    if value not in seq:
        seq.append(value)


def _numbered(prefix, rows, id_field):
    out = []
    for i, row in enumerate(rows, 1):
        rec = dict(row)
        rec.setdefault(id_field, f"{prefix}-{i:03d}")
        out.append(rec)
    return out


def _link_rows(pairs, id_prefix, owner_field):
    rows = []
    for item in pairs:
        owner_id, object_type, object_id, link_role = item
        rows.append({
            owner_field: owner_id,
            "objectType": object_type,
            "objectId": object_id,
            "linkRole": link_role,
        })
    return _numbered(id_prefix, rows, "linkId")


def _placement_rows(items, id_prefix, owner_field):
    rows = []
    for item in items:
        owner_id, object_type, object_id, parent_type, parent_id, rank = item[:6]
        role = item[6] if len(item) > 6 else "container-child"
        rows.append({
            owner_field: owner_id,
            "objectType": object_type,
            "objectId": object_id,
            "parentObjectType": parent_type,
            "parentObjectId": parent_id,
            "placementRole": role,
            "rank": rank,
        })
    return _numbered(id_prefix, rows, "placementId")


def _membership_rows(pairs, id_prefix):
    rows = []
    for item in pairs:
        group_or_place_field, container_id, member_id, rank = item
        rows.append({group_or_place_field: container_id, "memberId": member_id, "rank": rank})
    key = "groupMembershipId" if id_prefix.startswith("group-membership") else "placeMembershipId"
    return _numbered(id_prefix, rows, key)


def derive_lookups(export):
    lookups = OrderedDict()
    roles, statuses, rel_types = [], [], []
    for rec in export["memberships"]:
        unique_append(statuses, rec["status"])
        for role in rec.get("roles", []):
            unique_append(roles, role)
    for rec in export["systemRelationships"]:
        unique_append(rel_types, rec["relationshipType"])
    lookups["roles"] = roles
    lookups["membershipStatuses"] = statuses
    lookups["relationshipTypes"] = rel_types

    rel_statuses, sys_statuses, account_types, placement_roles = [], [], [], []
    for rec in export["systemRelationships"]:
        if rec.get("relationshipStatus"):
            unique_append(rel_statuses, rec["relationshipStatus"])
    for rec in export["systems"]:
        if rec.get("status"):
            unique_append(sys_statuses, rec["status"])
    for rec in export["accountObjectLinks"]:
        unique_append(account_types, rec["objectType"])
    for rec in export["accountObjectPlacements"] + export["systemObjectPlacements"]:
        unique_append(placement_roles, rec["placementRole"])
    if rel_statuses:
        lookups["relationshipStatuses"] = rel_statuses
    if sys_statuses:
        lookups["systemStatuses"] = sys_statuses
    if account_types:
        lookups["accountObjectTypes"] = account_types
    if placement_roles:
        lookups["placementRoles"] = placement_roles
    return dict(lookups)


def assemble(spec):
    """Expand a compact topology into a complete flattened export."""
    account_rec = spec["account"]
    systems = list(spec["systems"])
    membership_specs = spec.get("memberships")
    if membership_specs is None:
        memberships = []
        for i, system in enumerate(systems, 1):
            override = spec.get("membership_overrides", {}).get(system["systemId"], {})
            memberships.append({
                "membershipId": f"membership-{i:03d}",
                "accountId": account_rec["accountId"],
                "systemId": system["systemId"],
                "status": override.get("status", "Active"),
                "roles": list(override.get("roles", ["Owner"])),
            })
    else:
        memberships = _numbered("membership", membership_specs, "membershipId")

    relationships = []
    for i, rel in enumerate(spec.get("relationships", []), 1):
        rec = {
            "relationshipId": rel.get("relationshipId", f"relationship-{i:03d}"),
            "systemId": rel["systemId"],
            "relationshipType": rel["relationshipType"],
            "parentSystemId": rel.get("parentSystemId"),
            "targetSystemId": rel.get("targetSystemId"),
            "rank": rel.get("rank", 1),
        }
        for key in ("associatedObjectType", "associatedObjectId", "relationshipStatus", "description"):
            if key in rel:
                rec[key] = rel[key]
        relationships.append(rec)

    export = {
        "pluralBridgeExport": {
            "exportVersion": EXPORT_VERSION,
            "exportKind": EXPORT_KIND,
            "exampleId": spec["example_id"],
            "exampleName": spec["example_name"],
            "modelingNote": spec["modeling_note"],
        },
        "accounts": [account_rec],
        "memberships": memberships,
        "systems": systems,
        "systemRelationships": relationships,
        "accountObjectLinks": _link_rows(spec.get("account_links", []), "account-link", "accountId"),
        "accountObjectPlacements": _placement_rows(
            spec.get("account_placements", []), "account-placement", "accountId"),
        "systemObjectLinks": _link_rows(spec.get("system_links", []), "link", "systemId"),
        "systemObjectPlacements": _placement_rows(
            spec.get("system_placements", []), "placement", "systemId"),
        "members": list(spec.get("members", [])),
        "groups": list(spec.get("groups", [])),
        "groupMemberships": _membership_rows(
            [("groupId", gid, mid, rank) for gid, mid, rank in spec.get("group_memberships", [])],
            "group-membership"),
        "places": list(spec.get("places", [])),
        "placeMemberships": _membership_rows(
            [("placeId", pid, mid, rank) for pid, mid, rank in spec.get("place_memberships", [])],
            "place-membership"),
        "notes": list(spec.get("notes", [])),
        "frontHistory": list(spec.get("front_history", [])),
        "customFields": list(spec.get("custom_fields", [])),
        "privacyBuckets": list(spec.get("privacy_buckets", [])),
        "visibilityScopes": list(spec.get("visibility_scopes", [])),
        "provenance": {
            "source": "synthetic",
            "sourceGenerator": SOURCE_GENERATOR,
            "sourceIdsPreserved": True,
            "lossyMappings": [],
        },
        "audit": dict(FIXED_AUDIT),
    }
    export["lookups"] = derive_lookups(export)
    assert list(export) == list(REQUIRED_COLLECTIONS)
    return export


# ---------------------------------------------------------------- topologies


def spec_001():
    harbor = "system-001"
    return {
        "filename": "example-001-simple-single-system.json",
        "example_id": "example-001",
        "example_name": "Simple Single-System Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "System context is represented by explicit relationship and object-link records. "
            "Group placement is modeled explicitly so groups can be anchored anywhere within a system."
        ),
        "account": account(1),
        "systems": [system_rec(harbor, "The Harbor",
                               "A simple single-system example with one shared System context.", "#8367ea")],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
        ],
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
    harbor, observatory = "system-001", "system-002"
    return {
        "filename": "example-002-multiple-top-level-systems.json",
        "example_id": "example-002",
        "example_name": "Multiple Top-Level Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example has two root-level Systems. Neither System owns or contains the other."
        ),
        "account": account(2),
        "systems": [
            system_rec(harbor, "The Harbor", "Primary root-level System.", "#8367ea"),
            system_rec(observatory, "The Observatory",
                       "Second root-level System. Neither root owns the other.", "#4f8fcf"),
        ],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": observatory, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
        ],
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
    main, workshop = "system-001", "system-002"
    return {
        "filename": "example-003-parent-child-system.json",
        "example_id": "example-003",
        "example_name": "Parent / Child System Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example has one root-level System and one child System. The parent/child "
            "relationship describes structure; access is represented through explicit memberships "
            "rather than inherited ownership."
        ),
        "account": account(3),
        "systems": [
            system_rec(main, "Main House", "Root-level System.", "#8367ea"),
            system_rec(workshop, "The Workshop",
                       "Child System structurally related to Main House. Access and privacy remain "
                       "governed by membership, consent, and policy.", "#4f8fcf"),
        ],
        "relationships": [
            {"systemId": main, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": workshop, "relationshipType": "child", "parentSystemId": main,
             "targetSystemId": None, "rank": 1},
        ],
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
    day, night = "system-001", "system-002"
    return {
        "filename": "example-004-sibling-systems.json",
        "example_id": "example-004",
        "example_name": "Sibling Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example has two sibling Systems with an explicit peer relationship. "
            "Neither System owns, contains, or controls the other."
        ),
        "account": account(4),
        "systems": [
            system_rec(day, "Day Team", "Root-level System operating in parallel with Night Team.", "#8367ea"),
            system_rec(night, "Night Team", "Root-level System operating in parallel with Day Team.", "#4f8fcf"),
        ],
        "relationships": [
            {"systemId": day, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": night, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
            {"systemId": day, "relationshipType": "sibling", "parentSystemId": None,
             "targetSystemId": night, "rank": 1},
            {"systemId": night, "relationshipType": "sibling", "parentSystemId": None,
             "targetSystemId": day, "rank": 1},
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
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in Day Team.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in Day Team.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_005():
    harbor, archive = "system-001", "system-002"
    return {
        "filename": "example-005-related-systems.json",
        "example_id": "example-005",
        "example_name": "Related Systems Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example has two Systems associated by reciprocal related records. "
            "Each System is labeled related with no arrow, so both directions are encoded. "
            "The records describe association without parentage, containment, ownership, "
            "or automatic authority."
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
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": archive, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
            {"systemId": archive, "relationshipType": "related", "parentSystemId": None,
             "targetSystemId": harbor, "rank": 1},
            {"systemId": harbor, "relationshipType": "related", "parentSystemId": None,
             "targetSystemId": archive, "rank": 1},
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
        ],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_006():
    harbor = "system-001"
    return {
        "filename": "example-006-subsystem.json",
        "example_id": "example-006",
        "example_name": "Subsystem Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "Morgan's Room is a Place inside The Harbor, not a second System. Place containment "
            "uses system object-link and placement records; M1 and M2 belong to the Place rather "
            "than to The Harbor member list."
        ),
        "account": account(6),
        "systems": [system_rec(harbor, "The Harbor",
                               "Root-level System containing members, a group, and a Place.", "#8367ea")],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
        ],
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
    harbor, north = "system-001", "system-002"
    return {
        "filename": "example-007-evolving-uncertain-relationship.json",
        "example_id": "example-007",
        "example_name": "Evolving / Uncertain Relationship Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example preserves a real but unresolved relationship between two Systems "
            "without prematurely naming it as parent, child, sibling, subsystem, or ownership."
        ),
        "account": account(7),
        "systems": [
            system_rec(harbor, "The Harbor",
                       "Root-level System with an unresolved relationship to North Wing.", "#8367ea"),
            system_rec(north, "North Wing",
                       "System connected to The Harbor. The exact relationship is still forming.", "#4f8fcf"),
        ],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": north, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
            {"systemId": north, "relationshipType": "evolving", "parentSystemId": None,
             "targetSystemId": harbor, "relationshipStatus": "unknown",
             "description": "North Wing is connected to The Harbor, but the user has not resolved "
                            "whether that connection is sibling, child, subsystem, related, or another structure.",
             "rank": 1},
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
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in The Harbor.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in The Harbor.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_008():
    current, old = "system-001", "system-002"
    return {
        "filename": "example-008-archived-system.json",
        "example_id": "example-008",
        "example_name": "Archived System Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example preserves an archived System as historically meaningful data. "
            "Old Map and its existing members, groups, notes, front history, and associations "
            "are retained. Per-object archive flags on those associated records are independent "
            "facts, not an automatic cascade from the System lifecycle."
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
        "membership_overrides": {old: {"status": "Historical"}},
        "relationships": [
            {"systemId": current, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": old, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
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
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in Current System.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in Current System.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_009():
    a, b, c = "system-001", "system-002", "system-003"
    return {
        "filename": "example-009-non-tree-graph.json",
        "example_id": "example-009",
        "example_name": "Non-Tree / Graph Model",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "This example breaks the ordinary tree assumption by representing Systems as graph "
            "nodes connected through multiple explicit relationship records. No single trunk, "
            "root hierarchy, or forced parentage is required."
        ),
        "account": account(9),
        "systems": [
            system_rec(a, "A", "Graph node System A.", "#8367ea"),
            system_rec(b, "B", "Graph node System B.", "#4f8fcf"),
            system_rec(c, "C", "Graph node System C.", "#f5a623"),
        ],
        "relationships": [
            {"systemId": a, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": b, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
            {"systemId": c, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 3},
            {"systemId": a, "relationshipType": "related", "parentSystemId": None,
             "targetSystemId": b, "rank": 1, "description": "System A is related to System B."},
            {"systemId": b, "relationshipType": "sibling", "parentSystemId": None,
             "targetSystemId": c, "rank": 1, "description": "System B is a sibling of System C."},
            {"systemId": c, "relationshipType": "associated", "parentSystemId": None,
             "targetSystemId": a, "rank": 1, "description": "System C is associated with System A."},
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
        "custom_fields": [field_rec("custom-field-001", "System Role",
                                    "Synthetic custom field defined in System A.")],
        "privacy_buckets": [bucket_rec("privacy-bucket-001", "Trusted",
                                       "Synthetic privacy bucket defined in System A.")],
        "visibility_scopes": [scope_rec("visibility-scope-001", ["member-001"])],
    }


def spec_010():
    harbor, house = "system-001", "system-002"
    acct = account(10)
    aid = acct["accountId"]
    return {
        "filename": "example-010-top-level-group-containing-systems.json",
        "example_id": "example-010",
        "example_name": "Top-Level Group Containing Systems",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "Account-level structure is represented by explicit account object-link and placement "
            "records so a group can act as a top-level container for systems. Systems remain "
            "relationship-graph roots because they have no parent System."
        ),
        "account": acct,
        "systems": [
            system_rec(harbor, "The Harbor",
                       "Synthetic system contained within the Household group.", "#8367ea"),
            system_rec(house, "Main House",
                       "Second synthetic system contained within the Household group.", "#4a90e2"),
        ],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": house, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
        ],
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
    harbor, house = "system-001", "system-002"
    acct = account(11)
    aid = acct["accountId"]
    return {
        "filename": "example-011-top-level-place-containing-systems.json",
        "example_id": "example-011",
        "example_name": "Place Collection of Systems",
        "modeling_note": (
            "Synthetic PluralBridge example using flattened top-level collections. "
            "A top-level place contains two systems via account placements. Waiting Room is a "
            "Place inside Main House and is modeled with system object-link and placement records."
        ),
        "account": acct,
        "systems": [
            system_rec(harbor, "The Harbor", "System under Central Hub place.", "#8367ea"),
            system_rec(house, "Main House",
                       "System under Central Hub place containing nested Waiting Room place.", "#4a90e2"),
        ],
        "relationships": [
            {"systemId": harbor, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 1},
            {"systemId": house, "relationshipType": "root", "parentSystemId": None,
             "targetSystemId": None, "rank": 2},
        ],
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


SPECS = [
    spec_001, spec_002, spec_003, spec_004, spec_005, spec_006,
    spec_007, spec_008, spec_009, spec_010, spec_011,
]


def build_all():
    """Return {filename: export} for all eleven canonical configurations."""
    out = OrderedDict()
    for spec_fn in SPECS:
        spec = spec_fn()
        export = assemble(spec)
        out[spec["filename"]] = export
    return dict(out)


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
]


# ---------------------------------------------------------------- validation


def ids_in(collection, id_field):
    return {row[id_field] for row in collection}


def validate_schema(export, name="export"):
    missing = [key for key in REQUIRED_COLLECTIONS if key not in export]
    extra = [key for key in export if key not in REQUIRED_COLLECTIONS]
    assert not missing, f"{name}: missing collections {missing}"
    assert not extra, f"{name}: unexpected collections {extra}"
    for key in REQUIRED_COLLECTIONS:
        if key in ("pluralBridgeExport", "provenance", "audit", "lookups"):
            assert isinstance(export[key], dict), f"{name}: {key} must be an object"
        else:
            assert isinstance(export[key], list), f"{name}: {key} must be an array"


def validate_unique_memberships(export, name="export"):
    seen = []
    for rec in export["memberships"]:
        key = (rec["accountId"], rec["systemId"])
        assert key not in seen, f"{name}: duplicate membership for {key}"
        seen.append(key)


def _resolve(export, object_type, object_id, name, context):
    if object_type not in OBJECT_ID_FIELDS:
        raise AssertionError(f"{name}: unknown objectType {object_type!r} in {context}")
    coll, field = OBJECT_ID_FIELDS[object_type]
    assert object_id in ids_in(export[coll], field), (
        f"{name}: {context} references {object_type} {object_id} missing from {coll}")


def validate_references(export, name="export"):
    account_ids = ids_in(export["accounts"], "accountId")
    system_ids = ids_in(export["systems"], "systemId")
    member_ids = ids_in(export["members"], "memberId")
    group_ids = ids_in(export["groups"], "groupId")
    place_ids = ids_in(export["places"], "placeId")

    for rec in export["memberships"]:
        assert rec["accountId"] in account_ids, f"{name}: membership account {rec['accountId']}"
        assert rec["systemId"] in system_ids, f"{name}: membership system {rec['systemId']}"
    for rec in export["systemRelationships"]:
        assert rec["systemId"] in system_ids, f"{name}: relationship system {rec['systemId']}"
        for key in ("parentSystemId", "targetSystemId"):
            if rec.get(key) is not None:
                assert rec[key] in system_ids, f"{name}: relationship {key} {rec[key]}"
        if rec.get("associatedObjectType"):
            _resolve(export, rec["associatedObjectType"], rec["associatedObjectId"],
                     name, rec["relationshipId"])
    for rec in export["systemObjectLinks"]:
        assert rec["systemId"] in system_ids, f"{name}: system link {rec['linkId']}"
        _resolve(export, rec["objectType"], rec["objectId"], name, rec["linkId"])
    for rec in export["accountObjectLinks"]:
        assert rec["accountId"] in account_ids, f"{name}: account link {rec['linkId']}"
        _resolve(export, rec["objectType"], rec["objectId"], name, rec["linkId"])
    for rec in export["systemObjectPlacements"]:
        assert rec["systemId"] in system_ids, f"{name}: placement {rec['placementId']}"
        _resolve(export, rec["objectType"], rec["objectId"], name, rec["placementId"])
        _resolve(export, rec["parentObjectType"], rec["parentObjectId"],
                 name, rec["placementId"] + " parent")
    for rec in export["accountObjectPlacements"]:
        assert rec["accountId"] in account_ids, f"{name}: account placement {rec['placementId']}"
        _resolve(export, rec["objectType"], rec["objectId"], name, rec["placementId"])
        _resolve(export, rec["parentObjectType"], rec["parentObjectId"],
                 name, rec["placementId"] + " parent")
    for rec in export["groupMemberships"]:
        assert rec["groupId"] in group_ids, f"{name}: groupMembership {rec['groupMembershipId']}"
        assert rec["memberId"] in member_ids, f"{name}: groupMembership member {rec['memberId']}"
    for rec in export["placeMemberships"]:
        assert rec["placeId"] in place_ids, f"{name}: placeMembership {rec['placeMembershipId']}"
        assert rec["memberId"] in member_ids, f"{name}: placeMembership member {rec['memberId']}"
    for rec in export["frontHistory"]:
        for mid in rec["memberIds"]:
            assert mid in member_ids, f"{name}: frontHistory {rec['frontHistoryId']} member {mid}"
    for rec in export["visibilityScopes"]:
        for mid in rec["memberIds"]:
            assert mid in member_ids, f"{name}: visibilityScope {rec['visibilityScopeId']} member {mid}"


def _rel_set(export):
    return {(r["systemId"], r["relationshipType"], r.get("parentSystemId"), r.get("targetSystemId"))
            for r in export["systemRelationships"]}


def _sys_place_set(export):
    return {(p["systemId"], p["objectType"], p["objectId"], p["parentObjectType"], p["parentObjectId"])
            for p in export["systemObjectPlacements"]}


def _acct_place_set(export):
    return {(p["accountId"], p["objectType"], p["objectId"], p["parentObjectType"], p["parentObjectId"])
            for p in export["accountObjectPlacements"]}


def _sys_link_set(export):
    return {(l["systemId"], l["objectType"], l["objectId"], l["linkRole"])
            for l in export["systemObjectLinks"]}


def _system_members(export, system_id):
    member_ids = {l["objectId"] for l in export["systemObjectLinks"]
                  if l["systemId"] == system_id and l["objectType"] == "member"}
    names = {m["memberId"]: m["displayName"] for m in export["members"]}
    return {names[mid] for mid in member_ids}


def validate_topology(export, name="export"):
    example_id = export["pluralBridgeExport"]["exampleId"]
    names = {s["systemId"]: s["name"] for s in export["systems"]}
    member_names = {m["memberId"]: m["displayName"] for m in export["members"]}
    group_names = {g["groupId"]: g["name"] for g in export["groups"]}
    place_names = {p["placeId"]: p["name"] for p in export["places"]}
    rels = _rel_set(export)
    sys_places = _sys_place_set(export)
    acct_places = _acct_place_set(export)

    if example_id == "example-001":
        assert names == {"system-001": "The Harbor"}
        assert {m["displayName"] for m in export["members"]} == {"A", "B", "C"}
        assert set(group_names.values()) == {"Musicians", "Dancers", "Ballet"}
        assert ("system-001", "group", "group-003", "group", "group-002") in sys_places
        assert ("system-001", "frontHistory", "front-002", "fronting-context") in _sys_link_set(export)
        assert export["places"] == []
        assert len(export["memberships"]) == 1
        assert len(export["systemRelationships"]) == 1
        root = export["systemRelationships"][0]
        assert root["systemId"] == "system-001"
        assert root["relationshipType"] == "root"
        assert root["parentSystemId"] is None
        assert root["targetSystemId"] is None
    elif example_id == "example-002":
        assert set(names.values()) == {"The Harbor", "The Observatory"}
        assert {r[1] for r in rels} == {"root"}
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
        assert len(export["memberships"]) == 2
        assert _system_members(export, "system-002") == {"C"}
    elif example_id == "example-003":
        assert ("system-002", "child", "system-001", None) in rels
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
        assert not any(p[2] == "system-002" for p in sys_places)
        assert _system_members(export, "system-002") == {"Kit", "Lark"}
    elif example_id == "example-004":
        assert ("system-001", "sibling", None, "system-002") in rels
        assert ("system-002", "sibling", None, "system-001") in rels
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
        assert len(export["memberships"]) == 2
    elif example_id == "example-005":
        assert ("system-002", "related", None, "system-001") in rels
        assert ("system-001", "related", None, "system-002") in rels
        assert {r[1] for r in rels if r[1] != "root"} == {"related"}
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
    elif example_id == "example-006":
        assert names == {"system-001": "The Harbor"}
        assert set(place_names.values()) == {"Morgan's Room"}
        assert ("system-001", "place", "place-001", "system", "system-001") in sys_places
        assert ("system-001", "place", "place-001", "scoped-to-system") in _sys_link_set(export)
        assert _system_members(export, "system-001") == {"Alex", "Morgan", "Rae"}
        assert {member_names[r["memberId"]] for r in export["placeMemberships"]} == {"M1", "M2"}
        # This example uses Place containment under Harbor. Broader subsystem
        # endpoints and associated-object semantics are unspecified; this example
        # must not encode either.
        assert not any(r["relationshipType"] == "subsystem" for r in export["systemRelationships"])
        assert not any(r.get("associatedObjectId") == "member-002" for r in export["systemRelationships"])
        assert len(export["memberships"]) == 1
        assert len(export["systems"]) == 1
    elif example_id == "example-007":
        evolving = [r for r in export["systemRelationships"] if r["relationshipType"] == "evolving"]
        assert len(evolving) == 1
        assert evolving[0]["systemId"] == "system-002"
        assert evolving[0]["targetSystemId"] == "system-001"
        assert evolving[0]["relationshipType"] == "evolving"
        assert evolving[0]["parentSystemId"] is None
        assert ("system-002", "evolving", None, "system-001") in rels
        assert evolving[0]["relationshipStatus"] == "unknown"
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
        assert len(export["memberships"]) == 2
    elif example_id == "example-008":
        assert {r[1] for r in rels} == {"root"}
        assert not any(r[1] == "archived-predecessor" for r in rels)
        old = next(s for s in export["systems"] if s["systemId"] == "system-002")
        current = next(s for s in export["systems"] if s["systemId"] == "system-001")
        assert old["isArchived"] is True and old["status"] == "archived"
        assert current["isArchived"] is False and current["status"] == "active"
        statuses = {m["systemId"]: m["status"] for m in export["memberships"]}
        assert statuses == {"system-001": "Active", "system-002": "Historical"}
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
        assert ("system-002", "group", "group-002", "system", "system-002") in sys_places
        archive_members = [m for m in export["members"] if m["memberId"] in ("member-003", "member-004")]
        assert all(m["isArchived"] is True for m in archive_members)
        old_group = next(g for g in export["groups"] if g["groupId"] == "group-002")
        assert old_group["isArchived"] is True
        old_note = next(n for n in export["notes"] if n["noteId"] == "note-002")
        assert old_note["isArchived"] is True
        old_front = next(f for f in export["frontHistory"] if f["frontHistoryId"] == "front-002")
        assert old_front["isArchived"] is True
    elif example_id == "example-009":
        graph_edges = {
            ("system-001", "related", None, "system-002"),
            ("system-002", "sibling", None, "system-003"),
            ("system-003", "associated", None, "system-001"),
        }
        assert graph_edges <= rels
        assert {r[1] for r in rels} == {"root", "related", "sibling", "associated"}
        assert not any(r[1] == "child" for r in rels)
        assert len(export["memberships"]) == 3
        assert ("system-001", "group", "group-001", "system", "system-001") in sys_places
    elif example_id == "example-010":
        assert group_names["group-001"] == "Household"
        aid = export["accounts"][0]["accountId"]
        assert (aid, "group", "group-001", "account", aid) in acct_places
        assert (aid, "system", "system-001", "group", "group-001") in acct_places
        assert (aid, "system", "system-002", "group", "group-001") in acct_places
        assert {r[1] for r in rels} == {"root"}
        assert _system_members(export, "system-001") == {"W", "Y"}
        assert _system_members(export, "system-002") == {"X", "Z"}
        household = {member_names[r["memberId"]] for r in export["groupMemberships"]}
        assert household == {"A", "E", "I", "O"}
        assert export["places"] == []
        assert export["systemObjectPlacements"] == []
    elif example_id == "example-011":
        assert set(place_names.values()) == {"Central Hub", "Waiting Room"}
        aid = export["accounts"][0]["accountId"]
        assert (aid, "place", "place-001", "account", aid) in acct_places
        assert (aid, "system", "system-001", "place", "place-001") in acct_places
        assert (aid, "system", "system-002", "place", "place-001") in acct_places
        assert not any(p[2] == "place-002" for p in acct_places)
        assert ("system-002", "place", "place-002", "system", "system-002") in sys_places
        assert ("system-002", "place", "place-002", "scoped-to-system") in _sys_link_set(export)
        assert _system_members(export, "system-001") == {"Popeye", "Gilligan"}
        assert _system_members(export, "system-002") == set()
        waiting = {member_names[r["memberId"]] for r in export["placeMemberships"]
                   if r["placeId"] == "place-002"}
        assert waiting == {"Mickey", "Minnie"}
        assert export["groups"] == []
    else:
        raise AssertionError(f"{name}: unknown exampleId {example_id}")


def validate_export(export, name="export"):
    header = export["pluralBridgeExport"]
    assert header.get("exportKind") == EXPORT_KIND, f"{name}: exportKind"
    assert str(header.get("modelingNote", "")).startswith("Synthetic"), f"{name}: modelingNote"
    validate_schema(export, name)
    validate_unique_memberships(export, name)
    validate_references(export, name)
    validate_topology(export, name)


def structural_facts(export):
    """Order-independent facts used to compare generated output with fixtures."""
    def freeze_links(rows, owner):
        return sorted((r[owner], r["objectType"], r["objectId"], r["linkRole"]) for r in rows)

    def freeze_places(rows, owner):
        return sorted((r[owner], r["objectType"], r["objectId"], r["parentObjectType"],
                       r["parentObjectId"], r["placementRole"], r["rank"]) for r in rows)

    return {
        "example_id": export["pluralBridgeExport"]["exampleId"],
        "collections": tuple(sorted(export)),
        "account_ids": sorted(ids_in(export["accounts"], "accountId")),
        "system_names": sorted((s["systemId"], s["name"]) for s in export["systems"]),
        "member_names": sorted((m["memberId"], m["displayName"]) for m in export["members"]),
        "group_names": sorted((g["groupId"], g["name"]) for g in export["groups"]),
        "place_names": sorted((p["placeId"], p["name"]) for p in export["places"]),
        "memberships": sorted((m["accountId"], m["systemId"], m["status"]) for m in export["memberships"]),
        "relationships": sorted(
            (r["systemId"], r["relationshipType"], r.get("parentSystemId"), r.get("targetSystemId"),
             r.get("relationshipStatus"))
            for r in export["systemRelationships"]),
        "system_links": freeze_links(export["systemObjectLinks"], "systemId"),
        "account_links": freeze_links(export["accountObjectLinks"], "accountId"),
        "system_placements": freeze_places(export["systemObjectPlacements"], "systemId"),
        "account_placements": freeze_places(export["accountObjectPlacements"], "accountId"),
        "group_memberships": sorted(
            (g["groupId"], g["memberId"], g["rank"]) for g in export["groupMemberships"]),
        "place_memberships": sorted(
            (p["placeId"], p["memberId"], p["rank"]) for p in export["placeMemberships"]),
    }
