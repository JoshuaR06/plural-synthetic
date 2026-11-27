# PluralPort sample export and record reference

This note describes `PP/pluralport-comprehensive-example.json`. The sample is fictional. It follows the four Markdown files inside the supplied ZIP and does not use another specification.

## Source

| Item | Value |
| --- | --- |
| ZIP filename | `PP/pluralport.zip` |
| SHA-256 | `845e33126b5fa9047c0779080214c6120e90065f03f3bb9c7f40e5f5ef6e2979` |
| Files in the ZIP | `spec.md`, `spec-records.md`, `spec-fronting.md`, `spec-modules.md` |
| Draft label | draft v0.1 |
| Envelope version key | `openplural_version` = `"0.1"` |

The ZIP titles and the envelope still use the OpenPlural name. `spec.md` is titled “OpenPlural Draft API Spec”. `spec-records.md`, `spec-fronting.md`, and `spec-modules.md` are titled “OpenPlural Spec”. There is no `pluralport_version` key in these files.

`spec-modules.md`, section “Validator plans”, says a JSON Schema for `openplural_version: "0.1"` is planned. The ZIP does not contain a JSON Schema. Checks below are local checks against the Markdown tables.

Words used here:

- **Required** means the field table cell says `yes`.
- **Optional** means that cell says `no`. An optional field may be omitted.
- **Nullable** means the published type includes `null`.
- **Default** means the notes state a default. A default is not the same as a required value.
- **Recommended** means a sidebar lists values but the field type remains `string`.
- **Provisional** means `spec-modules.md` marks that module provisional. The sample still uses the published field tables.

## Envelope and module placement

`spec.md`, section “Top-level envelope”, gives one JSON example and no field table. The sample uses that example’s version key and these keys:

| Key | JSON type in the sample | Role |
| --- | --- | --- |
| `openplural_version` | string | `"0.1"`. |
| `exported_at` | string | `2026-04-29T18:00:00Z`. |
| `producer` | object | Producer record. |
| `capabilities` | object | Capabilities record. |
| `systems` | array | System records. |
| `members` | array | Member records. Birthdays and proxy tags are nested here. |
| `groups` | array | Group records. |
| `group_memberships` | array | GroupMembership records. |
| `taxonomy_terms` | array | TaxonomyTerm records. |
| `taxonomy_assignments` | array | TaxonomyAssignment records. |
| `custom_fields` | array | CustomFieldDefinition records. |
| `custom_field_values` | array | CustomFieldValue records. |
| `notes` | array | Note records. |
| `assets` | array | Asset records. |
| `front_periods` | array | FrontPeriod records. FrontAssignment records are nested in `assignments`. |
| `front_events` | array | FrontEvent records. FrontAssignment records are nested in `assignments`. |
| `front_comments` | array | FrontComment records. |
| `chat` | object | `conversations`, `messages`, `attachments`, `reactions`. |
| `boards` | object | `posts`. |
| `relationships` | object | Provisional. `types` and `edges`. |
| `extensions` | object | Empty object. |
| `warnings` | array | Warning records. |

`capabilities.modules` lists only modules that contain records in this file:

`systems`, `members`, `groups`, `taxonomy`, `custom_fields`, `front_periods`, `front_events`, `front_comments`, `notes`, `assets`, `chat`, `boards`, `relationships`.

The legal module strings are the Capabilities table in `spec-records.md`. `groups` covers both `groups` and `group_memberships`. `taxonomy` covers terms and assignments. `custom_fields` covers definitions and values. `chat`, `boards`, and `relationships` are objects, not top-level arrays. Front assignments are not a module and not a top-level array.

These module names are only sketches in `spec-modules.md`, section “Other optional modules”: `polls`, `reminders`, `habits`, `proxy`, `sharing`, `safety`. They are absent from `capabilities.modules` and absent as keys. No record shape is invented for them. The sketched `proxy` module is not the member `ProxyTag` record.

## Identifiers, source references, timestamps, nulls, and omission

`spec.md`, “File-local IDs”, says every record has a file-local `id`, prefers UUIDv7 or ULID, and says importers must not assume an algorithm. `spec-records.md`, “Type notation”, defines `UUID` as a file-local id and names UUIDv4, UUIDv7, and ULID. The sample uses RFC 4122 UUID version 4 strings for file-local ids. Code samples in the specification use prefixed strings such as `sys_01HV4Z...`. Those samples are not declared as the identifier grammar. See “Ambiguities”.

`source_refs[].id` is the original app’s string key, not a file-local UUID. The sample uses synthetic ids such as `synthetic-member-0001` and, for the PluralKit-shaped member ref, `abcde`. `source_refs[].uuid`, when present and not null, is a UUID. Blair’s Sheaf ref omits `uuid`. Other refs set `uuid` to null. The specification does not say that omission and JSON null are equivalent.

Timestamps are UTC `YYYY-MM-DDTHH:MM:SSZ`, from `spec.md`, “UTC timestamps”. Date fields that use the `Date` notation are `YYYY-MM-DD`. Birthday `value` uses the four forms named on the Birthday table.

Nullable fields in the sample are often explicit JSON null. Optional fields that the tables do not list are omitted. Examples: GroupMembership, Attachment, Reaction, and FrontAssignment have no `extensions` key because their tables do not list one.

## Privacy, extensions, and warnings

Privacy `visibility` uses the closed set `public`, `friends`, `private`, `trusted`, `unknown` (`spec-records.md`, Privacy). The sample uses each value at least once: Harbor `private`, Alex `friends`, Blair `trusted`, Blur `public`, Side Loft and Drew `unknown`.

`privacy.source` is an open object. Harbor and Alex set `source_label`. That key is fictional raw content inside the open object. It is not a specified field. Other privacy objects use `source: {}`.

`extensions` on the envelope and on records is `{}`. `spec-records.md` says member Markdown depends on `extensions.openplural.markdown_fields`, but it does not define that object. The sample does not invent it. The reserved `openplural` namespace is named in `spec.md`, “Registered app IDs”, and is unused here.

Registered app ids used in `source_refs` are `simply_plural`, `lighthouse`, `pluralkit`, `sheaf`, `plural_star`, and `prism`. Producer `app` is the fictional display name “Harbor Notes”. `app_id` is omitted because that name is not in the registered list.

Envelope warnings:

- `asset_uri_only` points at the banner asset, which has `uri` and null `data_base64` and `data_uri`. `spec-records.md`, Asset callout, asks for this warning when only `uri` is populated.
- `relationships_parsed_from_text` points at the first relationship edge. That edge’s `note` keeps the opaque sentence it was parsed from. `spec-modules.md`, relationships callout, names this code for a lossy text parse.

Both warnings use `level` `warning`, `count` 1, and a `record_id` that exists. No warning claims a condition the sample does not contain.

`spec.md` says the `warnings` fragment can appear on any record, and `spec-records.md` says warnings can appear at file level or on individual records. No record field table lists a `warnings` field. The sample puts warnings only on the envelope. See “Ambiguities”.

## Reference relationships in the sample

| From | To |
| --- | --- |
| Side Loft `parent_system_id` | Harbor system |
| Harbor `avatar_asset_id` | avatar asset |
| Side Loft `banner_asset_id` | uri-only banner asset |
| Each member `system_id` | Harbor, except Eden, whose system is Side Loft |
| Alex `avatar_asset_id` | avatar asset |
| Bedtime `parent_group_id` | Daily group |
| Group memberships | Daily contains Alex and Blair; Bedtime contains Alex again |
| Journal term `parent_term_id` | Labels term |
| Taxonomy assignments | Host role on Alex (`profile`) and Blair (`appearance`); Journal tag on the member note (`scope` null) and the text asset (`custom`); Host role on the closed front period (`session`) |
| Custom field values | Role label and Likes on Alex; Noted on on Harbor; Away span on Blair |
| Member note | Alex, authors Alex and Blair, attachment the text asset |
| System note | `member_id` null |
| Front periods and events | member ids in nested assignments; comments link to the closed period or the switch-in event |
| Chat | messages belong to General; the reply points at the text message; the reply and the file message reference the text asset; the Attachment row points at the reply and that asset; reactions point at the text message |
| Board posts | one targets Alex and is written by Blair; one has null target and null author |
| Relationship edges | Blair `parent_of` Eden; Alex `partner` Blair. See the cross-system note under Ambiguities. |
| Warning `record_id` | banner asset; first relationship edge |

`source_refs` do not point at file-local records.

## Records

### Producer

Identifies the app that wrote the export. Path: `$.producer`. Source: `spec-records.md`, “Producer”.

```json
{
  "app": "Harbor Notes",
  "app_version": "0.0.0-sample",
  "exporter_version": "0.0.0-sample"
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `app` | string | yes | Display name of the producing app. | Not required to be a registered id. |
| `app_version` | string | no | Producing app release version. | |
| `exporter_version` | string | no | Exporter implementation version, when separate from the app. | |
| `app_id` | string | no | Short canonical app id from `spec.md`, “Registered app IDs”. | Omitted. “Harbor Notes” is not registered. |

### Capabilities

Declares which modules the file populates. Path: `$.capabilities`. Source: `spec-records.md`, “Capabilities”.

```json
{
  "modules": [
    "systems",
    "members",
    "groups",
    "taxonomy",
    "custom_fields",
    "front_periods",
    "front_events",
    "front_comments",
    "notes",
    "assets",
    "chat",
    "boards",
    "relationships"
  ]
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `modules` | array of strings | yes | Module names this file populates. | The table lists the allowed strings, including the six sketched modules. This file lists only populated modules. |

### SourceRef

Original app identifier for a converted record. Paths: `source_refs` arrays on the records whose tables include that field. Source: `spec-records.md`, “SourceRef”. Representative ref from Alex:

```json
{
  "app": "pluralkit",
  "collection": "members",
  "id": "abcde",
  "uuid": "5b2c1d40-1111-4111-8111-0000000000aa"
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `app` | string | yes | Registered app id. | Sample uses registered ids only. |
| `collection` | string | yes | Source collection or table name. | Free string. Values such as `custom_fronts` and `group_members` are source names, not OpenPlural collections. |
| `id` | string | yes | Source primary key, string-coerced. | Not a file-local UUID. |
| `uuid` | string or null | no | Separate stable UUID when the source app has one. | Blair’s ref omits it. |

Alex has two refs, which is the stated round-trip case. Blur’s ref uses collection `custom_fronts` because `is_custom_front` is true.

### Privacy

Conservative privacy descriptor plus original source detail. Paths: `privacy` on System, Member, and CustomFieldDefinition. Source: `spec-records.md`, “Privacy”.

```json
{
  "visibility": "private",
  "source": {
    "source_label": "system-only"
  }
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `visibility` | string | no | Common privacy bucket. | Closed set: `public`, `friends`, `private`, `trusted`, `unknown`. |
| `source` | object | no | Raw source privacy data. | Open object. Keys inside it are not specified. |

The Privacy type is not nullable. Where the sample includes `privacy`, it is an object.

### Warning

Loss, degradation, or skipped data. Path: `$.warnings[]`. Also used inside ImportResult, which is not part of the export. Source: `spec-records.md`, “Warning”.

```json
{
  "level": "warning",
  "code": "asset_uri_only",
  "record_type": "Asset",
  "record_id": "9a1b2c3d-4e5f-4a6b-8c7d-111111111002",
  "message": "Banner asset 9a1b2c3d-4e5f-4a6b-8c7d-111111111002 has only uri and no inline bytes.",
  "count": 1
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `level` | string | yes | Severity. | `info`, `warning`, or `error`. `error` means data was lost. `warning` means degraded or partial preservation. |
| `code` | string | yes | Machine-readable code. | Sample uses `asset_uri_only` and `relationships_parsed_from_text`, both named in the source. |
| `record_type` | string or null | no | OpenPlural record type or path. | Sample uses type names. The ImportResult example uses `chat.messages`. |
| `record_id` | string or null | no | File-local id, when there is one. | Both sample warnings resolve. |
| `message` | string | yes | Human-readable explanation. | |
| `count` | number or null | no | Aggregate count. | Sample uses 1. |

### System

Plurality system profile and nesting. Path: `$.systems[]`. Source: `spec-records.md`, “System”. Two systems: Harbor, and archived Side Loft nested under Harbor.

```json
{
  "id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1002",
  "name": "Side Loft",
  "display_name": null,
  "description": null,
  "tag": null,
  "color": null,
  "avatar_asset_id": null,
  "banner_asset_id": "9a1b2c3d-4e5f-4a6b-8c7d-111111111002",
  "parent_system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "archived": true,
  "privacy": { "visibility": "unknown", "source": {} },
  "settings": {},
  "source_refs": [
    {
      "app": "lighthouse",
      "collection": "systems",
      "id": "synthetic-system-0002",
      "uuid": "5b2c1d40-1111-4111-8111-000000000002"
    }
  ],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | Target of `system_id` and `parent_system_id`. |
| `name` | string | yes | System name. | |
| `display_name` | string or null | no | Alternate display form. | Null on Side Loft. |
| `description` | string or null | no | Description. Markdown is allowed. | |
| `tag` | string or null | no | System tag or suffix. | Harbor uses `\| hs`. |
| `color` | string or null | no | Accent color. | `#RRGGBB` or null. |
| `avatar_asset_id` | string or null | no | Avatar asset. | `assets[].id`. |
| `banner_asset_id` | string or null | no | Banner asset. | `assets[].id`. Side Loft points at the uri-only asset. |
| `parent_system_id` | string or null | no | Parent system for nesting. | `systems[].id`. |
| `archived` | boolean | no | Archived flag. | Default `false` is stated. Sample sets both `false` and `true`. |
| `privacy` | object | no | Privacy record. | |
| `settings` | object | no | App-agnostic settings. | No keys are specified. Sample uses `{}`, matching the System example. App-specific settings belong in `extensions`. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | Sample uses `{}`. |

### Member

Member, alter, headmate, custom front, or equivalent profile. Role-like labels are taxonomy, not fields on this record. Path: `$.members[]`. Source: `spec-records.md`, “Member”.

Alex is the populated profile. Blair shows month-day birthday and trusted privacy. Blur is a custom front with `birthday` null. Drew has `name` null, display name “Unnamed”, and `archived` true. Eden belongs to Side Loft.

```json
{
  "id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3003",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "name": "Blur",
  "display_name": "Blur",
  "pronouns": null,
  "description": "Fictional custom front, not a profile member.",
  "age": null,
  "birthday": null,
  "color": "#999999",
  "avatar_asset_id": null,
  "banner_asset_id": null,
  "proxy_tags": [],
  "is_custom_front": true,
  "archived": false,
  "created_at": null,
  "sort_order": 2,
  "privacy": { "visibility": "public", "source": {} },
  "source_refs": [
    {
      "app": "simply_plural",
      "collection": "custom_fronts",
      "id": "synthetic-front-0001",
      "uuid": null
    }
  ],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `name` | string or null | no | Member name. | Null is specified for apps that allow nameless alters. Drew uses null and `display_name` “Unnamed”. |
| `display_name` | string or null | no | Display form. | Null on Eden. |
| `pronouns` | string or null | no | Free text. | No pronoun enum. |
| `description` | string or null | no | Bio. | Markdown is conditional on an undefined extension. Sample text does not rely on that extension. |
| `age` | string or null | no | Free text, including ranges and “ageless”. | Alex is `ageless`. Drew is `30s`. |
| `birthday` | object or null | no | Birthday record. | Null on Blur. |
| `color` | string or null | no | `#RRGGBB` or null. | |
| `avatar_asset_id` | string or null | no | Avatar asset. | `assets[].id`. |
| `banner_asset_id` | string or null | no | Banner asset. | `assets[].id`. |
| `proxy_tags` | array | no | ProxyTag records. | This is the member sub-record, not the sketched proxy module. |
| `is_custom_front` | boolean | no | Custom front rather than an ordinary profile. | Default `false`. Blur is `true`. |
| `archived` | boolean | no | Archived flag. | Default `false`. Drew is `true`. |
| `created_at` | string or null | no | Creation time. | UTC timestamp or null. |
| `sort_order` | number or null | no | Lower sorts earlier. | Drew is null. |
| `privacy` | object | no | Privacy record. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### Birthday

Birthday precision on a member. Path: `$.members[].birthday`. Source: `spec-records.md`, “Birthday”. Alex is a full day. Blair is month-day with the year hidden. Drew is year only. Eden is year-month.

```json
{
  "value": "--11-02",
  "precision": "month_day",
  "year_visible": false
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `value` | string | yes | Date text matching `precision`. | `YYYY-MM-DD`, `--MM-DD`, `YYYY`, or `YYYY-MM`. |
| `precision` | string | yes | Known granularity. | `day`, `month`, `year`, or `month_day`. There is no `unknown` value in this table. |
| `year_visible` | boolean | no | When `false`, importers should hide the year in UI. | Default `true`. Blair sets `false`. |

### ProxyTag

PluralKit-style proxy tag on a member. Path: `$.members[].proxy_tags[]`. Source: `spec-records.md`, “ProxyTag”. Alex has a prefix-only tag and a suffix-only tag. Blair has both sides. This is not the `proxy` module sketch.

```json
{ "prefix": "a:", "suffix": null }
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `prefix` | string or null | no | Match prefix. | |
| `suffix` | string or null | no | Match suffix. | |

A tag with both sides null is not in the sample.

### Group

Hierarchical member grouping. Path: `$.groups[]`. Source: `spec-records.md`, “Group”. Daily is the parent. Bedtime nests under Daily.

```json
{
  "id": "6d5c4b3a-2918-4f70-8e6d-222222222002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "name": "Bedtime",
  "description": null,
  "color": null,
  "emoji": null,
  "parent_group_id": "6d5c4b3a-2918-4f70-8e6d-222222222001",
  "sort_order": 1,
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `name` | string | yes | Group name. | |
| `description` | string or null | no | Description. | |
| `color` | string or null | no | `#RRGGBB` or null. | |
| `emoji` | string or null | no | Single emoji. | No Unicode matching rule is stated. Daily uses U+2600. |
| `parent_group_id` | string or null | no | Parent group. | `groups[].id`. Null means a root group. |
| `sort_order` | number or null | no | Sort position. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

The Sheaf callout says inline `member_ids` become GroupMembership records. The sample uses that normalized shape.

### GroupMembership

Many-to-many edge between a group and a member. Path: `$.group_memberships[]`. Source: `spec-records.md`, “GroupMembership”. Alex is in both groups.

```json
{
  "id": "71a0b1c2-d3e4-4f56-8a78-333333333003",
  "group_id": "6d5c4b3a-2918-4f70-8e6d-222222222002",
  "member_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3001",
  "sort_order": null,
  "source_refs": []
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `group_id` | string | yes | Group. | `groups[].id`. |
| `member_id` | string | yes | Member. | `members[].id`. |
| `sort_order` | number or null | no | Position within the group. | |
| `source_refs` | array | no | SourceRef records. | |

### TaxonomyTerm

Reusable label of a given kind. Path: `$.taxonomy_terms[]`. Source: `spec-records.md`, “TaxonomyTerm”. Host is `kind` `role`. Labels is a parent tag. Journal is a child tag.

```json
{
  "id": "82b1c2d3-e4f5-4a67-8b89-444444444003",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "kind": "tag",
  "name": "Journal",
  "description": null,
  "color": "#e8a13c",
  "parent_term_id": "82b1c2d3-e4f5-4a67-8b89-444444444002",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `kind` | string | yes | Label kind. | Recommended, not closed: `role`, `tag`, `source`, `relationship`, `identity`, `topic`, `status`, `custom`, `unknown`. |
| `name` | string | yes | Term name. | |
| `description` | string or null | no | Description. | |
| `color` | string or null | no | `#RRGGBB` or null. | |
| `parent_term_id` | string or null | no | Parent term. | `taxonomy_terms[].id`. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### TaxonomyAssignment

Attaches a term to a subject. Path: `$.taxonomy_assignments[]`. Source: `spec-records.md`, “TaxonomyAssignment”.

```json
{
  "id": "93c2d3e4-f506-4b78-8c9a-555555555001",
  "term_id": "82b1c2d3-e4f5-4a67-8b89-444444444001",
  "subject_type": "member",
  "subject_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3001",
  "scope": "profile",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `term_id` | string | yes | Term. | `taxonomy_terms[].id`. |
| `subject_type` | string | yes | Subject collection. | `member`, `note`, `asset`, `front_period`, or `custom`. |
| `subject_id` | string | yes | Subject id. | For the four concrete types, the sample points at that collection. |
| `scope` | string or null | no | Optional context. | `profile`, `appearance`, `session`, `custom`, or null. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

`subject_type` `custom` is not used. The table does not name a target collection for it.

### CustomFieldDefinition

Name, type, and metadata for a custom field. Path: `$.custom_fields[]`. Source: `spec-records.md`, “CustomFieldDefinition”.

The sample has a select (“Role label”, options as a string array), a date (“Noted on”, options as an object, `date_precision` `day`), a date range (“Away span”, `options` null), and a multiselect (“Likes”).

```json
{
  "id": "c6f50617-2839-4eab-8fcd-888888888003",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "name": "Away span",
  "field_type": "date_range",
  "options": null,
  "supports_markdown": false,
  "date_precision": "day",
  "sort_order": null,
  "privacy": { "visibility": "private", "source": {} },
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `name` | string | yes | Display name. | |
| `field_type` | string | yes | Value kind. | Recommended, not closed: `text`, `markdown`, `number`, `boolean`, `color`, `date`, `date_range`, `timestamp`, `month`, `year`, `month_year`, `month_day`, `select`, `multiselect`, `json`. |
| `options` | array, object, or null | no | Select options, or a verbatim object. | String array for Role label and Likes. Object for Noted on. Null for Away span. Keys inside the object are not specified. |
| `supports_markdown` | boolean | no | Rendering hint for text or markdown types. | The type is not nullable. No default is stated. |
| `date_precision` | string or null | no | Precision for date and date-range fields. | Same four strings as Birthday, or null. |
| `sort_order` | number or null | no | Display order. | |
| `privacy` | object | no | Privacy record. | Not nullable. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### CustomFieldValue

One value for one definition and one subject. Path: `$.custom_field_values[]`. Source: `spec-records.md`, “CustomFieldValue”.

```json
{
  "id": "d7061728-394a-4fbc-80de-999999999003",
  "field_id": "c6f50617-2839-4eab-8fcd-888888888003",
  "subject_type": "member",
  "subject_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3002",
  "value": { "start": "2026-04-01", "end": "2026-04-03" },
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `field_id` | string | yes | Definition. | `custom_fields[].id`. |
| `subject_type` | string | yes | Subject kind for v0.1. | `member` or `system` only. |
| `subject_id` | string | yes | Subject id. | `members[].id` or `systems[].id`. |
| `value` | any JSON value | yes | Payload matching `field_type`. | `multiselect` is a string array. `date_range` is an object with `start` and `end`. Other value encodings are not given separate schemas. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

The select value is the string `host`, one of that field’s options. The date value is the string `2026-04-29`. Those two JSON types are applications of “type matches the field’s `field_type`”, not separately tabulated encodings. `start` and `end` are named but not given types; the sample uses `YYYY-MM-DD` strings.

### Note

Journal or member note. Path: `$.notes[]`. Source: `spec-records.md`, “Note”. One note is attached to Alex, pinned, with two authors and a file attachment. One note is system-wide (`member_id` null, `visibility` `system`).

```json
{
  "id": "a4d3e4f5-0617-4c89-8dab-666666666002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "member_id": null,
  "title": null,
  "body": "Fictional system-wide note.",
  "created_at": "2026-04-28T12:00:00Z",
  "updated_at": null,
  "entry_date": null,
  "author_member_ids": [],
  "color": null,
  "visibility": "system",
  "pinned": false,
  "content_warning": null,
  "attachment_asset_ids": [],
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `member_id` | string or null | no | Primary subject member. | Null for a system-wide entry. `members[].id`. |
| `title` | string or null | no | Title. | |
| `body` | string | yes | Body. Markdown unless flagged otherwise. | |
| `created_at` | string | yes | Creation time. | UTC timestamp. Not nullable. |
| `updated_at` | string or null | no | Update time. | |
| `entry_date` | string or null | no | Journal day. | `YYYY-MM-DD` or null. |
| `author_member_ids` | array of strings | no | Co-authors. | `members[].id`. |
| `color` | string or null | no | `#RRGGBB` or null. | |
| `visibility` | string or null | no | Note visibility. | `private`, `system`, `friends`, `trusted`, `public`, or null. This is not the Privacy record. |
| `pinned` | boolean | no | Pinned flag. | No default is stated. |
| `content_warning` | string or null | no | Content warning. | |
| `attachment_asset_ids` | array of strings | no | Attached assets. | `assets[].id`. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

The same section says multi-member journal subjects might later need something like `subject_member_ids`. That field is not defined. The sample does not add it. `author_member_ids` is who wrote the note.

### Asset

Image, file, or media blob referenced by id. Path: `$.assets[]`. Source: `spec-records.md`, “Asset”.

The avatar is a 1×1 PNG stored as both `data_base64` and `data_uri` for the same bytes. The banner is uri-only and is the `asset_uri_only` warning. The text file is `data_base64` only: bytes `fictional-note`, size 14.

```json
{
  "id": "9a1b2c3d-4e5f-4a6b-8c7d-111111111003",
  "kind": "file",
  "mime_type": "text/plain",
  "file_name": "note.txt",
  "uri": null,
  "data_base64": "ZmljdGlvbmFsLW5vdGU=",
  "data_uri": null,
  "size_bytes": 14,
  "sha256": "4df3e61e92527cfd936c19fe79c62df73040386dcd27bcdc216da9b453e038f7",
  "width": null,
  "height": null,
  "duration_ms": null,
  "source_refs": [],
  "extensions": {}
}
```

Avatar payload, shared by `data_base64` and the base64 part of `data_uri`:

`iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mPYEqUBAAL8ATdHJTIjAAAAAElFTkSuQmCC`

Decoded size 69. SHA-256 `83803707a337c9ced1fcd0cfd609f8d9f363f7e207f73d434117402fd6e19e3b`. MIME `image/png`. IHDR width 1 and height 1.

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `kind` | string | yes | Asset kind. | `avatar`, `banner`, `image`, `audio`, `video`, `file`, `thumbnail`, or `unknown`. |
| `mime_type` | string or null | no | MIME type. | |
| `file_name` | string or null | no | File name. | |
| `uri` | string or null | no | External URL. | Treated as fragile. |
| `data_base64` | string or null | no | Base64 payload without a data-URI prefix. | |
| `data_uri` | string or null | no | Full `data:<mime>;base64,<...>` value. | |
| `size_bytes` | number or null | no | Decoded size. | |
| `sha256` | string or null | no | Hex digest. Recommended for dedupe, not required. | |
| `width` | number or null | no | Pixel width. | |
| `height` | number or null | no | Pixel height. | |
| `duration_ms` | number or null | no | Audio or video duration. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | The notes mention Prism blurhash and waveform as examples. The sample does not add them. |

At least one of `uri`, `data_base64`, or `data_uri` must be populated. The prose also says to use either inline data or an external uri. The avatar populates both inline fields and not `uri`. The file populates only `data_base64`. The banner populates only `uri`.

### FrontPeriod

Interval during which one or more members were fronting. Path: `$.front_periods[]`. Source: `spec-fronting.md`, “FrontPeriod”.

Four periods:

- Closed tiered period, Alex `primary` and Blair `co_front`, `source_kind` `tiered`.
- Open Alex period, `ended_at` null, `front_role` `member`, `source_kind` `event_pair`.
- Open Blur custom-front period, `status` `masking`, `front_role` `custom_status`, `source_kind` `interval`.
- Closed Blair period, `front_role` `co_conscious`, `presence` `asleep`, `status` `sleep`, `source_kind` `unknown`.

`spec-fronting.md`, “Conversion notes”, says more than one member may be fronting at the same time and that every open entry should be preserved. The two open periods are different members.

```json
{
  "id": "b5e4f506-1728-4d9a-8ebc-777777777002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "started_at": "2026-04-29T16:00:00Z",
  "ended_at": null,
  "assignments": [
    {
      "member_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3001",
      "front_role": "member",
      "confidence": 1,
      "presence": "present",
      "mood": null,
      "energy": null,
      "location": null,
      "note": null,
      "source_refs": []
    }
  ],
  "status": null,
  "note": null,
  "source_kind": "event_pair",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `started_at` | string | yes | Interval start. | UTC timestamp. |
| `ended_at` | string or null | no | Interval end. | Null means currently fronting. |
| `assignments` | array | yes | FrontAssignment records. | At least one. |
| `status` | string or null | no | Period-level status, such as `sleep` or `masking`. | Examples, not a closed enum. |
| `note` | string or null | no | Note for the whole period. | Distinct from assignment `note`. |
| `source_kind` | string | no | How the period was derived. | `interval`, `event_pair`, `tiered`, `grouped`, or `unknown`. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### FrontAssignment

One member’s role inside a period or event. Paths: `$.front_periods[].assignments[]` and `$.front_events[].assignments[]`. Not a top-level collection. Source: `spec-fronting.md`, “FrontAssignment”.

```json
{
  "member_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3001",
  "front_role": "primary",
  "confidence": 0.9,
  "presence": "present",
  "mood": "steady",
  "energy": "medium",
  "location": "desk",
  "note": "Fictional per-assignment note.",
  "source_refs": []
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `member_id` | string | yes | Member in this front. | `members[].id`. |
| `front_role` | string | yes | Tier inside this period or event. | Recommended: `primary`, `co_front`, `co_conscious`, `influencing`, `member`, `custom_status`, `unknown`. Not a profile role. |
| `confidence` | number or null | no | Confidence from 0 to 1. | |
| `presence` | string or null | no | Presence metadata. | Listed examples: `present`, `background`, `muted`, `asleep`. The type also allows any string. |
| `mood` | string or null | no | Mood text. | |
| `energy` | string or null | no | Energy text. | |
| `location` | string or null | no | Location text. | |
| `note` | string or null | no | Per-assignment note. | |
| `source_refs` | array | no | SourceRef records. | |

### FrontEvent

Point-in-time switch. Path: `$.front_events[]`. Source: `spec-fronting.md`, “FrontEvent”. One event assigns Alex. One event has an empty `assignments` array, which the table allows for a switch-out.

```json
{
  "id": "c6f61728-3940-4eab-8fcd-aaaaaaaaa002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "at": "2026-04-29T11:00:00Z",
  "assignments": [],
  "note": "Fictional switch-out with nobody fronting.",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `at` | string | yes | Switch instant. | UTC timestamp. |
| `assignments` | array | yes | Members fronting after the switch. | May be empty. Items are FrontAssignment records. |
| `note` | string or null | no | Event note. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### FrontComment

Comment anchored to a time, optionally linked to a period or event. Path: `$.front_comments[]`. Source: `spec-fronting.md`, “FrontComment”. One comment links to the closed period. One links to the switch-in event and has `edited_at` set.

```json
{
  "id": "d708293a-4b51-4fcd-80ef-bbbbbbbbb002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "front_period_id": null,
  "front_event_id": "c6f61728-3940-4eab-8fcd-aaaaaaaaa001",
  "target_time": "2026-04-29T16:00:00Z",
  "author_member_id": null,
  "body": "Fictional comment about the switch.",
  "created_at": "2026-04-29T16:05:00Z",
  "edited_at": "2026-04-29T16:06:00Z",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `front_period_id` | string or null | no | Linked period. | `front_periods[].id`. |
| `front_event_id` | string or null | no | Linked event. | `front_events[].id`. |
| `target_time` | string | yes | Instant the comment is about. | UTC timestamp. |
| `author_member_id` | string or null | no | Author. | `members[].id`. |
| `body` | string | yes | Comment text. | |
| `created_at` | string | yes | Creation time. | UTC timestamp. |
| `edited_at` | string or null | no | Edit time. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

The table does not require either link. A comment with both links null is not in the sample.

### Conversation

Container for chat messages. Path: `$.chat.conversations[]`. Source: `spec-modules.md`, “Conversation”. General is `internal_chat` with an empty participant list. The second conversation is an archived, muted direct message between Alex and Blair.

```json
{
  "id": "e8193a4b-5c62-40de-81f0-ccccccccc002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "kind": "direct_message",
  "title": null,
  "category": null,
  "description": null,
  "emoji": null,
  "participant_member_ids": [
    "4c0e8b11-2d55-4a6f-8c33-11aa22bb3001",
    "4c0e8b11-2d55-4a6f-8c33-11aa22bb3002"
  ],
  "creator_member_id": null,
  "archived": true,
  "muted": true,
  "direct_message": true,
  "created_at": null,
  "sort_order": null,
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `kind` | string | yes | Conversation surface. | Recommended: `internal_chat`, `forum`, `thread`, `direct_message`, `proxy_log`, `unknown`. |
| `title` | string or null | no | Title. | |
| `category` | string or null | no | Optional grouping. | |
| `description` | string or null | no | Description. | |
| `emoji` | string or null | no | Emoji. | No single-emoji rule is stated here. General uses U+2709. |
| `participant_member_ids` | array of strings | no | Participants. | Empty for a system-wide channel. `members[].id`. |
| `creator_member_id` | string or null | no | Creator. | `members[].id`. |
| `archived` | boolean | no | Archived flag. | Default `false`. |
| `muted` | boolean | no | Muted flag. | No default is stated. |
| `direct_message` | boolean | no | Direct-message flag. | No default is stated. The sample sets it true only on the direct conversation. |
| `created_at` | string or null | no | Creation time. | |
| `sort_order` | number or null | no | Sort position. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### ChatMessage

One chat message. Path: `$.chat.messages[]`. Source: `spec-modules.md`, “ChatMessage”. Kinds present: `text`, `reply`, `system`, and `file`. The system message has a null author and `system_message` true. The reply points at the text message and carries the text asset.

```json
{
  "id": "f92a4b5c-6d73-41ef-8201-ddddddddd003",
  "conversation_id": "e8193a4b-5c62-40de-81f0-ccccccccc001",
  "author_member_id": null,
  "kind": "system",
  "body": "Fictional system message.",
  "created_at": "2026-04-29T18:03:00Z",
  "edited_at": null,
  "reply_to_message_id": null,
  "attachment_asset_ids": [],
  "system_message": true,
  "pinned": false,
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `conversation_id` | string | yes | Conversation. | `chat.conversations[].id`. |
| `author_member_id` | string or null | no | Author. | Null for a system message. `members[].id`. |
| `kind` | string | no | Message kind. | Closed set: `text`, `image`, `file`, `system`, `reply`, `reaction`, `unknown`. Default `text`. |
| `body` | string | yes | Message body. | |
| `created_at` | string | yes | Creation time. | UTC timestamp. |
| `edited_at` | string or null | no | Edit time. | |
| `reply_to_message_id` | string or null | no | Replied-to message. | `chat.messages[].id`. |
| `attachment_asset_ids` | array of strings | no | Lightweight asset refs. | `assets[].id`. Richer metadata is an Attachment record. |
| `system_message` | boolean | no | System-message flag. | No default is stated. |
| `pinned` | boolean | no | Pinned flag. | No default is stated. |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### Attachment

Richer metadata for one message attachment. Path: `$.chat.attachments[]`. Source: `spec-modules.md`, “Attachment”. The sample row uses role `primary` on the reply message and the text asset. The file-kind message uses only `attachment_asset_ids`.

```json
{
  "id": "0a3b5c6d-7e84-42f0-8312-eeeeeeeeee01",
  "message_id": "f92a4b5c-6d73-41ef-8201-ddddddddd002",
  "asset_id": "9a1b2c3d-4e5f-4a6b-8c7d-111111111003",
  "role": "primary",
  "caption": "Fictional caption.",
  "sort_order": 0,
  "source_refs": []
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `message_id` | string | yes | Message. | `chat.messages[].id`. |
| `asset_id` | string | yes | Asset. | `assets[].id`. |
| `role` | string or null | no | Attachment role. | `primary`, `thumbnail`, `preview`, `inline`, or null. |
| `caption` | string or null | no | Caption. | |
| `sort_order` | number or null | no | Sort position. | |
| `source_refs` | array | no | SourceRef records. | |

### Reaction

A reaction on a message. Path: `$.chat.reactions[]`. Source: `spec-modules.md`, “Reaction”. One reaction is Blair’s `👍`. One has `member_id` null and value `:wave:`.

```json
{
  "id": "1b4c6d7e-8f95-4301-8423-000000000002",
  "message_id": "f92a4b5c-6d73-41ef-8201-ddddddddd001",
  "member_id": null,
  "value": ":wave:",
  "created_at": null,
  "source_refs": []
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `message_id` | string | yes | Message. | `chat.messages[].id`. |
| `member_id` | string or null | no | Reacting member. | Null for an anonymous reaction. |
| `value` | string | yes | Emoji, `:shortcode:`, or an app-specific reaction id. | |
| `created_at` | string or null | no | Creation time. | |
| `source_refs` | array | no | SourceRef records. | |

### BoardPost

Member-addressed post, or a system timeline post when the target is null. Path: `$.boards.posts[]`. Source: `spec-modules.md`, “BoardPost”. v0.1 has no replies, threading, or per-post reactions. The sample does not put those in `extensions`.

One post targets Alex, is public, and is pinned. One post has null target, null author, `audience` `unknown`, and `deleted_at` set.

```json
{
  "id": "2c5d7e8f-90a6-4412-8534-101010101002",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "target_member_id": null,
  "author_member_id": null,
  "title": null,
  "body": "Fictional system timeline post with no surviving author.",
  "audience": "unknown",
  "pinned": false,
  "created_at": "2026-04-20T12:00:00Z",
  "written_at": null,
  "edited_at": null,
  "deleted_at": "2026-04-21T12:00:00Z",
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `target_member_id` | string or null | no | Addressed member. | Null means the system-wide timeline. `members[].id`. |
| `author_member_id` | string or null | no | Author. | Null means no surviving author. |
| `title` | string or null | no | Title. | |
| `body` | string | yes | Post body. | Required and non-empty. |
| `audience` | string | no | Audience. | `public`, `private`, or `unknown`. Default `public`. |
| `pinned` | boolean | no | Pinned flag. | Default `false`. |
| `created_at` | string | yes | Time the post entered the source system. | UTC timestamp. |
| `written_at` | string or null | no | User-facing authored time. | May differ from `created_at`. |
| `edited_at` | string or null | no | Edit time. | |
| `deleted_at` | string or null | no | Soft-delete time. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### RelationshipType

Provisional reusable type for a member-to-member edge. Path: `$.relationships.types[]`. Source: `spec-modules.md`, “RelationshipType”. The section heading marks the module provisional. The sample follows this table anyway.

`parent_of` is asymmetric and names the inverse `child_of`. `partner` is symmetric and has a null inverse.

```json
{
  "id": "3d6e8f90-a1b7-4523-8645-202020202001",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "name": "parent_of",
  "inverse_name": "child_of",
  "symmetric": false,
  "description": "Fictional asymmetric type. Provisional module.",
  "color": "#4f8fcf",
  "sort_order": 0,
  "source_refs": [],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | Owning system. | `systems[].id`. |
| `name` | string | yes | Type name. | Free string. No enum. |
| `inverse_name` | string or null | no | Opposite-direction name for an asymmetric type. | Null for a symmetric type. |
| `symmetric` | boolean | no | One stored edge covers both directions when true. | Default `false`. |
| `description` | string or null | no | Description. | |
| `color` | string or null | no | `#RRGGBB` or null. | |
| `sort_order` | number or null | no | Sort position. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

### MemberRelationship

Provisional edge between two members. Path: `$.relationships.edges[]`. The record name in the specification is MemberRelationship. The collection key in the example is `edges`, not `member_relationships`. Source: `spec-modules.md`, “MemberRelationship”.

The first edge is the parsed-from-text case. The second is a symmetric edge with `ended_at` and `deleted_at` set.

```json
{
  "id": "4e7f90a1-b2c8-4634-8756-303030303001",
  "system_id": "8f3c1a20-6b14-4c2e-9a71-0d5e6f7a1001",
  "from_member_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3002",
  "to_member_id": "4c0e8b11-2d55-4a6f-8c33-11aa22bb3005",
  "type_id": "3d6e8f90-a1b7-4523-8645-202020202001",
  "note": "Parsed from the opaque sentence: Blair looks after Eden.",
  "started_at": "2024-01-01T00:00:00Z",
  "ended_at": null,
  "created_at": "2026-04-29T18:00:00Z",
  "deleted_at": null,
  "source_refs": [
    {
      "app": "lighthouse",
      "collection": "relationships",
      "id": "synthetic-rel-text-0001",
      "uuid": null
    }
  ],
  "extensions": {}
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `id` | string | yes | File-local id. | |
| `system_id` | string | yes | System id on the edge. | `systems[].id`. The table does not require this to equal each member’s `system_id`. |
| `from_member_id` | string | yes | Subject member. For an asymmetric type, the parent in `parent_of`. | `members[].id`. |
| `to_member_id` | string | yes | Object member. | `members[].id`. |
| `type_id` | string | yes | Relationship type. | `relationships.types[].id`. |
| `note` | string or null | no | Annotation on this edge. | The parsed sentence is stored here, not in an extension. |
| `started_at` | string or null | no | Real-world start. | Distinct from `created_at`. |
| `ended_at` | string or null | no | Real-world end. | Null means ongoing. |
| `created_at` | string or null | no | When the record was written. | |
| `deleted_at` | string or null | no | Soft-delete time. | |
| `source_refs` | array | no | SourceRef records. | |
| `extensions` | object | no | Namespaced raw data. | |

## Provisional and incompletely specified areas

- Relationships are marked provisional in `spec-modules.md`. RelationshipType and MemberRelationship still have field tables. The sample uses those tables and the `relationships.types` / `relationships.edges` nesting from the example. The status is provisional, not an invitation to add fields.
- Polls, reminders, habits, proxy, sharing, and safety have module-card sketches only. No record tables. They are not populated and not listed in `capabilities.modules`.
- The proxy module sketch is explicitly distinct from member ProxyTag. ProxyTag is populated. The proxy module is not.
- `spec-records.md` says Note may later need an explicit multi-member subject field. It is not a current field.
- `spec-modules.md` says board replies, threading, and reactions are out of the v0.1 shape and may be stored in `extensions` until v0.2. The sample has none, and it does not invent an extension for them.
- Custom field `value` is `unknown`. Only multiselect and date_range have a stated JSON shape. Select and date values in the sample are strings.
- Several string fields have recommended values rather than closed enums: taxonomy `kind`, custom `field_type`, conversation `kind`, and `front_role`. Chat message `kind`, asset `kind`, privacy `visibility`, note `visibility`, attachment `role`, board `audience`, and front `source_kind` are closed lists.

## Fields and variants the sample does not demonstrate

These are specified values or situations that a coherent extra record was not required to show:

- Taxonomy `kind`: `source`, `relationship`, `identity`, `topic`, `status`, `custom`, `unknown`.
- Taxonomy `subject_type` `custom`, because no target collection is named.
- Custom `field_type`: `text`, `markdown`, `number`, `boolean`, `color`, `timestamp`, `month`, `year`, `month_year`, `month_day`, `json`.
- Note `visibility`: `friends`, `trusted`, `public`, and null.
- Asset `kind`: `image`, `audio`, `video`, `thumbnail`, `unknown`. An asset with `duration_ms` set. An asset that combines `uri` with inline bytes.
- Front `source_kind` `grouped`. Front role `influencing` and `unknown`.
- A FrontComment with both `front_period_id` and `front_event_id` null.
- Conversation `kind`: `forum`, `thread`, `proxy_log`, `unknown`.
- Chat message `kind`: `image`, `reaction`, `unknown`.
- Attachment `role`: `thumbnail`, `preview`, `inline`, and null.
- Board `audience` `private`.
- Warning `level` `info` and `error`.
- A ProxyTag with both `prefix` and `suffix` null.
- Per-record `warnings` arrays. The fragment is described; the field is not in the record tables.
- Registered producer `app_id`.
- Non-empty `extensions`, including `extensions.openplural.markdown_fields`.

Omission of a default is also not shown by deleting the key. The sample sets `archived`, `is_custom_front`, and `year_visible` explicitly. The stated defaults remain `false`, `false`, and `true`.

## Ambiguities

These are unresolved in the four source files. The sample’s choice is not claimed as the settled form.

1. Envelope requiredness. `spec.md`, “Top-level envelope”, is an example, not a required/optional table. The sample includes the keys that example uses, plus populated `boards` and `relationships`.
2. Null versus omission for unpopulated modules. The envelope example sets `chat` to null and omits `boards`, `relationships`, and the sketched modules. The sample omits unpopulated module keys instead of setting them to null. Populated `chat`, `boards`, and `relationships` are objects.
3. Identifier grammar. `spec.md` prefers UUIDv7 or ULID. The type legend also allows UUIDv4. Examples use prefixed ids such as `sys_01HV4Z...`. No pattern for ULID or for those prefixes is defined. The sample uses UUID version 4.
4. Null versus omitted optional fields. Tables say optional fields are not required. They do not say JSON null and a missing key mean the same thing. The sample uses both: explicit null for nullable fields, and omission of `uuid` on one SourceRef.
5. Per-record warnings. `spec.md`, “Shared record fragments”, and `spec-records.md`, “Envelope helpers”, say warnings can appear on individual records. No record table lists `warnings`. The sample uses only `$.warnings`.
6. `extensions.openplural.markdown_fields`. Named in the Member description notes. No shape is defined.
7. Asset inline versus uri. The Asset prose says either inline `data_base64` / `data_uri` or external `uri`. The callout says at least one of the three must be populated. It does not say whether both inline fields may be set together, or whether `uri` may accompany inline bytes. The avatar sets both inline fields to the same bytes and leaves `uri` null.
8. Warning `record_type`. The notes say “record type or path”. The sample uses `Asset` and `MemberRelationship`. The ImportResult example uses `chat.messages`. Both readings fit the notes.
9. Custom field values. `value` for `select` and `date` has no separate schema. `date_range` names `start` and `end` without types. The object form of `options` is allowed verbatim; `allow_partial` on “Noted on” is fictional content of that open object, not a specified options key.
10. Group emoji. “Single emoji” has no matching rule.
11. Cross-system edge. Blair’s `system_id` is Harbor. Eden’s `system_id` is Side Loft. The edge `system_id` is Harbor. MemberRelationship requires `system_id`, `from_member_id`, and `to_member_id`, and those member ids resolve. It does not say the two members must belong to `system_id`. The sample does not treat that silence as permission or as a prohibition.
12. Privacy `source` keys. The type is an open object. `source_label` is not a specified field.
13. System `settings` keys. The type is an open object and the notes say app-specific settings belong in `extensions`. No app-agnostic keys are listed. The sample uses `{}`.

## ImportResult

ImportResult is the importer’s report after a run. Source: `spec-modules.md`, “ImportResult”. It is not an export record. It does not appear in `pluralport-comprehensive-example.json`.

The field table describes the result object. The specification example wraps that object in a key named `import_result`. That wrapper is not a row in the field table, and it is not an envelope key. The example below is the specification’s example, copied here so the result shape is documented beside the export records. Its counts are the specification’s example counts. They are not a report from importing this sample.

```json
{
  "import_result": {
    "started_at": "2026-04-29T18:05:00Z",
    "finished_at": "2026-04-29T18:05:14Z",
    "source": {
      "openplural_version": "0.1",
      "producer_app": "Sheaf",
      "producer_app_version": "1.4.2"
    },
    "counts": {
      "imported": 284,
      "skipped": 3,
      "degraded": 12,
      "preserved_only": 158,
      "failed": 0
    },
    "per_module": {
      "members": { "imported": 24, "skipped": 0, "degraded": 0, "preserved_only": 0, "failed": 0 },
      "chat": { "imported": 0, "skipped": 0, "degraded": 0, "preserved_only": 158, "failed": 0 }
    },
    "warnings": [
      {
        "level": "warning",
        "code": "module_archived_only",
        "record_type": "chat.messages",
        "message": "Target app does not display chat. Messages retained as archive data.",
        "count": 158
      }
    ]
  }
}
```

| Field | JSON type | Required | Meaning | References / constraints |
| --- | --- | --- | --- | --- |
| `started_at` | string | yes | Run start. | UTC timestamp. |
| `finished_at` | string | yes | Run finish. | UTC timestamp. |
| `source` | object | yes | Echo of the imported envelope. | Keys: `openplural_version` string, `producer_app` string, `producer_app_version` string or null. |
| `counts` | object | yes | Totals across modules. | Keys: `imported`, `skipped`, `degraded`, `preserved_only`, `failed`, each a number. |
| `per_module` | object | no | Same count object per module name. | The table calls this value shape ModuleCounts. There is no separate export record by that name. |
| `warnings` | array | no | Warning records. | Same Warning table as the export. |
| `extensions` | object | no | Namespaced extra result data. | Omitted in the specification example. |

No other result-only record is defined in the four files. `module_archived_only` and `front_comments_archived` are importer warning codes in the module and fronting notes. They are not export warnings in this sample, because this file is the export, not an importer that archived a module.

## Local checks

The ZIP contains no JSON Schema, and the validator described in `spec-modules.md` is a plan, not a tool in this repository. Nothing here is an official schema validation.

A local Python check parsed the sample, checked UUID version-4 form, UTC timestamps, closed enumerations used by the sample, required keys, reference targets, module names against populated collections, absence of the six sketched modules, absence of ImportResult, and the two inline assets.

Asset results from that check:

| Asset | Bytes | `size_bytes` | SHA-256 |
| --- | --- | --- | --- |
| Avatar PNG | 69 | 69 | `83803707a337c9ced1fcd0cfd609f8d9f363f7e207f73d434117402fd6e19e3b` |
| Text file | 14 (`fictional-note`) | 14 | `4df3e61e92527cfd936c19fe79c62df73040386dcd27bcdc216da9b453e038f7` |

The avatar `data_uri` uses `data:image/png;base64,` plus the same base64 as `data_base64`. The PNG signature is present and the IHDR width and height are 1. The banner has no inline bytes, matching `asset_uri_only`. The relationship warning’s `record_id` is the edge whose `note` contains the opaque sentence.
