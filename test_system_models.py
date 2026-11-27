#!/usr/bin/env python3
"""Automated checks for generated PluralBridge canonical models and feed note references.

The canonical tests call generate_system_models and simplyplural_official in memory.
They compare the twelve exports with fixtures/pluralbridge-system-models and
with the matching files under sample-output. example-shape.json is not part
of that set. They do not run generate.py --out and they do not read feed output.

The feed note tests parse small in-memory feeds. They do not write files.
"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import system_models
from generate import dump, dump_system_model, generate_system_models, simplyplural_official

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "pluralbridge-system-models"
SAMPLE_OUTPUT = ROOT / "sample-output" / "pluralbridge-system-models"


class SystemModelGenerationTests(unittest.TestCase):
    """The twelve assembled exports: schema, references, topology, and fixture bytes."""
    @classmethod
    def setUpClass(cls):
        cls.exports = generate_system_models()

    def test_all_twelve_filenames(self):
        self.assertEqual(list(self.exports), system_models.SYSTEM_MODEL_FILENAMES)
        self.assertEqual(len(self.exports), 12)

    def test_each_export_valid(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_export(obj, name)

    def test_hierarchical_envelope(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_schema(obj, name)
                account = obj["account"]
                self.assertIn("members", account)
                self.assertIn("anchors", account)
                self.assertIn("tree", account)
                self.assertNotIn("accounts", obj)
                self.assertNotIn("systems", obj)
                for key in system_models.REMOVED_ACCOUNT_COLLECTIONS:
                    self.assertNotIn(key, account)
                if name.endswith("example-012-non-system-anchors.json"):
                    self.assertNotIn("notes", account)
                    self.assertNotIn("frontHistory", account)
                    self.assertNotIn("customFields", account)
                if name.endswith("example-011-top-level-place-containing-systems.json"):
                    self.assertEqual(system_models._anchors_of_type(obj, "group"), [])
                if name.endswith("example-010-top-level-group-containing-systems.json"):
                    self.assertEqual(system_models._anchors_of_type(obj, "place"), [])

    def test_unique_memberships(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_unique_memberships(obj, name)

    def test_graph_and_placement_examples(self):
        ex1 = self.exports["example-001-simple-single-system.json"]
        self.assertNotIn("relationships", ex1["account"])
        tree = system_models._tree_index(ex1)
        self.assertEqual(system_models._tree_member_ids(tree["system-001"]),
                         ["member-001", "member-002", "member-003"])
        self.assertEqual(system_models._tree_member_ids(tree["group-003"]), ["member-001"])
        self.assertEqual(system_models._tree_member_ids(tree["group-001"]),
                         ["member-001", "member-003"])

        ex3 = self.exports["example-003-parent-child-system.json"]
        self.assertNotIn("relationships", ex3["account"])
        tree3 = system_models._tree_index(ex3)
        self.assertEqual([node["anchorId"] for node in ex3["account"]["tree"]], ["system-001"])
        self.assertEqual(system_models._child_ids(tree3["system-001"]), ["group-001", "system-002"])
        self.assertEqual(system_models._tree_member_ids(tree3["system-002"]),
                         ["member-003", "member-004"])

        ex5 = self.exports["example-005-related-systems.json"]
        self.assertEqual(
            system_models._rel_labels(ex5),
            {
                ("system-001", "related", "system-002"),
                ("system-002", "related", "system-001"),
            },
        )

        ex6 = self.exports["example-006-subsystem.json"]
        self.assertEqual(ex6["pluralBridgeExport"]["exampleName"], "Nested Structure Model")
        self.assertEqual(len(system_models._anchors_of_type(ex6, "system")), 1)
        self.assertEqual(system_models._anchor_names(ex6, "place")["place-001"], "Morgan's Room")
        tree6 = system_models._tree_index(ex6)
        self.assertEqual(system_models._child_ids(tree6["system-001"]), ["group-001", "place-001"])
        self.assertNotIn("relationships", ex6["account"])

        ex7 = self.exports["example-007-evolving-uncertain-relationship.json"]
        self.assertEqual(
            system_models._rel_labels(ex7),
            {("system-002", "evolving", None), ("system-002", "unknown", None)},
        )

        ex8 = self.exports["example-008-archived-system.json"]
        self.assertEqual(system_models._rel_labels(ex8), {("system-002", "archived", None)})
        old = next(a for a in ex8["account"]["anchors"] if a["anchorId"] == "system-002")
        self.assertTrue(old["isArchived"])
        self.assertEqual(old["status"], "archived")
        current_members = [m for m in ex8["account"]["members"] if not m["isArchived"]]
        archived_members = [m for m in ex8["account"]["members"] if m["isArchived"]]
        self.assertEqual(len(current_members), 2)
        self.assertEqual(len(archived_members), 2)

        ex9 = self.exports["example-009-non-tree-graph.json"]
        self.assertEqual(
            system_models._rel_labels(ex9),
            {
                ("system-001", "related", "system-002"),
                ("system-002", "sibling", "system-003"),
                ("system-003", "associated", "system-001"),
            },
        )

        ex10 = self.exports["example-010-top-level-group-containing-systems.json"]
        tree10 = system_models._tree_index(ex10)
        self.assertEqual([node["anchorId"] for node in ex10["account"]["tree"]], ["group-001"])
        self.assertEqual(system_models._child_ids(tree10["group-001"]), ["system-001", "system-002"])
        self.assertNotIn("relationships", ex10["account"])

        ex11 = self.exports["example-011-top-level-place-containing-systems.json"]
        tree11 = system_models._tree_index(ex11)
        self.assertEqual(system_models._child_ids(tree11["system-002"]), ["place-002"])
        self.assertNotIn("place-002", system_models._child_ids(tree11["place-001"]))

    def test_member_wide_fronting_and_repeated_members(self):
        ex1 = self.exports["example-001-simple-single-system.json"]
        by_id = {m["memberId"]: m for m in ex1["account"]["members"]}
        self.assertTrue(by_id["member-001"]["fronting"])
        self.assertTrue(by_id["member-002"]["fronting"])
        self.assertFalse(by_id["member-003"]["fronting"])
        tree = system_models._tree_index(ex1)
        harbor_occ = tree["system-001"]["members"][0]
        ballet_occ = tree["group-003"]["members"][0]
        # The same shared memberId may appear on more than one tree node.
        self.assertEqual(harbor_occ["memberId"], "member-001")
        self.assertEqual(ballet_occ["memberId"], "member-001")
        system_models.validate_export(ex1, "repeated-member-occurrences")
        self.assertNotIn("fronting", harbor_occ)
        self.assertNotIn("fronting", ballet_occ)

        ex12 = self.exports["example-012-non-system-anchors.json"]
        self.assertTrue(all(m["fronting"] is False for m in ex12["account"]["members"]))
        self.assertNotIn("frontHistory", ex12["account"])

    def test_removed_collections_and_inherit_settings(self):
        """Independent checks against example-shape.json; fixture equality is not enough."""
        shape = json.loads((SAMPLE_OUTPUT / "example-shape.json").read_text(encoding="utf-8"))
        inherit = shape["account"]["notes"][0]["visibility"]
        self.assertEqual(inherit, {"mode": "inherit"})
        self.assertEqual(shape["account"]["notes"][0]["permissions"], inherit)
        self.assertEqual(shape["account"]["customFields"][0]["visibility"], inherit)
        explicit = shape["account"]["tree"][0]["members"][0]["visibility"]
        self.assertEqual(explicit["mode"], "explicit")

        preserved = {"mode": "explicit", "value": "self"}
        rec = {"visibility": dict(preserved), "other": 1}
        system_models._ensure_inherit_settings(rec)
        self.assertEqual(rec["visibility"], preserved)
        self.assertEqual(rec["permissions"], inherit)

        for name, obj in self.exports.items():
            with self.subTest(name=name):
                account = obj["account"]
                for key in system_models.REMOVED_ACCOUNT_COLLECTIONS:
                    self.assertNotIn(key, account)
                for rec in account.get("notes") or []:
                    self.assertEqual(rec["visibility"], inherit)
                    self.assertEqual(rec["permissions"], inherit)
                    self.assertNotIn("fronting", rec)
                for rec in account.get("customFields") or []:
                    self.assertEqual(rec["visibility"], inherit)
                    self.assertEqual(rec["permissions"], inherit)
                for node in system_models.walk_tree(account["tree"]):
                    for occ in node.get("members") or []:
                        self.assertEqual(occ["visibility"], inherit)
                        self.assertEqual(occ["permissions"], inherit)
                        self.assertNotIn("fronting", occ)
                for member in account["members"]:
                    self.assertNotIn("visibility", member)
                    self.assertNotIn("permissions", member)
                    self.assertIsInstance(member["fronting"], bool)

    def test_non_system_anchor_example(self):
        obj = self.exports["example-012-non-system-anchors.json"]
        account = obj["account"]
        self.assertEqual(system_models._anchors_of_type(obj, "system"), [])
        for key in ("memberships", "relationships", "notes", "frontHistory",
                    "customFields", "privacyBuckets", "visibilityScopes"):
            self.assertNotIn(key, account)
        tree = system_models._tree_index(obj)
        self.assertEqual(system_models._child_ids(tree["place-001"]), ["group-001", "group-002"])
        self.assertEqual(system_models._child_ids(tree["group-002"]), ["place-002"])
        self.assertEqual(system_models._tree_member_ids(tree["group-001"]),
                         ["member-001", "member-002"])
        self.assertEqual(system_models._tree_member_ids(tree["place-002"]),
                         ["member-003", "member-004"])
        self.assertNotIn("frontHistory", account)
        self.assertEqual(obj["provenance"]["sourceGenerator"], "example-012-document-transcription")

    def test_rejects_structural_corruption(self):
        original = self.exports["example-012-non-system-anchors.json"]
        for case in ("invented-system", "flattened-place", "wrong-group", "duplicate-tree"):
            with self.subTest(case=case):
                obj = copy.deepcopy(original)
                if case == "invented-system":
                    obj["account"]["anchors"].append({
                        "anchorId": "system-001", "objectType": "system", "name": "Invented",
                    })
                elif case == "flattened-place":
                    hub = obj["account"]["tree"][0]
                    house = hub["children"][1]
                    waiting = house["children"].pop(0)
                    hub["children"].append(waiting)
                elif case == "wrong-group":
                    tree = system_models._tree_index(obj)
                    tree["group-002"]["members"] = [{
                        "memberId": "member-001",
                        "visibility": {"mode": "inherit"},
                        "permissions": {"mode": "inherit"},
                    }]
                else:
                    obj["account"]["tree"].append(dict(obj["account"]["tree"][0]))
                with self.assertRaises(AssertionError):
                    system_models.validate_export(obj)

        ex7 = copy.deepcopy(self.exports["example-007-evolving-uncertain-relationship.json"])
        ex7["account"]["relationships"][0]["sourceAnchorId"] = "missing-anchor"
        with self.assertRaises(AssertionError):
            system_models.validate_export(ex7, "missing-relationship-source")

        missing_ref = copy.deepcopy(self.exports["example-001-simple-single-system.json"])
        missing_ref["account"]["tree"][0]["members"][0]["memberId"] = "member-999"
        with self.assertRaises(AssertionError):
            system_models.validate_export(missing_ref, "missing-tree-member")

        # Two anchors of different types must not share a name.
        dup_anchor_name = copy.deepcopy(self.exports["example-001-simple-single-system.json"])
        dup_anchor_name["account"]["anchors"].append({
            "anchorId": "group-dup",
            "objectType": "group",
            "name": "The Harbor",
        })
        with self.assertRaises(AssertionError):
            system_models.validate_export(dup_anchor_name, "duplicate-anchor-name")

        # noteId values must be unique; titles are not required to be unique.
        dup_note_id = copy.deepcopy(self.exports["example-001-simple-single-system.json"])
        dup_note_id["account"]["notes"].append(dict(dup_note_id["account"]["notes"][0]))
        with self.assertRaises(AssertionError):
            system_models.validate_export(dup_note_id, "duplicate-note-id")

    def test_approved_relationship_rows(self):
        """Independent checks for the approved relationship shape across the 12 examples."""
        ex7 = self.exports["example-007-evolving-uncertain-relationship.json"]
        labels7 = system_models._rel_labels(ex7)
        self.assertEqual(labels7, {("system-002", "evolving", None), ("system-002", "unknown", None)})
        self.assertEqual(len(ex7["account"]["relationships"]), 2)
        for rec in ex7["account"]["relationships"]:
            self.assertEqual(rec["sourceAnchorId"], "system-002")
            self.assertIsNone(rec["targetAnchorId"])
            self.assertEqual(
                list(rec),
                ["relationshipId", "sourceAnchorId", "fieldId", "targetAnchorId"],
            )

        ex8 = self.exports["example-008-archived-system.json"]
        labels8 = system_models._rel_labels(ex8)
        self.assertEqual(labels8, {("system-002", "archived", None)})
        self.assertEqual(len(ex8["account"]["relationships"]), 1)
        archived = ex8["account"]["relationships"][0]
        self.assertEqual(archived["sourceAnchorId"], "system-002")
        self.assertIsNone(archived["targetAnchorId"])
        self.assertEqual(
            list(archived),
            ["relationshipId", "sourceAnchorId", "fieldId", "targetAnchorId"],
        )

        total = 0
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_references(obj, name)
                rows = obj["account"].get("relationships") or []
                total += len(rows)
                rel_fields = {r["fieldId"] for r in rows}
                for rec in rows:
                    self.assertEqual(
                        list(rec),
                        ["relationshipId", "sourceAnchorId", "fieldId", "targetAnchorId"],
                    )
                for anchor in obj["account"]["anchors"]:
                    overlap = rel_fields.intersection(anchor.get("fieldIds") or [])
                    self.assertEqual(overlap, set(), f"{name}: relationship field on {anchor['anchorId']}")
        self.assertEqual(total, 10)

        for name, generated in self.exports.items():
            with self.subTest(match=name):
                fixture_text = (FIXTURES / name).read_text(encoding="utf-8")
                sample_text = (SAMPLE_OUTPUT / name).read_text(encoding="utf-8")
                generated_text = dump_system_model(generated)
                self.assertEqual(generated, json.loads(fixture_text))
                self.assertEqual(generated_text, fixture_text)
                self.assertEqual(generated_text, sample_text)

    def test_matches_canonical_fixtures(self):
        """Generated text equals the committed fixture and the sample-output copy."""
        for name, generated in self.exports.items():
            with self.subTest(name=name):
                fixture_text = (FIXTURES / name).read_text(encoding="utf-8")
                fixture = json.loads(fixture_text)
                self.assertEqual(generated, fixture)
                self.assertEqual(dump_system_model(generated), fixture_text)
                self.assertEqual(
                    system_models.structural_facts(generated),
                    system_models.structural_facts(fixture),
                )


class SimplyPluralRegressionTests(unittest.TestCase):
    """Aurora's official export stays sorted-key JSON and keeps its collection shape."""
    def test_official_export_shape(self):
        export = simplyplural_official()
        self.assertEqual(len(export["members"]), 5)
        self.assertEqual(len(export["groups"]), 6)
        open_fronts = [e for e in export["frontHistory"] if "endTime" not in e]
        self.assertEqual(len(open_fronts), 2)
        self.assertTrue(all(m["_id"].startswith("synthetic-") for m in export["members"]))

    def test_dump_is_deterministic(self):
        export = simplyplural_official()
        self.assertEqual(dump(export), dump(simplyplural_official()))


class SystemModelDeterminismTests(unittest.TestCase):
    """A second in-memory generation matches the first. Insertion order is part of the text."""
    def test_system_models_are_deterministic(self):
        first = generate_system_models()
        second = generate_system_models()
        self.assertEqual(list(first), list(second))
        for name in first:
            with self.subTest(name=name):
                self.assertEqual(dump_system_model(first[name]), dump_system_model(second[name]))


def _load_hyphen(filename):
    spec = importlib.util.spec_from_file_location(filename.replace("-", "_").replace(".py", ""), ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AnchorNoteReferenceTests(unittest.TestCase):
    """Place, System, and Group notes stay on the anchor that cited them."""

    @classmethod
    def setUpClass(cls):
        cls.engine = _load_hyphen("gen-import-engine.py")
        cls.pluralbridge = _load_hyphen("gen-pluralbridge.py")
        cls.simplyplural = _load_hyphen("gen-simplyplural.py")
        cls.pluralport = _load_hyphen("gen-pluralport.py")
        cls.pluralkit = _load_hyphen("gen-pluralkit.py")

    def _parse(self, text):
        return self.engine._Parser("feed.txt", text).parse()

    def test_anchor_notes_are_separate_from_member_notes(self):
        model = self._parse("""
Account
[
  name: n
  email: n@example.org
  Place: Hub
  [
    note: placeNote
    note: placeNote
    note: laterNote
  ]
  System: Harbor
  [
    note: sysNote
    Member: Ada
    [
      note: memberNote
      note: placeNote
    ]
  ]
  Group: Theatre
  [
    note: groupNote
  ]
  Notes
  [
    Note:placeNote 'place body'
    Note:laterNote 'later body'
    Note:sysNote 'system body'
    Note:groupNote 'group body'
    Note:memberNote 'member body'
  ]
]
""")
        by_name = {anchor["name"]: anchor for anchor in model["anchors"]}
        self.assertEqual(by_name["Hub"]["note_refs"], ["placeNote", "laterNote"])
        self.assertEqual(by_name["Harbor"]["note_refs"], ["sysNote"])
        self.assertEqual(by_name["Theatre"]["note_refs"], ["groupNote"])
        ada = model["members"][0]
        self.assertEqual(ada["note_refs"], ["memberNote", "placeNote"])
        self.assertNotIn("groupNote", ada["note_refs"])
        self.assertNotIn("sysNote", ada["note_refs"])
        self.assertNotIn("memberNote", by_name["Hub"]["note_refs"])

        export, _gaps = self.pluralbridge.render_import_model(model)
        self.pluralbridge.check_import_export(export, "feed.txt")
        anchors = {anchor["name"]: anchor for anchor in export["account"]["anchors"]}
        self.assertEqual(anchors["Theatre"]["noteIds"], ["groupNote"])
        self.assertEqual(anchors["Hub"]["noteIds"], ["placeNote", "laterNote"])
        self.assertEqual(anchors["Harbor"]["noteIds"], ["sysNote"])
        note_ids = [note["noteId"] for note in export["account"]["notes"]]
        self.assertIn("groupNote", note_ids)
        members = {member["displayName"]: member for member in export["account"]["members"]}
        self.assertEqual(members["Ada"]["noteIds"], ["memberNote", "placeNote"])
        self.assertNotIn("groupNote", members["Ada"]["noteIds"])
        for node in system_models.walk_tree(export["account"]["tree"]):
            self.assertNotIn("noteIds", node)

    def test_undefined_note_names_the_reference_line(self):
        text = "\n".join([
            "Account",
            "[",
            "  name: n",
            "  email: n@example.org",
            "  System: Harbor",
            "  [",
            "    note: missing",
            "  ]",
            "]",
        ])
        with self.assertRaises(self.engine.FeedError) as caught:
            self.engine._Parser("specimen.txt", text).parse()
        self.assertIn("specimen.txt:7:", str(caught.exception))
        self.assertIn("undefined note 'missing'", str(caught.exception))

    def test_other_targets_do_not_assign_anchor_notes_to_members(self):
        model = self._parse("""
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Member: Ada
    [
      note: memberNote
    ]
    Group: Theatre
    [
      note: groupNote
    ]
  ]
  Notes
  [
    Note:memberNote 'member body'
    Note:groupNote 'group body'
  ]
]
""")
        with self.assertRaises(self.simplyplural.SimplyPluralError) as sp:
            self.simplyplural.render_import_model(model)
        self.assertIn("anchor note association is not supported", str(sp.exception))
        self.assertIn("groupNote", str(sp.exception))
        with self.assertRaises(self.pluralport.PluralPortError) as pp:
            self.pluralport.render_import_model(model)
        self.assertIn("anchor note association is not supported", str(pp.exception))
        self.assertIn("groupNote", str(pp.exception))
        _export, notices = self.pluralkit.render_import_model(model)
        self.assertTrue(any("Theatre" in notice and "groupNote" in notice for notice in notices))
        self.assertTrue(all("groupNote" not in json.dumps(member) for member in _export["members"]))

    def test_member_only_note_still_belongs_to_the_member(self):
        model = self._parse("""
Account
[
  name: n
  email: n@example.org
  System: Harbor
  [
    Member: Ada
    [
      note: memberNote
    ]
  ]
  Notes
  [
    Note:memberNote 'member body'
  ]
]
""")
        self.assertEqual(model["anchors"][0]["note_refs"], [])
        self.assertEqual(model["members"][0]["note_refs"], ["memberNote"])
        export, _notices = self.simplyplural.render_import_model(model)
        self.assertEqual(export["notes"][0]["member"], model["members"][0]["json_id"])
        self.assertEqual(export["notes"][0]["_id"], "memberNote")

    def test_top_level_group_custom_field_is_rejected(self):
        model = self._parse("""
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
""")
        destination = Path(tempfile.mkdtemp()) / "existing.json"
        destination.write_bytes(b"previous-output")
        before = destination.read_bytes()
        try:
            export, _warnings = self.pluralport.render_import_model(model)
            self.pluralport.write_import_export(destination, export)
        except self.pluralport.PluralPortError as exc:
            message = str(exc)
        else:
            self.fail("expected PluralPortError before write")
        self.assertIn("feed.txt:", message)
        self.assertIn("Group custom-field associations are not supported", message)
        self.assertEqual(destination.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
