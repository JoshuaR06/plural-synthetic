# PluralBridge canonical JSON format

This document describes every record type and serialized field currently present in the twelve canonical examples.

Sources:

- `fixtures/pluralbridge-system-models/example-001-simple-single-system.json` through `example-012-non-system-anchors.json`
- Relationship encoding in `fixtures/pluralbridge-system-models/README.md`
- `fixtures/pluralbridge-system-models/Canonical Model Minimum Base.txt`
- `sample-output/pluralbridge-system-models/example-shape.json`
- `system_models.py`, where needed to establish generation behavior

Presence in the examples does not by itself establish that a field is required by the format. Observed values do not establish a complete allowed vocabulary.

The current encoding omits empty optional account collections: `notes`, `customFields`, `relationships`, and `frontHistory`. Empty `members` and `children` arrays on tree nodes remain present. Other empty-collection requirements are identified below.

`privacyBuckets`, `visibilityScopes`, and access `memberships` are not export containers in this format.

## Identifiers and references

Identifiers and references are scoped to the single account in the document.

| Identifier | Defined on | Referenced from |
| --- | --- | --- |
| `accountId` | `account.accountId` | Not referenced by other records in this JSON. |
| `memberId` | `account.members[].memberId` | Tree member occurrences and `account.frontHistory[].memberIds`. |
| `noteId` | `account.notes[].noteId` | `account.members[].noteIds`. |
| `fieldId` | `account.customFields[].fieldId` | Member `fieldIds`, anchor `fieldIds`, and relationship `fieldId`. |
| `anchorId` | `account.anchors[].anchorId` | Tree nodes, relationship `sourceAnchorId`, and non-null relationship `targetAnchorId`. |
| `relationshipId` | `account.relationships[].relationshipId` | Not referenced by other records. |
| `frontHistoryId` | `account.frontHistory[].frontHistoryId` | Not referenced by other records. |

Shared member payload is stored once in `account.members[]`. A tree occurrence references that member and carries occurrence-specific settings.

- `noteIds` associates account-owned notes with a shared member.
- `fieldIds` associates account-owned custom fields with a member or anchor.
- Relationship `fieldId` selects the field whose `fieldName` supplies the relationship label.
- A relationship-label field is not added to an anchor’s `fieldIds` merely to render the relationship.

A relationship target is an anchor identifier or literal JSON `null`. It is never `0`, `""`, or `"null"`.

Tree nesting expresses containment. Array order in `tree`, `children`, and occurrence `members` expresses display order. Relationship rows do not reposition anchors.

## Document envelope

**Path:** `$`

One document containing a single account and export metadata.

```json
{
  "account": {},
  "audit": {},
  "pluralBridgeExport": {},
  "provenance": {}
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `account` | object | The single account payload. | Present in all twelve examples. |
| `audit` | object | Export-level timestamps. | Present in all twelve examples. |
| `pluralBridgeExport` | object | Header identifying the synthetic example. | Present in all twelve examples. |
| `provenance` | object | Information about how the example was produced. | Present in all twelve examples. |

## Account

**Path:** `$.account`

Account identity, shared record collections, and the placement tree.

The following example shows the collections together to identify their locations. Empty optional collections are omitted in generated output.

```json
{
  "config": {
    "avatar-width": 64,
    "avatar-height": 64,
    "avatar": "solid"
  },
  "accountId": "account-001",
  "displayName": "Example 1",
  "email": "example-1@pluralbridge.org",
  "status": "Active",
  "username": "example-1",
  "members": [],
  "notes": [],
  "customFields": [],
  "anchors": [],
  "tree": [],
  "relationships": [],
  "frontHistory": []
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `config` | object | Account avatar defaults: `avatar-width`, `avatar-height`, and `avatar`. | First account property in all twelve canonical examples, with values `64`, `64`, and `solid`. Feed imports write the same keys from the feed’s resolved global default. |
| `accountId` | string | Account identifier. Observed pattern: `account-NNN`. | Present in all twelve examples. |
| `displayName` | string | Account display name. | Present in all twelve examples. |
| `email` | string | Account email address. | Present in all twelve examples. |
| `status` | string | Account lifecycle label. Observed value: `Active`. | Present in all twelve examples. Complete vocabulary unresolved. |
| `username` | string | Account username. | Present in all twelve examples. |
| `members` | array | Shared member records. | Present and non-empty in all twelve examples. Empty-account behavior unresolved. |
| `notes` | array | Account-owned note records, associated with members through `noteIds`. | Present in 001–011; omitted in 012. Omitted when empty. |
| `customFields` | array | Account-owned custom fields, including relationship-label fields. | Present in 001–009; omitted in 010–012. Omitted when empty. |
| `anchors` | array | Shared System, Group, and Place records. | Present and non-empty in all twelve examples. Empty-account behavior unresolved. |
| `tree` | array | Root anchor placements and their nested structure. | Present and non-empty in all twelve examples. Empty-account behavior unresolved. |
| `relationships` | array | Directed relationship records and standalone labels. | Present in 004, 005, 007, 008, and 009. Omitted when empty. |
| `frontHistory` | array | Historical and current fronting events. | Present in 001–011; omitted in 012. Omitted when empty. |

The twelve canonical examples do not include account-level `permissions` or `visibility`. Feed imports do. See **Feed-import account settings**.

## Shared members

**Path:** `$.account.members[]`

One shared record per member. Member-wide payload applies wherever that member appears in the tree.

```json
{
  "memberId": "member-001",
  "color": "#69d563",
  "description": "Synthetic member A.",
  "displayName": "A",
  "isArchived": false,
  "pronouns": "she/her",
  "fieldIds": [],
  "noteIds": ["note-001"],
  "fronting": true
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `memberId` | string | Member identity, unique within the account’s member collection. | Present on every member. |
| `displayName` | string | Member display name. | Present on every member. |
| `fronting` | boolean | Current fronting state across every occurrence of this member, independent of focused anchor. | Present on every member. |
| `isArchived` | boolean | Member archive flag. Independent of an anchor’s archive state. | Present on every member. True on Example 008 members 003 and 004. |
| `fieldIds` | array of string | References to custom fields associated with this member. | Present on every member. Empty in the twelve examples; non-empty in the illustrative shape. |
| `noteIds` | array of string | References to notes associated with this member. | Present on every member. Empty when no notes are associated. |
| `color` | string | Member color. Observed form: hexadecimal `#rrggbb`. | Present in 001–011; omitted in 012. |
| `description` | string | Member description. | Present in 001–011; omitted in 012. |
| `pronouns` | string | Member pronouns. | Present in 001–011; omitted in 012. |
| `archivedReason` | string | Explanation of the member’s archived state. | Present only on Example 008 members 003 and 004. |

Generation assigns all notes in each example to `member-001`. That assignment is example data, not a restriction that notes can belong only to the first member.

In Examples 001–011, current fronting is derived from events where `endedAt` is `null` and `isLive` is `true`. Example 012 explicitly sets every member’s `fronting` to `false` without generating front-history events.

Shared member records do not currently carry `visibility` or `permissions`; those settings are on member occurrences.

## Notes

**Path:** `$.account.notes[]`

Account-owned note records. A member’s `noteIds` associates notes with that member.

```json
{
  "noteId": "note-001",
  "body": "Synthetic note text.",
  "supportsMarkdown": true,
  "title": "Example note",
  "visibility": {
    "mode": "inherit"
  },
  "permissions": {
    "mode": "inherit"
  }
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `noteId` | string | Note identity, unique within the account’s note collection. | Present on every note. |
| `title` | string | Note title. | Present on every canonical note. |
| `body` | string | Note body text. | Present on every canonical note. |
| `supportsMarkdown` | boolean | Whether the note body supports Markdown. | Present on every canonical note; observed value is `true`. |
| `visibility` | object | Visibility settings for this note. | Present on every canonical note. |
| `permissions` | object | Permission settings for this note. | Present on every canonical note. |
| `isArchived` | boolean | Note archive flag, independent of anchor archive state. | Present on both Example 008 notes; omitted elsewhere. |
| `tags` | array of string | Extensible descriptive labels. | Example 008 note 002 has `historical-note`; omitted elsewhere. |

Notes are associated with members, not anchors. Historical wording inside existing note bodies does not change the association established by `noteIds`.

## Custom fields

**Path:** `$.account.customFields[]`

Account-owned field records. Ordinary custom fields and relationship-label fields share this collection and its identifier namespace.

Ordinary field:

```json
{
  "fieldId": "custom-field-001",
  "description": "Synthetic custom field example.",
  "fieldName": "System Role",
  "fieldType": "text",
  "supportsMarkdown": false,
  "visibility": {
    "mode": "inherit"
  },
  "permissions": {
    "mode": "inherit"
  }
}
```

Relationship-label field:

```json
{
  "fieldId": "custom-field-sibling",
  "fieldName": "sibling",
  "visibility": {
    "mode": "inherit"
  },
  "permissions": {
    "mode": "inherit"
  }
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `fieldId` | string | Field identity, unique within the account’s custom-field collection. | Present on every field. |
| `fieldName` | string | User-visible field label. Supplies the relationship label when referenced by a relationship row. | Present on every field. |
| `description` | string | Field description. | Present on ordinary fields in the examples; omitted on relationship-label fields. |
| `fieldType` | string | Field data type. Observed value: `text`. | Present on ordinary fields; omitted on relationship-label fields. Complete vocabulary unresolved. |
| `supportsMarkdown` | boolean | Whether associated field content supports Markdown. | Present on ordinary fields; observed value is `false`. |
| `visibility` | object | Visibility settings for this field. | Present on every field. |
| `permissions` | object | Permission settings for this field. | Present on every field. |

Field identity is established by `fieldId`, not `fieldName`. Labels do not establish identity or uniqueness.

Ordinary fields are associated through member or anchor `fieldIds`. Relationship fields are associated through relationship `fieldId`.

The current examples do not define a separate field-value record or serialize a custom-field value. Defining a field label is distinct from supplying a value for it.

## Anchors

**Path:** `$.account.anchors[]`

Shared System, Group, and Place records. Tree nodes reference these records by `anchorId`.

Anchor names must be unique across the account’s anchors, including across different anchor types.

System example:

```json
{
  "anchorId": "system-001",
  "objectType": "system",
  "color": "#8367ea",
  "description": "A System containing members and groups.",
  "name": "The Harbor",
  "fieldIds": ["custom-field-001"]
}
```

Group example:

```json
{
  "anchorId": "group-001",
  "objectType": "group",
  "color": "#cccccc",
  "description": "A group of members.",
  "name": "Musicians"
}
```

Place example:

```json
{
  "anchorId": "place-001",
  "objectType": "place",
  "color": "#4f8fcf",
  "description": "A Place with its own member structure.",
  "name": "Morgan's Room"
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `anchorId` | string | Anchor identity, unique within the account’s anchor collection. | Present on every anchor. |
| `objectType` | string | Anchor kind. Current anchor types: `system`, `group`, `place`. | Present on every anchor. |
| `name` | string | User-visible anchor name. | Present on every anchor. |
| `color` | string | Anchor color. Observed form: hexadecimal color. | Present in 001–011; omitted in 012. |
| `description` | string | Anchor description. | Present in 001–011; omitted in 012. |
| `fieldIds` | array of string | References to ordinary custom fields associated with this anchor. | Present on some System anchors when non-empty. Omitted otherwise in these examples. |
| `isArchived` | boolean | Archive flag for this anchor. Independent of the `archived` relationship label and other records’ archive flags. | Present on both Systems and both Groups in Example 008. |
| `status` | string | System lifecycle state. Observed values: `active`, `archived`. | Present on Example 008 Systems only. |
| `archivedAt` | string | Archive timestamp. Observed form: UTC timestamp ending in `Z`. | Present on Example 008 Old Map only. |
| `archivedReason` | string | Reason for archiving. | Present on Example 008 Old Map only. |
| `tags` | array of string | Extensible descriptive labels. | Example 008 Old Map Group has `historical-organization`. |

The current examples do not place `visibility`, `permissions`, `permissionIds`, or `visibilityIds` on anchor records.

The absence of Group or Place `fieldIds` in these examples does not establish that only Systems can have custom fields.

## Tree nodes

**Path:** `$.account.tree[]`, recursively through `children[]`

An occurrence of an anchor in the containment tree.

```json
{
  "anchorId": "system-001",
  "members": [
    {
      "memberId": "member-001",
      "visibility": {
        "mode": "inherit"
      },
      "permissions": {
        "mode": "inherit"
      }
    }
  ],
  "children": [
    {
      "anchorId": "group-001",
      "members": [],
      "children": []
    }
  ]
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `anchorId` | string | Reference to a shared anchor record in this account. | Present on every node. |
| `members` | array | Member occurrences directly under this anchor placement, in display order. | Present on every node; `[]` when empty. |
| `children` | array | Child anchor placements, using this same recursive record shape. | Present on every node; `[]` for leaves. |

The root `tree` array contains top-level placements. Each anchor appears at most once in the current examples.

Example 003 places The Workshop beneath Main House. It has no separate child relationship row.

Relationship records do not add, remove, reorder, or reparent tree nodes.

## Member occurrences

**Path:** `$.account.tree[].members[]`, including recursively nested tree nodes

A reference to a shared member under one anchor placement, with settings specific to that occurrence.

```json
{
  "memberId": "member-001",
  "visibility": {
    "mode": "inherit"
  },
  "permissions": {
    "mode": "inherit"
  }
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `memberId` | string | Reference to a shared member in this account. The same identifier may appear beneath several anchors. | Present on every occurrence. |
| `visibility` | object | Visibility settings for this occurrence. | Present on every canonical occurrence. |
| `permissions` | object | Permission settings for this occurrence. | Present on every canonical occurrence. |
| `tags` | array of string | Extensible descriptive labels. | Example 008 occurrences under Old Map have `historical-system-member`. |

Occurrences do not duplicate the shared member’s `fronting`, `fieldIds`, `noteIds`, or descriptive payload.

## Visibility and permissions

**Paths:**

- `$.account.notes[].visibility`
- `$.account.notes[].permissions`
- `$.account.customFields[].visibility`
- `$.account.customFields[].permissions`
- Tree member occurrence `visibility`
- Tree member occurrence `permissions`

Settings attached to the containing record or occurrence.

Canonical form:

```json
{
  "mode": "inherit"
}
```

Illustrative explicit visibility from `example-shape.json`:

```json
{
  "mode": "explicit",
  "value": "self"
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `mode` | string | How the setting is supplied. `inherit` delegates to inherited settings; `explicit` supplies a value directly. | All twelve canonical examples use `inherit`. The illustrative shape demonstrates explicit visibility. |
| `value` | string | Explicit setting value. Its vocabulary depends on whether the object represents visibility or permissions. | Demonstrated only as visibility `self` in the illustrative shape. Absent for `inherit`. |

The current canonical files use only `{"mode":"inherit"}`. They do not specify the complete inheritance-resolution algorithm.

Permission types and visibility audiences used by feed imports are listed in `docs/visibility-permissions-roles.txt`. An explicit permission value is an array of those types, including a one-element array. `all` is not expanded. The type `inherit` inside that array is not the same thing as `{"mode":"inherit"}`.

Roles in that file are not permission types. Feed imports do not map one to the other.

The illustrative shape uses visibility `self`. That token is not in the visibility list. The list’s corresponding audience is `only you`. Feed imports keep a supplied `self` unchanged.

## Relationships

**Path:** `$.account.relationships[]`

A directed association from a source anchor through a custom-field label to an optional target anchor.

```json
{
  "relationshipId": "relationship-003",
  "sourceAnchorId": "system-001",
  "fieldId": "custom-field-sibling",
  "targetAnchorId": "system-002"
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `relationshipId` | string | Identity of this relationship row, unique within the collection. | Present on every row. |
| `sourceAnchorId` | string | Reference to the source anchor in this account. | Present on every row; never null. |
| `fieldId` | string | Reference to a custom field in this account. Its `fieldName` supplies the label. | Present on every row; never null. |
| `targetAnchorId` | string or null | Reference to a target anchor, or literal JSON `null` for a standalone source label. | Always present. |

Null-target example:

```json
{
  "relationshipId": "relationship-003",
  "sourceAnchorId": "system-002",
  "fieldId": "custom-field-evolving",
  "targetAnchorId": null
}
```

Relationship rules:

- One row identifies one source, one label field, and one optional target.
- Reverse direction requires a separate row.
- Multiple labels require separate rows.
- Labels sharing a source and target are combined for display.
- A non-null target appends `->Target`.
- Null-target labels have no arrow.
- Relationship rows do not express tree containment.
- No `root` or `child` relationship rows are emitted.
- Empty relationship collections are omitted.

Approved example results:

| Example | Relationships |
| --- | --- |
| 004 | Day Team `sibling->Night Team`; Night Team `sibling->Day Team`. |
| 005 | The Harbor `related->The Archive`; The Archive `related->The Harbor`. |
| 007 | North Wing has separate `evolving` and `unknown` rows, both null-target. |
| 008 | Old Map has an `archived` null-target row. Archive flags remain independent. |
| 009 | A `related->B`; B `sibling->C`; C `associated->A`. |

Examples 001, 002, 003, 006, and 010–012 have no relationship rows. The twelve examples contain ten relationship rows in total.

`sibling, evolving->B` illustrates combined display syntax; that combination is not present in the canonical examples.

## Front history

**Path:** `$.account.frontHistory[]`

Historical and current fronting events, distinct from each member’s current `fronting` Boolean.

```json
{
  "frontHistoryId": "front-002",
  "endedAt": null,
  "isLive": true,
  "memberIds": ["member-001", "member-002"],
  "startedAt": "2026-01-01T13:00:00Z",
  "status": "co-fronting"
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `frontHistoryId` | string | Event identity, unique within the event collection. | Present on every event. |
| `memberIds` | array of string | References to participating shared members. | Present and non-empty on every canonical event. |
| `startedAt` | string | Event start timestamp. Observed form: `YYYY-MM-DDTHH:MM:SSZ`. | Present on every event; never null. |
| `endedAt` | string or null | Event end timestamp, or `null` while open. | Present on every event. |
| `isLive` | boolean | Live-event flag. | Present on every event. Current canonical events combine `true` with `endedAt: null`. |
| `status` | string or null | Event status label. Observed values: `co-fronting`, `historical`, and `null`. | Present on every event. Complete vocabulary unresolved. |
| `isArchived` | boolean | Event archive flag, independent of anchor archive state. | Present on both Example 008 events. |
| `tags` | array of string | Extensible descriptive labels. | Example 008 event 002 has `historical-fronting-context`. |

Examples 001–011 derive member-wide current fronting from their live, open events. Example 012 supplies explicit false values without events.

The current records have no anchor reference. Their participants are identified by `memberIds`.

Fronting visibility was discussed as a requirement, but the current JSON does not define where that setting is serialized. See **Pending model alignment**.

## Export metadata

**Path:** `$.pluralBridgeExport`

Header describing the synthetic example.

```json
{
  "exampleId": "example-001",
  "exampleName": "Simple Single-System Model",
  "exportKind": "self-contained-pluralbridge-example",
  "exportVersion": "0.1-draft",
  "modelingNote": "Synthetic PluralBridge example with one account and one System."
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `exampleId` | string | Example identifier, matching the filename prefix. | Present in all twelve examples. |
| `exampleName` | string | Human-readable example name. | Present in all twelve examples. |
| `exportKind` | string | Export classification. Observed value: `self-contained-pluralbridge-example`. | Present in all twelve examples. |
| `exportVersion` | string | Format-version marker. Observed value: `0.1-draft`. | Present in all twelve examples. Versioning semantics unresolved. |
| `modelingNote` | string | Explanation of what the synthetic example demonstrates. | Present in all twelve examples. |

Example 006 is named `Nested Structure Model`; its filename remains `example-006-subsystem.json`.

## Audit metadata

**Path:** `$.audit`

Export-document timestamps. Retained database audit records are not serialized here.

```json
{
  "createdAt": "2026-01-01T00:00:00Z",
  "updatedAt": "2026-01-01T00:00:00Z"
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `createdAt` | string | Export-level creation timestamp. | Present in all twelve examples; a fixed synthetic timestamp is used. |
| `updatedAt` | string | Export-level update timestamp. | Present in all twelve examples; currently equal to `createdAt`. |

General lifecycle behavior for these timestamps has not been specified.

## Provenance

**Path:** `$.provenance`

Information about the source and production of the example.

```json
{
  "lossyMappings": [],
  "source": "synthetic",
  "sourceGenerator": "plural-synthetic",
  "sourceIdsPreserved": true
}
```

Example 012:

```json
{
  "lossyMappings": [],
  "source": "synthetic",
  "sourceDocument": "PluralBridge-Plural-Maps-and-Design-Rules.txt",
  "sourceExample": 12,
  "sourceGenerator": "example-012-document-transcription",
  "sourceIdsPreserved": false
}
```

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `lossyMappings` | array | Information about mappings that lose source meaning or data. | Present as `[]` in all examples. Non-empty element shape unresolved. |
| `source` | string | Source classification. Observed value: `synthetic`. | Present in all twelve examples. |
| `sourceGenerator` | string | Producer identifier. | `plural-synthetic` in 001–011; `example-012-document-transcription` in 012. |
| `sourceIdsPreserved` | boolean | Whether identifiers from the source were preserved. | True in 001–011; false in 012. |
| `sourceDocument` | string | Historical source-document filename. | Present only in 012. The current specification’s filename differs. |
| `sourceExample` | number | Example number in the source document. | Present only in 012, with value `12`. |

## Tags

**Paths:**

- `$.account.anchors[].tags`
- `$.account.notes[].tags`
- `$.account.frontHistory[].tags`
- Tree member occurrence `tags`

Arrays of extensible string labels. Current historical tags preserve descriptive source metadata.

```json
{
  "tags": ["historical-note"]
}
```

| Observed value | Location |
| --- | --- |
| `historical-organization` | Example 008 Old Map Group. |
| `historical-note` | Example 008 note 002. |
| `historical-fronting-context` | Example 008 front-history event 002. |
| `historical-system-member` | Example 008 member occurrences directly under Old Map. |

Tags do not establish containment or replace relationship records. Unrecognized tags may be ignored by consumers that cannot use them.

Empty tag arrays are omitted in the current examples.

## Illustrative shape file

`sample-output/pluralbridge-system-models/example-shape.json` illustrates the core account, shared records, and tree occurrence shape.

It is not a thirteenth canonical example and is not generated.

Compared with the twelve canonical examples:

- It omits export metadata and several account identity fields.
- It omits relationships and front history.
- It demonstrates a non-empty member `fieldIds` association.
- It demonstrates explicit occurrence visibility using `value: "self"`.
- Its notes omit `supportsMarkdown`.
- Its custom fields omit `fieldType` and `supportsMarkdown`.

These differences must be distinguished from formal required-field rules, which remain to be completed.

## Pending model alignment

The current JSON files and the newer generator-feed discussion are not yet fully aligned.

1. **Account defaults:** The twelve canonical examples still have no account-level permission or visibility. Feed imports now serialize both. See **Feed-import account settings**. They do not add `username` when the feed does not supply one.

2. **Anchor settings:** The broader model calls for visibility and permissions at anchors. The current JSON contains no such settings on shared anchors or anchor tree occurrences. Their serialized placement remains to be settled.

3. **Fronting visibility:** Fronting was specified to have visibility without a separate fronting-permission setting. The current JSON has no explicit fronting-visibility representation.

4. **Roles and permissions:** Role names and operation permissions must be defined separately. Existing role-like UI values are not an approved operation-permission vocabulary.

5. **Custom-field values:** Current records define fields and associations, but no serialized value-bearing record has been established.

These are documented gaps. The feed-import setting objects below are the exception: they are written by the proof-of-concept importer and are not present in the twelve examples.

## Feed-import account settings

**Paths:** `$.account.permissions`, `$.account.visibility`

Present on proof-of-concept feed imports. Absent from the twelve canonical examples. `username` stays present on those examples and is omitted on feed imports.

Explicit account permissions, including a single type:

```json
{
  "mode": "explicit",
  "value": ["read", "write"]
}
```

Explicit account visibility:

```json
{
  "mode": "explicit",
  "value": "trusted friends"
}
```

A member occurrence uses the same permission array when the feed sets `permission:`. Popeye’s visibility in the main feed remains the string `self`. Omitted occurrence settings stay `{"mode":"inherit"}`.

| Field | JSON type | Meaning | Presence / null handling |
| --- | --- | --- | --- |
| `mode` | string | `explicit` when the feed supplies a value. `inherit` when that account or occurrence setting is omitted. | Required on these feed-import objects. |
| `value` | array of string, or string | Permission types, or one visibility audience. | Present only when `mode` is `explicit`. A single permission type is still an array. |

Permission types are `read`, `write`, `create`, `delete`, `inherit`, and `all`. Visibility audiences are `only you`, `trusted friends`, `all friends`, `selected people`, and `inherit`. The feed token `self` is preserved and is not renamed to `only you`.

## Feed-import avatars

**Paths:** `$.account.config`, `$.account.anchors[].config`, `$.account.members[].config`

The twelve canonical examples already store `account.config` as 64 × 64 `solid`. This section is the feed-import resolution. Generating PNG files for those twelve examples is not part of the feed importer.

Without a `Config` block the global default is width `64`, height `64`, and avatar `none`. A `Config` value replaces one attribute at a time. An anchor bracket then replaces attributes for members declared in that bracket, outer anchor before inner anchor. A member or member-range block replaces attributes again. The position of a setting inside the brackets does not matter.

`account.config` stores that resolved global default. It uses `avatar-width`, `avatar-height`, and `avatar`. `color` is added there only when `Config` itself sets `#RRGGBB`. An anchor `config` stores only the attributes written on that anchor. A shared member `config` stores only the attributes written on that member, including `color` when the member sets it. Tree occurrences do not receive `config`.

One shared member has one avatar. An attribute written on the member applies to every placement. A later placement that omits it does not clear it. Two member blocks that set different values are an error, as are enclosing scopes that disagree on an attribute the member never sets. The message names both member declaration lines and the setting lines. The importer does not keep the later request.

PNG files are written beside the feed JSON:

`out/imports/pluralbridge/<feed-stem>-avatars/<memberId>.png`

`<memberId>` is `account.members[].memberId`. That directory belongs to one feed. A successful rerun removes PNGs in that directory that the new run did not generate. It does not clear `out/` or another feed’s directory. `avatar` `none` writes no file for that member. The JSON does not embed the PNG bytes and does not add an asset collection.

## Unresolved format requirements

- Complete vocabularies for account and System status, `fieldType`, and front-history status. Feed-import permission types and visibility audiences are listed under **Feed-import account settings**. Enforcement of those values is not specified.
- The inheritance-resolution algorithm and explicit override behavior.
- Authoritative roles, operation permissions, visibility definitions, and their enforcement.
- Which fields are required, optional, or nullable beyond the established relationship-target rule.
- Whether empty account-level `members`, `anchors`, or `tree` collections may be omitted.
- The element shape of non-empty `provenance.lossyMappings`.
- Format-version semantics beyond `0.1-draft`.
- General lifecycle semantics of export audit timestamps.
- The pending model-alignment items above.

Database audit, link, placement, and access-membership records are not serialized as separate collections in this format.