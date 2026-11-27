# Two-System acceptance feed

[`acceptance-two-systems.txt`](acceptance-two-systems.txt) is the PluralBridge specimen for two Systems and 500 generated members, with one avatar style on each System. Shared syntax is in [`model-feed-usage.md`](model-feed-usage.md).

## Contents

`Config` sets width 64, height 64, and avatar `solid`. Account `example-two-system-model`, permission `read,write`, visibility `trusted friends`.

```text
System North
└─ Member:1-250
   avatar: crosshatch
System South
└─ Member:1-250
```

Each `Member:1-250` is its own set of people. North’s declaration is line 16, so those members are `system-001:L16:1` through `system-001:L16:250`, with ids `member-system-001-L16-1` through `member-system-001-L16-250`. South’s declaration is line 22, so those members are `system-002:L22:1` through `system-002:L22:250`. The same numbers are not the same members. The account has 500 shared members and 2 anchors. There are no notes, fields, groups, or relationships.

`avatar:crosshatch` is written on North’s System, after the range, so it applies to all 250 North members. South has no avatar line, so its 250 members keep the Config style `solid`. Neither System sets a color, so each PNG color is derived from that member’s id. North’s anchor `config` contains only `avatar: crosshatch`. South’s anchor has no `config`. `account.config` remains 64 by 64 `solid`.

## Command and output

From the repository root:

```text
python gen-import-engine.py --model pluralbridge --scriptfspec templates/acceptance-two-systems.txt
```

| Output | What this run writes |
| --- | --- |
| `out/imports/pluralbridge/acceptance-two-systems.json` | One account, two Systems, 500 members. |
| `out/imports/pluralbridge/acceptance-two-systems-avatars/` | 500 PNGs, one per member id. North’s files are crosshatch. South’s files are solid. |

The run prints no notices and no gaps. Account permission and visibility are the explicit values from the feed.

Simply Plural, PluralPort, and PluralKit require one System. This file has two, so those commands return an error and do not replace an existing output for this stem.

## Tests and fixtures

`test_model_feeds.py` method `test_pluralbridge_acceptance` reads the template, checks 250 members on each System, and compares every PNG with `gen-avatars.py`. Expected files:

- `fixtures/model-feeds/pluralbridge/acceptance-two-systems.json`
- `fixtures/model-feeds/pluralbridge/acceptance-two-systems.stderr.txt` (empty)
- `fixtures/model-feeds/pluralbridge/acceptance-two-systems.avatars.sha256` (500 digests, not the PNG bytes)

Refreshing those fixtures is described in [`../README.md`](../README.md).
