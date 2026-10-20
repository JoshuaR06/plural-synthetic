#!/usr/bin/env python3
"""Automated checks for generated PluralBridge system-model configurations."""
import json
import unittest
from pathlib import Path

import system_models
from generate import dump, generate_system_models, simplyplural_official

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "pluralbridge-system-models"


class SystemModelGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = generate_system_models()

    def test_all_eleven_filenames(self):
        self.assertEqual(list(self.exports), system_models.SYSTEM_MODEL_FILENAMES)
        self.assertEqual(len(self.exports), 11)

    def test_each_export_valid(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_export(obj, name)

    def test_complete_collection_set(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_schema(obj, name)
                self.assertEqual(obj["customFields"] == [], name.startswith("example-01"))
                if name.endswith("example-011-top-level-place-containing-systems.json"):
                    self.assertEqual(obj["groups"], [])
                    self.assertEqual(obj["groupMemberships"], [])
                if name.endswith("example-010-top-level-group-containing-systems.json"):
                    self.assertEqual(obj["places"], [])
                    self.assertEqual(obj["placeMemberships"], [])
                    self.assertEqual(obj["systemObjectPlacements"], [])

    def test_unique_memberships(self):
        for name, obj in self.exports.items():
            with self.subTest(name=name):
                system_models.validate_unique_memberships(obj, name)

    def test_graph_and_placement_examples(self):
        ex1 = self.exports["example-001-simple-single-system.json"]
        self.assertEqual(len(ex1["systemRelationships"]), 1)
        root = ex1["systemRelationships"][0]
        self.assertEqual(root["systemId"], "system-001")
        self.assertEqual(root["relationshipType"], "root")
        self.assertIsNone(root["parentSystemId"])
        self.assertIsNone(root["targetSystemId"])

        ex3 = self.exports["example-003-parent-child-system.json"]
        self.assertIn(("system-002", "child", "system-001", None), system_models._rel_set(ex3))
        self.assertFalse(any(p[2] == "system-002" for p in system_models._sys_place_set(ex3)))

        ex5 = self.exports["example-005-related-systems.json"]
        self.assertEqual(
            {r for r in system_models._rel_set(ex5) if r[1] != "root"},
            {
                ("system-002", "related", None, "system-001"),
                ("system-001", "related", None, "system-002"),
            },
        )

        ex6 = self.exports["example-006-subsystem.json"]
        self.assertEqual(len(ex6["systems"]), 1)
        self.assertEqual(ex6["places"][0]["name"], "Morgan's Room")
        self.assertIn(("system-001", "place", "place-001", "system", "system-001"),
                      system_models._sys_place_set(ex6))
        self.assertFalse(any(r["relationshipType"] == "subsystem" for r in ex6["systemRelationships"]))
        self.assertFalse(any(r.get("associatedObjectId") == "member-002" for r in ex6["systemRelationships"]))

        ex7 = self.exports["example-007-evolving-uncertain-relationship.json"]
        evolving = [r for r in ex7["systemRelationships"] if r["relationshipType"] == "evolving"]
        self.assertEqual(len(evolving), 1)
        self.assertEqual(evolving[0]["systemId"], "system-002")
        self.assertEqual(evolving[0]["targetSystemId"], "system-001")
        self.assertEqual(evolving[0]["relationshipType"], "evolving")
        self.assertEqual(evolving[0]["relationshipStatus"], "unknown")
        self.assertIsNone(evolving[0]["parentSystemId"])

        ex8 = self.exports["example-008-archived-system.json"]
        self.assertEqual({r[1] for r in system_models._rel_set(ex8)}, {"root"})
        old = next(s for s in ex8["systems"] if s["systemId"] == "system-002")
        self.assertTrue(old["isArchived"])
        self.assertEqual(old["status"], "archived")

        ex9 = self.exports["example-009-non-tree-graph.json"]
        rels = system_models._rel_set(ex9)
        self.assertEqual(
            {r for r in rels if r[1] != "root"},
            {
                ("system-001", "related", None, "system-002"),
                ("system-002", "sibling", None, "system-003"),
                ("system-003", "associated", None, "system-001"),
            },
        )
        self.assertEqual({r[1] for r in rels}, {"root", "related", "sibling", "associated"})

        ex10 = self.exports["example-010-top-level-group-containing-systems.json"]
        aid = ex10["accounts"][0]["accountId"]
        self.assertIn((aid, "system", "system-001", "group", "group-001"),
                      system_models._acct_place_set(ex10))
        self.assertEqual({r[1] for r in system_models._rel_set(ex10)}, {"root"})

        ex11 = self.exports["example-011-top-level-place-containing-systems.json"]
        self.assertIn(("system-002", "place", "place-002", "system", "system-002"),
                      system_models._sys_place_set(ex11))
        self.assertFalse(any(p[2] == "place-002" for p in system_models._acct_place_set(ex11)))

    def test_matches_canonical_fixtures(self):
        for name, generated in self.exports.items():
            with self.subTest(name=name):
                fixture = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
                self.assertEqual(
                    system_models.structural_facts(generated),
                    system_models.structural_facts(fixture),
                )


class SimplyPluralRegressionTests(unittest.TestCase):
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
    def test_system_models_are_deterministic(self):
        first = generate_system_models()
        second = generate_system_models()
        self.assertEqual(list(first), list(second))
        for name in first:
            with self.subTest(name=name):
                self.assertEqual(dump(first[name]), dump(second[name]))


if __name__ == "__main__":
    unittest.main()
