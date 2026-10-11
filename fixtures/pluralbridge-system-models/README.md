# PluralBridge System-Model Fixtures

This folder contains nine self-contained PluralBridge system-model examples.

Files:

- `example-001-simple-single-system.json`: one root system
- `example-002-multiple-top-level-systems.json`: multiple independent root systems
- `example-003-parent-child-system.json`: explicit parent/child structure
- `example-004-sibling-systems.json`: explicit sibling peer relationship
- `example-005-related-systems.json`: explicit non-hierarchical related relationship
- `example-006-subsystem.json`: subsystem associated to a member
- `example-007-evolving-uncertain-relationship.json`: evolving relationship with uncertain status
- `example-008-archived-system.json`: archived system retained with historical context
- `example-009-non-tree-graph.json`: graph-style model across multiple systems

Shared modeling notes:

- System access is explicit through `memberships`; relationship type does not imply access.
- System context is explicit through `systemObjectLinks`; object ownership is not implied by nesting.
- Relationship semantics are explicit through `systemRelationships` (`relationshipType`, optional status and associated object fields).
