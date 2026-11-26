# PluralBridge Canonical Model Samples

Twelve generated canonical models:

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
- `example-012-non-system-anchors.json`

These files are produced by `generate.py` from Python topologies. Each file is
one account with shared peer collections (members, notes, custom fields, anchors)
and a hierarchical `tree`. Tree nodes reference anchors; member occurrences
reference shared members. Nesting is containment; array order is display order.
Directed graph records stay in `relationships` (`sourceAnchorId`, `fieldId`,
`targetAnchorId`); the label comes from the referenced custom field. The
relationship JSON format, worked examples, and per-example results are in
[`fixtures/pluralbridge-system-models/README.md`](../../fixtures/pluralbridge-system-models/README.md#field-level-relationship-encoding).
Empty relationship collections are omitted. `privacyBuckets`, `visibilityScopes`, and
access memberships are omitted. Notes, custom fields, and tree member occurrences
carry visibility and permissions. Current fronting is a Boolean on the shared
member and applies across every occurrence, independently of focused anchor.

`example-shape.json` is an illustrative reference for that shape. It is not a
thirteenth canonical model and is not generated or overwritten.

Canonical serialized examples live in `fixtures/pluralbridge-system-models/`.
Refresh the twelve example JSON files with:

```sh
python3 generate.py --out DIR --sync-system-model-sample-output
```

`--out DIR` must be a new temporary directory, not this folder.
