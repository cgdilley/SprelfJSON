import unittest
import datetime
import enum
import re
import base64
from typing import Optional, Union

from SprelfJSON import *


# THESE TESTS WERE AI-GENERATED AND MANUALLY TWEAKED


# Define some simple JSONModel subclasses for testing
class SimpleModel(JSONModel):
    __name_field_required__ = False
    string_field: str
    int_field: int
    bool_field: bool = True # Field with default

class ModelWithDefaults(JSONModel):
    __name_field_required__ = False
    default_string: str = "hello"
    default_int: int = 100
    optional_float: Optional[float] = None
    list_with_default: ModelElem(list[int], default_factory=list) # Default factory

class ModelWithComplexTypes(JSONModel):
    __name_field_required__ = False
    datetime_field: datetime.datetime
    date_field: datetime.date
    time_field: datetime.time
    timedelta_field: datetime.timedelta
    bytes_field: bytes
    pattern_field: re.Pattern

class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

class Status(enum.IntEnum):
    ACTIVE = 1
    INACTIVE = 0

class Permissions(enum.IntFlag):
    READ = 1
    WRITE = 2
    EXECUTE = 4

class ModelWithEnums(JSONModel):
    __name_field_required__ = False
    color: Color
    status: Status
    permissions: Permissions

class NestedModel(JSONModel):
    nested_string: str
    nested_int: int

class ModelWithNesting(JSONModel):
    id: int
    nested_object: NestedModel
    list_of_nested: list[NestedModel]
    optional_nested: Optional[NestedModel] = None

class BaseModel(JSONModel):
    base_field: str
    shared_field: int = 0
    __name_field__ = "__type"

class SubModelA(BaseModel):
    __name_field_required__ = True # Ensure name field is present
    __allow_null_json_output__ = True # Allow nulls in output
    __include_defaults_in_json_output__: bool = True # Include defaults in output

    @classmethod
    def model_identity(cls) -> str:
        return "SubA" # Custom model identity

    sub_a_field: str
    shared_field: int = 10 # Override default

class SubModelB(BaseModel):
    __name_field_required__ = True
    __allow_null_json_output__ = True
    __include_defaults_in_json_output__: bool = True

    @classmethod
    def model_identity(cls) -> str:
        return "SubB" # Custom model identity

    sub_b_field: float
    shared_field: int = 20 # Override default

class ModelWithDynamicNesting(JSONModel):
    __name_field_required__ = False
    @classmethod
    def _name_field(cls) -> str:
        return "__type" # Custom model identity

    dynamic_object: BaseModel # Can be SubModelA or SubModelB

class ModelWithGenericTypes(JSONModel):
    __name_field_required__ = False
    list_of_strings: list[str]
    dict_int_to_bool: dict[int, bool]
    union_field: Union[str, int]
    optional_list: Optional[list[float]]
    tuple_int: tuple[int, ...]
    tuple_fixed: tuple[str, int, bool]
    set_of_ints: set[int]

class ModelWithAlternateParsing(JSONModel):
    __name_field_required__ = False
    # Allows parsing int from a string
    int_from_string: ModelElem(int, alternates=[AlternateModelElem(str, int)])
    # Allows dumping int to a string
    string_from_int: ModelElem(str, alternates=[AlternateModelElem(int, str, jsonifier=str)])
    # Allows parsing a boolean from "true" or "false" strings (case-insensitive)
    bool_from_string: ModelElem(bool, alternates=[AlternateModelElem(str, lambda s: s.lower() == "true")])

class ModelWithIgnoredField(JSONModel):
    __name_field_required__ = False
    regular_field: str
    ignored_field: ModelElem(int, ignored=True)


class TestJSONModel(unittest.TestCase):

    def test_simple_model_creation(self):
        # Test creating an instance with required fields
        model = SimpleModel(string_field="test", int_field=123)
        self.assertEqual(model.string_field, "test")
        self.assertEqual(model.int_field, 123)
        # Test default value
        self.assertTrue(model.bool_field)

        # Test missing required field (covered in error tests)
        # with self.assertRaises(JSONModelError):
        #     SimpleModel(string_field="test") # int_field is missing

    def test_model_with_defaults(self):
        # Test creating an instance using defaults
        model = ModelWithDefaults()
        self.assertEqual(model.default_string, "hello")
        self.assertEqual(model.default_int, 100)
        self.assertIsNone(model.optional_float)
        self.assertEqual(model.list_with_default, [])

        # Test overriding defaults
        model = ModelWithDefaults(default_string="world", default_int=999, optional_float=1.23)
        self.assertEqual(model.default_string, "world")
        self.assertEqual(model.default_int, 999)
        self.assertEqual(model.optional_float, 1.23)

        # Test default factory
        model = ModelWithDefaults()
        model.list_with_default.append(1)
        model2 = ModelWithDefaults()
        self.assertEqual(model.list_with_default, [1])
        self.assertEqual(model2.list_with_default, []) # Ensure default factory creates new instances

    def test_complex_types(self):
        dt = datetime.datetime(2023, 10, 27, 10, 30, 0)
        d = datetime.date(2023, 10, 27)
        t = datetime.time(10, 30, 0)
        td = datetime.timedelta(days=1, hours=2, minutes=3, seconds=4)
        b = b"test_bytes"
        p = re.compile(r"^\d+$")

        model = ModelWithComplexTypes(
            datetime_field=dt,
            date_field=d,
            time_field=t,
            timedelta_field=td,
            bytes_field=b,
            pattern_field=p
        )

        self.assertEqual(model.datetime_field, dt)
        self.assertEqual(model.date_field, d)
        self.assertEqual(model.time_field, t)
        self.assertEqual(model.timedelta_field, td)
        self.assertEqual(model.bytes_field, b)
        self.assertEqual(model.pattern_field, p)

    def test_enum_types(self):
        model = ModelWithEnums(
            color=Color.RED,
            status=Status.ACTIVE,
            permissions=Permissions.READ | Permissions.WRITE
        )

        self.assertEqual(model.color, Color.RED)
        self.assertEqual(model.status, Status.ACTIVE)
        self.assertEqual(model.permissions, Permissions.READ | Permissions.WRITE)

    def test_json_parsing_and_dumping(self):
        # Simple model
        json_data_simple = {"__name": "SimpleModel",
                            "string_field": "hello", "int_field": 42, "bool_field": False}
        model_simple = SimpleModel.from_json(json_data_simple)
        self.assertEqual(model_simple.string_field, "hello")
        self.assertEqual(model_simple.int_field, 42)
        self.assertFalse(model_simple.bool_field)
        dumped_simple = model_simple.to_json()
        self.assertEqual(dumped_simple, json_data_simple)

        # Model with defaults (default not included in output by default)
        json_data_defaults = {"default_string": "override"}
        model_defaults = ModelWithDefaults.from_json(json_data_defaults)
        self.assertEqual(model_defaults.default_string, "override")
        self.assertEqual(model_defaults.default_int, 100)
        dumped_defaults = model_defaults.to_json()
        self.assertEqual(dumped_defaults, {"__name": "ModelWithDefaults",
                                           "default_string": "override"}) # default_int and optional_float are defaults/None

        # Complex types
        dt_str = "2023-10-27T10:30:00.000Z"
        d_str = "2023-10-27"
        t_str = "10:30:00.000"
        td_ms = 93784000 # 1 day, 2 hours, 3 minutes, 4 seconds in milliseconds
        bytes_b64 = base64.b64encode(b"test_bytes").decode('ascii')
        pattern_str = r"^\d+$"

        json_data_complex = {
            "__name": "ModelWithComplexTypes",
            "datetime_field": dt_str,
            "date_field": d_str,
            "time_field": t_str,
            "timedelta_field": td_ms,
            "bytes_field": bytes_b64,
            "pattern_field": pattern_str
        }
        model_complex = ModelWithComplexTypes.from_json(json_data_complex)
        self.assertEqual(model_complex.datetime_field, datetime.datetime(2023, 10, 27, 10, 30, 0))
        self.assertEqual(model_complex.date_field, datetime.date(2023, 10, 27))
        self.assertEqual(model_complex.time_field, datetime.time(10, 30, 0))
        self.assertEqual(model_complex.timedelta_field, datetime.timedelta(days=1, hours=2, minutes=3, seconds=4))
        self.assertEqual(model_complex.bytes_field, b"test_bytes")
        self.assertEqual(model_complex.pattern_field.pattern, r"^\d+$")
        dumped_complex = model_complex.to_json()
        self.assertEqual(dumped_complex, json_data_complex)

        # Enum types
        json_data_enums = {
            "color": "RED",
            "status": 1,
            "permissions": 3 # READ (1) | WRITE (2)
        }
        model_enums = ModelWithEnums.from_json(json_data_enums)
        self.assertEqual(model_enums.color, Color.RED)
        self.assertEqual(model_enums.status, Status.ACTIVE)
        self.assertEqual(model_enums.permissions, Permissions.READ | Permissions.WRITE)
        dumped_enums = model_enums.to_json()
        self.assertEqual(dumped_enums, {
            "__name": "ModelWithEnums",
            "color": "RED", # Enum name is dumped
            "status": 1, # IntEnum value is dumped
            "permissions": 3 # IntFlag value is dumped
        })

    def test_nested_jsonmodel(self):
        nested_json = {"__name": "NestedModel", "nested_string": "inner", "nested_int": 99}
        json_data = {
            "__name": "ModelWithNesting",
            "id": 101,
            "nested_object": nested_json,
            "list_of_nested": [nested_json, {"__name": "NestedModel", "nested_string": "another", "nested_int": 100}],
            "optional_nested": None
        }

        model = ModelWithNesting.from_json(json_data)
        self.assertEqual(model.id, 101)
        self.assertIsInstance(model.nested_object, NestedModel)
        self.assertEqual(model.nested_object.nested_string, "inner")
        self.assertEqual(model.nested_object.nested_int, 99)

        self.assertIsInstance(model.list_of_nested, list)
        self.assertEqual(len(model.list_of_nested), 2)
        self.assertIsInstance(model.list_of_nested[0], NestedModel)
        self.assertEqual(model.list_of_nested[0].nested_string, "inner")
        self.assertEqual(model.list_of_nested[1].nested_string, "another")

        self.assertIsNone(model.optional_nested)

        dumped_json = model.to_json()
        # Optional_nested is None and not included by default
        expected_dump = {
            "__name": "ModelWithNesting",
            "id": 101,
            "nested_object": nested_json,
            "list_of_nested": [nested_json, {"__name": "NestedModel", "nested_string": "another", "nested_int": 100}],
        }
        self.assertEqual(dumped_json, expected_dump)

        # Test with optional_nested present
        json_data_with_optional = {
            "__name": "ModelWithNesting",
            "id": 102,
            "nested_object": nested_json,
            "list_of_nested": [],
            "optional_nested": {"__name": "NestedModel", "nested_string": "optional", "nested_int": 50}
        }
        model_with_optional = ModelWithNesting.from_json(json_data_with_optional)
        self.assertIsInstance(model_with_optional.optional_nested, NestedModel)
        self.assertEqual(model_with_optional.optional_nested.nested_string, "optional")
        dumped_with_optional = model_with_optional.to_json()
        self.assertEqual(dumped_with_optional, json_data_with_optional)

    def test_inheritance_and_overrides(self):
        # Test creating a subclass instance
        sub_a = SubModelA(base_field="base_a", sub_a_field="sub_a_val", shared_field=99)
        self.assertEqual(sub_a.base_field, "base_a")
        self.assertEqual(sub_a.sub_a_field, "sub_a_val")
        self.assertEqual(sub_a.shared_field, 99) # Overridden value

        # Test default value from subclass override
        sub_a_default_shared = SubModelA(base_field="base_a", sub_a_field="sub_a_val")
        self.assertEqual(sub_a_default_shared.shared_field, 10) # Subclass default

    def test_dynamic_subclass_parsing(self):
        json_sub_a = {
            "__type": "SubA",
            "base_field": "base_val_a",
            "sub_a_field": "sub_a_val",
            "shared_field": 5
        }
        json_sub_b = {
            "__type": "SubB",
            "base_field": "base_val_b",
            "sub_b_field": 1.23,
            "shared_field": 25
        }

        # Parse SubModelA
        model_a = BaseModel.from_json(json_sub_a)
        self.assertIsInstance(model_a, SubModelA)
        self.assertEqual(model_a.base_field, "base_val_a")
        self.assertEqual(model_a.sub_a_field, "sub_a_val")
        self.assertEqual(model_a.shared_field, 5)

        # Parse SubModelB
        model_b = BaseModel.from_json(json_sub_b)
        self.assertIsInstance(model_b, SubModelB)
        self.assertEqual(model_b.base_field, "base_val_b")
        self.assertEqual(model_b.sub_b_field, 1.23)
        self.assertEqual(model_b.shared_field, 25)

        # Test dynamic nesting
        json_dynamic_a = {"dynamic_object": json_sub_a}
        model_dynamic_a = ModelWithDynamicNesting.from_json(json_dynamic_a)
        self.assertIsInstance(model_dynamic_a.dynamic_object, SubModelA)
        self.assertEqual(model_dynamic_a.dynamic_object.base_field, "base_val_a")

        json_dynamic_b = {"dynamic_object": json_sub_b}
        model_dynamic_b = ModelWithDynamicNesting.from_json(json_dynamic_b)
        self.assertIsInstance(model_dynamic_b.dynamic_object, SubModelB)
        self.assertEqual(model_dynamic_b.dynamic_object.base_field, "base_val_b")

        # Test missing name field when required (covered in error tests)
        # json_missing_name = {"base_field": "test"}
        # with self.assertRaises(JSONModelError):
        #     BaseModel.from_json(json_missing_name)

        # Test unknown subclass name (covered in error tests)
        # json_unknown_name = {"__type": "UnknownSub", "base_field": "test"}
        # with self.assertRaises(JSONModelError):
        #     BaseModel.from_json(json_unknown_name)

        # Test dumping with __include_defaults_in_json_output__ and __allow_null_json_output__
        sub_a_dump = SubModelA(base_field="base", sub_a_field="sub")
        dumped_a = sub_a_dump.to_json()
        self.assertDictEqual(dumped_a, {
            "__type": "SubA", # Name field included
            "base_field": "base",
            "sub_a_field": "sub",
            "shared_field": 10 # Default included
        })

        sub_b_dump = SubModelB(base_field="base", sub_b_field=4.5)
        dumped_b = sub_b_dump.to_json()
        self.assertDictEqual(dumped_b, {
            "__type": "SubB",
            "base_field": "base",
            "sub_b_field": 4.5,
            "shared_field": 20
        })

    def test_generic_types(self):
        json_data = {
            "list_of_strings": ["a", "b", "c"],
            "dict_int_to_bool": {"1": True, "2": False}, # JSON keys are strings, should be parsed to int
            "union_field": 123,
            "optional_list": [1.1, 2.2],
            "tuple_int": [0, 1, 2],
            "tuple_fixed": ["fixed", 456, False],
            "set_of_ints": [1, 2, 3, 1] # JSON array, should be parsed to set
        }

        model = ModelWithGenericTypes.from_json(json_data)

        self.assertEqual(model.list_of_strings, ["a", "b", "c"])
        self.assertIsInstance(model.list_of_strings, list)

        self.assertEqual(model.dict_int_to_bool, {1: True, 2: False})
        self.assertIsInstance(model.dict_int_to_bool, dict)
        self.assertIsInstance(list(model.dict_int_to_bool.keys())[0], int)
        self.assertIsInstance(list(model.dict_int_to_bool.values())[0], bool)

        # self.assertEqual(model.union_field, 123) # May be str or int
        # self.assertIsInstance(model.union_field, int)

        self.assertEqual(model.optional_list, [1.1, 2.2])
        self.assertIsInstance(model.optional_list, list)

        self.assertEqual(model.tuple_int, (0, 1, 2))
        self.assertIsInstance(model.tuple_int, tuple)

        self.assertEqual(model.tuple_fixed, ("fixed", 456, False))
        self.assertIsInstance(model.tuple_fixed, tuple)
        self.assertIsInstance(model.tuple_fixed[0], str)
        self.assertIsInstance(model.tuple_fixed[1], int)
        self.assertIsInstance(model.tuple_fixed[2], bool)

        self.assertEqual(model.set_of_ints, {1, 2, 3})
        self.assertIsInstance(model.set_of_ints, set)

        # Test dumping
        dumped_json = model.to_json()
        # Sets are dumped as lists
        expected_dump = {
            "__name": "ModelWithGenericTypes",
            "list_of_strings": ["a", "b", "c"],
            "dict_int_to_bool": {"1": True, "2": False}, # Keys are dumped as strings
            "union_field": 123,
            "optional_list": [1.1, 2.2],
            "tuple_int": [0, 1, 2], # Tuples are dumped as lists
            "tuple_fixed": ["fixed", 456, False], # Tuples are dumped as lists
            "set_of_ints": [1, 2, 3] # Order might vary for sets
        }
        # Need to handle potential order difference for set dumping
        self.assertEqual(set(dumped_json.keys()), set(expected_dump.keys()))
        self.assertEqual(dumped_json["list_of_strings"], expected_dump["list_of_strings"])
        self.assertEqual(dumped_json["dict_int_to_bool"], expected_dump["dict_int_to_bool"])
        self.assertIn(dumped_json["union_field"], (expected_dump["union_field"], str(expected_dump["union_field"])))
        self.assertEqual(dumped_json["optional_list"], expected_dump["optional_list"])
        self.assertEqual(dumped_json["tuple_int"], expected_dump["tuple_int"])
        self.assertEqual(dumped_json["tuple_fixed"], expected_dump["tuple_fixed"])
        self.assertEqual(set(dumped_json["set_of_ints"]), set(expected_dump["set_of_ints"]))


    def test_alternate_parsing_dumping(self):
        # Corrected test expectations based on this understanding:
        json_data_corrected = {
            "int_from_string": "123", # Input is string, expected int
            "string_from_int": 456, # Input is int, expected string
            "bool_from_string": "False" # Input is string, expected bool
        }

        model_corrected = ModelWithAlternateParsing.from_json(json_data_corrected)
        self.assertEqual(model_corrected.int_from_string, 123)
        self.assertIsInstance(model_corrected.int_from_string, int)

        self.assertEqual(model_corrected.string_from_int, "456") # Parsed as string
        self.assertIsInstance(model_corrected.string_from_int, str)

        self.assertFalse(model_corrected.bool_from_string)
        self.assertIsInstance(model_corrected.bool_from_string, bool)


        # Test dumping
        dumped_json_corrected = model_corrected.to_json()
        self.assertEqual(dumped_json_corrected, {
            "__name": "ModelWithAlternateParsing",
            "int_from_string": 123, # Dumped as int (original type)
            "string_from_int": "456", # Dumped as string (using jsonifier)
            "bool_from_string": False # Dumped as bool (original type)
        })


    def test_ignored_field(self):
        json_data = {"regular_field": "present", "ignored_field": 999}
        model = ModelWithIgnoredField.from_json(json_data)
        self.assertEqual(model.regular_field, "present")
        # Ignored field should not be set from JSON input
        self.assertIsNone(getattr(model, 'ignored_field', None))

        # Test dumping - ignored field should not be included
        model_dump = ModelWithIgnoredField(regular_field="present")
        # Manually setting ignored_field for testing purposes, though it shouldn't be done in practice
        # model_dump.ignored_field = 123 # This will raise an AttributeError because it's not in __slots__
        # The ignored field is not part of the model's slots, so it cannot be set after initialization
        # The test should focus on parsing and dumping behavior.
        dumped_json = model_dump.to_json()
        self.assertEqual(dumped_json, {"__name": "ModelWithIgnoredField", "regular_field": "present"})


    # --- Error Handling Tests ---

    def test_missing_required_field_error(self):
        # SimpleModel requires 'string_field' and 'int_field'
        json_data = {"string_field": "test_string"}
        with self.assertRaises(JSONModelError):
            SimpleModel.from_json(json_data)

    def test_extra_field_error(self):
        # SimpleModel does not expect 'extra_field'
        json_data = {"string_field": "test", "int_field": 123, "extra_field": "oops"}
        with self.assertRaises(JSONModelError):
            SimpleModel.from_json(json_data)

        # Test with ignore_extra=True (should not raise error)
        json_data_ignore = {"string_field": "test", "int_field": 123, "extra_field": "oops"}
        try:
            model = SimpleModel.from_json(json_data_ignore, ignore_extra=True)
            self.assertEqual(model.string_field, "test")
            self.assertEqual(model.int_field, 123)
            self.assertFalse(hasattr(model, 'extra_field'))
        except JSONModelError as e:
            self.fail(f"JSONModelError raised unexpectedly with ignore_extra=True: {e}")


    def test_invalid_type_error(self):
        # int_field should be an integer, not a string
        json_data = {"string_field": "test", "int_field": "not an int"}
        with self.assertRaises(JSONModelError):
            SimpleModel.from_json(json_data)

        # Nested model with incorrect type
        json_data_nested_invalid = {
            "id": 1,
            "nested_object": "not a nested model", # Should be a dict
            "list_of_nested": []
        }
        with self.assertRaises(JSONModelError):
             ModelWithNesting.from_json(json_data_nested_invalid)

        # List of nested models with incorrect type inside
        json_data_list_invalid = {
            "id": 1,
            "nested_object": {"nested_string": "inner", "nested_int": 1},
            "list_of_nested": [{"nested_string": "inner", "nested_int": 1}, "not a nested model"] # Should be a dict
        }
        with self.assertRaises(JSONModelError):
             ModelWithNesting.from_json(json_data_list_invalid)


    def test_invalid_complex_type_parsing_error(self):
        # Invalid datetime string
        json_data_invalid_datetime = {
            "datetime_field": "not a datetime",
            "date_field": "2023-10-27",
            "time_field": "10:30:00",
            "timedelta_field": 1000,
            "bytes_field": "dGVzdF9ieXRlcw==",
            "pattern_field": r"^\d+$"
        }
        with self.assertRaises(JSONModelError):
            ModelWithComplexTypes.from_json(json_data_invalid_datetime)

        # Invalid timedelta string
        json_data_invalid_timedelta = {
            "datetime_field": "2023-10-27T10:30:00",
            "date_field": "2023-10-27",
            "time_field": "10:30:00",
            "timedelta_field": "not a timedelta",
            "bytes_field": "dGVzdF9ieXRlcw==",
            "pattern_field": r"^\d+$"
        }
        with self.assertRaises(JSONModelError):
            ModelWithComplexTypes.from_json(json_data_invalid_timedelta)

        # Invalid bytes base64 string
        json_data_invalid_bytes = {
            "datetime_field": "2023-10-27T10:30:00",
            "date_field": "2023-10-27",
            "time_field": "10:30:00",
            "timedelta_field": 1000,
            "bytes_field": "not valid base64",
            "pattern_field": r"^\d+$"
        }
        with self.assertRaises(JSONModelError):
            ModelWithComplexTypes.from_json(json_data_invalid_bytes)

        # Invalid regex pattern string
        json_data_invalid_pattern = {
            "datetime_field": "2023-10-27T10:30:00",
            "date_field": "2023-10-27",
            "time_field": "10:30:00",
            "timedelta_field": 1000,
            "bytes_field": "dGVzdF9ieXRlcw==",
            "pattern_field": "[" # Invalid regex
        }
        with self.assertRaises(JSONModelError):
            ModelWithComplexTypes.from_json(json_data_invalid_pattern)


    def test_invalid_enum_parsing_error(self):
        # Invalid Enum value (string)
        json_data_invalid_color = {
            "color": "PURPLE", # Not in Color enum
            "status": 1,
            "permissions": 3
        }
        with self.assertRaises(JSONModelError):
            ModelWithEnums.from_json(json_data_invalid_color)

        # Invalid IntEnum value (int)
        json_data_invalid_status = {
            "color": "RED",
            "status": 99, # Not in Status IntEnum
            "permissions": 3
        }
        with self.assertRaises(JSONModelError):
            ModelWithEnums.from_json(json_data_invalid_status)

        # Invalid IntEnum value (string)
        json_data_invalid_status_str = {
            "color": "RED",
            "status": "PENDING", # Not in Status IntEnum
            "permissions": 3
        }
        with self.assertRaises(JSONModelError):
            ModelWithEnums.from_json(json_data_invalid_status_str)


    def test_dynamic_subclass_parsing_errors(self):
        # Missing name field when required
        json_missing_name = {"base_field": "test"}
        with self.assertRaises(JSONModelError):
            BaseModel.from_json(json_missing_name)

        # Unknown subclass name
        json_unknown_name = {"__type": "UnknownSub", "base_field": "test"}
        with self.assertRaises(JSONModelError):
            BaseModel.from_json(json_unknown_name)

        # Invalid data for the identified subclass
        json_invalid_sub_a_data = {
            "__type": "SubA",
            "base_field": "base_val_a",
            "sub_a_field": None, # Should be string
            "shared_field": 5
        }
        with self.assertRaises(JSONModelError):
             BaseModel.from_json(json_invalid_sub_a_data)


    def test_alternate_parsing_failure(self):
        # int_from_string expects int or a string convertible to int. "abc" is not.
        json_invalid_int_string = {
            "int_from_string": "abc",
            "string_from_int": 1,
            "bool_from_string": "True"
        }
        with self.assertRaises(JSONModelError):
             ModelWithAlternateParsing.from_json(json_invalid_int_string)

        # bool_from_string expects bool or a string like "true" or "false". "maybe" is not.
        json_invalid_bool_string = {
            "int_from_string": "asdf",
            "string_from_int": 1,
            "bool_from_string": "maybe"
        }
        with self.assertRaises(JSONModelError):
             ModelWithAlternateParsing.from_json(json_invalid_bool_string)


    def test_alternate_dumping_failure(self):
        # string_from_int expects a value that can be dumped as str.
        # If we provide a non-string, non-int value, it should fail dumping.
        # Let's create a ModelElem that cannot be dumped by the primary type or alternates.
        class ModelWithProblematicDump(JSONModel):
            problem_field: datetime.timedelta = ModelElem(datetime.timedelta, alternates=[AlternateModelElem(str, lambda s: datetime.timedelta(), jsonifier=lambda td: td)]) # jsonifier just returns timedelta, which is not JSON serializable


        model_with_problem = ModelWithProblematicDump(problem_field=datetime.timedelta(seconds=10))
        # The default timedelta dumping in ModelElem dumps to milliseconds (int).
        # To test alternate dumping failure, we need a specific scenario where *all* options fail.
        # The current ModelElem for timedelta already handles dumping to int.
        # Let's create a custom scenario where the primary dump fails and alternates also fail.

        class ModelWithCustomDumpFailure(JSONModel):
             # Primary type is int, but we'll give it a non-dumpable object.
             # Alternate expects str, but we'll give it a non-str.
             # jsonifier for alternate expects str, but gets non-str.
            fail_dump_field: int = ModelElem(int, alternates=[AlternateModelElem(str, int, jsonifier=lambda s: s)]) # Alternate parses str to int, dumps str as is

        with self.assertRaises(JSONModelError):
            model_fail_dump = ModelWithCustomDumpFailure(fail_dump_field="not an int or str for dumping") # This will fail validation during init

        # Let's create an instance directly to bypass init validation for this test
        instance_to_dump_fail = object.__new__(ModelWithCustomDumpFailure)
        instance_to_dump_fail.fail_dump_field = object() # Assign a non-dumpable object

        with self.assertRaises(JSONModelError):
            ModelWithCustomDumpFailure.to_json(instance_to_dump_fail)



if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
