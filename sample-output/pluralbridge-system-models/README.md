# PluralBridge System-Model Samples

Eleven generated configurations:

- `example-001-simple-single-system.json`
- `example-002-multiple-top-level-systems.json`
- `example-003-parent-child-system.json`
- `example-004-sibling-systems.json`
- `example-005-related-systems.json`
- `example-006-subsystem.json`
- `example-007-evolving-uncertain-relationship.json`
- `example-008-archived-system.json`
- `example-009-non-tree-graph.json`
- `example-010-top-level-group-containing-systems.json`
- `example-011-top-level-place-containing-systems.json`

These files are produced by `generate.py` from Python topologies. They use one
shared collection schema, explicit system relationship records, and separate
object-placement records for containment.

Canonical serialized examples live in `fixtures/pluralbridge-system-models/`.
Refresh this folder with `python3 generate.py --sync-system-model-sample-output`.
