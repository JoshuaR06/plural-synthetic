# plural-synthetic

A small generator that makes a **completely fictional** plural-system export, in the formats
that plural apps actually exchange, so importers can be built and tested without anyone's real
data.

One made-up system ("Aurora") is defined once in `generate.py` and written out as:

- a **Simply Plural** official single-file export
- a **PluralBridge** per-collection export (folder and zip)
- an **avatars** zip
- a set of **edge cases**: shapes real exports can contain that tend to break importers

No real people, members, notes, fronting history, avatars, tokens or database files were used.
Every id starts with `synthetic-` so fixture data can never be mistaken for real data.

## Quick start

You need Python 3.8 or newer. Nothing else: it only uses the standard library.

```sh
git clone https://github.com/JoshuaR06/plural-synthetic.git
cd plural-synthetic
python3 generate.py            # writes everything to ./out
python3 generate.py --out DIR  # or somewhere else
```

Don't want to run anything? The same files are already in [`sample-output/`](sample-output/).

The output is **byte-identical every run** (fixed dates, sorted keys, fixed zip timestamps), so
you can commit it as test fixtures and diff it in review.

## What you get

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

## The fictional system

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

## How to use it

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

**4. Use it in automated tests.** Because the output never changes, you can check the files
into your test folder and assert exact counts and names. A minimal Python example:

```python
import json
export = json.load(open("sample-output/simplyplural-official.json"))
assert len(export["members"]) == 5
open_fronts = [e for e in export["frontHistory"] if "endTime" not in e]
assert len(open_fronts) == 2
```

**5. Make it your own.** Everything is defined in plain Python lists near the top of
`generate.py` (`MEMBERS`, `GROUPS`, `EDGE_GROUPS`, `FRONT_HISTORY` and so on). Add a member or
an edge case there, run it again, and every output format updates together. Keep new ids
starting with `synthetic-`; the built-in check refuses to write output otherwise.

## Notes on the formats

These shapes are based on the official Simply Plural export and PluralBridge's per-collection
export as seen in practice, not on a formal spec. If you know a format does something
differently, an issue or pull request is very welcome.

## License

MIT. See [LICENSE](LICENSE). Use it, copy it, or bring it into your own project.

Made by Joshua Reid, the developer of [Lighthouse - DID Hub](https://lighthousedid.com), while
building its Simply Plural and PluralBridge import.
