# Model feed usage (proof of concept)

This is the shared syntax accepted by `gen-import-engine.py`. Brackets establish scope. Indentation is ignored. There is no comment syntax.

The three checked-in templates, and what each one becomes, are in:

- [`model-feed-multiple.md`](model-feed-multiple.md) for [`model-feed-multiple.txt`](model-feed-multiple.txt)
- [`model-feed-single.md`](model-feed-single.md) for [`model-feed-single.txt`](model-feed-single.txt)
- [`acceptance-two-systems.md`](acceptance-two-systems.md) for [`acceptance-two-systems.txt`](acceptance-two-systems.txt)

```text
python gen-import-engine.py --model pluralbridge --scriptfspec <path>
```

PluralBridge JSON is `out/imports/pluralbridge/<feed-stem>.json`. Its PNGs are `out/imports/pluralbridge/<feed-stem>-avatars/<memberId>.png`. Simply Plural JSON is `out/imports/simplyplural/<feed-stem>.json`, with PNGs in `out/imports/simplyplural/<feed-stem>-avatars/<member _id>.png`. PluralPort JSON is `out/imports/pluralport/<feed-stem>.json`. Avatar bytes are inside that JSON. PluralKit JSON is `out/imports/pluralkit/<feed-stem>.json`, with PNGs in `out/imports/pluralkit/<feed-stem>-avatars/<member short id>.png`. Paths are relative to the working directory. A failed run replaces neither that target’s JSON nor that feed’s avatar directory. `lighthouse` is not implemented.

## Blocks

An optional `Config` block, then one `Account` block. `Config` holds the global avatar defaults. Inside `Account`:

- `name:` and `email:` at account scope. These become `account.displayName` and `account.email` in PluralBridge. Both are required. The importer does not invent a username.
- `Permission:` and `Visibility:` at account scope. A permission list is comma-separated (`read` or `read,write`). Each type stays a separate array entry. `all` is not expanded. The type `inherit` stays in the array and does not become `{"mode":"inherit"}`. Omitted account permission or visibility is `{"mode":"inherit"}` in PluralBridge.
- `Place:`, `System:`, and `Group:` create anchors. A following `[` … `]` block is that anchor’s body. Nesting is tree containment. An optional `:scriptId` on those anchors resolves forward references. Member lines do not take a script id in this cut.
- `Notes`, `CustomFields`, `PrivacyBuckets`, `Friends`, and `CustomFronts` are account-level definition blocks. Anchor names are unique. Anchor script ids are unique. Note, field, bucket, friend, and custom-front script ids are unique inside their own block.

```text
System: The Harbor:anchor1
[
  related->Main House:anchor2
  Member: Popeye
  [
    visibility: self
    field: id1
    front: true
  ]
  Member: 1-50
]
```

`Member: Name` is one shared member for the whole account. The same name later is another occurrence of that member, not a new member. `Member:1-250` and `Member: 1-250` expand to 250 distinct members in that declaration. A second range, including the same numbers under another anchor, is another 250 members. A range member’s PluralBridge id is `member-<anchorId>-L<line>-<n>` and its display name is `<anchorId>:L<line>:<n>`.

Inside a member block: `visibility:`, `permission:`, `field:`, `note:`, `front:true` or `front:false`, `archived:true` or `archived:false`, `archivedReason: 'text'`, `bucket: bucketId`, and `description: 'text'`. `field: id1` still refers to a definition. `field: id1 'Sailor'` also stores that member’s value. Omitted visibility and permission on an occurrence become `{"mode":"inherit"}` in PluralBridge. A supplied permission becomes `{"mode":"explicit","value":["read"]}` or a longer array. A supplied visibility becomes `{"mode":"explicit","value":"..."}`. Permission types are not mapped to roles.

```text
PrivacyBuckets
[
  Bucket: Close Friends:bucket1
]
Friends
[
  Friend: Alex:friend1
  [
    trusted: true
    bucket: bucket1
  ]
]
CustomFronts
[
  CustomFront: Blurry:customfront1
  [
    description: 'A synthetic custom front.'
    front: false
  ]
]
```

`archived` and `archivedReason` belong to the shared member. `bucket:` refers to a `PrivacyBuckets` script id. A custom front’s `front` is that front’s current state, not a member’s `front`. `front:false` does not create history. Quoted text is UTF-8; a curly apostrophe inside the quotes is part of the text.

Visibility values are `only you`, `trusted friends`, `all friends`, `selected people`, and `inherit`. The token `self` is kept as written. It is not the vocabulary’s `only you`, and the run prints a notice rather than renaming it. The vocabulary list is [`docs/visibility-permissions-roles.txt`](../docs/visibility-permissions-roles.txt).

`field:` and `note:` refer to account-level definitions. `field:` on an anchor, not inside a member, is that anchor’s `fieldIds`. `note:` on a Place, System, or Group is that anchor’s `noteIds`. `note:` inside a member block is that member’s `noteIds`. The two lists are separate. The same note may appear in both. A repeated script id on one anchor or member is stored once, in first-seen order. The Notes block may follow the anchor or member that cites it. An undefined note id is an error at the reference line. An anchor note is not copied onto the members placed inside that anchor.

```text
Notes
[
  Note:id1 'this is note one'
]
CustomFields
[
  Field:id1 'title'
]
```

Quoted note text is the body. Quoted field text is the label (`fieldName`), not a value stored on a member.

`front` belongs to the shared member. `front:false` does not create front history. This cut does not accept a front-history syntax. Two placements of the same member that set different `front` values are an error. The same rule applies to `archived`, `archivedReason`, and `description`. Visibility and permission are placement-specific.

## Avatars

Avatar attributes are `avatar-width`, `avatar-height`, `avatar` (`none`, `solid`, or `crosshatch`), and `color` (`#RRGGBB`). Each attribute resolves independently:

1. Built-in default when `Config` is absent or omits it: width `64`, height `64`, avatar `none`. There is no default color.
2. `Config`, the global scope.
3. Enclosing anchor scopes, outer anchor then inner anchor. Brackets define the scope. A setting applies to every member in that block, including a member or range declared earlier in the same brackets.
4. A `Member` or member-range block. Those values override the enclosing scope for every member created by that declaration.

`color` is an avatar-color override. Without it, the image color is derived from the member id. Explicit `avatar:none` writes no PNG for that member.

The same named member placed under more than one anchor has one avatar. An attribute written in a member block applies to every placement of that member. A later placement that omits it does not reset it. The run stops if two member blocks set different values, or if the member never sets an attribute and the enclosing scopes disagree. The message names the disagreeing lines. It does not keep the later placement.

JSON records the explicit layer, not a copy of the inherited request:

- `account.config` is the resolved global default. It always has `avatar-width`, `avatar-height`, and `avatar`, and `color` only when `Config` sets it.
- An anchor’s `config` contains only attributes written in that anchor’s brackets.
- A shared member’s `config` contains only attributes written in that member’s block, including `color` when the member sets it.
- Tree member occurrences do not carry `config` or image bytes.

## Relationships

Inside an anchor body:

```text
related->Main House:anchor2
related->
```

The word before `->` is a label. PluralBridge stores it as an account custom field and points the relationship row at that field. It is not added to the source anchor’s `fieldIds`. The source is the enclosing anchor. The target is the named anchor. An empty target is JSON `null`, and each such declaration stays its own row. A label that matches an existing field’s `fieldName` reuses that field. Relationships do not move anchors in the tree.

The empty-target form is accepted. It is the `label->target` form with the target omitted. The current templates use targets.

## PluralBridge defaults

The feed supplies account name and email. It does not supply a username or a clock. These PluralBridge values are fixed for every feed:

| Output | Value |
| --- | --- |
| `accountId` | `account-001` |
| `displayName` | Account `name:` |
| `email` | Account `email:` |
| `username` | Omitted. It is not derived from the display name. |
| `status` | `Active` (not an authorization claim) |
| `audit.createdAt` and `updatedAt` | `2026-01-01T00:00:00Z` |
| Declared anchor, note, and field script ids | Copied into JSON ids |
| Anchor with no script id | `system-001`, `group-001`, or `place-001`, counted per type |
| Named member id | `member-001` in first-seen order |
| Range member id and display name | `member-<anchorId>-L<line>-<n>` and `<anchorId>:L<line>:<n>` |
| Omitted `front` | `false`, with no `frontHistory` |
| Omitted avatar `Config` | `account.config` is width `64`, height `64`, avatar `none` |
| Avatar PNG | `<feed-stem>-avatars/<memberId>.png` beside the JSON, one file per shared member whose resolved avatar is not `none` |
| `isArchived` | `false` |
| Note title, `supportsMarkdown`, and custom-field `fieldType` | Omitted. The feed does not supply them. |

Range names include the anchor id and the declaration line so two `Member:1-250` blocks cannot become the same members. A generated name or id that collides with another record is an error.

## Notices and gaps

Visibility `self` is kept and printed as a notice. [`docs/visibility-permissions-roles.txt`](../docs/visibility-permissions-roles.txt) calls the same idea `only you`.

Account name, email, permission, and visibility are serialized in PluralBridge. They are not reported as omitted gaps.

Anchor-level permission and visibility still have no JSON field. A feed that sets them is reported as a gap and those values are not serialized. The templates in this directory do not set them.

PluralBridge reports buckets, friends, custom fronts, archive state, member descriptions, and field values as gaps instead of inventing JSON for them. Simply Plural, PluralPort, and PluralKit each apply their own mapping. Those results are in the template guides and in:

- [`docs/simplyplural/simplyplural-source-analysis.md`](../docs/simplyplural/simplyplural-source-analysis.md), section 11
- [`docs/pluralport/pluralport-feed-mapping.md`](../docs/pluralport/pluralport-feed-mapping.md)
- [`docs/pluralkit/pluralkit-feed-mapping.md`](../docs/pluralkit/pluralkit-feed-mapping.md)
