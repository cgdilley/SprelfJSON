from __future__ import annotations

from unittest import TestCase

from SprelfJSON import *


class TestJSONBasics(TestCase):

    def test_definitions(self):
        self.assertTrue(is_json_type(None, JSONValue))
        self.assertTrue(is_json_type(None, JSONType))
        self.assertTrue(is_json_type(True, JSONValue))
        self.assertTrue(is_json_type(False, JSONType))
        self.assertTrue(is_json_type(0, JSONValue))
        self.assertTrue(is_json_type(1, JSONType))
        self.assertTrue(is_json_type(0.5, JSONValue))
        self.assertTrue(is_json_type(-0.8, JSONType))
        self.assertTrue(is_json_type("a", JSONValue))
        self.assertTrue(is_json_type("b", JSONType))
        self.assertTrue(is_json_type([], JSONArray))
        self.assertTrue(is_json_type(["a"], JSONContainer))
        self.assertTrue(is_json_type([1], JSONType))
        self.assertTrue(is_json_type(dict(), JSONObject))
        self.assertTrue(is_json_type({"a": 1}, JSONContainer))
        self.assertTrue(is_json_type({"a": []}, JSONType))
        
        self.assertFalse(is_json_type(tuple(), JSONValue))
        self.assertFalse(is_json_type(tuple(), JSONType))
        self.assertFalse(is_json_type([], JSONValue))
        self.assertFalse(is_json_type(set(), JSONType))
        self.assertFalse(is_json_type(dict(), JSONValue))
        self.assertFalse(is_json_type(range(1), JSONType))
        self.assertFalse(is_json_type(set(), JSONArray))
        self.assertFalse(is_json_type("a", JSONArray))
        self.assertFalse(is_json_type(0, JSONContainer))
        self.assertFalse(is_json_type("a", JSONContainer))
        self.assertFalse(is_json_type([], JSONObject))
        self.assertFalse(is_json_type("a", JSONObject))
        self.assertFalse(is_json_type(None, JSONContainer))
        self.assertFalse(is_json_type("a", JSONContainer))

    def test_get(self):
        obj = {"a": {"b": 0, "c": [1, 2, {"d": False}], "e": "f"}, "g": [[[3]]]}
        self.assertEqual(0, json_get(obj, ("a", "b")))
        self.assertEqual(0, json_get(obj, "a.b"))
        self.assertEqual(2, json_get(obj, ("a", "c", 1)))
        self.assertEqual(2, json_get(obj, "a.c.1"))
        self.assertFalse(json_get(obj, ("a", "c", 2, "d")))
        self.assertFalse(json_get(obj, "a.c.2.d"))
        self.assertDictEqual({"d": False}, json_get(obj, ("a", "c", 2)))
        self.assertDictEqual({"d": False}, json_get(obj, "a.c.2"))
        self.assertEqual("f", json_get(obj, ("a", "e")))
        self.assertEqual("f", json_get(obj, "a.e"))
        self.assertListEqual([3], json_get(obj, ("g", "0", 0)))
        self.assertListEqual([3], json_get(obj, "g.0.0"))
        self.assertDictEqual(obj, json_get(obj, ()))
        self.assertIsNone(json_get(obj, ("asdf",)))
        self.assertIsNone(json_get(None, ("a",)))
        self.assertIsNone(json_get(obj, ("a", "c", 4)))
        self.assertEqual("asdf", json_get(obj, "x", default="asdf"))
