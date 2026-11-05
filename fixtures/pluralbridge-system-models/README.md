# PluralBridge Canonical Fixtures

This folder contains twelve self-contained PluralBridge canonical examples.
The authoritative specification is
[`PluralBridge-Plural-Maps-and-Design-Rules.txt`](PluralBridge-Plural-Maps-and-Design-Rules.txt).

`generate.py` builds these configurations from Python topologies in
`system_models.py`. It does not copy the JSON files into output. The committed
JSON here is the canonical serialized form of those topologies and is checked
structurally against generated output.

Files:

- `example-001-simple-single-system.json`: one root system with nested groups
- `example-002-multiple-top-level-systems.json`: multiple independent root systems
- `example-003-parent-child-system.json`: explicit parent/child system relationship
- `example-004-sibling-systems.json`: explicit sibling peer relationship
- `example-005-related-systems.json`: reciprocal related records (both Systems labeled, no arrow)
- `example-006-subsystem.json`: a Place inside a System (Morgan's Room)
- `example-007-evolving-uncertain-relationship.json`: evolving relationship with unknown status
- `example-008-archived-system.json`: archived System lifecycle; associated records retained; no predecessor edge
- `example-009-non-tree-graph.json`: graph-style relationships across multiple systems
- `example-010-top-level-group-containing-systems.json`: account-level group containing systems
- `example-011-top-level-place-containing-systems.json`: account-level place containing systems and a nested place
- `example-012-non-system-anchors.json`: Place and Group anchors with zero Systems

Shared modeling notes:

- All twelve files use the same collection set. Unused collections are empty arrays.
- System access is explicit through `memberships`; relationship type does not imply access.
- There is one membership record per unique account–System pair.
- System context is explicit through `systemObjectLinks`; object ownership is not implied by nesting.
- In-system containment (groups or places inside a system, groups inside groups) uses `systemObjectPlacements`.
- Account-level containment (a group or place as the account root, systems inside that container) uses `accountObjectLinks` and `accountObjectPlacements`.
- `systemRelationships` describe the System–System graph. `root` means no parent System, not "top-level in the account tree".
- Relationship semantics are explicit (`relationshipType`, optional status and associated object fields). Graph records are directed. When a diagram labels two Systems with the same peer type and no arrow, both directions are encoded.
- Model 7 uses `relationshipStatus: unknown` on an `evolving` record. Broader status catalogs are deferred.
- Model 8 encodes archived as System lifecycle. Per-object archive flags on associated records are independent facts, not a cascade.

## Field-level relationship encoding

These rules describe the established canonical JSON encoding.

| Field or record | Encoding rule |
| --- | --- |
| `systemId` | Source System of a directed graph record. |
| `relationshipType` | Kind of connection recorded in `systemRelationships`. |
| `targetSystemId` | Destination System for peer and named connections such as `sibling`, `related`, `associated`, and `evolving`. |
| `parentSystemId` | Parent System on a `child` record; `systemId` identifies the child and `targetSystemId` is null. No reverse `parent` record is added. |
| `root` record | A System with no parent System relationship; both `parentSystemId` and `targetSystemId` are null. A System can retain this record while placed inside a Group or Place, as in Models 10 and 11. |
| `relationshipStatus` | Optional state of a graph record. Model 7 uses `unknown` on an `evolving` record. Broader status rules remain deferred. |
| `associatedObjectType` / `associatedObjectId` | Optional associated-object reference, supplied only when specified. These examples do not establish broader subsystem semantics. |

When two Systems have the same peer label and no arrow, these examples encode two directed records, one in each direction. A single arrow encodes one directed record. This preserves Model 4's reciprocal sibling records and Model 9's single directed sibling record.

Containment uses placements. Structural member membership uses the appropriate membership collection, including `groupMemberships` and `placeMemberships`. Account access uses `memberships`. These layers remain separate; graph relationships do not grant access.

Model 3's Workshop-to-Main House connection uses a `child` graph record with `parentSystemId` identifying Main House. Workshop is not also encoded as a placement beneath Main House.

## Per-example encoding notes

### Model 5: Related Systems

Encoding: related is a directed graph record (systemId -> targetSystemId). It is not parent/child and does not grant access. Both Systems are labeled (related) with no arrow, so encode two records: The Archive related -> The Harbor, and The Harbor related -> The Archive.

### Model 6: Nested Place

Encoding: Harbor is the only System. Morgan's Room is a Place contained in Harbor (systemObjectPlacements, parent = Harbor). Alex, Morgan, and Rae are Harbor members and Harbor Group members. M1 and M2 belong to the Place (placeMemberships) and are not Harbor System members. The name "Morgan's Room" is a label. This example does not record a member-to-Place association and does not set associatedObjectId.

Model 6 uses the Place structure shown in its diagram. The permitted endpoints and associated-object semantics of the subsystem relationship remain a separate specification question.

### Model 7: Evolving Relationship

Encoding: North Wing and The Harbor are both root Systems. Encode one directed graph record: relationshipType evolving, systemId = North Wing, targetSystemId = The Harbor, relationshipStatus unknown. Do not name the connection as parent, child, sibling, related, subsystem, or ownership. unknown is the status of that evolving record, not a separate relationship type.

### Model 8: Archived System

Encoding: Old Map is a root System that is no longer active. Encode lifecycle on that System: status archived, isArchived true. Current System remains status active, isArchived false. Both Systems remain relationshipType root. This example does not include a predecessor or other graph edge between Old Map and Current System.

Historical meaning is preserved by retaining Old Map and its existing members, groups, notes, front history, and associations. Archiving the System does not automatically change the lifecycle state of those associated objects. Per-object archive flags on those associated records are independent facts, not an automatic cascade.

### Model 9: Directed Graph

Encoding: encode exactly the three directed edges drawn here, plus a root record for each System: A related -> B, B sibling -> C, C associated -> A. Do not add B related -> A, C sibling -> B, or A associated -> C. Reciprocal records are used only where a diagram labels both sides with no arrow.

### Model 12: Non-System Anchors

Central Hub is a root Place. It contains the Harbor and Main House Groups; Main House contains the Waiting Room Place. These placements use `accountObjectPlacements`, with account context recorded by `accountObjectLinks`. Popeye and Gilligan belong to Harbor through `groupMemberships`; Mickey and Minnie belong to Waiting Room through `placeMemberships`.

There are no Systems, System relationships, System links, System placements, or System access memberships in this example. Notes and front-history collections are empty because the example specifies no individual records for them. No System is invented to support these anchors.

## Deferred questions (for a future GitHub discussion)

Recorded here only. Not opened or published.

### 1. Broader use of statuses across relationship types

`relationshipStatus` is retained as an optional field on graph records. Model 7 uses `unknown` on an `evolving` record. Open questions: which other relationship types may carry a status; which status tokens are valid; whether statuses belong in a lookup catalog or table; and whether type/status combinations should be constrained.

### 2. Subsystem endpoints and associated-object semantics

Model 6 encodes an internal cluster as a Place. The permitted endpoints and associated-object semantics of `subsystem` remain unresolved. The optional `associatedObjectType` / `associatedObjectId` fields exist on relationship records; their SQL columns have no type CHECK or associated-object foreign key. The generator separately validates supplied associated-object references. Open questions: permitted endpoints of `subsystem` (System, member, group, Place, or others); when associated-object fields are required or forbidden; and how that relates to Place containment.

### 3. Independent archive states of associated objects

Archiving a System does not automatically change the lifecycle of its members, groups, notes, front history, or associations. Model 8 currently keeps per-object archive flags as independent facts. Open questions: which associated objects may be archived independently; how those flags are presented; and whether any later cascade or inheritance rule is wanted.
