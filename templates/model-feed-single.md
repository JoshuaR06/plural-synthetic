# Single-System feed

[`model-feed-single.txt`](model-feed-single.txt) is the specimen for Simply Plural, PluralPort, and PluralKit. It is one System, The Harbor (`anchor1`), with nested Groups, notes, fields, a friend, a privacy bucket, and a custom front. Shared syntax is in [`model-feed-usage.md`](model-feed-usage.md).

## Contents

`Config` is 64 by 64, avatar `none`. Account `example-pb-model-single`, permission `read`, visibility `self`.

```text
System The Harbor (anchor1)
├─ Popeye, Gilligan, Penny
└─ Group Theatre (anchor2)
   ├─ members 1-50, then Gilligan
   └─ Group Backstage (anchor3)
      └─ Penny
```

Popeye: note `id1`, visibility `trusted friends`, bucket `bucket1`, field values `id1` `Sailor` and `id3` `Popeye`, `front: true`, solid avatar `#4A90E2`. Gilligan: note `id3`, archived with reason `Retained for historical testing`. Penny: note `id2`, `front: true`, crosshatch avatar `#FF8800`. The note bodies use curly apostrophes and are kept exactly.

Fields: `id1` title, `id3` author. Bucket Close Friends (`bucket1`). Friend Alex (`friend1`), trusted, in that bucket. Custom front Blurry (`customfront1`), description quoted in the template, `front: false`.

The range is 50 members, so ordinary members are Popeye, Gilligan, Penny, and those 50: 53. Blurry is not one of them.

## Commands and output

From the repository root:

```text
python gen-import-engine.py --model simplyplural --scriptfspec templates/model-feed-single.txt
python gen-import-engine.py --model pluralport --scriptfspec templates/model-feed-single.txt
python gen-import-engine.py --model pluralkit --scriptfspec templates/model-feed-single.txt
```

| Target | JSON | Avatars |
| --- | --- | --- |
| Simply Plural | `out/imports/simplyplural/model-feed-single.json` | `out/imports/simplyplural/model-feed-single-avatars/synthetic-member-0001.png` and `synthetic-member-0003.png` |
| PluralPort | `out/imports/pluralport/model-feed-single.json` | Two Asset records inside the JSON. No PNG directory. |
| PluralKit | `out/imports/pluralkit/model-feed-single.json` | `out/imports/pluralkit/model-feed-single-avatars/xfzjd.png` and `locum.png` |

Those PNG names are the member ids the adapters assign. Popeye is `synthetic-member-0001` and `xfzjd`. Penny is `synthetic-member-0003` and `locum`. Both images are 64 by 64. Popeye is solid `#4a90e2`. Penny is crosshatch `#ff8800`. Members whose resolved style is `none` have no file. PluralKit leaves `avatar_url` null. A local PNG is not a hosted URL.

The file also parses as PluralBridge. That target is not the regression fixture for this template. PluralBridge would keep the tree, including Backstage nested under Theatre, and print gaps for field values, archive state, buckets, friends, and the custom front. Use [`model-feed-multiple.md`](model-feed-multiple.md) and [`acceptance-two-systems.md`](acceptance-two-systems.md) for the PluralBridge counts the tests lock.

## How the three targets differ

| Feed fact | Simply Plural | PluralPort | PluralKit |
| --- | --- | --- | --- |
| Members | 53 ordinary members | 54 members, Blurry included with `is_custom_front` | 53 ordinary members |
| Groups | Theatre, 51 members, parent `root`. Backstage, Penny only, parent Theatre | 2 groups and 52 group memberships | 2 flat groups. Backstage’s parent is not written |
| Notes | 3 notes. `id1` Popeye, `id2` Penny, `id3` Gilligan | 3 notes, each `member_id` set | Not written. Notice lists `id1, id2, id3` |
| Field values | Popeye `info` `id1` Sailor, `id3` Popeye | 2 custom field values | Not written. A notice for each value |
| Fronting | 2 `frontHistory` rows, Popeye then Penny | 2 front periods, Popeye then Penny | 1 switch at `2026-01-01T00:00:00Z` containing both short ids |
| Blurry `front: false` | One custom-front record, no history row | A member and no front period | Not a member. Notice names `customfront1` |
| Account visibility `self` | `private` true, `preventTrusted` true. Notice | Privacy `private`. The token is kept in `privacy.source` | Every privacy key is `private`. Notice |
| Popeye `trusted friends` | `private` true, `preventTrusted` false, bucket kept. Notice that current friend listing still needs a shared bucket | Privacy `trusted` | Exported as `private`, which is narrower. Notice |
| Permission `read` | Notice. Not a field, role, or bucket | Warning. Kept in the account extension, not a role | Notice. Not privacy and not a role |
| Email and account name | Username is the account name. Email is omitted. System description is The Harbor | System name is The Harbor. Account name and email are in the extension. Warning | System name is The Harbor. Account name and email are notices |
| Gilligan archive | `archived` true and the reason | `archived` on the member. The reason is in an extension. Warning | Notice. Not written |
| Friend and bucket | Friend Alex and bucket Close Friends are written | Kept in `extensions.org.thepluralbridge`. Sharing is not a declared module. Warning | Notices. Not written |

Simply Plural prints six notices: the `self` token, permission, email, the privacy-flag explanation, and two lines about Alex. PluralPort prints the `self` notice and four warnings: archive reason, account, permission, and sharing. PluralKit prints the `self` notice plus a notice for each unsupported fact, including Backstage’s nesting and the null avatar URLs.

A generated file is a fixture. It is not evidence that an app accepts the import.

## Tests and fixtures

`test_model_feeds.py` reads this template in `test_simplyplural_single`, `test_pluralport_single`, and `test_pluralkit_single`. Expected files:

- `fixtures/model-feeds/simplyplural/model-feed-single.json`
- `fixtures/model-feeds/simplyplural/model-feed-single.stderr.txt`
- `fixtures/model-feeds/simplyplural/model-feed-single.avatars.sha256`
- `fixtures/model-feeds/pluralport/model-feed-single.json`
- `fixtures/model-feeds/pluralport/model-feed-single.stderr.txt`
- `fixtures/model-feeds/pluralport/model-feed-single.avatars.sha256` (empty, because assets are inside the JSON)
- `fixtures/model-feeds/pluralkit/model-feed-single.json`
- `fixtures/model-feeds/pluralkit/model-feed-single.stderr.txt`
- `fixtures/model-feeds/pluralkit/model-feed-single.avatars.sha256`

Longer mapping notes are in [`../docs/simplyplural/simplyplural-source-analysis.md`](../docs/simplyplural/simplyplural-source-analysis.md), [`../docs/pluralport/pluralport-feed-mapping.md`](../docs/pluralport/pluralport-feed-mapping.md), and [`../docs/pluralkit/pluralkit-feed-mapping.md`](../docs/pluralkit/pluralkit-feed-mapping.md).
