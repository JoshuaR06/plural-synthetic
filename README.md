# plural-synthetic

A small generator that makes **completely fictional** plural-system exports, so importers can be
built and tested without anyone's real data.

Two workflows are available.

**`generate.py`** is Joshua's original generator. It writes the Aurora exports (Simply Plural,
PluralBridge collection folder and zip, and an avatar zip), the edge-case files, and the twelve
canonical PluralBridge models. Those twelve models come from `system_models.py`. They are a
separate product from Aurora.

**`gen-import-engine.py`** is a proof of concept. It reads a user-authored model-feed file and
writes a target-specific test import. A file produced this way is a fixture. It is not evidence
that a particular app accepts the import.

The directory map is [`repo-map.md`](repo-map.md).

No real people, members, notes, fronting history, avatars, tokens, or database files were used.
Identifiers are fictional and chosen so a run does not depend on the clock. Aurora and the edge
files use the `synthetic-` prefix. The other workflows use their own identifier styles, described
below.

## Quick start

You need Python 3.8 or newer. Nothing else: it only uses the standard library.

```sh
git clone https://github.com/JoshuaR06/plural-synthetic.git
cd plural-synthetic
python3 generate.py            # writes everything to ./out
python3 generate.py --out DIR  # or somewhere else
python3 generate.py --out DIR --sync-system-model-sample-output  # refresh the twelve canonical JSON files
```

`--out` deletes the selected directory and writes it again. The default directory is `out` next
to `generate.py`. Feed files written from the repository root also live under that `out/`, so
the default `generate.py` command removes them. Use a separate `--out` directory when you want
to keep the feed files.

The same Aurora files and the twelve canonical models are already in
[`sample-output/`](sample-output/). Feed import files are written only when you run the engine.

`generate.py` is byte-identical every run: fixed dates, insertion-order canonical models,
sorted-key Aurora and edge JSON, and fixed zip timestamps. Feed runs also use fixed timestamps
and identifiers derived from the feed, so the same feed and target repeat. Each target has its
own identifier convention.

From the repository root, the feed commands are:

```sh
python gen-import-engine.py --model pluralbridge --scriptfspec templates/model-feed-multiple.txt
python gen-import-engine.py --model pluralbridge --scriptfspec templates/acceptance-two-systems.txt
python gen-import-engine.py --model simplyplural --scriptfspec templates/model-feed-single.txt
python gen-import-engine.py --model pluralport --scriptfspec templates/model-feed-single.txt
python gen-import-engine.py --model pluralkit --scriptfspec templates/model-feed-single.txt
```

Syntax and behavior are in
[`templates/model-feed-usage.md`](templates/model-feed-usage.md).
Each template has its own guide:

- [`templates/model-feed-multiple.md`](templates/model-feed-multiple.md)
- [`templates/model-feed-single.md`](templates/model-feed-single.md)
- [`templates/acceptance-two-systems.md`](templates/acceptance-two-systems.md)

`templates/model-feed-multiple.txt` includes `note: id2` on Group Theatre. That
note stays on the Group.

## Supported feed targets

This table is the proof-of-concept feed path. It does not mean every target can store every
feed feature.

| Target | What this cut writes | What it does not take as-is |
|---|---|---|
| PluralBridge | One hierarchical account. Place, System, and Group anchors, shared members, repeated placements, and relationships. | Anchor permission and visibility, field values, archive state, privacy buckets, friends, custom fronts, and member descriptions are printed as gaps and left out of the JSON. Visibility `self` is kept and printed as a notice. |
| Simply Plural | The observed direct-export shape: collection arrays and `_id` records. The supplied specimen is the single-System feed. | A Place, a second or nested System, an anchor relationship, or a Group custom-field association is an error. Account email and operation permissions are notices, not fields. Privacy is mapped to the observed `private` and `preventTrusted` flags. |
| PluralPort | One file using the captured specification, `openplural_version` `"0.1"`. The supplied specimen is the single-System feed. | A Place, a second or nested System, an anchor relationship, a Group custom-field association, or a note with no member is an error. Account identity, archive reasons, operation permissions, and friend or bucket data are preserved in an extension and reported as warnings. There is no official JSON Schema check. |
| PluralKit | One native version-2 owner export. The supplied specimen is the single-System feed. | A Place or a second or nested System is an error. Group nesting, notes, custom fields, friends, buckets, custom fronts, archive state, and relationships are notices. They are not extra JSON keys. Privacy is only `public` or `private`, so a narrower audience is reported. |
| Lighthouse | The feed target prints that it is not implemented and returns 2. | Joshua's Lighthouse application, and the Simply Plural and PluralBridge import work named at the bottom of this file, are separate from this feed target. |

## Templates and output locations

| Template | Role |
|---|---|
| [`templates/model-feed-multiple.txt`](templates/model-feed-multiple.txt) | PluralBridge specimen with a Place, two Systems, relationships, nested Groups, and a Group note. Guide: [`model-feed-multiple.md`](templates/model-feed-multiple.md). |
| [`templates/model-feed-single.txt`](templates/model-feed-single.txt) | One System, used for the Simply Plural, PluralPort, and PluralKit commands above. It also parses as PluralBridge. Guide: [`model-feed-single.md`](templates/model-feed-single.md). |
| [`templates/acceptance-two-systems.txt`](templates/acceptance-two-systems.txt) | Two Systems, `Member:1-250` in each, 250 members per System. Guide: [`acceptance-two-systems.md`](templates/acceptance-two-systems.md). |
| [`templates/model-feed-usage.md`](templates/model-feed-usage.md) | Shared feed syntax: brackets, identity, references, settings, relationships, and avatar resolution. |

Output paths are relative to the working directory. The file name uses the feed's filename
stem. `templates/model-feed-single.txt` therefore writes `model-feed-single.json`.

| Target | JSON |
|---|---|
| PluralBridge | `out/imports/pluralbridge/<feed-stem>.json` |
| Simply Plural | `out/imports/simplyplural/<feed-stem>.json` |
| PluralPort | `out/imports/pluralport/<feed-stem>.json` |
| PluralKit | `out/imports/pluralkit/<feed-stem>.json` |

PluralBridge, Simply Plural, and PluralKit also write feed-specific PNG sidecars:

- `out/imports/pluralbridge/<feed-stem>-avatars/<member id>.png`
- `out/imports/simplyplural/<feed-stem>-avatars/<member _id>.png`
- `out/imports/pluralkit/<feed-stem>-avatars/<member short id>.png`

PluralPort embeds the avatar bytes in Asset records and does not write a PNG directory. A local
PNG sidecar is not a hosted avatar URL. PluralKit leaves its native avatar URL fields null for
that reason.

## Architecture

| File | Responsibility |
|---|---|
| `generate.py` | Original generation entry point for Aurora, the edge cases, and the twelve canonical models. |
| `system_models.py` | Canonical PluralBridge model definitions and assembly. |
| `gen-import-engine.py` | Shared feed parsing, the intermediate model, and dispatch to a target. |
| `gen-avatars.py` | Shared deterministic PNG generation for feed imports. |
| `gen-pluralbridge.py` | Canonical serialization helpers, and the PluralBridge feed adapter. |
| `gen-simplyplural.py` | Simply Plural feed adapter. |
| `gen-pluralport.py` | PluralPort feed adapter. |
| `gen-pluralkit.py` | PluralKit feed adapter. |

Each feed adapter maps the shared model directly into its own format. It does not convert the
model through PluralBridge JSON. Aurora's avatar zip is built inside `generate.py`. Feed PNGs
come from `gen-avatars.py`.

## What `generate.py` writes

These paths are inside the directory selected by `--out`. The committed copies are under
[`sample-output/`](sample-output/).

| File | What it is |
|---|---|
| `simplyplural-official.json` | Simply Plural's official single-file export: plain records with `_id` |
| `pluralbridge/` | PluralBridge per-collection folder, each record wrapped as `{exists, id, content}` |
| `pluralbridge-export.zip` | the same folder, zipped |
| `avatars.zip` | small solid-colour PNGs named `<memberId>.png` |
| `edge/fronthistory-iso8601-timestamps.json` | front history with ISO 8601 strings instead of epoch milliseconds |
| `edge/fronthistory-open-without-live-flag.json` | open fronts with no `live` field at all |
| `edge/groups-structural-edge-cases.json` | the normal groups plus damaged or unusual group structures |
| `edge/simplyplural-official-with-edge-groups.json` | a complete Simply Plural export using those edge-case groups |
| `pluralbridge-system-models/*.json` | twelve generated PluralBridge canonical models (001-012) |

## PluralBridge canonical models

The repository includes twelve PluralBridge canonical models in
[`sample-output/pluralbridge-system-models/`](sample-output/pluralbridge-system-models).
The authoritative specification is
[`Canonical Model Minimum Base.txt`](fixtures/pluralbridge-system-models/Canonical%20Model%20Minimum%20Base.txt).
Each file is one `account` with shared peer collections and a hierarchical `tree`.
Empty optional collections are omitted.

They cover:

- simple single-system with nested groups
- multiple top-level roots
- parent/child
- sibling
- related (non-hierarchical; reciprocal records when both sides are labeled)
- a Place inside a System (Morgan's Room)
- evolving relationship
- archived system state
- non-tree graph relationships
- a top-level Group containing Systems
- a top-level Place containing Systems and a nested Place
- a root Place containing Groups and a nested Place, with zero Systems (Example 12)

`generate.py` builds these from Python topologies in `system_models.py` (entities,
graph relationships, and placements). It does not copy the JSON files. Canonical serialized
examples live in [`fixtures/pluralbridge-system-models/`](fixtures/pluralbridge-system-models).
`--sync-system-model-sample-output` refreshes the twelve canonical JSON files in the committed
sample-output mirror. It does not overwrite `example-shape.json`, which is an illustrative
reference and not a thirteenth canonical model.

Shared members and anchors live in account-level peer collections. Tree nodes reference anchors;
member occurrences reference shared members. Nesting is containment; array order is display
order. Notes belong to members through `noteIds`; fields are associated through `fieldIds`.
Directed structure uses `account.relationships` (`sourceAnchorId`, `fieldId`, `targetAnchorId`).
The label comes from the referenced custom field's `fieldName`. Reverse direction is a separate
row. A null target is literal JSON `null`. Display combines labels for the same source/target and
appends `->Target` only when a target exists. Root and child graph records are omitted.
The relationship JSON format, worked examples, and per-example results are in
[`fixtures/pluralbridge-system-models/README.md`](fixtures/pluralbridge-system-models/README.md#field-level-relationship-encoding).
`privacyBuckets`, `visibilityScopes`, and access memberships are omitted. Notes, custom fields,
and tree member occurrences carry visibility and permissions. Current fronting is a Boolean on
the shared member and applies across every occurrence, independently of focused anchor.

These examples keep PluralBridge's own id style. Aurora and the edge files use the `synthetic-`
prefix. The built-in check requires each canonical example to declare itself synthetic in its
header (`exportKind: self-contained-pluralbridge-example`, `modelingNote` starting with
"Synthetic"). It also fails on any example not listed in `SYSTEM_MODEL_FIXTURE_NAMES`, on a
complete mismatch with the canonical JSON, and on a stale sample-output mirror. CI
(`.github/workflows/check.yml`) runs `generate.py` and `python3 -m unittest` on every pull request.

Field definitions for the twelve models are in
[`docs/pluralbridge/pluralbridge-json-format.md`](docs/pluralbridge/pluralbridge-json-format.md).

## The fictional system

Aurora, defined in `generate.py`, is the system behind the Simply Plural file, the PluralBridge
collection folder, the avatar zip, and the edge files.

**Members**

| Name | Pronouns | Notes |
|---|---|---|
| Nova | she/her | has custom field values and an avatar |
| Ember | they/them | has one custom field value |
| Wren | he/him | empty `info` object (no custom field values) |
| Halcyon | they/them | archived, with an `archivedReason` |
| Juniper | she/they | in a nested group and in two groups at once |

Plus one **custom front**, "Blurry / unsure".

**Groups** (`parent` is `"root"` at the top level, or another group's id)

```
Daily front        Nova, Ember, Juniper
Resting            Halcyon
Sidesystem         (no members of its own)
└─ Subsystem       Juniper
Littles            Wren
└─ Bedtime         Ember
```

**Front history**: six entries, including a custom-front entry, an entry for a member who was
deleted before the export, and two members who are fronting right now (open entries with a
start time and no end time).

**Notes**: two notes, one with an empty title.

## Edge cases, and why each one is there

Each of these came from a real importer tripping on it, or from PluralBridge's guidance.

- **Front history for a deleted member.** The entry points at `synthetic-member-deleted-0099`,
  which is in no members list. An importer has to decide to skip it or keep it, on purpose.
- **Two open fronts at once.** In Simply Plural more than one member can front at the same
  time. Every entry with a `startTime` and no `endTime` is a current front, and all of them
  should be kept, not collapsed to one.
- **Open front with no `live` flag** (edge file). The rule is "no end time", not the flag.
- **ISO 8601 timestamps** (edge file). Real exports use epoch milliseconds; this catches code
  that assumes numbers.
- **Custom fields split across two places.** Definitions live in `customfields.json`, the values
  live in each member's `info`, keyed by field id. Reading only one side loses data quietly.
- **Empty `info` object, a note with an empty title, an archived member with `archivedReason`.**
- **Nested groups, a group that only holds a subgroup, and a member in two groups.**
- **A custom-front entry in front history** (`custom: true`, `member` is a custom front id).

Structural group cases (only in the `edge/` group files):

- a chain **five levels deep**
- a group whose **parent doesn't exist**
- **two groups that are each other's parent** (a loop)
- an **empty group**
- a group whose **only member was deleted**

A robust importer shouldn't loop, crash, or invent members on any of these.

## How to use the Aurora exports

**1. Point your importer at a format.** Use `simplyplural-official.json` to test a Simply
Plural import, or `pluralbridge/` (or the zip) to test a PluralBridge import. Both describe the
same system, so the results should match.

**2. Check the results against the tables above.** For example: five members plus one custom
front, the deleted member's front entry handled the way you decided, and both open fronts
still current after import.

**3. Try the edge cases.** Each edge file replaces one file from the main export:

- swap `pluralbridge/fronthistory_starttime_and_endtime.json` for one of the
  `edge/fronthistory-*.json` files
- swap `pluralbridge/groups.json` for `edge/groups-structural-edge-cases.json`
- or import `edge/simplyplural-official-with-edge-groups.json` as a complete export

**4. Use it in automated tests.** Because the Aurora output never changes, you can check the files
into your test folder and assert exact counts and names. A minimal Python example:

```python
import json
export = json.load(open("sample-output/simplyplural-official.json"))
assert len(export["members"]) == 5
open_fronts = [e for e in export["frontHistory"] if "endTime" not in e]
assert len(open_fronts) == 2
```

**5. Make the Aurora system your own.** Aurora and the Simply Plural / edge exports are defined
in plain Python lists near the top of `generate.py` (`MEMBERS`, `GROUPS`, `EDGE_GROUPS`,
`FRONT_HISTORY` and so on). Change those lists and run `generate.py` again to rewrite the Aurora
formats together. Keep new Aurora ids starting with `synthetic-`; the built-in check refuses to
write that export otherwise. The twelve canonical models are topologies in `system_models.py`.
Feed imports are the adapter files listed above. Editing `generate.py` does not update them.

## Format documentation

Aurora's Simply Plural file and PluralBridge collection folder follow those exports as seen in
practice, not a formal spec. The twelve canonical models follow the canonical base and the
PluralBridge format document. The feed targets follow the source named in each mapping
document. If you know a format does something differently, an issue or pull request is very
welcome.

| Document | What it describes |
|---|---|
| [`docs/pluralbridge/pluralbridge-json-format.md`](docs/pluralbridge/pluralbridge-json-format.md) | Fields in the twelve canonical PluralBridge models. |
| [`docs/simplyplural/simplyplural-source-analysis.md`](docs/simplyplural/simplyplural-source-analysis.md) | Observed Simply Plural export shape, including the feed-import proof of concept. |
| [`docs/pluralport/pluralport-record-reference.md`](docs/pluralport/pluralport-record-reference.md) | Captured PluralPort record reference. |
| [`docs/pluralport/pluralport-feed-mapping.md`](docs/pluralport/pluralport-feed-mapping.md) | How the single-System feed is mapped to PluralPort. |
| [`docs/pluralkit/pluralkit-record-reference.md`](docs/pluralkit/pluralkit-record-reference.md) | PluralKit version-2 owner-export records. |
| [`docs/pluralkit/pluralkit-feed-mapping.md`](docs/pluralkit/pluralkit-feed-mapping.md) | How the single-System feed is mapped to PluralKit. |
| [`docs/visibility-permissions-roles.txt`](docs/visibility-permissions-roles.txt) | Visibility, permission, and role vocabulary used when a mapping names those words. |

These are reference samples, written to show a format. They are not the files produced by the
template commands:

- [`fixtures/pluralbridge-system-models/`](fixtures/pluralbridge-system-models) and the matching files in [`sample-output/pluralbridge-system-models/`](sample-output/pluralbridge-system-models), including the illustrative [`example-shape.json`](sample-output/pluralbridge-system-models/example-shape.json)
- [`docs/simplyplural/simplyplural-synthetic-reference.json`](docs/simplyplural/simplyplural-synthetic-reference.json)
- [`docs/pluralport/pluralport-comprehensive-example.json`](docs/pluralport/pluralport-comprehensive-example.json)
- [`docs/pluralkit/pluralkit-comprehensive-example.json`](docs/pluralkit/pluralkit-comprehensive-example.json)

Feed command output is the `out/imports/` tree in the table above.

## Tests

The checked-in feed templates are compared with fixtures in
[`fixtures/model-feeds/`](fixtures/model-feeds). The tests read the templates,
run the importer into a temporary directory, and do not write `out/`.

```sh
python -m unittest discover -s . -p "test_*.py" -v
```

A template or mapping change that alters JSON, notices, or avatar bytes fails
until the expected fixtures are refreshed on purpose and the diff is reviewed:

```sh
python refresh-feed-fixtures.py
```

The test run does not refresh those fixtures.

## License

MIT. See [LICENSE](LICENSE). Use it, copy it, or bring it into your own project.

Made by Joshua Reid, the developer of [Lighthouse - DID Hub](https://lighthousedid.com), while
building its Simply Plural and PluralBridge import.
