from __future__ import annotations

from types import UnionType, NoneType

from SprelfJSON.JSONDefinitions import JSONConvertible, JSONable, JSONType
from SprelfJSON.Helpers import ClassHelpers, TimeHelpers
from SprelfJSON.JSONModel.JSONModelError import JSONModelError

from typing import Iterable, Any, TypeVar, Pattern, Callable, Mapping, Collection, Union, Iterator
import typing_inspect
import inspect
import base64
import json
import re
from abc import ABC

from datetime import datetime, date, time, timedelta
from enum import Enum, StrEnum, IntEnum, IntFlag

T2 = TypeVar('T2')
SupportedTypes = (dict, list, set, tuple, bool, str, int, float, bytes, type, None,
                  datetime, date, time, timedelta,
                  Enum, StrEnum, IntEnum, IntFlag,
                  JSONable, UnionType, NoneType)
SupportedTypeMap = {t.__name__: t for t in SupportedTypes if t is not None}
T = Union[SupportedTypes[:-1]]
_SupportedTypes_O1 = set(SupportedTypes)


class ModelElemError(JSONModelError):

    def __init__(self, model_elem: _BaseModelElem, *args):
        super().__init__(*args)
        self.model_elem = model_elem


#


class _BaseModelElem(ABC):
    """
    Base definition for a ModelElem.  Contains all elements related to storing a particular
    type, and parsing/dumping values of that type.  Not intended to be used directly.
    """
    __base64_altchars__: tuple[str, ...] = ("-_", "+/")

    def __init__(self, typ: type[T]):
        t, gen = type(self)._validate_definition(typ)
        self.origin: type[T] = t
        self.generics: tuple[_BaseModelElem, ...] = gen

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.origin.__name__})"

    def is_generic(self) -> bool:
        return len(self.generics) > 0

    @property
    def T(self) -> type[T]:
        return self.origin

    @property
    def annotated_type(self) -> type[T]:
        return ClassHelpers.as_generic(self.origin, *(g.annotated_type for g in self.generics))

    def is_valid(self, value: Any) -> bool:
        try:
            _ = self.validate(value)
            return True
        except ModelElemError:
            return False

    def validate(self, value: Any) -> T:
        """
        Validates that the given value conforms to the type defined by this model element, transforming
        it if needed, and returning that potentially-transformed value.
        """
        parsed = self.parse_value(value)
        if self._is_valid(parsed):
            return parsed

        if isinstance(value, list) or isinstance(value, set):
            t_str = f"{type(value).__name__}[{'|'.join({type(v).__name__ for v in value})}]"
        elif isinstance(value, Mapping):
            t_str = f"dict[{'|'.join({type(k).__name__ for k in value.keys()})}, " \
                    f"{'|'.join({type(v).__name__ for v in value.values()})}]"
        else:
            t_str = type(value).__name__

        raise ModelElemError(self, f"Schema mismatch: Expected type '{self.annotated_type!r}', "
                                   f"but got '{t_str}' instead")

    def _is_valid(self, val: T) -> bool:
        return self._validate_type(val, self.origin, *self.generics)

    #

    @classmethod
    def _validate_type(cls, val: T, origin: type, *generics: _BaseModelElem) -> bool:
        if val is None and origin is None:
            return True
        elif inspect.isclass(origin):
            if issubclass(origin, list):
                return (isinstance(val, list) and
                        (len(generics) == 0 or all(generics[0].is_valid(elem) for elem in val)))
            elif issubclass(origin, set):
                return (isinstance(val, set) and
                        (len(generics) == 0 or all(generics[0].is_valid(elem) for elem in val)))
            elif issubclass(origin, tuple):
                if not isinstance(val, tuple):
                    return False
                if len(generics) == 2 and generics[1] is Ellipsis:
                    return all(generics[0].is_valid(elem) for elem in val)
                if len(generics) != len(val):
                    return False
                return all(g.is_valid(elem) for g, elem in zip(generics, val))
            elif issubclass(origin, dict):
                return (isinstance(val, dict) and
                        (len(generics) == 0 or all(generics[0].is_valid(k) and generics[1].is_valid(v)
                                                   for k, v in val.items())))
        elif origin in (Iterable, Iterator):
            return (isinstance(val, Iterable) or isinstance(val, Iterator)) \
                and (len(generics) == 0 or all(generics[0].is_valid(elem) for elem in val))
        elif typing_inspect.is_optional_type(origin):
            if val is None:
                return True
            return generics[0].is_valid(val)
        elif typing_inspect.is_union_type(origin):
            return any(cls._validate_type(val, g.origin, *g.generics) for g in generics)
        elif origin == type:
            return (inspect.isclass(val) and
                    (len(generics) == 0 or ClassHelpers.check_subclass(val, generics[0].annotated_type)))

        return isinstance(val, origin)

    def parse_value(self, val: Any) -> T:
        """
        Parses the given value to conform with the type defined by this model element, if possible.
        If unsuccessful, a ModelElemError is raised.
        """
        return self._parse_value(val)

    def _parse_value(self, val: Any) -> T:
        v_t = type(val).__name__
        if typing_inspect.is_optional_type(self.origin):
            if val is None:
                return None
            return self.generics[0].parse_value(val)

        elif typing_inspect.is_union_type(self.origin):
            for g in self.generics:
                try:
                    return g.parse_value(val)
                except ModelElemError:
                    pass
            raise ModelElemError(self, f"Given value of type '{v_t}' does not meet any of the allowed "
                                       f"types: {', '.join(repr(g.annotated_type) for g in self.generics)}")

        elif self.origin in (Iterable, Iterator):
            if not any(isinstance(val, x) for x in (Iterable, Iterator)):
                raise ModelElemError(self, f"Given value of type '{v_t}' is not iterable.")
            return (self.generics[0].parse_value(v) for v in val)

        elif inspect.isclass(self.origin):

            if issubclass(self.origin, list):
                if not isinstance(val, Iterable):
                    raise ModelElemError(self,
                                         f"Given value of type '{v_t}' is not iterable; cannot parse as a list.")
                return [self.generics[0].parse_value(v) for v in val]

            elif issubclass(self.origin, set):
                if not isinstance(val, Iterable):
                    raise ModelElemError(self,
                                         f"Given value of type '{v_t}' is not iterable; cannot parse as a set.")
                return {self.generics[0].parse_value(v) for v in val}

            elif issubclass(self.origin, tuple):
                if not isinstance(val, Collection):
                    raise ModelElemError(self,
                                         f"Given value of type '{v_t}' is not a collection; cannot parse as a tuple.")
                if len(self.generics) == 2 and self.generics[1].origin is Ellipsis:
                    return tuple(self.generics[0].parse_value(v) for v in val)
                elif len(self.generics) != len(val):
                    raise ModelElemError(self,
                                         f"Given value of type '{type(val).__name__}' has the wrong number of elements to be parsed "
                                         f"as a '{self.annotated_type!r}'; has ({len(val)}).")
                return tuple(g.parse_value(v) for g, v in zip(self.generics, val))

            elif issubclass(self.origin, dict):
                if ClassHelpers.check_generic_instance(val, Iterable, tuple[Any, Any]):
                    d = {k: v for k, v in val}
                else:
                    d = val
                if isinstance(d, Mapping):
                    if all(isinstance(k, str) for k in d.keys()):
                        if self.generics[0].origin == str:
                            return {k: self.generics[1].parse_value(v) for k, v in d.items()}
                        return {self.generics[0].parse_value(json.loads(k)): self.generics[1].parse_value(v)
                                for k, v in d.items()}
                    else:
                        return {self.generics[0].parse_value(k): self.generics[1].parse_value(v)
                                for k, v in d.items()}
                raise ModelElemError(self, f"Given value of type '{v_t}' could not be parsed as a dictionary.")

            elif issubclass(self.origin, type):
                if isinstance(val, str):
                    if val.lower() == "datetime":
                        return datetime
                    elif val.lower() == "date":
                        return date
                    elif val.lower() == "time":
                        return time
                    elif val.lower() in ("null", "none"):
                        return None
                    t = ClassHelpers.locate_class(val)
                    if t is None:
                        raise ModelElemError(self, f"Unable to parse string value '{val}' as a type; "
                                                   f"type is not found.")
                if not inspect.isclass(val):
                    raise ModelElemError(self,
                                         f"Given value of type '{type(val).__name__}' could not be interpreted as a type; "
                                         f"is it an instance?")
                return val

            # If it's not a generic type, and we just simply have an isinstance match, end here
            elif isinstance(val, self.origin):
                return val

            # All other conditions past this point are conversions from an invalid type to the type we're looking for

            elif issubclass(self.origin, float) and isinstance(val, int):
                return float(val)

            elif issubclass(self.origin, datetime):
                try:
                    return TimeHelpers.parse_datetime(val)
                except ValueError:
                    raise ModelElemError(self, f"Unable to smart-parse value of type '{v_t}' into "
                                               f"a datetime.")

            elif issubclass(self.origin, date):
                try:
                    return TimeHelpers.parse_date(val)
                except ValueError:
                    raise ModelElemError(self, f"Unable to smart-parse value of type '{v_t}' into "
                                               f"a date.")

            elif issubclass(self.origin, time):
                try:
                    return TimeHelpers.parse_time(val)
                except ValueError:
                    raise ModelElemError(self, f"Unable to smart-parse value of type '{v_t}' into "
                                               f"a time.")

            elif issubclass(self.origin, timedelta):
                if isinstance(val, str):
                    if m := TimeHelpers.TIMEDELTA_REGEX.match(val):
                        groups = m.groupdict()
                        try:
                            return timedelta(days=int(groups.get("d", 0)) or 0,
                                             hours=int(groups.get("h", 0)) or 0,
                                             minutes=int(groups.get("m", 0)) or 0,
                                             seconds=int(groups.get("s", 0)) or 0,
                                             milliseconds=int(groups.get("ms", 0)) or 0)
                        except ValueError:
                            pass
                    raise ModelElemError(self, f"Unable to parse timedelta string; format is invalid.")
                elif isinstance(val, int):
                    return timedelta(seconds=val / 1000)
                elif isinstance(val, float):
                    return timedelta(seconds=val)
                raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as a timedelta.")

            elif issubclass(self.origin, IntFlag):
                if isinstance(val, int):
                    try:
                        return self.origin(val)
                    except ValueError as e:
                        raise ModelElemError(self, f"Unable to parse IntFlag: {e}")
                raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as an IntFlag.")

            elif issubclass(self.origin, IntEnum):

                if isinstance(val, int):
                    try:
                        return self.origin(val)
                    except ValueError:
                        raise ModelElemError(self, f"Unable to parse IntEnum from integer; "
                                                   f"Unrecognized IntEnum value ({val}) for '{type(self.origin).__name__}'.")
                elif isinstance(val, str):
                    try:
                        return self.origin[val]
                    except ValueError:
                        raise ModelElemError(self, f"Unable to parse IntEnum from string; "
                                                   f"Unrecognized IntEnum value ({val}) for '{type(self.origin).__name__}'.")

                raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as an IntEnum.")

            elif issubclass(self.origin, StrEnum):
                if isinstance(val, str):
                    try:
                        return self.origin(val)
                    except ValueError:
                        raise ModelElemError(self, f"Unable to parse StrEnum; "
                                                   f"Unrecognized StrEnum value ({val}) for '{type(self.origin).__name__}")
                raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as a StrEnum.")

            elif issubclass(self.origin, Enum):
                if isinstance(val, str):
                    try:
                        return self.origin[val]
                    except ValueError:
                        pass
                try:
                    return self.origin(val)
                except ValueError:
                    raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as an Enum; "
                                               f"Value is unrecognized.")

            if issubclass(self.origin, Pattern):
                if isinstance(val, str):
                    try:
                        return re.compile(val)
                    except:
                        raise ModelElemError(self, f"Unable to compile string as a regular expression.")
                raise ModelElemError(self, f"Unable to parse value of type '{v_t}' as a regular expression.")

            elif issubclass(self.origin, JSONConvertible):
                if isinstance(val, str):
                    return self.origin.from_json(json.loads(val))
                if ClassHelpers.check_generic_instance(val, dict, str, Any):
                    return self.origin.from_json(val)

            elif issubclass(self.origin, bytes):
                if ClassHelpers.check_generic_instance(val, Collection, int):
                    if all(0 <= x <= 255 for x in val):
                        return bytes(val)
                    raise ModelElemError(self, f"Given array of integers to parse as bytes has one or more values "
                                               f"outside the range of 0-255.")
                if ClassHelpers.check_generic_instance(val, Collection, str):
                    try:
                        parsed = [int(s, 16) for s in val]
                    except ValueError:
                        raise ModelElemError(self, f"Given array of strings to parse as bytes has one or more invalid "
                                                   f"hexadecimal strings.")
                    if all(0 <= x <= 255 for x in parsed):
                        return bytes(parsed)
                    raise ModelElemError(self, f"Given array of strings to parse as bytes has one or more hexadecimal "
                                               f"values outside the range of 0-255.")
                if isinstance(val, str):
                    for alt in type(self).__base64_altchars__:
                        try:
                            return base64.b64decode(val, alt)
                        except ValueError:
                            pass
                    raise ModelElemError(self, f"Unable to parse string to bytes; is not valid base-64")

        #

        raise ModelElemError(self, f"Unable to parse value of type '{v_t}' into "
                                   f"and object of type '{self.annotated_type!r}'.")

    #

    def dump_value(self, val: T, *, key: str | None = None, **kwargs) -> JSONType:
        """
        Dumps the given value into a JSON-friendly type representing the type
        defined by this model element, if the given value can be validated (see validate()).
        If unable to validate, or unable to dump the validated value, a
        ModelElemError is raised.
        """
        return self._dump_value(val, key=key)

    def _dump_value(self, val: T, *, key: str | None, **kwargs) -> JSONType:
        v_t = type(val).__name__
        k_str = f" on key '{key}'" if key else ""

        if self.origin is None or self.origin == NoneType:
            return None
        elif typing_inspect.is_optional_type(self.origin):
            if val is None:
                return None
            return self.generics[0].dump_value(val)

        elif typing_inspect.is_union_type(self.origin):
            for g in self.generics:
                try:
                    return g.dump_value(val)
                except ModelElemError:
                    pass
            raise ModelElemError(self,
                                 f"Given value of type '{v_t}'{k_str} cannot be dumped as any of the allowed "
                                 f"types: {', '.join(repr(g.annotated_type) for g in self.generics)}")

        try:
            parsed = self.validate(val)
        except ModelElemError as e:
            raise ModelElemError(self, f"Unable to dump value of type '{v_t}'{k_str} as "
                                       f"the expected type '{self.annotated_type!r}'; "
                                       f"could not be validated: {str(e)}")

        if any(isinstance(parsed, x) for x in (str, int, float, bool)):
            return parsed

        if any(issubclass(self.origin, x) for x in (list, set, tuple, Iterable, Iterator)):
            if not isinstance(parsed, Iterable):
                raise ModelElemError(self, f"Given value of type '{v_t}'{k_str} is not iterable; "
                                           f"cannot dump as a JSON array.")
            if len(self.generics) > 0:
                return [self.generics[0].dump_value(v) for v in parsed]
            return list(parsed)

        if not inspect.isclass(self.origin):
            raise ModelElemError(self, f"Origin type '{self.origin.__name__}' is not dumpable.")

        if issubclass(self.origin, dict):
            if len(self.generics) == 0:
                return dict(parsed)
            if self.generics[0].origin == str:
                return {k: self.generics[1].dump_value(v) for k, v in parsed.items()}
            return {json.dumps(self.generics[0].dump_value(k)): self.generics[1].dump_value(v)
                    for k, v in parsed.items()}

        elif issubclass(self.origin, type):
            return None if parsed is None else ClassHelpers.full_name(parsed)

        if issubclass(self.origin, datetime):
            return TimeHelpers.stringify_datetime(parsed)

        elif issubclass(self.origin, date):
            return TimeHelpers.stringify_date(parsed)

        elif issubclass(self.origin, time):
            return TimeHelpers.stringify_time(parsed)

        elif issubclass(self.origin, timedelta):
            return int(parsed.seconds * 1000)

        elif any(issubclass(self.origin, x) for x in (IntFlag, IntEnum, StrEnum)):
            return parsed.value

        elif issubclass(self.origin, Enum):
            return parsed.name

        elif issubclass(self.origin, Pattern):
            return parsed.pattern

        elif issubclass(self.origin, JSONConvertible):
            return parsed.to_json()

        elif issubclass(self.origin, bytes):
            alts = type(self).__base64_altchars__
            alt = alts[0] if len(alts) > 0 else None
            return base64.b64encode(parsed, alt)

        raise ModelElemError(self, f"Unable to dump value of type '{v_t}'{k_str} as "
                                   f"the defined model type '{self.origin.__name__}'.")

    #

    @classmethod
    def _validate_definition(cls, val_type: type) -> tuple[type, tuple[_BaseModelElem, ...]]:
        t, gen = ClassHelpers.analyze_type(val_type)
        if t is None or (inspect.isclass(t) and all(not inspect.isclass(supported) or not issubclass(t, supported)
                                                    for supported in SupportedTypes)):
            raise JSONModelError(f"Cannot define ModelElem with unsupported type '{t.__name__}'.")
        if len(gen) == 0:
            return t, ()

        if inspect.isclass(t) and issubclass(t, dict) and len(gen) != 2:
            raise JSONModelError(f"Invalid dict definition for ModelElem: [{','.join(g.__name__ for g in gen)}]")

        return t, tuple(_BaseModelElem(arg) for arg in gen)


#


#


class ModelElem(_BaseModelElem):
    """
    Full implementation of ModelElem, implementing extra features over
    _BaseModelElem, including default values and alternate parsing.
    """

    def __init__(self, typ: type[T],
                 *,
                 default: T | tuple[()] | None = (),
                 default_factory: Callable[[], T] | None = None,
                 alternates: Iterable[AlternateModelElem] = (),
                 ignored: bool = False):
        super().__init__(typ)
        self._ignored = ignored
        self._alternates = list(alternates)
        if default_factory is not None:
            self._default_factory = default_factory
            self._default = ()
        else:
            self._default_factory = None
            self._default: tuple[T | None] = \
                (default,) if not isinstance(default, tuple) or len(default) > 0 else default

    # OVERRIDE
    def __str__(self) -> str:
        values = [self.origin.__name__]
        if not isinstance(self.default, tuple) or len(self.default) > 0:
            values.append(f"default={self.default!r}")
        return f"{type(self).__name__}({','.join(values)})"

    @property
    def default(self) -> T | None:
        if not self.has_default():
            raise ModelElemError(self, "ModelElem does not have a default value; cannot access")
        if self._default_factory is not None:
            return self._default_factory()
        return self._default[0]

    def has_default(self) -> bool:
        return len(self._default) > 0 or self._default_factory is not None

    @property
    def ignored(self) -> bool:
        return self._ignored

    #

    # OVERRIDE
    def parse_value(self, val: Any) -> T:
        if self.ignored:
            return None

        try:
            return self._parse_value(val)
        except:
            if len(self._alternates) == 0:
                raise
            for a in self._alternates:
                try:
                    return a.transformer(a.parse_value(val))
                except:
                    continue
        raise ModelElemError(self, f"Unable to parse value of type '{type(val).__name__}' as "
                                   f"an object of type '{self.annotated_type!r}'" +
                             (f" ({len(self._alternates)} alternates also failed)"
                              if len(self._alternates) > 0 else "") +
                             ".")

    # OVERRIDE
    def dump_value(self, val: T, *, key: str | None = None, **kwargs) -> JSONType:
        if self.ignored:
            return None

        try:
            return self._dump_value(val, key=key, **kwargs)
        except:
            if len(self._alternates) == 0:
                raise
            for a in self._alternates:
                if a.jsonifier is None:
                    continue
                try:
                    return a.jsonifier(val)
                except:
                    continue

        raise ModelElemError(self, f"Unable to dump value of type '{type(val).__name__}' as "
                                   f"an object of type '{self.annotated_type!r}'" +
                             (f" ({len(self._alternates)} alternates also failed)"
                              if len(self._alternates) > 0 else "") +
                             ".")

    # OVERRIDE
    def validate(self, value: Any) -> T:
        if self.ignored:
            return None
        return super().validate(value)


#


#


class AlternateModelElem(_BaseModelElem):

    def __init__(self, typ: type[T2],
                 transformer: Callable[[T2], T],
                 jsonifier: Callable[[Any], SupportedTypes] | None = None):
        super().__init__(typ)
        self.transformer = transformer
        self.jsonifier = jsonifier
