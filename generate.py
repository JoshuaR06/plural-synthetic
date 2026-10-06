#!/usr/bin/env python3
"""Deterministic synthetic plural-system export generator.

One fictional System ("Aurora") is defined once below and emitted in every shape an
importer needs to be tested against:

  out/pluralbridge/               PluralBridge per-collection folder ({exists,id,content} wrapped)
  out/pluralbridge-export.zip     the same folder, zipped
  out/simplyplural-official.json  the official Simply Plural single-file export (unwrapped, _id)
  out/avatars.zip                 tiny solid-colour PNGs named <memberId>.png
  out/edge/                       deliberately off-spec variants (see EDGE CASES)

Everything is fictional, every id is `synthetic-*`, and output is byte-identical run to run
(fixed timestamps, sorted keys, fixed zip dates), so fixtures can be committed and diffed.

Standard library only. Usage:  python3 generate.py [--out DIR]
"""
import argparse, json, os, shutil, struct, zipfile, zlib
from datetime import datetime, timezone

BASE_EPOCH = 1756000000  # fixed, so output never depends on the clock
MS = lambda day, hour=12: int((BASE_EPOCH + day * 86400 + hour * 3600) * 1000)
ZIP_DATE = (2026, 1, 1, 0, 0, 0)

SYSTEM_ID = "synthetic-system-0001"

# ---------------------------------------------------------------- the one System definition

ME = {"username": "Aurora (synthetic test system)", "uid": SYSTEM_ID, "color": "#7C5CBF",
      "desc": "Fictional system used for public tests. Not a real person."}

MEMBERS = [
    ("synthetic-member-0001", {"name": "Nova", "pronouns": "she/her", "color": "#7C5CBF",
        "desc": "Fictional member. Host role.", "avatarUuid": "synthetic-avatar-0001",
        "info": {"synthetic-field-0001": "Rainy days", "synthetic-field-0002": "Host"},
        "buckets": ["synthetic-bucket-0001"]}),
    ("synthetic-member-0002", {"name": "Ember", "pronouns": "they/them", "color": "#D9482B",
        "desc": "Fictional member. Protector role.", "avatarUuid": "synthetic-avatar-0002",
        "info": {"synthetic-field-0002": "Protector"}, "buckets": ["synthetic-bucket-0001"]}),
    ("synthetic-member-0003", {"name": "Wren", "pronouns": "he/him", "color": "#2B8C6B",
        "desc": "Fictional member with no custom field values.", "info": {}}),
    ("synthetic-member-0004", {"name": "Halcyon", "pronouns": "they/them", "color": "#8A8F98",
        "desc": "Fictional archived member.", "archived": True,
        "archivedReason": "Dormant (synthetic)", "info": {}, "buckets": ["synthetic-bucket-0002"]}),
    ("synthetic-member-0005", {"name": "Juniper", "pronouns": "she/they", "color": "#E8A13C",
        "desc": "Fictional member in a subsystem, and in two groups at once.", "info": {}}),
]
for _, m in MEMBERS:
    m.setdefault("uid", SYSTEM_ID)

# SP groups: top-level groups have parent "root"; nested groups point at their parent's id.
GROUPS = [
    ("synthetic-group-0001", {"name": "Daily front", "parent": "root", "emoji": "\U0001F31E",
        "color": "#7C5CBF", "desc": "Fictional group.",
        "members": ["synthetic-member-0001", "synthetic-member-0002", "synthetic-member-0005"]}),
    ("synthetic-group-0002", {"name": "Resting", "parent": "root", "emoji": "\U0001F319",
        "color": "#8A8F98", "desc": "Fictional group.", "members": ["synthetic-member-0004"]}),
    ("synthetic-group-0003", {"name": "Sidesystem", "parent": "root", "emoji": "\U0001F33F",
        "color": "#2B8C6B", "desc": "Fictional top-level group that only holds a subgroup.",
        "members": []}),
    ("synthetic-group-0004", {"name": "Subsystem", "parent": "synthetic-group-0003",
        "emoji": "\U0001F331", "color": "#5B7345", "desc": "Fictional nested group.",
        "members": ["synthetic-member-0005"]}),
    # A realistic two-level nest. Ember is also in "Daily front", so a consumer that files each
    # member in one place has to pick (and should say what it did with the other membership).
    ("synthetic-group-0005", {"name": "Littles", "parent": "root", "emoji": "\U0001F9F8",
        "color": "#E89AC7", "desc": "Fictional group with a nested group inside it.",
        "members": ["synthetic-member-0003"]}),
    ("synthetic-group-0006", {"name": "Bedtime", "parent": "synthetic-group-0005",
        "emoji": "\U0001F6CF", "color": "#6C7BD9", "desc": "Fictional group nested in Littles.",
        "members": ["synthetic-member-0002"]}),
]

# Structural EDGE cases for groups: shapes a hand-edited, damaged or very old export can hold.
# Kept out of the main fixture (see edge_variants): a robust importer must not loop, crash, or
# invent members on any of these.
EDGE_GROUPS = [
    # Five levels deep (a consumer with a depth limit has to shorten or flatten somehow).
    ("synthetic-group-0101", {"name": "Level 1", "parent": "root", "members": []}),
    ("synthetic-group-0102", {"name": "Level 2", "parent": "synthetic-group-0101", "members": []}),
    ("synthetic-group-0103", {"name": "Level 3", "parent": "synthetic-group-0102", "members": []}),
    ("synthetic-group-0104", {"name": "Level 4", "parent": "synthetic-group-0103", "members": []}),
    ("synthetic-group-0105", {"name": "Level 5", "parent": "synthetic-group-0104",
        "members": ["synthetic-member-0001"]}),
    # Parent id that matches no group.
    ("synthetic-group-0106", {"name": "Orphaned link", "parent": "synthetic-group-9999",
        "members": ["synthetic-member-0003"]}),
    # Two groups that are each other's parent (a cycle).
    ("synthetic-group-0107", {"name": "Loop A", "parent": "synthetic-group-0108",
        "members": ["synthetic-member-0004"]}),
    ("synthetic-group-0108", {"name": "Loop B", "parent": "synthetic-group-0107",
        "members": ["synthetic-member-0005"]}),
    # No members at all, and only a member that no longer exists.
    ("synthetic-group-0109", {"name": "Empty group", "parent": "root", "members": []}),
    ("synthetic-group-0110", {"name": "Only deleted members", "parent": "root",
        "members": ["synthetic-member-deleted-0099"]}),
]
for _, g in EDGE_GROUPS:
    g.setdefault("uid", SYSTEM_ID); g.setdefault("desc", "Fictional structural edge case.")

CUSTOM_FIELDS = [
    ("synthetic-field-0001", {"name": "Likes", "order": 0, "type": 0, "private": False,
                              "preventTrusted": False}),
    ("synthetic-field-0002", {"name": "Role in system", "order": 1, "type": 0, "private": False,
                              "preventTrusted": False}),
]

CUSTOM_FRONTS = [
    ("synthetic-front-0001", {"name": "Blurry / unsure", "desc": "Fictional custom front.",
                              "color": "#999999"}),
]

PRIVACY_BUCKETS = [
    ("synthetic-bucket-0001", {"name": "Trusted friends", "desc": "Fictional privacy bucket.",
                               "icon": "\U0001F510"}),
    ("synthetic-bucket-0002", {"name": "Private", "desc": "Fictional privacy bucket.",
                               "icon": "\U0001F512"}),
]

# Front history. Per Simply Plural semantics (confirmed by PluralBridge, issue #38): an entry
# with a startTime and no endTime is a CURRENT front, and several may be open at once.
FRONT_HISTORY = [
    ("synthetic-fh-0001", {"member": "synthetic-member-0001", "startTime": MS(0, 9),
        "endTime": MS(0, 15), "live": False, "custom": False, "customStatus": "synthetic status"}),
    ("synthetic-fh-0002", {"member": "synthetic-member-0002", "startTime": MS(0, 15),
        "endTime": MS(0, 22), "live": False, "custom": False, "customStatus": ""}),
    ("synthetic-fh-0003", {"member": "synthetic-front-0001", "startTime": MS(1, 8),
        "endTime": MS(1, 10), "live": False, "custom": True, "customStatus": "custom front entry"}),
    # A member deleted before export: its id is in no members.json record.
    ("synthetic-fh-0004", {"member": "synthetic-member-deleted-0099", "startTime": MS(1, 12),
        "endTime": MS(1, 14), "live": False, "custom": False, "customStatus": ""}),
    # Two members fronting right now (co-front), started at different times.
    ("synthetic-fh-0005", {"member": "synthetic-member-0001", "startTime": MS(2, 9),
        "live": True, "custom": False, "customStatus": "still fronting"}),
    ("synthetic-fh-0006", {"member": "synthetic-member-0005", "startTime": MS(2, 11),
        "live": True, "custom": False, "customStatus": ""}),
]

NOTES = {
    "notes/1.json": [("synthetic-note-0001", {"title": "Synthetic note",
        "note": "Fictional note body for tests.", "member": "synthetic-member-0001",
        "date": MS(0, 20), "supportMarkdown": False})],
    "notes/2.json": [("synthetic-note-0002", {"title": "",
        "note": "Fictional note with an empty title.", "member": "synthetic-member-0002",
        "date": MS(1, 15), "supportMarkdown": False})],
}

AVATAR_COLOURS = {"synthetic-member-0001": (124, 92, 191), "synthetic-member-0002": (217, 72, 43),
                  "synthetic-member-0003": (43, 140, 107), "synthetic-member-0005": (232, 161, 60)}

# ---------------------------------------------------------------- shapes

def wrap(recs):
    """PluralBridge record wrapping."""
    return [{"exists": True, "id": rid, "content": c} for rid, c in recs]

def unwrap(recs):
    """Official Simply Plural export: plain records with an _id."""
    return [dict(c, _id=rid) for rid, c in recs]

def dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

def pluralbridge_files():
    files = {
        "me.json": {"exists": True, "id": SYSTEM_ID, "content": ME},
        "members.json": wrap(MEMBERS),
        "groups.json": wrap(GROUPS),
        "customfields.json": wrap(CUSTOM_FIELDS),
        "customfronts.json": wrap(CUSTOM_FRONTS),
        "privacybuckets.json": wrap(PRIVACY_BUCKETS),
        "fronthistory_starttime_and_endtime.json": wrap(FRONT_HISTORY),
        "avatar_manifest.json": {"generated": "synthetic",
            "note": "Manifest shape only. Image bytes ship separately in avatars.zip.",
            "avatars": [{"memberId": mid, "file": f"{mid}.png", "present": True}
                        for mid in sorted(AVATAR_COLOURS)]},
    }
    files.update({path: wrap(recs) for path, recs in NOTES.items()})
    return files

def simplyplural_official():
    return {
        "users": [dict(ME, _id=SYSTEM_ID)],
        "members": unwrap(MEMBERS),
        "groups": unwrap(GROUPS),
        "customFields": unwrap(CUSTOM_FIELDS),
        "frontStatuses": unwrap(CUSTOM_FRONTS),
        "privacyBuckets": unwrap(PRIVACY_BUCKETS),
        "frontHistory": unwrap(FRONT_HISTORY),
        "notes": [n for recs in NOTES.values() for n in unwrap(recs)],
    }

def iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# EDGE CASES: variants no real SP export is known to produce, but that a robust importer
# should survive. Kept out of the main fixture so the main one stays faithful to real output.
def edge_variants():
    iso_history = [(rid, dict(e, startTime=iso(e["startTime"]),
                              **({"endTime": iso(e["endTime"])} if "endTime" in e else {})))
                   for rid, e in FRONT_HISTORY]
    # An open entry with no endTime and NO live flag: still a current front by the SP rule.
    no_live_flag = [(rid, {k: v for k, v in e.items() if k != "live"}) for rid, e in FRONT_HISTORY]
    official_with_edge_groups = dict(simplyplural_official(), groups=unwrap(GROUPS + EDGE_GROUPS))
    return {
        "fronthistory-iso8601-timestamps.json": wrap(iso_history),
        "fronthistory-open-without-live-flag.json": wrap(no_live_flag),
        # Swap in for pluralbridge/groups.json: the main groups plus the structural edge cases.
        "groups-structural-edge-cases.json": wrap(GROUPS + EDGE_GROUPS),
        # The same, as a complete official single-file export, ready to import as-is.
        "simplyplural-official-with-edge-groups.json": official_with_edge_groups,
    }

# ---------------------------------------------------------------- output

def png(rgb, size=64):
    raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def write_zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, entries[name])

def check(out):
    """Every id synthetic, every file parses, every reference resolvable or deliberately not."""
    ids = set()
    for root, _, names in os.walk(out):
        for n in names:
            if n.endswith(".json"):
                json.load(open(os.path.join(root, n)))
    member_ids = {rid for rid, _ in MEMBERS} | {rid for rid, _ in CUSTOM_FRONTS}
    dangling = [e["member"] for _, e in FRONT_HISTORY if e["member"] not in member_ids]
    assert dangling == ["synthetic-member-deleted-0099"], dangling
    open_fronts = [rid for rid, e in FRONT_HISTORY if "endTime" not in e]
    assert len(open_fronts) >= 2
    for recs in (MEMBERS, GROUPS, EDGE_GROUPS, CUSTOM_FIELDS, CUSTOM_FRONTS, PRIVACY_BUCKETS, FRONT_HISTORY):
        ids |= {rid for rid, _ in recs}
    assert all(i.startswith("synthetic-") for i in ids), "non-synthetic id"

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    out = ap.parse_args().out
    shutil.rmtree(out, ignore_errors=True)
    pb = pluralbridge_files()
    for path, obj in pb.items():
        full = os.path.join(out, "pluralbridge", path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write(dump(obj))
    write_zip(os.path.join(out, "pluralbridge-export.zip"), {p: dump(o) for p, o in pb.items()})
    open(os.path.join(out, "simplyplural-official.json"), "w").write(dump(simplyplural_official()))
    write_zip(os.path.join(out, "avatars.zip"),
              {f"{mid}.png": png(rgb) for mid, rgb in AVATAR_COLOURS.items()})
    os.makedirs(os.path.join(out, "edge"))
    for name, obj in edge_variants().items():
        open(os.path.join(out, "edge", name), "w").write(dump(obj))
    check(out)
    print(f"wrote {out}: {len(MEMBERS)} members, {len(GROUPS)} groups (2 nested) + {len(EDGE_GROUPS)} edge groups, "
          f"{len(FRONT_HISTORY)} front entries (2 open, 1 deleted-member), "
          f"{sum(len(v) for v in NOTES.values())} notes, {len(AVATAR_COLOURS)} avatars, 4 edge variants")

if __name__ == "__main__":
    main()
