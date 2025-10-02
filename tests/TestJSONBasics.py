from __future__ import annotations

from unittest import TestCase, main
from typing import Sequence

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


class TestJSONValueLike(TestCase):
    def test_value_like_instances(self):
        self.assertIsInstance(None, JSONValueLike)
        self.assertIsInstance(True, JSONValueLike)
        self.assertIsInstance(42, JSONValueLike)
        self.assertIsInstance(3.14, JSONValueLike)
        self.assertIsInstance("hello", JSONValueLike)

        self.assertNotIsInstance([], JSONValueLike)
        self.assertNotIsInstance({}, JSONValueLike)

    def test_value_like_subclasses(self):
        self.assertTrue(issubclass(int, JSONValueLike))
        self.assertTrue(issubclass(str, JSONValueLike))
        self.assertTrue(issubclass(float, JSONValueLike))
        self.assertTrue(issubclass(bool, JSONValueLike))
        self.assertTrue(issubclass(type(None), JSONValueLike))

        self.assertFalse(issubclass(list, JSONValueLike))
        self.assertFalse(issubclass(dict, JSONValueLike))


class TestJSONObjectLike(TestCase):
    def test_object_like_instances(self):
        self.assertIsInstance({"a": 1}, JSONObjectLike)
        self.assertIsInstance({"a": [1, 2]}, JSONObjectLike)
        self.assertIsInstance({"a": {"b": "c"}}, JSONObjectLike)

        self.assertNotIsInstance({1: "bad"}, JSONObjectLike)   # non-str key
        self.assertNotIsInstance({"a": set()}, JSONObjectLike) # invalid value type
        self.assertNotIsInstance([], JSONObjectLike)

    def test_object_like_subclasses(self):
        self.assertTrue(issubclass(dict[str, int], JSONObjectLike))
        self.assertTrue(issubclass(dict[str, list[int]], JSONObjectLike))

        self.assertFalse(issubclass(dict[int, str], JSONObjectLike))
        self.assertFalse(issubclass(list[int], JSONObjectLike))


class TestJSONArrayLike(TestCase):
    def test_array_like_instances(self):
        self.assertIsInstance([1, 2, 3], JSONArrayLike)
        self.assertIsInstance(["a", {"b": 2}], JSONArrayLike)
        self.assertIsInstance((1, 2), JSONArrayLike)

        self.assertNotIsInstance("not an array", JSONArrayLike)
        self.assertNotIsInstance([set()], JSONArrayLike)  # invalid element

    def test_array_like_subclasses(self):
        self.assertTrue(issubclass(list[int], JSONArrayLike))
        self.assertTrue(issubclass(Sequence[str], JSONArrayLike))
        self.assertTrue(issubclass(list[dict[str, int]], JSONArrayLike))

        self.assertFalse(issubclass(dict[str, int], JSONArrayLike))


class TestJSONContainerLike(TestCase):
    def test_container_like_instances(self):
        self.assertIsInstance([], JSONContainerLike)
        self.assertIsInstance({}, JSONContainerLike)
        self.assertIsInstance([{"a": 1}], JSONContainerLike)

        self.assertNotIsInstance(42, JSONContainerLike)
        self.assertNotIsInstance("hello", JSONContainerLike)

    def test_container_like_subclasses(self):
        self.assertTrue(issubclass(list[int], JSONContainerLike))
        self.assertTrue(issubclass(dict[str, int], JSONContainerLike))

        self.assertFalse(issubclass(int, JSONContainerLike))


class TestJSONLike(TestCase):
    def test_json_like_instances(self):
        self.assertIsInstance(None, JSONLike)
        self.assertIsInstance(True, JSONLike)
        self.assertIsInstance(123, JSONLike)
        self.assertIsInstance("abc", JSONLike)
        self.assertIsInstance([], JSONLike)
        self.assertIsInstance({}, JSONLike)
        self.assertIsInstance([{"a": 1}, 2, "x"], JSONLike)

        class Foo: pass
        self.assertNotIsInstance(Foo(), JSONLike)

    def test_json_like_subclasses(self):
        self.assertTrue(issubclass(int, JSONLike))
        self.assertTrue(issubclass(str, JSONLike))
        self.assertTrue(issubclass(dict[str, int], JSONLike))
        self.assertTrue(issubclass(list[int], JSONLike))

        self.assertFalse(issubclass(set, JSONLike))   # sets not allowed

if __name__ == "__main__":
    main()
