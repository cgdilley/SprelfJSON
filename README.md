# SprelfJSON - `JSONModel`

**JSONModel** simplifies the process of working with JSON data in Python by allowing you to define the structure of your 
JSON objects using class annotations. It provides robust parsing (`from_json()`) and dumping (`to_json()`) capabilities, 
handling a variety of data types and supporting nested and polymorphic JSON structures.

## Features:

- Define JSON structure using Python class annotations.
- Automatic parsing of JSON data into Python objects.
- Automatic dumping of Python objects into JSON-compatible dictionaries.
- Support for standard Python types (`string`, `int`, `float`, `bool`, `list`, `dict`, etc.).
- Handling of additional types like `datetime`, `date`, `time`, `timedelta`, `bytes`, `re.Pattern`, `Enum`,`IntEnum`, `StrEnum`, and `IntFlag`.
- Flexibility to add support for additional data types by subclassing `ModelType`
- Seamless handling of nested `JSONModel` objects.
- Dynamic parsing of `JSONModel` subclasses based on a designated field.
- Ability to define alternate parsing and dumping logic.
- Clear error reporting for validation and parsing issues.

## Basic Usage
Define a simple JSON structure:

```python
from SprelfJSON import JSONModel

class User(JSONModel):
    name: str
    age: int
    is_active: bool = True # Field with a default value
```

Parse JSON data into a User object:

```python
json_data = {"name": "Alice", "age": 30}
user = User.from_json(json_data)

print(user.name)       # Output: Alice
print(user.age)        # Output: 30
print(user.is_active)  # Output: True (default value)

# JSON data can include the default value explicitly
json_data_with_default = {"name": "Bob", "age": 25, "is_active": False}
user_explicit = User.from_json(json_data_with_default)
print(user_explicit.is_active) # Output: False
```

Dump a User object back into JSON data:

```python
user_to_dump = User(name="Charlie", age=40, is_active=False)
dumped_data = User.to_json()

print(dumped_data) # Output: {'name': 'Charlie', 'age': 40, 'is_active': False}

# Default values are not included by default unless specified in the class
user_with_default = User(name="David", age=35)
dumped_data_default = user_with_default.to_json()
print(dumped_data_default) # Output: {'name': 'David', 'age': 35} (is_active is omitted)
```

## Defining Models
You define a JSON model by creating a class that inherits from `JSONModel` and using type annotations for the expected fields.

```python
from __future__ import annotations

from typing import Optional, Union
from SprelfJSON import JSONModel, ModelElem
import datetime

class Product(JSONModel):
    id: int
    name: str
    price: float
    tags: list[str] # List of strings
    
    attributes: dict[str, str] # Dictionary with string keys and string values
    description: Optional[str] = None # Optional field, can be None
    created_at: datetime.datetime # Using a complex type
```

## Fields with Default Values
You can provide default values directly in the class definition:

```python
class Settings(JSONModel):
    theme: str = "dark"
    notifications_enabled: bool = True
```

For mutable default values (like lists or dictionaries), use `ModelElem` with `default_factory`:

```python
class UserProfile(JSONModel):
    username: str
    favorite_numbers: ModelElem(list[int], default_factory=list) # Use default_factory for mutable defaults
```

## Handling Different Types
This library handles a variety of common datatypes, converting them to and from native JSON types when dumping and parsing.

### JSON Native Types
`str`, `int`, `float`, `bool`, `None` are parsed and dumped directly.

### Complex Types
`datetime.datetime`, `datetime.date`, `datetime.time`, `datetime.timedelta`, `bytes`, `re.Pattern` are automatically 
parsed and dumped to/from appropriate JSON representations (e.g., strings for dates/times, base64 for bytes, string for patterns).

```python
import datetime
import re

class Event(JSONModel):
    start_time: datetime.datetime
    duration: datetime.timedelta
    event_id: bytes
    pattern: re.Pattern

# Example usage
json_event = {
    "start_time": "2023-10-27T14:00:00.000Z",
    "duration": 3600000, # timedelta in milliseconds
    "event_id": "YWJjMTIz", # base64 encoded bytes
    "pattern": "^[A-Z]+$"
}
event = Event.from_json(json_event)

print(type(event.start_time).__name__)  # Output: "datetime"
print(type(event.duration).__name__)    # Output: "timedelta"
print(type(event.event_id).__name__)    # Output: "bytes"
print(type(event.pattern).__name__)     # Output: "Pattern"

dumped_event = event.to_json()
print(dumped_event)     # Output: The original JSON
```

### Enums
`enum.Enum`, `enum.IntEnum`, `enum.StrEnum`, and `enum.IntFlag` are supported. Plain Enums are dumped by name, the others by value.  They can be parsed as either.

```python
import enum

class Status(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class ErrorCode(enum.IntEnum):
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

class Flags(enum.IntFlag):
    FLAG_A = 1
    FLAG_B = 2
    FLAG_C = 4

class Task(JSONModel):
    status: Status
    error_code: Optional[ErrorCode] = None
    flags: Flags

# Example usage
json_task = {
    "status": "PROCESSING",
    "flags": 3 # FLAG_A | FLAG_B
}
task = Task.from_json(json_task)

print(task.status)      # Output: Status.PROCESSING
print(task.flags)       # Output: Flags.FLAG_A | Flags.FLAG_B

dumped_task = task.to_json()
print(dumped_task)      # Output: {'status': 'PROCESSING', 'flags': 3}
```

### Generic Types
`list`, `dict`, `set`, `tuple`, `type`, `Iterable`, `Iterator`, `Sequence`, `Mapping`, `MutableMapping`, `Collection`, `Union`, and `Optional` are supported.
`Iterable`s are not handled lazily.

```python
from __future__ import annotations
from typing import Union, Optional
from SprelfJSON import JSONModel

class DataContainer(JSONModel):
    items: list[int]
    settings: dict[str, bool]
    value: Union[str, int]
    optional_items: Optional[list[float]]
    a_type: type[JSONModel]
    coords: tuple[float, float]
    tags: set[str]

# Example usage
json_data = {
    "items": [1, 2, 3],
    "settings": {"enabled": True, "visible": False},
    "value": "hello",
    "optional_items": [1.1, 2.2],
    "a_type": "SomeJSONModelType",
    "coords": [10.5, 20.1], # JSON array is parsed as tuple
    "tags": ["tag1", "tag2", "tag1"] # JSON array is parsed as set
}
container = DataContainer.from_json(json_data)

print(type(container.items).__name__)           # Output: "list"
print(type(container.settings).__name__)        # Output: "dict"
print(type(container.value).__name__)           # Output: "str"
print(type(container.optional_items).__name__)  # Output: "list"
print(type(container.a_type).__name__)          # Output: "type"
print(type(container.coords).__name__)          # Output: "tuple"
print(type(container.tags).__name__)            # Output: "set"

dumped_data = container.to_json()
print(dumped_data) # Note: sets and tuples are dumped as JSON arrays (lists)
```

### Nested Models
You can nest `JSONModel` definitions within other `JSONModel`s.

```python
class Address(JSONModel):
    street: str
    city: str
    zip_code: str

class Order(JSONModel):
    order_num: int

class Customer(JSONModel):
    customer_id: int
    name: str
    shipping_address: Address
    past_orders: list[Order]
```

### Dynamic Subclass Parsing
`JSONModel` can automatically determine and instantiate the correct subclass based on a field in the JSON data.

Define a base class and subclasses:

```python
class Shape(JSONModel):
    # Base class - often abstract, but can have common fields
    __name_field__ = "type" # Field to check for subclass name
    __name_field_required__ = True # Require the type field

    color: str

class Circle(Shape):
    radius: float
    
    @classmethod
    def model_identity(cls) -> str:
        return "circle" # Value in the 'type' field for this subclass

class Square(Shape):
    side_length: float
    
    @classmethod
    def model_identity(cls) -> str:
        return "square" # Value in the 'type' field for this subclass

# You can then have a model containing a list of shapes
class Drawing(JSONModel):
    shapes: list[Shape] # List can contain Circle or Square objects
```

Parse JSON containing different shape types:

```python
json_drawing = {
    "shapes": [
        {"type": "circle", "color": "red", "radius": 10.0},
        {"type": "square", "color": "blue", "side_length": 5.0},
        {"type": "circle", "color": "green", "radius": 2.5}
    ]
}

drawing = Drawing.from_json(json_drawing)

for shape in drawing.shapes:
    print(f"Shape color: {shape.color}")
    if isinstance(shape, Circle):
        print(f"Circle radius: {shape.radius}")
    elif isinstance(shape, Square):
        print(f"Square side length: {shape.side_length}")

# Output:
# Shape color: red
# Circle radius: 10.0
# Shape color: blue
# Square side length: 5.0
# Shape color: green
# Circle radius: 2.5
```

### Support for Additional Types

If you want to extend the supported types, you can create a new class that is a subclass of `ModelType`, implementing
the required methods.  

```python
class ModelType_PatternExample(ModelType):

    # This is used to test whether this model type applies to the given model element.
    # The first ModelType to return True here is the one used.
    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin == re.Pattern
    
    # This is used for validating if a value in a particular field meets the criteria for this type
    @classmethod
    def is_valid(cls, val: Any, elem: _BaseModelElem, **kwargs) -> bool:
        return isinstance(val, elem.origin)

    # This is used for parsing a value to the desired type; usually is given a JSON value
    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, re.Pattern):
            return val
        if isinstance(val, str):
            return re.compile(val)
        raise ModelElemError(elem, "Woops, can't parse this!")

    # This is used to dump the value into a JSON-compatible type
    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        definitely_a_pattern_now = elem.parse_value(val, **kwargs)
        return definitely_a_pattern_now.pattern  # This is a str
```

> **Note:**
> 
>A list of all `ModelType` subclasses is cached the first time any `JSONModel` object is
>dumped, parsed, or validated.  As long as your subclass is defined before this, it will be automatically included.
>If you need further manipulation of the allowed types, see `_AliasedModelTypes` and `_ConcreteModelTypes` on `ModelElem`


### Alternate Parsing and Dumping
Use `AlternateModelElem` within a `ModelElem` definition to specify alternative ways to parse incoming data or dump outgoing data.
These objects are defined like `ModelElem`, but expect to find a different type, and define a function to convert
from that type to the original type that the `ModelElem` expects.

When parsing or dumping, it will first attempt to operate in its native type.  Only if that fails, it will then attempt
doing so with each of the defined alternate definitions.  To override this behavior and forcibly use these alternates, you 
may provide the `use_alternates_only` parameter.

```python
from SprelfJSON import JSONModel, ModelElem, AlternateModelElem

class DataItem(JSONModel):
    # Can parse an integer from a string
    count: ModelElem(int, alternates=[AlternateModelElem(str, int)])

    # Can dump a boolean as a string "true" or "false"
    is_valid: ModelElem(bool, alternates=[AlternateModelElem(str, lambda s: s.lower() == "true", jsonifier=lambda b: str(b).lower())],
                        use_alternates_only=True)

# Example usage
json_data = {
    "count": "50", # Input is string
    "is_valid": "True" # Input is string
}
item = DataItem.from_json(json_data)

print(item.count)     # Output: 50 (parsed as int)
print(item.is_valid)  # Output: True (parsed as bool)

dumped_data = item.to_json()
print(dumped_data)  # Output: {'count': 50, 'is_valid': "true"} # 'count' dumped as int, 'is_valid' dumped as string
```

## Error Handling
`JSONModel` uses `JSONModelError` and a subclass `ModelElemError` to indicate issues during parsing, 
validation, or dumping.

```python
from SprelfJSON import JSONModel, JSONModelError

class StrictModel(JSONModel):
    required_field: str
    int_field: int

# Example of missing required field error
json_missing = {"int_field": 123}
try:
    StrictModel.from_json(json_missing)
except JSONModelError as e:
    print(f"Caught expected error: {e}") # Output: Caught expected error: Missing required key 'required_field' on 'StrictModel'.

# Example of invalid type error
json_invalid_type = {"required_field": "hello", "int_field": "not an int"}
try:
    StrictModel.from_json(json_invalid_type)
except JSONModelError as e:
    print(f"Caught expected error: {e}") # Output: Caught expected error: Model error on key 'int_field' of 'StrictModel': Schema mismatch: Expected type '<class 'int'>', but got 'str' instead

# Example of extra field error (by default)
json_extra_field = {"required_field": "hello", "int_field": 123, "extra": "data"}
try:
    StrictModel.from_json(json_extra_field)
except JSONModelError as e:
    print(f"Caught expected error: {e}") # Output: Caught expected error: The following keys are not found in the model for 'StrictModel': extra
```


## Extra options

There are some class-level options to define certain types of behavior by the class it's applied to and all subclasses.

- `__name_field__: str`: When parsing, the name of the JSON field that stores the name of the `JSONModel` object to dynamically parse.  Defaults as `"__name"`
- `__name_field_required__: bool`: When parsing, will reject any JSON objects that do not have the name field defined.  Defaults as `True`
- `__allow_null_json_output__: bool`: When dumping, whether to include the name field in the output.  Defaults as `True`
- `__allow_null_json_output__: bool`: When dumping, whether to allow null JSON values.  Defaults as `False`
- `__include_defaults_in_json_output__: bool`: When dumping, whether to include fields whose values are equal to the default value.  Defaults as `False`.
- `__allow_extra_fields__: bool`: When parsing, whether to raise an error if there are extra fields that don't belong to the model.  If `True`, then they are simply ignored.  Defaults as `False`
- `__exclusions__: list[str]`: A list of fields that are defined, but should be ignored for the purposes of parsing/dumping.
- `__eval_context__: dict[str, ...]`: A map of modules and classes to include when evaluating the annotations (which are read as strings) into actual types.
