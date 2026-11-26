# PluralBridge Canonical Models

This folder contains twelve self-contained PluralBridge canonical examples.
The authoritative specification is
[`Canonical Model Minimum Base.txt`](Canonical%20Model%20Minimum%20Base.txt).
The repository overview is in [`README.md`](../../README.md). Generated copies
live under
[`sample-output/pluralbridge-system-models/`](../../sample-output/pluralbridge-system-models/README.md).

`generate.py` builds these configurations from Python topologies in
`system_models.py`. It does not copy the JSON files into output. The committed
JSON here is the canonical serialized form of those topologies and is checked
against generated output for complete object and text equality.

Files:

- `example-001-simple-single-system.json`: one root system with nested groups
- `example-002-multiple-top-level-systems.json`: multiple independent root systems
- `example-003-parent-child-system.json`: Workshop nested under Main House
- `example-004-sibling-systems.json`: explicit sibling peer relationship
- `example-005-related-systems.json`: reciprocal related records (both Systems labeled, no arrow)
- `example-006-subsystem.json`: a Place inside a System (Morgan's Room)
- `example-007-evolving-uncertain-relationship.json`: evolving and unknown labels on North Wing, both null-target
- `example-008-archived-system.json`: archived System lifecycle plus an archived graph label on Old Map; associated records retained; no predecessor edge
- `example-009-non-tree-graph.json`: graph-style relationships across multiple systems
- `example-010-top-level-group-containing-systems.json`: account-level group containing systems
- `example-011-top-level-place-containing-systems.json`: account-level place containing systems and a nested place
- `example-012-non-system-anchors.json`: Place and Group anchors with zero Systems

## Serialized shape

Each example is one `account` with shared peer collections and a hierarchical `tree`.

- One `account` object per document. Shared members and anchors live in account-level peer collections.
- Tree nodes reference anchors; member occurrences reference shared members. Repeated occurrences retain one shared member identity.
- Nesting expresses containment; array position expresses display order.
- Notes belong to members through `noteIds`; fields are associated through `fieldIds`.
- Notes, custom fields, and each tree member occurrence carry `visibility` and `permissions`. Shared `account.members[]` records keep member-wide data, including `fronting`, and do not carry occurrence settings.
- Current fronting is a Boolean on the shared member and applies across every occurrence, independently of focused anchor. For examples 001–011 it is true when that member appears in a current front-history event (`endedAt` is null and `isLive` is true). Example 12 records `false` for all four members as an explicit fixture decision and has no front-history collection.
- Directed graph records live in `account.relationships[]`. Field definitions, worked JSON, display rules, and the results for Examples 004, 005, 007, 008, and 009 are under [Field-level relationship encoding](#field-level-relationship-encoding). Empty `relationships` collections are omitted.
- `privacyBuckets`, `visibilityScopes`, and access memberships are omitted from this canonical export format. Inherit settings on notes, custom fields, and tree occurrences are approved synthetic-example values, not a translation of those collections.
- Empty optional collections are omitted. `example-shape.json` in sample-output is an illustrative reference, not a thirteenth canonical model. Database links, placements, and access mechanisms are separate from this JSON encoding.

Shared modeling notes:

- System–System structure uses directed `relationships`. Containment uses the `tree`.
- Graph records are directed. When a diagram labels two Systems with the same peer type and no arrow, both directions are encoded as separate rows that share one field.
- Model 8 encodes archived as System lifecycle and also records Old Map as `archived` with `targetAnchorId` null. Per-object archive flags on associated records are independent facts, not a cascade. Historical `linkRole`s serialize as `tags`.

## Field-level relationship encoding

Relationship records live in `account.relationships[]`. The encoding rules below match
[`Canonical Model Minimum Base.txt`](Canonical%20Model%20Minimum%20Base.txt). JSON excerpts
are taken from the committed examples in this folder.

| Field | Encoding rule |
| --- | --- |
| `relationshipId` | Stable id of a surviving graph row. New ids are deterministic and unique within the collection. |
| `sourceAnchorId` | Required source. Must be an `account.anchors[].anchorId` in the same account. |
| `fieldId` | Required. Must be an `account.customFields[].fieldId` in the same account. That field's `fieldName` is the user-defined label. |
| `targetAnchorId` | An `account.anchors[].anchorId` in the same account, or literal JSON `null`. Never `0`, `""`, or `"null"`. |

Every `relationshipId`, `sourceAnchorId`, `fieldId`, and non-null `targetAnchorId` resolves inside the same account. Each row has one label and one optional target. Multiple labels use separate rows. Reverse direction is a separate row. Root and child graph records are omitted; nesting in `account.tree` expresses parent/child containment. When no graph rows remain, `relationships` is omitted.

When two Systems have the same peer label and no arrow, these examples encode two directed records, one in each direction, sharing one custom field. A single arrow encodes one directed record. This preserves Example 004's reciprocal sibling records and Example 009's single directed sibling record.

### Sibling example (Example 004)

Day Team (`system-001`) and Night Team (`system-002`) are peer Systems. Reciprocity is two directed rows that share one custom field. From [`example-004-sibling-systems.json`](example-004-sibling-systems.json):

```json
{
  "fieldId": "custom-field-sibling",
  "fieldName": "sibling",
  "visibility": { "mode": "inherit" },
  "permissions": { "mode": "inherit" }
}
```

```json
[
  {
    "relationshipId": "relationship-003",
    "sourceAnchorId": "system-001",
    "fieldId": "custom-field-sibling",
    "targetAnchorId": "system-002"
  },
  {
    "relationshipId": "relationship-004",
    "sourceAnchorId": "system-002",
    "fieldId": "custom-field-sibling",
    "targetAnchorId": "system-001"
  }
]
```

`sourceAnchorId` `system-001` is Day Team; `system-002` is Night Team. Day Team's `fieldIds` lists only `custom-field-001` (System Role). Night Team has no `fieldIds`. `custom-field-sibling` is referenced through these rows and is not copied onto either anchor to render the relationship.

### Null-target labels (Example 007)

North Wing (`system-002`) records `evolving` and `unknown` as two separate rows, both with literal `targetAnchorId: null`. From [`example-007-evolving-uncertain-relationship.json`](example-007-evolving-uncertain-relationship.json):

```json
[
  {
    "relationshipId": "relationship-003",
    "sourceAnchorId": "system-002",
    "fieldId": "custom-field-evolving",
    "targetAnchorId": null
  },
  {
    "relationshipId": "relationship-004",
    "sourceAnchorId": "system-002",
    "fieldId": "custom-field-unknown",
    "targetAnchorId": null
  }
]
```

The labels come from `customFields` entries whose `fieldName` values are `evolving` and `unknown`. Neither id appears on The Harbor's or North Wing's `fieldIds`. The Harbor is a peer root, not a relationship target.

### Display combination

Labels that share the same source and the same target are combined for display. Append `->Target` once, using the target anchor's `name`, only when `targetAnchorId` is an id. Null-target labels display without an arrow.

The form `sibling, evolving->B` is illustrative: it is how two labels on one source toward B would combine. No canonical example contains that combination. The closest committed case is Example 007, where two null-target labels combine as `evolving, unknown`.

### Containment vs relationships

Nesting in `account.tree` supplies containment and display order. Relationship rows do not move, parent, or reorder anchors. Example 003 nests The Workshop under Main House, after Main House Group, and has no relationship rows. Examples 001, 002, 006, and 010–012 also omit `relationships`.

Relationship-label fields are referenced through relationship rows. They are not added to `anchor.fieldIds` merely to render the relationship. Payload-bearing fields such as Example 004's `custom-field-001` remain on `fieldIds` independently.

Structural member membership is a tree occurrence under the owning group or place. Graph relationships do not grant access.

### Results in the canonical examples

| Example | File | Relationship results |
| --- | --- | --- |
| 004 | [`example-004-sibling-systems.json`](example-004-sibling-systems.json) | Day Team `sibling->Night Team`; Night Team `sibling->Day Team`. Two rows share `custom-field-sibling`. |
| 005 | [`example-005-related-systems.json`](example-005-related-systems.json) | The Harbor `related->The Archive`; The Archive `related->The Harbor`. Two rows share `custom-field-related`. |
| 007 | [`example-007-evolving-uncertain-relationship.json`](example-007-evolving-uncertain-relationship.json) | North Wing `evolving, unknown` (no arrows). Two null-target rows; The Harbor is not a target. |
| 008 | [`example-008-archived-system.json`](example-008-archived-system.json) | Old Map `archived` (no arrow). One null-target row; no edge to Current System. |
| 009 | [`example-009-non-tree-graph.json`](example-009-non-tree-graph.json) | A `related->B`; B `sibling->C`; C `associated->A`. Three directed rows; the reverse of each is omitted. |

Examples 001, 002, 003, 006, and 010–012 have no relationship rows.

## Per-example encoding notes

### Model 5: Related Systems

Related is not parent/child and does not grant access. Both Systems are labeled related with no arrow, so both directions are encoded. JSON and display results are under [Field-level relationship encoding](#field-level-relationship-encoding).

### Model 6: Nested Place

Encoding: Harbor is the only System. Morgan's Room is a Place nested under Harbor in the tree. Alex, Morgan, and Rae are Harbor members and Harbor Group members. M1 and M2 belong to the Place and are not Harbor System members. The name "Morgan's Room" is a label. This example has no relationship rows. `exampleName` is "Nested Structure Model"; the filename is unchanged.

### Model 7: Evolving Relationship

North Wing and The Harbor are both top-level Systems. Do not name the connection as parent, child, sibling, related, subsystem, or ownership. JSON and display results are under [Field-level relationship encoding](#field-level-relationship-encoding).

### Model 8: Archived System

Encoding: Old Map is a System that is no longer active. Encode lifecycle on that System: status archived, isArchived true. Current System remains status active, isArchived false. The `archived` graph label is a null-target row on Old Map, not a predecessor edge to Current System. JSON and display results are under [Field-level relationship encoding](#field-level-relationship-encoding).

Historical meaning is preserved by retaining Old Map and its existing members, groups, notes, front history, and associations. Archiving the System does not automatically change the lifecycle state of those associated objects. Per-object archive flags on those associated records are independent facts, not an automatic cascade.

### Model 9: Directed Graph

Encode exactly the three directed edges drawn here. Do not add B related -> A, C sibling -> B, or A associated -> C. Reciprocal records are used only where a diagram labels both sides with no arrow. JSON and display results are under [Field-level relationship encoding](#field-level-relationship-encoding).

### Model 12: Non-System Anchors

Central Hub is a root Place. It contains the Harbor and Main House Groups; Main House contains the Waiting Room Place. These placements are the tree. Popeye and Gilligan belong to Harbor; Mickey and Minnie belong to Waiting Room. Minnie is not also listed under Harbor.

There are no Systems or System relationships in this example. Notes and front-history collections are omitted because the example specifies no individual records for them. Shared members still carry explicit `fronting: false` as a fixture decision. No System is invented to support these anchors.

## Verified generation

```sh
python3 generate.py --out DIR
python3 generate.py --out DIR --sync-system-model-sample-output
python3 -m unittest discover -s . -p 'test_*.py' -v
```

`--out DIR` must be a new temporary directory, not this fixtures folder. `--sync-system-model-sample-output` refreshes only the twelve canonical JSON files under `sample-output/pluralbridge-system-models/` and does not overwrite `example-shape.json`.

## Deferred questions (for a future GitHub discussion)

Recorded here only. Not opened or published.

### Independent archive states of associated objects

Archiving a System does not automatically change the lifecycle of its members, groups, notes, front history, or associations. Model 8 currently keeps per-object archive flags as independent facts. Open questions: which associated objects may be archived independently; how those flags are presented; and whether any later cascade or inheritance rule is wanted.
