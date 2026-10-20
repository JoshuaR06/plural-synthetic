# PluralBridge System-Model Fixtures

This folder contains eleven self-contained PluralBridge system-model examples.
They are implementations of `System Model Minimum Base.txt`, which is the
authoritative specification.

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

Shared modeling notes:

- All eleven files use the same collection set. Unused collections are empty arrays.
- System access is explicit through `memberships`; relationship type does not imply access.
- There is one membership record per unique account–System pair.
- System context is explicit through `systemObjectLinks`; object ownership is not implied by nesting.
- In-system containment (groups or places inside a system, groups inside groups) uses `systemObjectPlacements`.
- Account-level containment (a group or place as the account root, systems inside that container) uses `accountObjectLinks` and `accountObjectPlacements`.
- `systemRelationships` describe the System–System graph. `root` means no parent System, not "top-level in the account tree".
- Relationship semantics are explicit (`relationshipType`, optional status and associated object fields). Graph records are directed. When a diagram labels two Systems with the same peer type and no arrow, both directions are encoded.
- Model 7 uses `relationshipStatus: unknown` on an `evolving` record. Broader status catalogs are deferred.
- Model 8 encodes archived as System lifecycle. Per-object archive flags on associated records are independent facts, not a cascade.

## Deferred questions (for a future GitHub discussion)

Recorded here only. Not opened or published.

### 1. Broader use of statuses across relationship types

`relationshipStatus` is retained as an optional field on graph records. Model 7 uses `unknown` on an `evolving` record. Open questions: which other relationship types may carry a status; which status tokens are valid; whether statuses belong in a lookup catalog or table; and whether type/status combinations should be constrained.

### 2. Subsystem endpoints and associated-object semantics

Model 6 encodes an internal cluster as a Place. `subsystem` remains listed among structural relationships in the design document, and `associatedObjectType` / `associatedObjectId` exist on relationship records without type or FK constraints. Open questions: permitted endpoints of `subsystem` (System, member, group, Place, or others); when associated-object fields are required or forbidden; and how that relates to Place containment.

### 3. Independent archive states of associated objects

Archiving a System does not automatically change the lifecycle of its members, groups, notes, front history, or associations. Model 8 currently keeps per-object archive flags as independent facts. Open questions: which associated objects may be archived independently; how those flags are presented; and whether any later cascade or inheritance rule is wanted.

