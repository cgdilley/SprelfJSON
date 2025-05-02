from __future__ import annotations

from typing import Any, Self
from abc import ABC, abstractmethod

#


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
