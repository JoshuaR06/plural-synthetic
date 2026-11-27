# Repository map

This is a map of the checkout. It does not move files. [`README.md`](README.md) is the introduction. The feed language is [`templates/model-feed-usage.md`](templates/model-feed-usage.md).

Four kinds of files show up below:

| Kind | Meaning |
| --- | --- |
| Source | Edit these. Python, feed templates, and the guides. |
| Reference | Format notes and hand-written samples. They are not the output of a template command. |
| Expected fixture | JSON the tests compare against. Change one only by the command named below, then review the diff. |
| Generated | `out/` is gitignored. Commands create it. Tests do not write it. |

## Tree

```text
plural-synthetic/
├─ generate.py                 source. Aurora, edge cases, and the twelve canonical models
├─ gen-import-engine.py        source. Feed parser, shared model, and target dispatch
├─ system_models.py            source. Twelve canonical topologies and their assembly
├─ gen-avatars.py              source. Deterministic PNG bytes for feed imports
├─ gen-pluralbridge.py         source. Canonical serialization and the PluralBridge feed adapter
├─ gen-simplyplural.py         source. Simply Plural feed adapter
├─ gen-pluralport.py           source. PluralPort feed adapter
├─ gen-pluralkit.py            source. PluralKit feed adapter
├─ test_system_models.py       source. Canonical models, plus focused feed failure tests
├─ test_model_feeds.py         source. Template regression tests
├─ refresh-feed-fixtures.py    source. Deliberate rewrite of fixtures/model-feeds
├─ README.md                   source. Workflows and commands
├─ LICENSE
├─ templates/
│  ├─ model-feed-usage.md      source. Shared feed syntax
│  ├─ model-feed-multiple.txt  source. PluralBridge multi-anchor specimen
│  ├─ model-feed-multiple.md   source. Guide for that specimen
│  ├─ model-feed-single.txt    source. Single-System specimen
│  ├─ model-feed-single.md     source. Guide comparing Simply Plural, PluralPort, and PluralKit
│  ├─ acceptance-two-systems.txt
│  └─ acceptance-two-systems.md
├─ docs/
│  ├─ visibility-permissions-roles.txt
│  ├─ pluralbridge/pluralbridge-json-format.md
│  ├─ simplyplural/            source analysis, a synthetic reference JSON, and an edge sample
│  ├─ pluralport/              record reference, comprehensive example, feed mapping
│  └─ pluralkit/               record reference, comprehensive example, feed mapping
├─ fixtures/
│  ├─ pluralbridge-system-models/   expected. Twelve canonical JSON files, the base spec, README
│  └─ model-feeds/                  expected. One JSON, stderr log, and PNG digest list per feed target
├─ sample-output/                   maintained copy of Aurora and the twelve models, plus example-shape.json
├─ .github/workflows/check.yml      CI
└─ out/                             generated, gitignored. Not listed file by file
```

`out/` from `generate.py` holds Aurora’s Simply Plural file, PluralBridge collection folder, zip files, `edge/`, and `pluralbridge-system-models/`. Feed commands add `out/imports/<target>/`. Avatar directories there can hold hundreds of PNGs. The acceptance feed writes 500 of them under `out/imports/pluralbridge/acceptance-two-systems-avatars/`. This map does not name those files.

`sample-output/pluralbridge-system-models/` has the twelve examples and `example-shape.json`. The shape file is an illustrative reference. It is not a thirteenth model and the sync command does not overwrite it.

## Where do I find...?

| Question | Where |
| --- | --- |
| Aurora export and the twelve canonical models | `generate.py` and `system_models.py`. Committed copies are in `sample-output/`. Expected canonical JSON is in `fixtures/pluralbridge-system-models/`. |
| The feed parser and shared model | `gen-import-engine.py` |
| Avatar bytes for a feed | `gen-avatars.py`. Aurora’s zip is built inside `generate.py`, not by this module. |
| A target’s mapping | `gen-pluralbridge.py`, `gen-simplyplural.py`, `gen-pluralport.py`, or `gen-pluralkit.py` |
| What a template contains | The `.txt` file and the `.md` guide beside it |
| Feed syntax that every template shares | `templates/model-feed-usage.md` |
| Canonical PluralBridge fields | `docs/pluralbridge/pluralbridge-json-format.md` and `fixtures/pluralbridge-system-models/Canonical Model Minimum Base.txt` |
| Simply Plural shape, including the feed proof of concept | `docs/simplyplural/simplyplural-source-analysis.md` |
| PluralPort records and the single-System mapping | `docs/pluralport/pluralport-record-reference.md` and `docs/pluralport/pluralport-feed-mapping.md` |
| PluralKit version-2 records and the single-System mapping | `docs/pluralkit/pluralkit-record-reference.md` and `docs/pluralkit/pluralkit-feed-mapping.md` |
| A hand-written sample that is not a template result | `docs/pluralport/pluralport-comprehensive-example.json`, `docs/pluralkit/pluralkit-comprehensive-example.json`, `docs/simplyplural/simplyplural-synthetic-reference.json`, and `sample-output/pluralbridge-system-models/example-shape.json` |
| Visibility, permission, and role words | `docs/visibility-permissions-roles.txt` |
| Expected feed JSON, notices, and PNG digests | `fixtures/model-feeds/<target>/` |
| JSON and PNGs just produced on this machine | `out/imports/<target>/`, relative to the working directory |
| Tests | `test_system_models.py` and `test_model_feeds.py` |
| CI | `.github/workflows/check.yml` |

## What updates a copy

| Command | What it writes | What it leaves alone |
| --- | --- | --- |
| `python3 generate.py` | Deletes and rewrites `out/` next to `generate.py`, including any `out/imports/` already there | `fixtures/`, `sample-output/`, and `example-shape.json` |
| `python3 generate.py --out DIR` | Deletes and rewrites `DIR` | The same, when `DIR` is not one of those trees |
| `python3 generate.py --out DIR --sync-system-model-sample-output` | Also refreshes the twelve JSON files in `sample-output/pluralbridge-system-models/` | `example-shape.json` and `fixtures/` |
| `python gen-import-engine.py --model <target> --scriptfspec <feed>` | That target’s JSON under `out/imports/<target>/`, and its PNG directory when the target uses sidecars | Other targets, `fixtures/`, and `sample-output/` |
| `python -m unittest discover -s . -p "test_*.py" -v` | Temporary directories only | `out/`, `fixtures/`, and `sample-output/` |
| `python refresh-feed-fixtures.py` | Replaces `fixtures/model-feeds/` from the current engine | Canonical fixtures and `sample-output/`. Review the diff before keeping it. The tests never run this script. |

CI checks out the repo, runs `generate.py` into a temporary directory, runs the same unittest discovery, generates a second time, and diffs the two temporary trees. A feed-template change that alters JSON, notices, or avatar bytes fails the tests until `refresh-feed-fixtures.py` has been run and the new fixtures have been reviewed.

Lighthouse as a feed target is not implemented. Joshua’s Lighthouse application is separate from that missing target.
