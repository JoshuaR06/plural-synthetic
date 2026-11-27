"""Regression tests for the checked-in model-feed templates.

Each test reads a template, runs gen-import-engine.main into a temporary
directory, and compares that JSON, stderr, and PNG digests with
fixtures/model-feeds. The comparison keeps array order because it uses the
file bytes. Tests do not write fixtures and do not touch out/.

Refresh the fixtures only on purpose, after reviewing the diff:

    python refresh-feed-fixtures.py

A template or mapping change that alters output fails here until that command
is run and the new fixtures are reviewed.
"""
import base64
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
FIXTURES = ROOT / "fixtures" / "model-feeds"

CASES = (
    ("pluralbridge", "model-feed-multiple.txt"),
    ("pluralbridge", "acceptance-two-systems.txt"),
    ("simplyplural", "model-feed-single.txt"),
    ("pluralport", "model-feed-single.txt"),
    ("pluralkit", "model-feed-single.txt"),
)


def load_engine():
    spec = importlib.util.spec_from_file_location("gen_import_engine", ROOT / "gen-import-engine.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_avatars():
    spec = importlib.util.spec_from_file_location("gen_avatars", ROOT / "gen-avatars.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_log(text, feed_path):
    """Replace the feed path and backslashes so a log fixture is portable."""
    path = Path(feed_path)
    variants = {str(path), path.as_posix(), str(path.resolve()), path.resolve().as_posix()}
    for variant in sorted(variants, key=len, reverse=True):
        text = text.replace(variant, "{feed}")
    return text.replace("\\", "/")


def avatar_digest(png_dir):
    if not png_dir.is_dir():
        return ""
    lines = []
    for png in sorted(png_dir.glob("*.png")):
        lines.append(f"{png.name} {hashlib.sha256(png.read_bytes()).hexdigest()}")
    return ("\n".join(lines) + "\n") if lines else ""


def run_feed(engine, model, feed_path, imports_root):
    """The command-line orchestration, writing only under imports_root."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = engine.main(
            ["--model", model, "--scriptfspec", str(feed_path)],
            imports_root=imports_root,
        )
    stem = Path(feed_path).stem
    return {
        "code": code,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "json_path": Path(imports_root) / model / f"{stem}.json",
        "png_dir": Path(imports_root) / model / f"{stem}-avatars",
    }


def write_fixtures(engine, destination=FIXTURES):
    """Replace fixtures/model-feeds from the current engine. Tests never call this."""
    for model, filename in CASES:
        feed = TEMPLATES / filename
        with tempfile.TemporaryDirectory() as tmp:
            result = run_feed(engine, model, feed, Path(tmp))
            if result["code"] != 0:
                raise SystemExit(f"{model} {filename} returned {result['code']}\n{result['stderr']}")
            case_dir = destination / model
            case_dir.mkdir(parents=True, exist_ok=True)
            stem = feed.stem
            (case_dir / f"{stem}.json").write_bytes(result["json_path"].read_bytes())
            (case_dir / f"{stem}.stderr.txt").write_bytes(
                normalize_log(result["stderr"], feed).encode("utf-8")
            )
            (case_dir / f"{stem}.avatars.sha256").write_bytes(
                avatar_digest(result["png_dir"]).encode("utf-8")
            )


def _quoted_bodies(template_text, keyword):
    bodies = {}
    for line in template_text.splitlines():
        stripped = line.strip()
        prefix = f"{keyword}:"
        if not stripped.startswith(prefix):
            continue
        rest = stripped[len(prefix):].strip()
        if " '" not in rest:
            continue
        script_id, quoted = rest.split(" '", 1)
        script_id = script_id.split()[-1]
        bodies[script_id] = quoted[:-1]
    return bodies


def _walk(nodes):
    for node in nodes or []:
        yield node
        yield from _walk(node.get("children"))


class FeedTemplateRegressionTests(unittest.TestCase):
    """The five checked-in template and target pairs."""

    @classmethod
    def setUpClass(cls):
        cls.engine = load_engine()
        cls.avatars = load_avatars()

    def _generate(self, model, filename):
        feed = TEMPLATES / filename
        template = feed.read_text(encoding="utf-8")
        first_dir = tempfile.TemporaryDirectory()
        second_dir = tempfile.TemporaryDirectory()
        self.addCleanup(first_dir.cleanup)
        self.addCleanup(second_dir.cleanup)
        first = run_feed(self.engine, model, feed, Path(first_dir.name))
        second = run_feed(self.engine, model, feed, Path(second_dir.name))
        self.assertEqual(first["code"], 0, first["stderr"])
        self.assertEqual(second["code"], 0, second["stderr"])
        self.assertEqual(first["json_path"].read_bytes(), second["json_path"].read_bytes())
        self.assertEqual(avatar_digest(first["png_dir"]), avatar_digest(second["png_dir"]))
        fixture = FIXTURES / model
        stem = feed.stem
        self.assertEqual(first["json_path"].read_bytes(), (fixture / f"{stem}.json").read_bytes())
        self.assertEqual(
            normalize_log(first["stderr"], feed),
            (fixture / f"{stem}.stderr.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(avatar_digest(first["png_dir"]), (fixture / f"{stem}.avatars.sha256").read_text(encoding="utf-8"))
        export = json.loads(first["json_path"].read_text(encoding="utf-8"))
        return template, export, first

    def test_pluralbridge_multiple(self):
        template, export, result = self._generate("pluralbridge", "model-feed-multiple.txt")
        self.assertNotIn("out/", result["stdout"].replace("\\", "/"))
        account = export["account"]
        theatre = template.split("Group: Theatre:anchor4", 1)[1].split("System: Main House", 1)[0]
        self.assertIn("note: id2", theatre)
        self.assertIn("field: id2", theatre)
        mickey = template.split("Member: Mickey", 1)[1].split("Member: Minnie", 1)[0]
        minnie = template.split("Member: Minnie", 1)[1]
        self.assertIn("note: id3", mickey)
        self.assertIn("note: id1", minnie)
        self.assertNotIn("note: id2", mickey)
        self.assertNotIn("note: id2", minnie)

        anchors = {anchor["name"]: anchor for anchor in account["anchors"]}
        self.assertEqual(anchors["Theatre"]["noteIds"], ["id2"])
        self.assertEqual(anchors["Theatre"]["fieldIds"], ["id2"])
        self.assertEqual(anchors["Theatre"]["anchorId"], "anchor4")
        members = {member["displayName"]: member for member in account["members"]}
        self.assertEqual(len(account["members"]), 55)
        self.assertEqual(members["Mickey"]["noteIds"], ["id3"])
        self.assertEqual(members["Minnie"]["noteIds"], ["id1"])
        self.assertEqual(members["Popeye"]["fieldIds"], ["id1", "id3"])
        self.assertTrue(members["Popeye"]["fronting"])
        self.assertFalse(members["Gilligan"]["fronting"])
        for member in account["members"]:
            self.assertNotIn("id2", member["noteIds"])
        notes = {note["noteId"]: note["body"] for note in account["notes"]}
        self.assertEqual(notes, _quoted_bodies(template, "Note"))
        fields = {field["fieldId"]: field["fieldName"] for field in account["customFields"]}
        self.assertEqual(fields["id1"], "title")
        self.assertEqual(fields["id2"], "auditorium")
        self.assertEqual(fields["id3"], "author")
        pairs = {(row["sourceAnchorId"], row["targetAnchorId"]) for row in account["relationships"]}
        self.assertEqual(pairs, {("anchor1", "anchor2"), ("anchor2", "anchor1")})
        tree = {node["anchorId"]: node for node in _walk(account["tree"])}
        self.assertEqual([node["anchorId"] for node in account["tree"]], ["place-001"])
        self.assertEqual([child["anchorId"] for child in tree["place-001"]["children"]], ["anchor1", "anchor2"])
        self.assertEqual([child["anchorId"] for child in tree["anchor1"]["children"]], ["anchor4"])
        self.assertEqual([child["anchorId"] for child in tree["anchor2"]["children"]], ["anchor3"])
        self.assertEqual(
            [occ["memberId"] for occ in tree["anchor3"]["members"]],
            [members["Mickey"]["memberId"], members["Minnie"]["memberId"]],
        )
        mickey_occ = tree["anchor3"]["members"][0]
        self.assertEqual(mickey_occ["permissions"], {"mode": "explicit", "value": ["read", "write"]})
        note_ids = set(notes)
        field_ids = set(fields)
        anchor_ids = {anchor["anchorId"] for anchor in account["anchors"]}
        for anchor in account["anchors"]:
            for note_id in anchor.get("noteIds") or []:
                self.assertIn(note_id, note_ids)
            for field_id in anchor.get("fieldIds") or []:
                self.assertIn(field_id, field_ids)
        for row in account["relationships"]:
            self.assertIn(row["sourceAnchorId"], anchor_ids)
            self.assertIn(row["targetAnchorId"], anchor_ids)
        self.assertIn("visibility 'self' is kept as written", result["stderr"])
        self.assertNotIn("gap:", result["stderr"])
        self.assertFalse(result["png_dir"].exists())
        self.assertEqual(account["config"]["avatar"], "none")

    def test_pluralbridge_acceptance(self):
        template, export, result = self._generate("pluralbridge", "acceptance-two-systems.txt")
        north_text, south_text = template.split("System: South", 1)
        self.assertEqual(north_text.count("Member:1-250"), 1)
        self.assertEqual(south_text.count("Member:1-250"), 1)
        self.assertIn("avatar: solid", north_text)
        self.assertIn("avatar:crosshatch", north_text)
        self.assertNotIn("avatar:crosshatch", south_text)
        account = export["account"]
        self.assertEqual(len(account["members"]), 500)
        self.assertEqual(len({member["memberId"] for member in account["members"]}), 500)
        anchors = {anchor["name"]: anchor for anchor in account["anchors"]}
        self.assertEqual(set(anchors), {"North", "South"})
        self.assertEqual(anchors["North"]["config"], {"avatar": "crosshatch"})
        self.assertNotIn("config", anchors["South"])
        self.assertEqual(account["config"]["avatar"], "solid")
        tree = {node["anchorId"]: node for node in _walk(account["tree"])}
        self.assertEqual(len(tree[anchors["North"]["anchorId"]]["members"]), 250)
        self.assertEqual(len(tree[anchors["South"]["anchorId"]]["members"]), 250)
        by_id = {member["memberId"]: member for member in account["members"]}
        north_ids = [occ["memberId"] for occ in tree[anchors["North"]["anchorId"]]["members"]]
        south_ids = [occ["memberId"] for occ in tree[anchors["South"]["anchorId"]]["members"]]
        self.assertEqual(len(set(north_ids) & set(south_ids)), 0)
        pngs = {path.name: path.read_bytes() for path in result["png_dir"].glob("*.png")}
        self.assertEqual(set(pngs), {f"{member_id}.png" for member_id in by_id})
        for member_id in north_ids:
            image = self.avatars.generate_avatar("crosshatch", member_id, width=64, height=64)
            self.assertEqual(pngs[f"{member_id}.png"], image.png)
            self.assertTrue(by_id[member_id]["displayName"].startswith("system-001:L16:"))
        for member_id in south_ids:
            image = self.avatars.generate_avatar("solid", member_id, width=64, height=64)
            self.assertEqual(pngs[f"{member_id}.png"], image.png)
            self.assertTrue(by_id[member_id]["displayName"].startswith("system-002:L22:"))
        self.assertEqual(account["visibility"], {"mode": "explicit", "value": "trusted friends"})
        self.assertEqual(account["permissions"], {"mode": "explicit", "value": ["read", "write"]})
        self.assertEqual(result["stderr"], "")

    def test_simplyplural_single(self):
        template, export, result = self._generate("simplyplural", "model-feed-single.txt")
        self.assertEqual(len(export["members"]), 53)
        self.assertEqual(export["users"][0]["username"], "example-pb-model-single")
        self.assertEqual(export["users"][0]["desc"], "The Harbor")
        names = {member["name"]: member for member in export["members"]}
        self.assertNotIn("Blurry", names)
        self.assertEqual(names["Popeye"]["info"], {"id1": "Sailor", "id3": "Popeye"})
        self.assertEqual(names["Popeye"]["color"], "#4a90e2")
        self.assertEqual(names["Penny"]["color"], "#ff8800")
        self.assertTrue(names["Gilligan"]["archived"])
        self.assertEqual(names["Gilligan"]["archivedReason"], "Retained for historical testing")
        groups = {group["name"]: group for group in export["groups"]}
        self.assertEqual(groups["Theatre"]["parent"], "root")
        self.assertEqual(len(groups["Theatre"]["members"]), 51)
        self.assertIn(names["Gilligan"]["_id"], groups["Theatre"]["members"])
        self.assertEqual(groups["Backstage"]["parent"], groups["Theatre"]["_id"])
        self.assertEqual(groups["Backstage"]["members"], [names["Penny"]["_id"]])
        notes = {note["_id"]: note for note in export["notes"]}
        bodies = _quoted_bodies(template, "Note")
        self.assertEqual(notes["id1"]["note"], bodies["id1"])
        self.assertEqual(notes["id1"]["member"], names["Popeye"]["_id"])
        self.assertEqual(notes["id2"]["member"], names["Penny"]["_id"])
        self.assertEqual(notes["id3"]["member"], names["Gilligan"]["_id"])
        member_ids = {member["_id"] for member in export["members"]}
        for note in export["notes"]:
            self.assertIn(note["member"], member_ids)
        for group in export["groups"]:
            for member_id in group["members"]:
                self.assertIn(member_id, member_ids)
        fronts = [row["member"] for row in export["frontHistory"]]
        self.assertEqual(fronts, [names["Popeye"]["_id"], names["Penny"]["_id"]])
        self.assertEqual(export["frontStatuses"][0]["name"], "Blurry")
        self.assertEqual(export["friends"][0]["username"], "Alex")
        self.assertEqual(export["privacyBuckets"][0]["name"], "Close Friends")
        self.assertIn("account email has no users[] field", result["stderr"])
        self.assertIn("Permission read has no Simply Plural field", result["stderr"])
        pngs = {path.stem: path.read_bytes() for path in result["png_dir"].glob("*.png")}
        self.assertEqual(set(pngs), {names["Popeye"]["_id"], names["Penny"]["_id"]})
        popeye = self.avatars.generate_avatar("solid", names["Popeye"]["_id"], width=64, height=64, color="#4A90E2")
        penny = self.avatars.generate_avatar("crosshatch", names["Penny"]["_id"], width=64, height=64, color="#FF8800")
        self.assertEqual(pngs[names["Popeye"]["_id"]], popeye.png)
        self.assertEqual(pngs[names["Penny"]["_id"]], penny.png)

    def test_pluralport_single(self):
        template, export, result = self._generate("pluralport", "model-feed-single.txt")
        self.assertEqual(export["openplural_version"], "0.1")
        self.assertEqual(len(export["systems"]), 1)
        self.assertEqual(export["systems"][0]["name"], "The Harbor")
        self.assertEqual(len(export["members"]), 54)
        self.assertEqual(len(export["groups"]), 2)
        self.assertEqual(len(export["group_memberships"]), 52)
        self.assertEqual(len(export["notes"]), 3)
        self.assertEqual(len(export["front_periods"]), 2)
        self.assertEqual(len(export["assets"]), 2)
        members = {member["name"]: member for member in export["members"]}
        self.assertTrue(members["Blurry"]["is_custom_front"])
        bodies = _quoted_bodies(template, "Note")
        for note in export["notes"]:
            self.assertIn(note["body"], bodies.values())
            self.assertIn(note["member_id"], {member["id"] for member in export["members"]})
        period_ids = [period["assignments"][0]["member_id"] for period in export["front_periods"]]
        self.assertEqual(period_ids, [members["Popeye"]["id"], members["Penny"]["id"]])
        values = {row["value"] for row in export["custom_field_values"]}
        self.assertEqual(values, {"Sailor", "Popeye"})
        self.assertNotIn("sharing", export["capabilities"]["modules"])
        codes = [warning["code"] for warning in export["warnings"]]
        self.assertEqual(codes, [
            "archive_reason_preserved_in_extension",
            "account_preserved_in_extension",
            "permission_not_mapped",
            "sharing_preserved_in_extension",
        ])
        for warning in export["warnings"]:
            self.assertIn(warning["message"], result["stderr"])
        group_ids = {group["id"] for group in export["groups"]}
        member_ids = {member["id"] for member in export["members"]}
        for row in export["group_memberships"]:
            self.assertIn(row["group_id"], group_ids)
            self.assertIn(row["member_id"], member_ids)
        assets = {asset["id"]: asset for asset in export["assets"]}
        linked = {member["name"]: member["avatar_asset_id"] for member in export["members"] if member.get("avatar_asset_id")}
        self.assertEqual(set(linked), {"Popeye", "Penny"})
        for name, style, color in (("Popeye", "solid", "#4A90E2"), ("Penny", "crosshatch", "#FF8800")):
            raw = base64.b64decode(assets[linked[name]]["data_base64"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), assets[linked[name]]["sha256"])
            image = self.avatars.generate_avatar(style, members[name]["id"], width=64, height=64, color=color)
            self.assertEqual(raw, image.png)
        self.assertFalse(result["png_dir"].exists())
        self.assertIn("visibility 'self' is kept as written", result["stderr"])

    def test_pluralkit_single(self):
        template, export, result = self._generate("pluralkit", "model-feed-single.txt")
        self.assertEqual(export["version"], 2)
        self.assertEqual(export["name"], "The Harbor")
        self.assertEqual(len(export["members"]), 53)
        self.assertEqual(export["accounts"], [])
        names = {member["name"]: member for member in export["members"]}
        self.assertNotIn("Blurry", names)
        groups = {group["name"]: group for group in export["groups"]}
        self.assertEqual(len(groups["Theatre"]["members"]), 51)
        self.assertEqual(groups["Backstage"]["members"], [names["Penny"]["id"]])
        self.assertNotIn("parent", groups["Backstage"])
        self.assertEqual(len(export["switches"]), 1)
        self.assertEqual(export["switches"][0]["members"], [names["Popeye"]["id"], names["Penny"]["id"]])
        self.assertEqual(export["switches"][0]["timestamp"], "2026-01-01T00:00:00Z")
        member_ids = {member["id"] for member in export["members"]}
        for group in export["groups"]:
            for member_id in group["members"]:
                self.assertIn(member_id, member_ids)
        for member_id in export["switches"][0]["members"]:
            self.assertIn(member_id, member_ids)
        self.assertIsNone(names["Popeye"]["avatar_url"])
        self.assertIsNone(names["Penny"]["avatar_url"])
        self.assertEqual(names["Popeye"]["color"], "4a90e2")
        self.assertEqual(names["Penny"]["color"], "ff8800")
        self.assertIn("Backstage", result["stderr"])
        self.assertIn("notes have no PluralKit field: id1, id2, id3", result["stderr"])
        self.assertIn("custom front customfront1 'Blurry'", result["stderr"])
        self.assertIn("trusted friends", result["stderr"])
        pngs = {path.stem: path.read_bytes() for path in result["png_dir"].glob("*.png")}
        self.assertEqual(set(pngs), {names["Popeye"]["id"], names["Penny"]["id"]})
        popeye = self.avatars.generate_avatar("solid", names["Popeye"]["id"], width=64, height=64, color="#4A90E2")
        penny = self.avatars.generate_avatar("crosshatch", names["Penny"]["id"], width=64, height=64, color="#FF8800")
        self.assertEqual(pngs[names["Popeye"]["id"]], popeye.png)
        self.assertEqual(pngs[names["Penny"]["id"]], penny.png)
        self.assertIn("Note:id1", template)


class RejectedFeedPreservesOutputTests(unittest.TestCase):
    """Parse and render failures go through main and do not replace a previous file."""

    @classmethod
    def setUpClass(cls):
        cls.engine = load_engine()

    def _reject(self, model, feed_text, needle):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        feed = root / "probe.txt"
        feed.write_bytes(feed_text.encode("utf-8"))
        destination = root / "imports" / model / "probe.json"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"sentinel")
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            code = self.engine.main(
                ["--model", model, "--scriptfspec", str(feed)],
                imports_root=root / "imports",
            )
        self.assertEqual(code, 1)
        self.assertIn(needle, stderr.getvalue())
        self.assertEqual(destination.read_bytes(), b"sentinel")
        self.assertFalse((root / "imports" / model / "probe-avatars").exists())

    def test_undefined_field_reference(self):
        self._reject("pluralbridge", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Member: Ada
    [
      field: missing
    ]
  ]
]
""", "undefined field 'missing'")

    def test_undefined_relationship_target(self):
        self._reject("pluralbridge", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    related->Nowhere:missing
  ]
]
""", "undefined anchor script id 'missing'")

    def test_conflicting_front(self):
        self._reject("pluralbridge", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Member: Ada
    [
      front: true
    ]
  ]
  Group: Elsewhere
  [
    Member: Ada
    [
      front: false
    ]
  ]
]
""", "front:false conflicts with front:true")

    def test_conflicting_avatar_style(self):
        self._reject("pluralbridge", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Member: Ada
    [
      avatar: solid
    ]
  ]
  Group: Elsewhere
  [
    Member: Ada
    [
      avatar: crosshatch
    ]
  ]
]
""", "avatar conflicts with line")

    def test_pluralport_rejects_second_system(self):
        self._reject("pluralport", """
Account
[
  name: n
  email: n@example.org
  System: North
  [
    Member: Ada
  ]
  System: South
  [
    Member: Bea
  ]
]
""", "exactly one System")

    def test_pluralport_rejects_group_field(self):
        self._reject("pluralport", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Group: Theatre
    [
      field: id1
      Member: Ada
    ]
  ]
  CustomFields
  [
    Field:id1 'title'
  ]
]
""", "Group custom-field associations are not supported")

    def test_simplyplural_rejects_place(self):
        self._reject("simplyplural", """
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Place: Hub
    [
      Member: Ada
    ]
  ]
]
""", "Place anchors are not supported")

    def test_pluralkit_rejects_place(self):
        self._reject("pluralkit", """
Account
[
  name: n
  email: n@example.org
  Place: Hub
  [
    System: Harbor
    [
      Member: Ada
    ]
  ]
]
""", "Place anchors are not supported")


if __name__ == "__main__":
    unittest.main()
