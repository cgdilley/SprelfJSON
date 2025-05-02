import unittest
from SprelfJSON.JSONModel import *
from typing import Optional, Union


# THESE TESTS HAVE BEEN AI-GENERATED

# ---------------------------
# ✅ BASIC FIELD TYPE TESTING
# ---------------------------

class TestJSONModel(unittest.TestCase):

    class BasicModel(JSONModel):
        an_int: int
        a_str: str
        a_float: float
        a_bool: bool
        a_list: list[int]
        a_dict: dict[str, str]

    def test_valid_input(self):
        model = self.BasicModel(
            an_int=5,
            a_str="hello",
            a_float=3.14,
            a_bool=True,
            a_list=[1, 2, 3],
            a_dict={"key": "value"}
        )
        self.assertEqual(model.an_int, 5)
        self.assertEqual(model.a_str, "hello")


# ---------------------------
# ✅ DEFAULTS AND MODELELEM
# ---------------------------

    class DefaultsModel(JSONModel):
        required: int
        optional: ModelElem(int, default=42)
        optional_str: str = "abc"


    def test_defaults_applied(self):
        model = self.DefaultsModel(required=7)
        self.assertEqual(model.optional, 42)
        self.assertEqual(model.optional_str, "abc")

    def test_override_defaults(self):
        model = self.DefaultsModel(required=7, optional=99)
        self.assertEqual(model.optional, 99)


# ---------------------------
# ✅ INHERITANCE
# ---------------------------

    class ParentModel(JSONModel):
        parent_field: str


    class ChildModel(ParentModel):
        child_field: int


    def test_inherited_fields(self):
        model = self.ChildModel(parent_field="base", child_field=123)
        self.assertEqual(model.parent_field, "base")
        self.assertEqual(model.child_field, 123)


# ---------------------------
# ✅ SUBCLASS RESOLUTION
# ---------------------------

    class Animal(JSONModel):
        __name_field_required__ = True
        kind: str


    class Dog(Animal):
        breed: str

        @classmethod
        def model_identity(cls):
            return "dog"


    def test_subclass_from_json(self):
        json = {
            "__name": "dog",
            "kind": "dog",
            "breed": "retriever"
        }
        obj = self.Animal.from_json(json)
        self.assertIsInstance(obj, self.Dog)
        self.assertEqual(obj.breed, "retriever")


# ---------------------------
# ✅ VALIDATION ERRORS
# ---------------------------

    def test_missing_required_field(self):
        with self.assertRaises(JSONModelError) as cm:
            self.BasicModel(
                an_int=1,
                a_str="hello",
                a_float=1.0,
                a_bool=True,
                a_list=[1, 2]
                # a_dict missing
            )
        self.assertIn("Missing required key 'a_dict'", str(cm.exception))

    def test_extra_field(self):
        with self.assertRaises(JSONModelError) as cm:
            self.BasicModel(
                an_int=1,
                a_str="hi",
                a_float=1.2,
                a_bool=True,
                a_list=[1],
                a_dict={},
                not_a_field="oops"
            )
        self.assertIn("not found in the model", str(cm.exception))

    def test_invalid_type(self):
        with self.assertRaises(JSONModelError) as cm:
            self.DefaultsModel(required="not an int")
        self.assertIn("Model error on key 'required'", str(cm.exception))


# ---------------------------
# ✅ OPTIONAL / UNION TYPES
# ---------------------------

    class OptionalModel(JSONModel):
        maybe_int: Optional[int]
        union_val: Union[int, str]


    def test_optional_none_and_union(self):
        model1 = self.OptionalModel(maybe_int=None, union_val="text")
        self.assertIsNone(model1.maybe_int)
        self.assertEqual(model1.union_val, "text")

    def test_optional_with_value_and_union(self):
        model2 = self.OptionalModel(maybe_int=5, union_val=42)
        self.assertEqual(model2.maybe_int, 5)
        self.assertEqual(model2.union_val, 42)


# ---------------------------
# ✅ MAIN RUNNER
# ---------------------------

if __name__ == '__main__':
    unittest.main()
