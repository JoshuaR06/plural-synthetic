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
- `example-005-related-systems.json`: explicit non-hierarchical related relationship
- `example-006-subsystem.json`: a Place inside a System (Morgan's Room)
- `example-007-evolving-uncertain-relationship.json`: evolving relationship with uncertain status
- `example-008-archived-system.json`: archived system retained with historical context
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
- Relationship semantics are explicit (`relationshipType`, optional status and associated object fields).
