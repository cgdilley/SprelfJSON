import unittest
import contextlib
import copy as _copy
import collections.abc as cabc

from SprelfJSON.Objects import Ephemeral
from SprelfJSON.JSONModel.JSONModel import JSONModel
from SprelfJSON.JSONModel.ModelElem import ModelElem, ModelElemError


class EphemeralTests(unittest.TestCase):
    def test_basic_wrapping_and_access(self):
        e = Ephemeral(42)
        # identity helpers
        self.assertTrue(Ephemeral.is_ephemeral(e))
        self.assertFalse(Ephemeral.is_ephemeral(42))
        # accessors
        self.assertEqual(42, e.value)
        self.assertEqual(42, e.V)
        # unwrap
        self.assertEqual(42, Ephemeral.unwrap(e))
        self.assertEqual(42, Ephemeral.unwrap(42))  # passthrough

    def test_attribute_delegation_get_set_del(self):
        class C:
            def __init__(self):
                self.x = 1
        c = C()
        e = Ephemeral(c)

        # get
        self.assertEqual(1, e.x)
        # set
        e.x = 10
        self.assertEqual(10, c.x)
        # del
        del e.x
        self.assertFalse(hasattr(c, "x"))

        # internal field guarded
        with self.assertRaises(AttributeError):
            delattr(e, type(e).__ephm_field__)

    def test_dunder_forwarding_only_if_supported(self):
        # int is not Iterable/Collection
        e_int = Ephemeral(7)
        self.assertFalse(isinstance(e_int, cabc.Collection))
        self.assertFalse(isinstance(e_int, cabc.Iterable))
        # int/float/index conversions should work when supported
        self.assertEqual(7, int(e_int))
        # __index__ must exist for slicing/indices
        self.assertEqual(7, e_int.__index__())
        self.assertEqual(7.0, float(e_int))

        # list should look like a Collection/Iterable
        e_list = Ephemeral([1, 2, 3])
        self.assertTrue(isinstance(e_list, cabc.Collection))
        self.assertTrue(isinstance(e_list, cabc.Iterable))
        self.assertEqual(3, len(e_list))
        self.assertEqual([1, 2, 3], list(iter(e_list)))
        self.assertIn(2, e_list)

        # bytes conversion only when underlying supports it
        e_bytes = Ephemeral(b"abc")
        self.assertEqual(b"abc", bytes(e_bytes))

    def test_equality_and_ordering(self):
        e1 = Ephemeral(5)
        e2 = Ephemeral(5)
        e3 = Ephemeral(6)

        self.assertTrue(e1 == e2)
        self.assertFalse(e1 != e2)
        self.assertTrue(e1 < e3)
        self.assertTrue(e3 > e1)
        self.assertTrue(e1 <= e2)
        self.assertTrue(e1 >= e2)

        # Compare against raw value
        self.assertTrue(e1 == 5)
        self.assertTrue(e3 > 5)

    def test_hash_behavior(self):
        # Hashable underlying
        e_hashable = Ephemeral("abc")
        self.assertEqual(hash("abc"), hash(e_hashable))

        # Unhashable underlying (list) => Ephemeral becomes unhashable (TypeError)
        e_unhashable = Ephemeral([1, 2, 3])
        with self.assertRaises(TypeError):
            hash(e_unhashable)

    def test_context_manager_delegation(self):
        @contextlib.contextmanager
        def cm():
            yield "ok"

        e = Ephemeral(cm())
        with e as v:
            self.assertEqual("ok", v)

    def test_copy_and_deepcopy(self):
        class Node:
            def __init__(self, val, child=None):
                self.val = val
                self.child = child

        n = Node(1, Node(2))
        e = Ephemeral(n)

        e_shallow = _copy.copy(e)
        self.assertIsInstance(e_shallow, Ephemeral)
        self.assertIsNot(e_shallow, e)
        # Shallow copy: top-level is new wrapper, underlying is shallow-copied if possible
        self.assertEqual(1, e_shallow.val)
        self.assertIsNot(Ephemeral.unwrap(e_shallow), Ephemeral.unwrap(e))

        e_deep = _copy.deepcopy(e)
        self.assertIsInstance(e_deep, Ephemeral)
        self.assertIsNot(e_deep, e)
        # Deep copy: underlying graph is copied
        self.assertEqual(1, e_deep.val)
        self.assertIsNot(Ephemeral.unwrap(e_deep), Ephemeral.unwrap(e))
        self.assertIsNot(e_deep.child, e.child)
        self.assertEqual(e.child.val, e_deep.child.val)

    def test_dir_includes_wrapped_attributes(self):
        class C:
            def __init__(self):
                self.foo = 123
            def bar(self):  # noqa
                return "ok"
        e = Ephemeral(C())
        d = dir(e)
        # Should include wrapper’s own attributes and wrapped object's attributes
        self.assertIn("foo", d)
        self.assertIn("bar", d)
        self.assertTrue(any(name for name in d if name.startswith("__") and name.endswith("__")))


class EphemeralModelElemIntegrationTests(unittest.TestCase):
    def test_model_elem_ignores_ephemeral_field_on_parse_and_dump(self):
        class MyModel(JSONModel):
            x: int
            y: Ephemeral[int]

        # Constructing with or without 'y' should be fine; 'y' is ignored and never stored
        m1 = MyModel(x=10)
        self.assertEqual(10, m1.x)
        self.assertTrue(hasattr(m1, "y"))
        self.assertIsNone(m1.y)
        self.assertEqual({"x": 10}, m1.to_json())

        m2 = MyModel(x=99, y=Ephemeral(123))
        self.assertEqual(99, m2.x)
        self.assertTrue(hasattr(m2, "y"))
        self.assertEqual(123, m2.y)
        self.assertEqual({"x": 99}, m2.to_json())

    def test_ephemeral_field_is_not_required_and_not_validated(self):
        class MyModel(JSONModel):
            a: int
            # Even with a default specified, Ephemeral fields are ignored by JSONModel
            b: Ephemeral[str] = Ephemeral("default")

        # Missing 'b' is fine (ignored)
        m = MyModel(a=1)
        self.assertEqual(1, m.a)
        self.assertTrue(hasattr(m, "b"))
        self.assertEqual({"a": 1}, m.to_json())
        self.assertEqual("default", m.b)

        # Passing a non-matching type for 'b' should not raise (it's ignored entirely)
        m2 = MyModel(a=2, b="not ephemeral")
        self.assertEqual(2, m2.a)
        self.assertTrue(hasattr(m2, "b"))
        self.assertEqual("not ephemeral", m2.b)
        self.assertEqual({"a": 2}, m2.to_json())

    def test_standalone_modelelem_for_ephemeral(self):
        me_int = ModelElem(Ephemeral[int])

        self.assertEqual(123, me_int.parse_value(123))
        with self.assertRaises(ModelElemError):
            me_int.parse_value("not an int")
        self.assertEqual(456, me_int.validate(456))
        # dump_value returns None (ignored)
        with self.assertRaises(ModelElemError):
            me_int.dump_value(Ephemeral(789), key="ephemeral_field")



if __name__ == "__main__":
    unittest.main()
