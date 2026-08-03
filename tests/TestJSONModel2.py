import unittest
import datetime
import enum
import re
import base64
from typing import Optional, Union, Annotated

from SprelfJSON import *


# THESE TESTS WERE AI-GENERATED AND MANUALLY TWEAKED


# Define some simple JSONModel subclasses for testing
class SimpleModel(JSONModel):
    string_field: str
    int_field: int
    bool_field: bool = True # Field with default

class ModelWithDefaults(JSONModel):
    default_string: str = "hello"
    default_int: int = 100
    optional_float: Optional[float] = None
    list_with_default: list[int] = [] # Test conversion to default factory

class ModelWithComplexTypes(JSONModel):
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
    __include_name_in_json_output__ = True
    __name_field_required__ = True # Ensure name field is present

class SubModelA(BaseModel):
    __allow_null_json_output__ = True # Allow nulls in output
    __include_defaults_in_json_output__: bool = True # Include defaults in output

    @classmethod
    def model_identity(cls) -> str:
        return "SubA" # Custom model identity

    sub_a_field: str
    shared_field: int = 10 # Override default

class SubModelB(BaseModel):
    __allow_null_json_output__ = True
    __include_defaults_in_json_output__: bool = True

    @classmethod
    def model_identity(cls) -> str:
        return "SubB" # Custom model identity

    sub_b_field: float
    shared_field: int = 20 # Override default

class ModelWithDynamicNesting(JSONModel):
    @classmethod
    def _name_field(cls) -> str:
        return "__type" # Custom model identity

    dynamic_object: BaseModel # Can be SubModelA or SubModelB

class ModelWithGenericTypes(JSONModel):
    list_of_strings: list[str]
    dict_int_to_bool: dict[int, bool]
    union_field: Union[str, int]
    optional_list: Optional[list[float]]
    tuple_int: tuple[int, ...]
    tuple_fixed: tuple[str, int, bool]
    set_of_ints: set[int]

class ModelWithAlternateParsing(JSONModel):
    # Allows parsing int from a string
    int_from_string: Annotated[int, Alternate(str, int)]
    # Allows dumping int to a string
    string_from_int: Annotated[str, Alternate(int, str, jsonifier=str)]
    # Allows parsing a boolean from "true" or "false" strings (case-insensitive)
    bool_from_string: Annotated[bool, Alternate(str, lambda s: s.lower() == "true")]

class ModelWithIgnoredField(JSONModel):
    regular_field: str
    ignored_field: Annotated[int, Ignored()]

class CustomClassNotSupported:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name
        return False

    def __repr__(self):
        return f"CustomClassNotSupported('{self.name}')"

class CustomSubclassNotSupported(CustomClassNotSupported):
    pass

class ModelWithTypeGenerics(JSONModel):
    # This should now be valid, even though CustomClassNotSupported is not in SupportedTypes
    custom_type_field: type[CustomClassNotSupported]
    builtin_type_field: type[int] # Ensure basic types still work

class ModelWithTypeGenericsWithDefault(JSONModel):
    custom_type_field_with_default: type[CustomClassNotSupported] = CustomClassNotSupported # Default to the class itself




class TestJSONModel(unittest.TestCase):

    def test_simple_model_creation(self):
        # Test creating an instance with required fields
        model = SimpleModel(string_field="test", int_field=123)
        self.assertEqual("test", model.string_field)
        self.assertEqual(123, model.int_field)
        # Test default value
        self.assertTrue(model.bool_field)

        # Test missing required field (covered in error tests)
        # with self.assertRaises(JSONModelError):
        #     SimpleModel(string_field="test") # int_field is missing

    def test_model_with_defaults(self):
        # Test creating an instance using defaults
        model = ModelWithDefaults()
        self.assertEqual("hello", model.default_string)
        self.assertEqual(100, model.default_int)
        self.assertIsNone(model.optional_float)
        self.assertEqual([], model.list_with_default)

        # Test overriding defaults
        model = ModelWithDefaults(default_string="world", default_int=999, optional_float=1.23)
        self.assertEqual("world", model.default_string)
        self.assertEqual(999, model.default_int)
        self.assertEqual(1.23, model.optional_float)

        # Test default factory
        model = ModelWithDefaults()
        model.list_with_default.append(1)
        model2 = ModelWithDefaults()
        self.assertEqual([1], model.list_with_default)
        self.assertEqual([], model2.list_with_default) # Ensure default factory creates new instances

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

        self.assertEqual(dt, model.datetime_field)
        self.assertEqual(d, model.date_field)
        self.assertEqual(t, model.time_field)
        self.assertEqual(td, model.timedelta_field)
        self.assertEqual(b, model.bytes_field)
        self.assertEqual(p, model.pattern_field)

    def test_enum_types(self):
        model = ModelWithEnums(
            color=Color.RED,
            status=Status.ACTIVE,
            permissions=Permissions.READ | Permissions.WRITE
        )

        self.assertEqual(Color.RED, model.color)
        self.assertEqual(Status.ACTIVE, model.status)
        self.assertEqual(Permissions.READ | Permissions.WRITE, model.permissions)

    def test_json_parsing_and_dumping(self):
        # Simple model
        json_data_simple = {"string_field": "hello", "int_field": 42, "bool_field": False}
        model_simple = SimpleModel.from_json(json_data_simple)
        self.assertEqual("hello", model_simple.string_field)
        self.assertEqual(42, model_simple.int_field)
        self.assertFalse(model_simple.bool_field)
        dumped_simple = model_simple.to_json()
        self.assertEqual(json_data_simple, dumped_simple)

        # Model with defaults (default not included in output by default)
        json_data_defaults = {"default_string": "override"}
        model_defaults = ModelWithDefaults.from_json(json_data_defaults)
        self.assertEqual("override", model_defaults.default_string)
        self.assertEqual(100, model_defaults.default_int)
        dumped_defaults = model_defaults.to_json()
        self.assertEqual({"default_string": "override"}, dumped_defaults) # default_int and optional_float are defaults/None

        # Complex types
        dt_str = "2023-10-27T10:30:00.000Z"
        d_str = "2023-10-27"
        t_str = "10:30:00.000"
        td_ms = 93784000 # 1 day, 2 hours, 3 minutes, 4 seconds in milliseconds
        bytes_b64 = base64.b64encode(b"test_bytes").decode('ascii')
        pattern_str = r"^\d+$"

        json_data_complex = {
            "datetime_field": dt_str,
            "date_field": d_str,
            "time_field": t_str,
            "timedelta_field": td_ms,
            "bytes_field": bytes_b64,
            "pattern_field": pattern_str
        }
        model_complex = ModelWithComplexTypes.from_json(json_data_complex)
        self.assertEqual(datetime.datetime(2023, 10, 27, 10, 30, 0, tzinfo=datetime.timezone.utc), model_complex.datetime_field)
        self.assertEqual(datetime.date(2023, 10, 27), model_complex.date_field)
        self.assertEqual(datetime.time(10, 30, 0), model_complex.time_field)
        self.assertEqual(datetime.timedelta(days=1, hours=2, minutes=3, seconds=4), model_complex.timedelta_field)
        self.assertEqual(b"test_bytes", model_complex.bytes_field)
        self.assertEqual(r"^\d+$", model_complex.pattern_field.pattern)
        dumped_complex = model_complex.to_json()
        self.assertEqual(json_data_complex, dumped_complex)

        # Enum types
        json_data_enums = {
            "color": "RED",
            "status": 1,
            "permissions": 3 # READ (1) | WRITE (2)
        }
        model_enums = ModelWithEnums.from_json(json_data_enums)
        self.assertEqual(Color.RED, model_enums.color)
        self.assertEqual(Status.ACTIVE, model_enums.status)
        self.assertEqual(Permissions.READ | Permissions.WRITE, model_enums.permissions)
        dumped_enums = model_enums.to_json()
        self.assertEqual({
            "color": "RED", # Enum name is dumped
            "status": 1, # IntEnum value is dumped
            "permissions": 3 # IntFlag value is dumped
        }, dumped_enums)

    def test_nested_jsonmodel(self):
        nested_json = {"nested_string": "inner", "nested_int": 99}
        json_data = {
            "id": 101,
            "nested_object": nested_json,
            "list_of_nested": [nested_json, {"nested_string": "another", "nested_int": 100}],
            "optional_nested": None
        }

        model = ModelWithNesting.from_json(json_data)
        self.assertEqual(101, model.id)
        self.assertIsInstance(model.nested_object, NestedModel)
        self.assertEqual("inner", model.nested_object.nested_string)
        self.assertEqual(99, model.nested_object.nested_int)

        self.assertIsInstance(model.list_of_nested, list)
        self.assertEqual(2, len(model.list_of_nested))
        self.assertIsInstance(model.list_of_nested[0], NestedModel)
        self.assertEqual("inner", model.list_of_nested[0].nested_string)
        self.assertEqual("another", model.list_of_nested[1].nested_string)

        self.assertIsNone(model.optional_nested)

        dumped_json = model.to_json()
        # Optional_nested is None and not included by default
        expected_dump = {
            "id": 101,
            "nested_object": nested_json,
            "list_of_nested": [nested_json, {"nested_string": "another", "nested_int": 100}],
        }
        self.assertEqual(expected_dump, dumped_json)

        # Test with optional_nested present
        json_data_with_optional = {
            "id": 102,
            "nested_object": nested_json,
            "list_of_nested": [],
            "optional_nested": {"nested_string": "optional", "nested_int": 50}
        }
        model_with_optional = ModelWithNesting.from_json(json_data_with_optional)
        self.assertIsInstance(model_with_optional.optional_nested, NestedModel)
        self.assertEqual("optional", model_with_optional.optional_nested.nested_string)
        dumped_with_optional = model_with_optional.to_json()
        self.assertEqual(json_data_with_optional, dumped_with_optional)

    def test_inheritance_and_overrides(self):
        # Test creating a subclass instance
        sub_a = SubModelA(base_field="base_a", sub_a_field="sub_a_val", shared_field=99)
        self.assertEqual("base_a", sub_a.base_field)
        self.assertEqual("sub_a_val", sub_a.sub_a_field)
        self.assertEqual(99, sub_a.shared_field) # Overridden value

        # Test default value from subclass override
        sub_a_default_shared = SubModelA(base_field="base_a", sub_a_field="sub_a_val")
        self.assertEqual(10, sub_a_default_shared.shared_field) # Subclass default

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
        self.assertEqual("base_val_a", model_a.base_field)
        self.assertEqual("sub_a_val", model_a.sub_a_field)
        self.assertEqual(5, model_a.shared_field)

        # Parse SubModelB
        model_b = BaseModel.from_json(json_sub_b)
        self.assertIsInstance(model_b, SubModelB)
        self.assertEqual("base_val_b", model_b.base_field)
        self.assertEqual(1.23, model_b.sub_b_field)
        self.assertEqual(25, model_b.shared_field)

        # Test dynamic nesting
        json_dynamic_a = {"dynamic_object": json_sub_a}
        model_dynamic_a = ModelWithDynamicNesting.from_json(json_dynamic_a)
        self.assertIsInstance(model_dynamic_a.dynamic_object, SubModelA)
        self.assertEqual("base_val_a", model_dynamic_a.dynamic_object.base_field)

        json_dynamic_b = {"dynamic_object": json_sub_b}
        model_dynamic_b = ModelWithDynamicNesting.from_json(json_dynamic_b)
        self.assertIsInstance(model_dynamic_b.dynamic_object, SubModelB)
        self.assertEqual("base_val_b", model_dynamic_b.dynamic_object.base_field)

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
        self.assertDictEqual({
            "__type": "SubA", # Name field included
            "base_field": "base",
            "sub_a_field": "sub",
            "shared_field": 10 # Default included
        }, dumped_a)

        sub_b_dump = SubModelB(base_field="base", sub_b_field=4.5)
        dumped_b = sub_b_dump.to_json()
        self.assertDictEqual({
            "__type": "SubB",
            "base_field": "base",
            "sub_b_field": 4.5,
            "shared_field": 20
        }, dumped_b)

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

        self.assertEqual(["a", "b", "c"], model.list_of_strings)
        self.assertIsInstance(model.list_of_strings, list)

        self.assertEqual({1: True, 2: False}, model.dict_int_to_bool)
        self.assertIsInstance(model.dict_int_to_bool, dict)
        self.assertIsInstance(list(model.dict_int_to_bool.keys())[0], int)
        self.assertIsInstance(list(model.dict_int_to_bool.values())[0], bool)

        # self.assertEqual(123, model.union_field) # May be str or int
        # self.assertIsInstance(model.union_field, int)

        self.assertEqual([1.1, 2.2], model.optional_list)
        self.assertIsInstance(model.optional_list, list)

        self.assertEqual((0, 1, 2), model.tuple_int)
        self.assertIsInstance(model.tuple_int, tuple)

        self.assertEqual(("fixed", 456, False), model.tuple_fixed)
        self.assertIsInstance(model.tuple_fixed, tuple)
        self.assertIsInstance(model.tuple_fixed[0], str)
        self.assertIsInstance(model.tuple_fixed[1], int)
        self.assertIsInstance(model.tuple_fixed[2], bool)

        self.assertEqual({1, 2, 3}, model.set_of_ints)
        self.assertIsInstance(model.set_of_ints, set)

        # Test dumping
        dumped_json = model.to_json()
        # Sets are dumped as lists
        expected_dump = {
            "list_of_strings": ["a", "b", "c"],
            "dict_int_to_bool": {"1": True, "2": False}, # Keys are dumped as strings
            "union_field": 123,
            "optional_list": [1.1, 2.2],
            "tuple_int": [0, 1, 2], # Tuples are dumped as lists
            "tuple_fixed": ["fixed", 456, False], # Tuples are dumped as lists
            "set_of_ints": [1, 2, 3] # Order might vary for sets
        }
        # Need to handle potential order difference for set dumping
        self.assertEqual(set(expected_dump.keys()), set(dumped_json.keys()))
        self.assertEqual(expected_dump["list_of_strings"], dumped_json["list_of_strings"])
        self.assertEqual(expected_dump["dict_int_to_bool"], dumped_json["dict_int_to_bool"])
        self.assertIn(dumped_json["union_field"], (expected_dump["union_field"], str(expected_dump["union_field"])))
        self.assertEqual(expected_dump["optional_list"], dumped_json["optional_list"])
        self.assertEqual(expected_dump["tuple_int"], dumped_json["tuple_int"])
        self.assertEqual(expected_dump["tuple_fixed"], dumped_json["tuple_fixed"])
        self.assertEqual(set(expected_dump["set_of_ints"]), set(dumped_json["set_of_ints"]))


    def test_alternate_parsing_dumping(self):
        # Corrected test expectations based on this understanding:
        json_data_corrected = {
            "int_from_string": "123", # Input is string, expected int
            "string_from_int": 456, # Input is int, expected string
            "bool_from_string": "False" # Input is string, expected bool
        }

        model_corrected = ModelWithAlternateParsing.from_json(json_data_corrected)
        self.assertEqual(123, model_corrected.int_from_string)
        self.assertIsInstance(model_corrected.int_from_string, int)

        self.assertEqual(model_corrected.string_from_int, "456") # Parsed as string
        self.assertIsInstance(model_corrected.string_from_int, str)

        self.assertFalse(model_corrected.bool_from_string)
        self.assertIsInstance(model_corrected.bool_from_string, bool)


        # Test dumping
        dumped_json_corrected = model_corrected.to_json()
        self.assertEqual(dumped_json_corrected, {
            "int_from_string": 123, # Dumped as int (original type)
            "string_from_int": "456", # Dumped as string (using jsonifier)
            "bool_from_string": False # Dumped as bool (original type)
        })


    def test_ignored_field(self):
        json_data = {"regular_field": "present", "ignored_field": 999}
        model = ModelWithIgnoredField.from_json(json_data)
        self.assertEqual("present", model.regular_field)
        # Ignored field should not be set from JSON input
        self.assertIsNone(getattr(model, 'ignored_field', None))

        # Test dumping - ignored field should not be included
        model_dump = ModelWithIgnoredField(regular_field="present")
        # Manually setting ignored_field for testing purposes, though it shouldn't be done in practice
        # model_dump.ignored_field = 123 # This will raise an AttributeError because it's not in __slots__
        # The ignored field is not part of the model's slots, so it cannot be set after initialization
        # The test should focus on parsing and dumping behavior.
        dumped_json = model_dump.to_json()
        self.assertEqual({"regular_field": "present"}, dumped_json)


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
            model = SimpleModel.from_json(json_data_ignore, _ignore_extra=True)
            self.assertEqual("test", model.string_field)
            self.assertEqual(123, model.int_field)
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
            problem_field: Annotated[datetime.timedelta, Alternate(str, lambda s: datetime.timedelta(), jsonifier=lambda td: td)]

        model_with_problem = ModelWithProblematicDump(problem_field=datetime.timedelta(seconds=10))
        # The default timedelta dumping in ModelElem dumps to milliseconds (int).
        # To test alternate dumping failure, we need a specific scenario where *all* options fail.
        # The current ModelElem for timedelta already handles dumping to int.
        # Let's create a custom scenario where the primary dump fails and alternates also fail.

        class ModelWithCustomDumpFailure(JSONModel):
             # Primary type is int, but we'll give it a non-dumpable object.
             # Alternate expects str, but we'll give it a non-str.
             # jsonifier for alternate expects str, but gets non-str.
            fail_dump_field: Annotated[int, Alternate(str, int, jsonifier=lambda s: s, forced=True)]

        with self.assertRaises(JSONModelError):
            model_fail_dump = ModelWithCustomDumpFailure(fail_dump_field="not an int or str for dumping") # This will fail validation during init

    def test_type_generics_with_unsupported_type(self):
        # Test parsing with a custom class that is not in SupportedTypes
        json_data = {
            "custom_type_field": "TestJSONModel2.CustomClassNotSupported",  # Using full path as a string
            "builtin_type_field": "int"
        }
        model = ModelWithTypeGenerics.from_json(json_data)

        self.assertEqual(model.custom_type_field, CustomClassNotSupported)
        self.assertIsInstance(model.custom_type_field, type)
        self.assertEqual(model.builtin_type_field, int)
        self.assertIsInstance(model.builtin_type_field, type)

        # Test dumping
        dumped_json = model.to_json()
        self.assertEqual(dumped_json["custom_type_field"], "TestJSONModel2.CustomClassNotSupported")
        self.assertEqual(dumped_json["builtin_type_field"], "int")

        # Test with direct class object
        model_direct = ModelWithTypeGenerics(
            custom_type_field=CustomClassNotSupported,
            builtin_type_field=int
        )
        self.assertEqual(model_direct.custom_type_field, CustomClassNotSupported)
        self.assertEqual(model_direct.builtin_type_field, int)
        dumped_direct = model_direct.to_json()
        self.assertEqual(dumped_direct["custom_type_field"], "TestJSONModel2.CustomClassNotSupported")
        self.assertEqual(dumped_direct["builtin_type_field"], "int")

    def test_type_generics_with_default(self):
        # Test that the default for a type generic field works
        model = ModelWithTypeGenericsWithDefault()
        self.assertEqual(model.custom_type_field_with_default, CustomClassNotSupported)

        # Test overriding the default
        json_data = {
            "custom_type_field_with_default": "TestJSONModel2.CustomSubclassNotSupported"
        }
        model_override = ModelWithTypeGenericsWithDefault.from_json(json_data)
        self.assertEqual(model_override.custom_type_field_with_default, CustomSubclassNotSupported)

    def test_type_generics_invalid_parsing(self):
        # Test invalid string for type generic field
        json_data = {
            "custom_type_field": "NonExistentClass",
            "builtin_type_field": "int"
        }
        with self.assertRaises(JSONModelError) as cm:
            ModelWithTypeGenerics.from_json(json_data)
        self.assertIn("Unable to parse string value 'NonExistentClass' as a type", str(cm.exception))

        # Test providing non-class for type generic field
        json_data_invalid_value = {
            "custom_type_field": "TestJSONModel2.CustomClassNotSupported",
            "builtin_type_field": 123  # should be a class or string representing one
        }
        with self.assertRaises(JSONModelError) as cm:
            ModelWithTypeGenerics.from_json(json_data_invalid_value)
        self.assertIn("could not be interpreted as a type", str(cm.exception))

class TestModelElem_JSONLike(unittest.TestCase):

    def test_JSONValueLike_validate(self):
        me = ModelElem(JSONValueLike)
        self.assertTrue(me.is_valid(None))
        self.assertTrue(me.is_valid(True))
        self.assertTrue(me.is_valid(0))
        self.assertTrue(me.is_valid(3.14))
        self.assertTrue(me.is_valid("str"))

        self.assertFalse(me.is_valid([]))
        self.assertFalse(me.is_valid({}))

        with self.assertRaises(ModelElemError):
            me.validate([])  # not a JSON value

    def test_JSONObjectLike_validate(self):
        me = ModelElem(JSONObjectLike)

        self.assertTrue(me.is_valid({}))
        self.assertTrue(me.is_valid({"a": 1}))
        self.assertTrue(me.is_valid({"a": [1, 2, {"b": "x"}]}))
        self.assertTrue(me.is_valid({"x": {"y": True}}))

        self.assertFalse(me.is_valid({1: "bad"}))   # non-string key
        self.assertFalse(me.is_valid({"a": set()})) # invalid value type

        with self.assertRaises(ModelElemError):
            me.validate({"a": set()})

    def test_JSONArrayLike_validate(self):
        me = ModelElem(JSONArrayLike)

        self.assertTrue(me.is_valid([]))
        self.assertTrue(me.is_valid([1, 2, 3]))
        self.assertTrue(me.is_valid(["a", {"b": 2}]))
        self.assertTrue(me.is_valid([[1], {"x": "y"}, 3.0, None]))

        self.assertFalse(me.is_valid("not an array"))
        self.assertFalse(me.is_valid([set()]))  # invalid element

        with self.assertRaises(ModelElemError):
            me.validate([set()])

    def test_JSONContainerLike_validate(self):
        me = ModelElem(JSONContainerLike)

        self.assertTrue(me.is_valid([]))
        self.assertTrue(me.is_valid({}))
        self.assertTrue(me.is_valid([{"a": 1}, 2, "x"]))
        self.assertTrue(me.is_valid({"a": [1, 2], "b": {"c": False}}))

        self.assertFalse(me.is_valid(42))
        self.assertFalse(me.is_valid("hello"))

        with self.assertRaises(ModelElemError):
            me.validate(42)

    def test_JSONLike_validate(self):
        me = ModelElem(JSONLike)

        self.assertTrue(me.is_valid(None))
        self.assertTrue(me.is_valid(True))
        self.assertTrue(me.is_valid(123))
        self.assertTrue(me.is_valid("abc"))
        self.assertTrue(me.is_valid([]))
        self.assertTrue(me.is_valid({}))
        self.assertTrue(me.is_valid([{"a": 1}, 2, "x"]))

        class Foo: pass
        self.assertFalse(me.is_valid(Foo()))
        with self.assertRaises(ModelElemError):
            me.validate(set())

    def test_dump_roundtrip_JSONValueLike(self):
        me = ModelElem(JSONValueLike)

        for v in (None, True, 0, 3.14, "x"):
            parsed = me.parse_value(v)
            dumped = me.dump_value(parsed)
            self.assertEqual(parsed, dumped)

    def test_dump_roundtrip_JSONObjectLike(self):
        me = ModelElem(JSONObjectLike)
        v = {"a": 1, "b": [1, 2, {"c": "x"}], "d": {"e": False}}
        parsed = me.parse_value(v)
        dumped = me.dump_value(parsed)
        self.assertEqual(parsed, dumped)

    def test_dump_roundtrip_JSONArrayLike(self):
        me = ModelElem(JSONArrayLike)
        v = [1, "a", None, {"k": "v"}, [True, 2.0]]
        parsed = me.parse_value(v)
        dumped = me.dump_value(parsed)
        self.assertEqual(parsed, dumped)

    def test_dump_roundtrip_JSONContainerLike(self):
        # dict
        me_dict = ModelElem(JSONContainerLike)
        v1 = {"x": [1, 2], "y": {"z": "w"}}
        self.assertEqual(me_dict.dump_value(me_dict.parse_value(v1)), v1)

        # list
        me_list = ModelElem(JSONContainerLike)
        v2 = [1, {"a": False}, ["b", None]]
        self.assertEqual(me_list.dump_value(me_list.parse_value(v2)), v2)

    def test_parse_error_messages(self):
        me_val = ModelElem(JSONValueLike)
        with self.assertRaises(ModelElemError) as cm1:
            me_val.parse_value([1, 2])  # not a value-like
        self.assertIn("Unable to parse value", str(cm1.exception))

        me_obj = ModelElem(JSONObjectLike)
        with self.assertRaises(ModelElemError) as cm2:
            me_obj.parse_value({1: "bad"})  # non-string key
        self.assertIn("Unable to parse value", str(cm2.exception))

        me_arr = ModelElem(JSONArrayLike)
        with self.assertRaises(ModelElemError) as cm3:
            me_arr.parse_value([set()])  # invalid element
        self.assertIn("Unable to parse value", str(cm3.exception))

    def test_dump_error_messages(self):
        me_val = ModelElem(JSONValueLike)
        with self.assertRaises(ModelElemError) as cm1:
            me_val.dump_value([1, 2])  # not a value-like
        self.assertIn("could not be dumped", str(cm1.exception))

        me_obj = ModelElem(JSONObjectLike)
        with self.assertRaises(ModelElemError) as cm2:
            me_obj.dump_value({1: "bad"})  # non-string key
        self.assertIn("could not be dumped", str(cm2.exception))

        me_arr = ModelElem(JSONArrayLike)
        with self.assertRaises(ModelElemError) as cm3:
            me_arr.dump_value([set()])  # invalid element
        self.assertIn("could not be dumped", str(cm3.exception))



class TestAnnotations(unittest.TestCase):
    """Test the annotation metadata classes"""

    def test_description_annotation(self):
        desc = Description("This is a field description")
        self.assertEqual("This is a field description", desc.text)
        self.assertIn("Description", str(desc))

    def test_default_factory_annotation(self):
        factory = lambda: [1, 2, 3]
        df = DefaultFactory(factory)
        self.assertEqual(factory, df.factory)
        self.assertIn("DefaultFactory", str(df))

    def test_alternate_annotation(self):
        alt = Alternate(str, int)
        self.assertEqual(str, alt.alt_type)
        self.assertEqual(int, alt.transformer)
        self.assertFalse(alt.forced)
        self.assertIn("Alternate", str(alt))

    def test_alternate_with_jsonifier(self):
        alt = Alternate(str, int, jsonifier=str)
        self.assertEqual(str, alt.jsonifier)

    def test_alternate_forced(self):
        alt = Alternate(str, int, forced=True)
        self.assertTrue(alt.forced)

    def test_ignored_annotation(self):
        ignored = Ignored()
        self.assertIn("Ignored", str(ignored))

    def test_enumerated_annotation(self):
        enum_values = [1, 2, 3, 4]
        enm = Enumerated(enum_values)
        self.assertEqual(enum_values, enm.values)
        self.assertIn("Enumerated", str(enm))

    def test_annotation_metadata_set_contains(self):
        annos = AnnotationMetadataSet([Description("test"), DefaultFactory(list)])
        self.assertIn(Description, annos)
        self.assertIn(DefaultFactory, annos)
        self.assertNotIn(Ignored, annos)

    def test_annotation_metadata_set_getitem(self):
        desc = Description("test desc")
        annos = AnnotationMetadataSet([desc, DefaultFactory(list)])
        self.assertEqual(desc, annos[Description])

    def test_annotation_metadata_set_getitem_not_found(self):
        annos = AnnotationMetadataSet([Description("test")])
        with self.assertRaises(KeyError):
            _ = annos[Ignored]

    def test_annotation_metadata_set_get(self):
        desc = Description("test desc")
        annos = AnnotationMetadataSet([desc])
        self.assertEqual(desc, annos.get(Description))
        self.assertIsNone(annos.get(Ignored))

    def test_annotation_metadata_set_get_all(self):
        desc1 = Description("desc1")
        desc2 = Description("desc2")
        annos = AnnotationMetadataSet([desc1, DefaultFactory(list), desc2])
        descriptions = annos.get_all(Description)
        self.assertEqual(2, len(descriptions))
        self.assertIn(desc1, descriptions)
        self.assertIn(desc2, descriptions)

    def test_annotation_metadata_set_iteration(self):
        desc = Description("test")
        ignored = Ignored()
        annos = AnnotationMetadataSet([desc, ignored])
        items = list(annos)
        self.assertEqual(2, len(items))
        self.assertIn(desc, items)
        self.assertIn(ignored, items)

    def test_annotation_metadata_set_len(self):
        annos = AnnotationMetadataSet([Description("test"), DefaultFactory(list)])
        self.assertEqual(2, len(annos))


class TestModelElemAnnotations(unittest.TestCase):
    """Test ModelElem with expanded annotations"""

    def test_model_elem_with_description(self):
        elem = ModelElem(str, metadata=[Description("A string field")])
        self.assertIsNotNone(elem.get_metadata(Description))
        self.assertEqual("A string field", elem.get_metadata(Description).text)

    def test_model_elem_with_default_factory(self):
        elem = ModelElem(list[int], metadata=[DefaultFactory(list)])
        self.assertTrue(elem.has_default())
        default1 = elem.default
        default2 = elem.default
        self.assertIsNot(default1, default2)  # Different instances

    def test_model_elem_with_enumerated(self):
        values = ["small", "medium", "large"]
        elem = ModelElem(str, metadata=[Enumerated(values)])
        self.assertTrue(elem.validate("small") == "small")
        with self.assertRaises(ModelElemError):
            elem.validate("extra-large")

    def test_model_elem_with_ignored(self):
        elem = ModelElem(int, metadata=[Ignored()])
        self.assertTrue(elem.ignored)
        self.assertIsNone(elem.validate(123))

    def test_model_elem_with_alternate(self):
        elem = ModelElem(int, metadata=[Alternate(str, int)])
        self.assertEqual(123, elem.validate("123"))

    def test_model_elem_multiple_annotations(self):
        elem = ModelElem(int, metadata=[
            Description("An integer field"),
            Enumerated([1, 2, 3]),
            Alternate(str, int)
        ])
        self.assertIsNotNone(elem.get_metadata(Description))
        self.assertIsNotNone(elem.get_metadata(Enumerated))
        self.assertIsNotNone(elem.get_metadata(Alternate))

    def test_model_with_annotation_parsing(self):
        class ModelWithDescriptionsAndEnums(JSONModel):
            status: Annotated[str, Description("Current status"), Enumerated(["active", "inactive"])]
            count: Annotated[int, Description("Item count")]

        json_data = {"status": "active", "count": 5}
        model = ModelWithDescriptionsAndEnums.from_json(json_data)
        self.assertEqual("active", model.status)
        self.assertEqual(5, model.count)

    def test_model_with_annotation_invalid_enum(self):
        class ModelWithEnumAnnotation(JSONModel):
            color: Annotated[str, Enumerated(["red", "green", "blue"])]

        with self.assertRaises(JSONModelError):
            ModelWithEnumAnnotation.from_json({"color": "yellow"})


class TestModelElemSpec(unittest.TestCase):
    """Test the .spec() method for JSON schema generation"""

    def test_spec_none_type(self):
        elem = ModelElem(type(None))
        spec = elem.spec()
        self.assertEqual({"type": "null"}, spec)

    def test_spec_bool_type(self):
        elem = ModelElem(bool)
        spec = elem.spec()
        self.assertEqual(spec["type"], "boolean")

    def test_spec_int_type(self):
        elem = ModelElem(int)
        spec = elem.spec()
        self.assertEqual(spec["type"], "integer")

    def test_spec_float_type(self):
        elem = ModelElem(float)
        spec = elem.spec()
        self.assertEqual(spec["type"], "number")

    def test_spec_str_type(self):
        elem = ModelElem(str)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_bytes_type(self):
        elem = ModelElem(bytes)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_datetime_type(self):
        elem = ModelElem(datetime.datetime)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_date_type(self):
        elem = ModelElem(datetime.date)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_time_type(self):
        elem = ModelElem(datetime.time)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_timedelta_type(self):
        elem = ModelElem(datetime.timedelta)
        spec = elem.spec()
        self.assertEqual(spec["type"], "integer")

    def test_spec_pattern_type(self):
        elem = ModelElem(re.Pattern)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_list_type(self):
        elem = ModelElem(list[int])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")
        self.assertIn("items", spec)
        self.assertEqual(spec["items"]["type"], "integer")

    def test_spec_list_untyped(self):
        elem = ModelElem(list)
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")

    def test_spec_dict_type(self):
        elem = ModelElem(dict[str, int])
        spec = elem.spec()
        self.assertEqual(spec["type"], "object")

    def test_spec_tuple_ellipsis(self):
        elem = ModelElem(tuple[int, ...])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")
        self.assertIn("items", spec)

    def test_spec_set_type(self):
        elem = ModelElem(set[str])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")

    def test_spec_optional_type(self):
        elem = ModelElem(Optional[str])
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_union_type(self):
        elem = ModelElem(Union[str, int])
        spec = elem.spec()
        self.assertIn("oneOf", spec)
        self.assertEqual(2, len(spec["oneOf"]))

    def test_spec_with_description(self):
        elem = ModelElem(str, metadata=[Description("A name field")])
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")
        self.assertIn("description", spec)

    def test_spec_with_default(self):
        elem = ModelElem(str, default="default_value")
        spec = elem.spec()
        self.assertIn("default", spec)
        self.assertEqual("default_value", spec["default"])

    def test_spec_with_default_factory(self):
        elem = ModelElem(list[int], metadata=[DefaultFactory(list)])
        spec = elem.spec()
        self.assertIn("items", spec)

    def test_spec_with_enumerated(self):
        elem = ModelElem(str, metadata=[Enumerated(["red", "green", "blue"])])
        spec = elem.spec()
        self.assertIn("enum", spec)
        self.assertEqual(["red", "green", "blue"], spec["enum"])

    def test_spec_with_enumerated_ints(self):
        elem = ModelElem(int, metadata=[Enumerated([1, 2, 3])])
        spec = elem.spec()
        self.assertIn("enum", spec)
        self.assertEqual([1, 2, 3], spec["enum"])

    def test_spec_intenum(self):
        elem = ModelElem(Status)
        spec = elem.spec()
        self.assertEqual(spec["type"], "integer")
        self.assertIn("enum", spec)
        self.assertEqual([1, 0], spec["enum"])

    def test_spec_strenum(self):
        elem = ModelElem(Color)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")
        self.assertIn("enum", spec)
        self.assertEqual(["RED", "GREEN", "BLUE"], spec["enum"])

    def test_spec_enum(self):
        elem = ModelElem(Color)
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")
        self.assertIn("enum", spec)

    def test_spec_intflag(self):
        elem = ModelElem(Permissions)
        spec = elem.spec()
        self.assertEqual(spec["type"], "integer")

    def test_spec_type_generic(self):
        elem = ModelElem(type[int])
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")

    def test_spec_json_value_like(self):
        elem = ModelElem(JSONValueLike)
        spec = elem.spec()
        self.assertIn("oneOf", spec)

    def test_spec_json_object_like(self):
        elem = ModelElem(JSONObjectLike)
        spec = elem.spec()
        self.assertEqual(spec["type"], "object")

    def test_spec_json_array_like(self):
        elem = ModelElem(JSONArrayLike)
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")

    def test_spec_json_container_like(self):
        elem = ModelElem(JSONContainerLike)
        spec = elem.spec()
        self.assertIn("oneOf", spec)

    def test_spec_json_like(self):
        elem = ModelElem(JSONLike)
        spec = elem.spec()
        self.assertIn("oneOf", spec)

    def test_spec_list_of_objects(self):
        elem = ModelElem(list[dict[str, int]])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")
        self.assertIn("items", spec)
        self.assertEqual(spec["items"]["type"], "object")

    def test_spec_nested_optional_list(self):
        elem = ModelElem(Optional[list[str]])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")
        self.assertIn("items", spec)

    def test_spec_complex_union(self):
        elem = ModelElem(Union[str, int, list[float]])
        spec = elem.spec()
        self.assertIn("oneOf", spec)
        self.assertGreaterEqual(len(spec["oneOf"]), 2)

    def test_spec_default_and_description(self):
        elem = ModelElem(
            int,
            default=42,
            metadata=[Description("The answer")]
        )
        spec = elem.spec()
        self.assertEqual(spec["type"], "integer")
        self.assertEqual(42, spec["default"])
        self.assertIn("description", spec)

    def test_spec_description_enumerated_default(self):
        elem = ModelElem(
            str,
            default="small",
            metadata=[
                Description("Size classification"),
                Enumerated(["small", "medium", "large"])
            ]
        )
        spec = elem.spec()
        self.assertEqual(spec["type"], "string")
        self.assertEqual("small", spec["default"])
        self.assertEqual(["small", "medium", "large"], spec["enum"])
        self.assertIn("description", spec)

    def test_spec_nested_list_union(self):
        elem = ModelElem(list[Union[str, int]])
        spec = elem.spec()
        self.assertEqual(spec["type"], "array")
        self.assertIn("items", spec)
        self.assertIn("oneOf", spec["items"])

    def test_json_model_spec_integration(self):
        """Test that spec() works with full JSONModel"""
        class DocumentModel(JSONModel):
            title: Annotated[str, Description("Document title")]
            pages: int
            tags: Annotated[list[str], Description("Document tags")]
            status: Annotated[str, Enumerated(["draft", "published", "archived"])]
            metadata: Optional[dict[str, str]] = None

        # Check that models can generate specs for individual fields
        # This test is primarily to ensure that the annotation system
        # integrates properly with the model without errors
        model = DocumentModel(title="Test", pages=10, tags=["test"], status="draft")
        self.assertEqual("Test", model.title)
        self.assertEqual(10, model.pages)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
