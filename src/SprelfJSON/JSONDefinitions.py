from __future__ import annotations

from typing import Any, Self, MutableMapping, Sequence, get_origin, get_args, Collection, Mapping
import collections
import inspect
from types import NoneType
from abc import ABC, abstractmethod

#

# Used for annotations
JSONArray = list["JSONType"]
JSONObject = dict[str, "JSONType"]
JSONValue = None | bool | int | float | str
JSONContainer = JSONObject | JSONArray
JSONType = JSONContainer | JSONValue

FieldPath = str | int | tuple[str | int, ...]


class SprelfJSONError(Exception):

    def __init__(self, *args):
        super().__init__(*args)


#


class _JSONObjectLike(type):
    ALLOWED = (dict, MutableMapping, Mapping, collections.abc.MutableMapping, collections.abc.Mapping)

    def __instancecheck__(cls, obj: Any) -> bool:
        return obj is not None and isinstance(obj, cls.ALLOWED) and \
            all(isinstance(v, JSONLike) for v in obj.values()) and all(isinstance(k, str) for k in obj.keys())

    def __subclasscheck__(cls, t: type) -> bool:
        if t == JSONObjectLike:
            return True
        origin = get_origin(t)
        args = get_args(t)
        return ((inspect.isclass(origin) and issubclass(origin, cls.ALLOWED)) or origin in cls.ALLOWED) and \
                len(args) == 2 and args[0] == str and issubclass(args[1], JSONLike)


class JSONObjectLike(metaclass=_JSONObjectLike):
    ...


class _JSONValueLike(type):

    def __instancecheck__(cls, obj: Any) -> bool:
        return obj is None or isinstance(obj, (str, int, float, bool))

    def __subclasscheck__(cls, t: type) -> bool:
        if t == JSONValueLike:
            return True
        return t is None or t == NoneType or issubclass(t, (str, int, float, bool))

class JSONValueLike(metaclass=_JSONValueLike):
    ...


class _JSONArrayLike(type):
    ALLOWED = (list, Sequence, collections.abc.Sequence)

    def __instancecheck__(cls, obj: Any) -> bool:
        return obj is not None and isinstance(obj, cls.ALLOWED) and \
            not isinstance(obj, str) and \
            all(isinstance(elem, JSONLike) for elem in obj)

    def __subclasscheck__(cls, t: type) -> bool:
        if t == JSONArrayLike:
            return True
        origin = get_origin(t)
        args = get_args(t)
        return ((inspect.isclass(origin) and issubclass(origin, cls.ALLOWED))
                or origin in cls.ALLOWED) and \
            not issubclass(origin, str) and \
            len(args) == 1 and issubclass(args[0], JSONLike)

class JSONArrayLike(metaclass=_JSONArrayLike):
    ...


class _JSONContainerLike(type):
    def __instancecheck__(cls, obj: Any) -> bool:
        return isinstance(obj, (JSONObjectLike, JSONArrayLike))

    def __subclasscheck__(self, t: type) -> bool:
        if t in (JSONContainerLike, JSONObjectLike, JSONArrayLike):
            return True
        return issubclass(t, (JSONObjectLike, JSONArrayLike))

class JSONContainerLike(metaclass=_JSONContainerLike):
    ...


class _JSONLike(type):
    def __instancecheck__(self, obj: Any) -> bool:
        return isinstance(obj, (JSONValueLike, JSONObjectLike, JSONArrayLike))

    def __subclasscheck__(cls, t: type) -> bool:
        if t in (JSONLike, JSONObjectLike, JSONArrayLike, JSONValueLike, JSONContainerLike):
            return True
        return issubclass(t, (JSONValueLike, JSONObjectLike, JSONArrayLike))

class JSONLike(metaclass=_JSONLike):
    ...


#


def is_json_type(value: Any, bound: JSONValue | JSONObject | JSONArray | JSONContainer | JSONType = JSONType) -> bool:
    if value is None:
        return bound in (JSONValue, JSONType)
    if isinstance(value, (bool, int, float, str)):
        return bound in (JSONValue, JSONType)
    if isinstance(value, list):
        return bound in (JSONArray, JSONContainer, JSONType) and (is_json_type(item) for item in value)
    if isinstance(value, dict):
        return bound in (JSONObject, JSONContainer, JSONType) and (isinstance(k, str) and is_json_type(v)
                                                                   for k, v in value.items())
    return False


class JSONable(ABC):

    @abstractmethod
    def to_json(self, **kwargs) -> JSONObject:
        ...


class JSONConvertible(JSONable, ABC):

    @classmethod
    @abstractmethod
    def from_json(cls, o: JSONObject, **kwargs) -> Self:
        ...
