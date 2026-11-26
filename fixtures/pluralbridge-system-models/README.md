# PluralBridge Canonical Models

This folder contains twelve self-contained PluralBridge canonical examples.
The authoritative specification is
[`Canonical Model Minimum Base.txt`](Canonical%20Model%20Minimum%20Base.txt).

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
- Directed graph records stay in `account.relationships` (`sourceAnchorId`, `fieldId`, `targetAnchorId`). The label is the referenced custom field's `fieldName`. Reverse direction is a separate row. A null target is literal JSON `null`. Display combines labels for the same source/target and appends `->Target` only when a target exists. Relationship-label fields are not added to `anchor.fieldIds` merely for relationship rendering. Root and child graph records are omitted; nesting expresses parent/child containment. Empty `relationships` collections are omitted.
- `privacyBuckets`, `visibilityScopes`, and access memberships are omitted from this canonical export format. Inherit settings on notes, custom fields, and tree occurrences are approved synthetic-example values, not a translation of those collections.
- Empty optional collections are omitted. `example-shape.json` in sample-output is an illustrative reference, not a thirteenth canonical model. Database links, placements, and access mechanisms are separate from this JSON encoding.

Shared modeling notes:

- System–System structure uses directed `relationships`. Containment uses the `tree`.
- Each relationship row points at an account-owned custom field for its label. Relationship fields are not added to `anchor.fieldIds` merely to display those labels.
- Graph records are directed. When a diagram labels two Systems with the same peer type and no arrow, both directions are encoded as separate rows that share one field.
- Model 7 records North Wing as `evolving` and `unknown`, each with `targetAnchorId` null.
- Model 8 encodes archived as System lifecycle and also records Old Map as `archived` with `targetAnchorId` null. Per-object archive flags on associated records are independent facts, not a cascade. Historical `linkRole`s serialize as `tags`.

## Field-level relationship encoding

These rules describe the established canonical JSON encoding.

| Field or record | Encoding rule |
| --- | --- |
| `relationshipId` | Stable id of a surviving graph row. New ids are deterministic and unique within the collection. |
| `sourceAnchorId` | Required source anchor in the same account. |
| `fieldId` | Required account-owned custom field. The visible label is that field's `fieldName`. |
| `targetAnchorId` | An existing anchor id in the same account, or JSON `null`. Never `0`, `""`, or `"null"`. |

Each row has one label and one optional target. Multiple labels use separate rows. All references resolve inside the same account. Root and child graph records are omitted; containment belongs in the tree. When no graph rows remain, `relationships` is omitted.

When two Systems have the same peer label and no arrow, these examples encode two directed records, one in each direction, sharing one custom field. A single arrow encodes one directed record. This preserves Model 4's reciprocal sibling records and Model 9's single directed sibling record.

Containment uses the tree. Structural member membership is a tree occurrence under the owning group or place. Graph relationships do not grant access.

Model 3 nests The Workshop under Main House, after Main House Group, and has no relationship rows. Examples 1, 2, 6, and 10–12 also have no relationship rows.

## Per-example encoding notes

### Model 5: Related Systems

Encoding: related is a directed graph record (`sourceAnchorId` -> `targetAnchorId`) whose label comes from an account-owned `related` custom field. It is not parent/child and does not grant access. Both Systems are labeled (related) with no arrow, so encode two records that share that field: The Harbor related -> The Archive, and The Archive related -> The Harbor.

### Model 6: Nested Place

Encoding: Harbor is the only System. Morgan's Room is a Place nested under Harbor in the tree. Alex, Morgan, and Rae are Harbor members and Harbor Group members. M1 and M2 belong to the Place and are not Harbor System members. The name "Morgan's Room" is a label. This example has no relationship rows. `exampleName` is "Nested Structure Model"; the filename is unchanged.

### Model 7: Evolving Relationship

Encoding: North Wing and The Harbor are both top-level Systems. Encode two directed graph records from North Wing, each with targetAnchorId = null: one referencing the account-owned `evolving` custom field, and one referencing a separate account-owned `unknown` custom field. Do not name the connection as parent, child, sibling, related, subsystem, or ownership.

### Model 8: Archived System

Encoding: Old Map is a System that is no longer active. Encode lifecycle on that System: status archived, isArchived true. Current System remains status active, isArchived false. Also encode one directed graph record from Old Map referencing an account-owned `archived` custom field, with targetAnchorId = null. This example does not include a predecessor or other graph edge between Old Map and Current System.

Historical meaning is preserved by retaining Old Map and its existing members, groups, notes, front history, and associations. Archiving the System does not automatically change the lifecycle state of those associated objects. Per-object archive flags on those associated records are independent facts, not an automatic cascade.

### Model 9: Directed Graph

Encoding: encode exactly the three directed edges drawn here, each referencing its own account-owned label field: A related -> B, B sibling -> C, C associated -> A. Do not add B related -> A, C sibling -> B, or A associated -> C. Reciprocal records are used only where a diagram labels both sides with no arrow. Root relationship records are omitted.

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
