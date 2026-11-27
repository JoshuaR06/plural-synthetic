# Multiple-anchor feed

[`model-feed-multiple.txt`](model-feed-multiple.txt) is the PluralBridge specimen for a Place, two Systems, a nested Group, relationships, and an anchor note. Syntax that is shared with the other templates is in [`model-feed-usage.md`](model-feed-usage.md).

## Contents

Account `example-pb-model-multiple`, permission `read`, visibility `self`. There is no `Config` block, so avatar resolution stays at the built-in default: 64 by 64, style `none`.

```text
Place Central Hub
├─ System The Harbor (anchor1)
│  ├─ Popeye, Gilligan
│  └─ Group Theatre (anchor4)
│     └─ members 1-50
└─ System Main House (anchor2)
   ├─ Henry
   └─ Place Waiting Room (anchor3)
      └─ Mickey, Minnie
```

Harbor `related->` Main House, and Main House `related->` Harbor. Those are two relationship rows. They do not move either System in the tree.

Named members, in first-seen order: Popeye, Gilligan, Henry, Mickey, Minnie. The range on line 28 adds 50 members that belong to Theatre. The account therefore has 55 shared members and 5 anchors.

Popeye is fronting and refers to fields `id1` and `id3` without quoted values. Mickey’s occurrence permission is `read,write`. Mickey’s note is `id3`. Minnie’s note is `id1`. Omitted `front` is false.

Notes, defined after the anchors that cite them:

| Script id | Body |
| --- | --- |
| `id1` | `this is note one` |
| `id2` | `this is note two` |
| `id3` | `this is note three` |

Fields: `id1` title, `id2` auditorium, `id3` author.

## Theatre’s note and Theatre’s field

`note: id2` inside Group Theatre is an anchor association. PluralBridge writes `noteIds: ["id2"]` on the Theatre anchor. The note record stays in `account.notes` with body `this is note two`. No member’s `noteIds` contains `id2`, including the 50 members declared inside Theatre.

`field: id2` on that same Group is a different association. It selects the custom field whose label is `auditorium` and is written as Theatre’s `fieldIds: ["id2"]`. It is not a note, and it does not store a field value.

Mickey keeps note `id3`. Minnie keeps note `id1`.

## Command and output

From the repository root:

```text
python gen-import-engine.py --model pluralbridge --scriptfspec templates/model-feed-multiple.txt
```

| Output | What this run writes |
| --- | --- |
| `out/imports/pluralbridge/model-feed-multiple.json` | One PluralBridge account. |
| Avatar directory | None. Every resolved style is `none`. |

Counts locked by the regression test: 55 members, 5 anchors, 2 relationships, 3 notes, and the three declared fields. The relationship label `related` is an additional custom field. Account visibility `self` is kept. The run prints two notices, one for the account and one for Popeye, and no `gap:` lines. This template does not set anchor permission, anchor visibility, archive state, buckets, friends, or custom fronts.

Simply Plural, PluralPort, and PluralKit do not accept this file. It has a Place, a second System, relationships, and a Group custom-field association. Those targets return an error and leave any previous output for that stem in place. Their supported specimen is [`model-feed-single.txt`](model-feed-single.txt).

## Tests and fixtures

`test_model_feeds.py` method `test_pluralbridge_multiple` reads the template and compares a temporary run with:

- `fixtures/model-feeds/pluralbridge/model-feed-multiple.json`
- `fixtures/model-feeds/pluralbridge/model-feed-multiple.stderr.txt`
- `fixtures/model-feeds/pluralbridge/model-feed-multiple.avatars.sha256` (empty, because there are no PNGs)

The test also checks Theatre’s `id2` note, Mickey’s `id3`, Minnie’s `id1`, and that no member acquires `id2`. Refreshing those fixtures is described in [`../README.md`](../README.md).
