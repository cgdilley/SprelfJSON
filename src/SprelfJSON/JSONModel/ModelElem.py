from __future__ import annotations

from types import UnionType, NoneType, GeneratorType

from SprelfJSON.JSONDefinitions import JSONConvertible, JSONable, JSONType
from SprelfJSON.Helpers import ClassHelpers, TimeHelpers
from SprelfJSON.JSONModel.JSONModelError import JSONModelError

from typing import Any, TypeVar, Callable, Union
from collections.abc import Sequence, MutableSequence, Mapping, MutableMapping, MutableSet, Collection, \
    Iterator, Iterable, Generator, Set
import typing_inspect
import inspect
import base64
import json
import re
from abc import ABC, abstractmethod

from datetime import datetime, date, time, timedelta
from enum import Enum, StrEnum, IntEnum, IntFlag

T2 = TypeVar('T2')
SupportedTypes = (dict, list, set, tuple, bool, str, int, float, bytes, type, None,
                  datetime, date, time, timedelta, re.Pattern,
                  Enum, StrEnum, IntEnum, IntFlag,
                  Sequence, MutableSequence, Mapping, MutableMapping, MutableSet, Collection,
                  Iterable, Iterator, Generator,
                  JSONable, UnionType, NoneType)
SupportedUnion = Union[SupportedTypes]
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
    __base64_altchars__: tuple[bytes, ...] = (b"-_", b"+/")
    _AliasedModelTypes: list[type[ModelType]] = None
    _ConcreteModelTypes: list[type[ModelType]] = None

    def __init__(self, typ: type[T]):
        t, gen = type(self)._validate_definition(typ)
        self.origin: type[T] = t
        self.generics: tuple[_BaseModelElem, ...] = gen
        self._model_type: type[ModelType] | None = None

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

    def is_valid(self, value: Any, *, key: str | None = None, **kwargs) -> bool:
        try:
            _ = self.validate(value, key=key, **kwargs)
            return True
        except ModelElemError:
            return False

    def validate(self, value: Any, *, key: str | None = None, **kwargs) -> T:
        """
        Validates that the given value conforms to the type defined by this model element, transforming
        it if needed, and returning that potentially-transformed value.
        """
        parsed = self.parse_value(value, key=key, **kwargs)
        if self._is_valid(parsed, key=key, **kwargs):
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

    def _is_valid(self, val: T, **kwargs) -> bool:
        return self.validate_type(val, **kwargs)

    #

    @classmethod
    def _resolve_model_types(cls):
        if cls._AliasedModelTypes is None or cls._ConcreteModelTypes is None:
            cls._AliasedModelTypes = [mt for mt in ClassHelpers.all_subclasses(ModelType)
                                      if not inspect.isabstract(mt)]
            cls._ConcreteModelTypes = [cls._AliasedModelTypes.pop(i)
                                       for i, mt in reversed(list(enumerate(cls._AliasedModelTypes)))
                                       if issubclass(mt, ModelType_Concrete)]

    def get_matching_model_type(self, **kwargs) -> type[ModelType]:
        if self._model_type is None:
            self._resolve_model_types()
            for mt in self._AliasedModelTypes:
                if mt.test_origin(self, **kwargs):
                    self._model_type = mt
                    return mt
            if inspect.isclass(self.origin):
                for mt in self._ConcreteModelTypes:
                    if mt.test_origin(self, **kwargs):
                        self._model_type = mt
                        return mt

            raise ModelElemError(self, f"Unable to identify matching ModelType for ModelElem with origin "
                                       f"of type '{self.annotated_type!r}'")

        return self._model_type

    #

    def validate_type(self, val: T, **kwargs) -> bool:
        try:
            mt = self.get_matching_model_type(**kwargs)
            return mt.is_valid(val, self, **kwargs)
        except ModelElemError:
            return False

    def parse_value(self, val: Any, **kwargs) -> T:
        """
        Parses the given value to conform with the type defined by this model element, if possible.
        If unsuccessful, a ModelElemError is raised.
        """
        return self._parse_value(val)

    def _parse_value(self, val: Any, **kwargs) -> T:
        mt = self.get_matching_model_type(**kwargs)
        return mt.parse(val, self, **kwargs)

    #

    def dump_value(self, val: T, *, key: str | None = None, **kwargs) -> JSONType:
        """
        Dumps the given value into a JSON-friendly type representing the type
        defined by this model element, if the given value can be validated (see validate()).
        If unable to validate, or unable to dump the validated value, a
        ModelElemError is raised.

        :keyword key: The key of the JSONModel that this ModelElem represents.  Just used for logging,
        not required.
        """
        return self._dump_value(val, key=key)

    def _dump_value(self, val: T, **kwargs) -> JSONType:
        mt = self.get_matching_model_type(**kwargs)
        return mt.dump(val, self, **kwargs)

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
                 use_alternates_only: bool = False,
                 ignored: bool = False):
        super().__init__(typ)
        self._ignored = ignored
        self._alternates = list(alternates)
        self._use_alternates_only = use_alternates_only
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
    def parse_value(self, val: Any, *, key: str | None = None, **kwargs) -> T:
        if self.ignored:
            return None

        if not self._use_alternates_only:
            try:
                return self._parse_value(val, key=key, **kwargs)
            except:
                if len(self._alternates) == 0:
                    raise

        for a in self._alternates:
            try:
                return a.transformer(a.parse_value(val, key=key, **kwargs))
            except:
                continue
        raise ModelElemError(self, f"Unable to parse value of type '{type(val).__name__}' as "
                                   f"an object of type '{self.annotated_type!r}'" +
                             (f" ({len(self._alternates)} alternate(s) also failed)"
                              if len(self._alternates) > 0 else "") +
                             ".")

    # OVERRIDE
    def dump_value(self, val: T, *, key: str | None = None, **kwargs) -> JSONType:
        if self.ignored:
            return None

        if not self._use_alternates_only:
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
    def validate(self, value: Any, **kwargs) -> T:
        if self.ignored:
            return None

        return super().validate(value, **kwargs)


#


#


class AlternateModelElem(_BaseModelElem):

    def __init__(self, typ: type[T2],
                 transformer: Callable[[T2], T],
                 jsonifier: Callable[[Any], SupportedTypes] | None = None):
        super().__init__(typ)
        self.transformer = transformer
        self.jsonifier = jsonifier


#


#


#


class ModelType(ABC):

    @classmethod
    @abstractmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        pass

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return isinstance(val, elem.origin)

    @classmethod
    @abstractmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        pass

    @classmethod
    @abstractmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        pass

    @classmethod
    def _parse_error(cls, val: Any, elem: _BaseModelElem, message: str, **kwargs):
        k_str = f" on key '{k}'" if (k := kwargs.pop("key", None)) else ""
        return ModelElemError(elem, f"Unable to parse value of type '{type(val).__name__}'{k_str} " + message)

    @classmethod
    def _dump_error(cls, val: Any, elem: _BaseModelElem, message: str, **kwargs) -> ModelElemError:
        k_str = f" on key '{k}'" if (k := kwargs.pop("key", None)) else ""
        return ModelElemError(elem, f"Given value of type '{type(val).__name__}'{k_str}) " + message)

    @classmethod
    def _parse_for_dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> Any:
        try:
            return elem.validate(val)
        except ModelElemError as e:
            raise cls._dump_error(val, elem, f"as the expected type '{elem.annotated_type!r}'; "
                                             f"could not be validated: {str(e)}", **kwargs)


#


class ModelType_None(ModelType):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin is None or elem.origin is NoneType

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return val is None

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        return None

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return None


class ModelType_Union(ModelType):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return typing_inspect.is_union_type(elem.origin)

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return any(g.validate_type(val) for g in elem.generics)

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        for g in elem.generics:
            try:
                return g.parse_value(val)
            except ModelElemError:
                pass
        raise ModelElemError(elem, f"Given value of type '{type(val).__name__}' does not meet any of the allowed "
                                   f"union types: {', '.join(repr(g.annotated_type) for g in elem.generics)}")

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        for g in elem.generics:
            try:
                return g.dump_value(val, **kwargs)
            except ModelElemError:
                pass
        raise cls._dump_error(val, elem, "cannot be dumped as any of the allowed "
                                         f"types: {', '.join(repr(g.annotated_type) for g in elem.generics)}",
                              **kwargs)


class ModelType_Optional(ModelType):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return typing_inspect.is_optional_type(elem.origin)

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if val is None:
            return val
        if len(elem.generics) > 0:
            return elem.generics[0].parse_value(val)
        return val

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        if val is None:
            return True
        return len(elem.generics) == 0 or elem.generics[0].is_valid(val)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        if val is None:
            return None
        if len(elem.generics) > 0:
            return elem.generics[0].dump_value(val, **kwargs)


class ModelType_Generator(ModelType):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin in (Generator, Iterable, Iterator, GeneratorType)

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if not isinstance(val, Iterable):
            raise cls._parse_error(val, elem, f"is not iterable.")
        if len(elem.generics) > 0:
            return (elem.generics[0].dump_value(v) for v in val)  # Stays lazy
        return val

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        if not isinstance(parsed, Iterable):
            raise cls._dump_error(val, elem, f"is not iterable; cannot dump as a JSON array.", **kwargs)
        if len(elem.generics) > 0:
            return [elem.generics[0].dump_value(v) for v in parsed]
        return list(parsed)


class ModelType_Sequence(ModelType_Generator):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin in (Sequence, Collection, MutableSequence, MutableSet, Set)

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return (isinstance(val, elem.origin)) \
            and (len(elem.generics) == 0 or all(elem.generics[0].is_valid(x) for x in val))

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if not isinstance(val, Iterable):
            raise cls._parse_error(val, elem, f"is not iterable.")
        if len(elem.generics) > 0:
            val = (elem.generics[0].parse_value(v) for v in val)
        if elem.origin in (Sequence, Collection, MutableSequence):
            return list(val)
        elif elem.origin in (MutableSet, Set):
            return set(val)
        raise ModelElemError(elem, f"Unable to find suitable type to parse value as given "
                                   f"the expected type '{elem.annotated_type!r}'")


class ModelType_Object(ModelType, ABC):
    t: type

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        try:
            return issubclass(elem.origin, cls.t)
        except TypeError:
            return False


class ModelType_List(ModelType_Object):
    t = list

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return (isinstance(val, cls.t) and
                (len(elem.generics) == 0 or all(elem.generics[0].is_valid(x, **kwargs)
                                                for x in val)))

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if not isinstance(val, Iterable):
            raise cls._parse_error(val, elem, f"as a list; object is not iterable.")
        if len(elem.generics) > 0:
            return cls.t(elem.generics[0].parse_value(v) for v in val)
        return cls.t(val)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        if not isinstance(parsed, Iterable):
            raise cls._dump_error(val, elem, f"is not iterable; "
                                             f"cannot dump as a JSON array.", **kwargs)
        if len(elem.generics) > 0:
            return [elem.generics[0].dump_value(v) for v in parsed]
        return list(parsed)


class ModelType_Set(ModelType_List):
    t = set


class ModelType_FrozenSet(ModelType_List):
    t = frozenset


class ModelType_Tuple(ModelType_List):
    t = tuple

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        if not isinstance(val, tuple):
            return False
        if len(elem.generics) == 2 and elem.generics[1].origin is Ellipsis:
            return all(elem.generics[0].is_valid(x) for x in val)
        if len(elem.generics) == 0:
            return True
        if len(elem.generics) != len(val):
            return False
        return all(g.is_valid(x) for g, x in zip(elem.generics, val))

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if not isinstance(val, Collection):
            raise cls._parse_error(val, elem, f"is not a collection; cannot parse as a tuple.", **kwargs)
        if len(elem.generics) == 2 and elem.generics[1].origin is Ellipsis:
            return cls.t(elem.generics[0].parse_value(v) for v in val)
        elif len(elem.generics) == 0:
            return cls.t(val)
        elif len(elem.generics) == len(val):
            return cls.t(g.parse_value(v) for g, v in zip(elem.generics, val))
        raise cls._parse_error(val, elem, f"has the wrong number of "
                                          f"elements to be parsed as a '{elem.annotated_type!r}'; has ({len(val)}).",
                               **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        if len(elem.generics) == 2 and elem.generics[1].origin is Ellipsis:
            return super().dump(val, elem, **kwargs)

        parsed = cls._parse_for_dump(val, elem, **kwargs)
        if not isinstance(parsed, Iterable):
            raise cls._dump_error(val, elem, f" is not iterable; "
                                             f"cannot dump as a JSON array.", **kwargs)
        if len(elem.generics) == 0:
            return list(parsed)
        if len(val) == len(elem.generics):
            return [g.dump_value(x) for x, g in zip(val, elem.generics)]
        raise cls._parse_error(val, elem, f"has the wrong number of "
                                          f"elements to be dumped as a '{elem.annotated_type!r}'; has ({len(val)}).",
                               **kwargs)


class ModelType_Dict(ModelType):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin in (Mapping, MutableMapping) \
            or (inspect.isclass(elem.origin) and issubclass(elem.origin, dict))

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return (isinstance(val, Mapping) and
                (len(elem.generics) == 0 or all(elem.generics[0].is_valid(k) and elem.generics[1].is_valid(v)
                                                for k, v in val.items())))

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if ClassHelpers.check_generic_instance(val, Iterable, tuple[Any, Any]):
            d = {k: v for k, v in val}
        else:
            d = val
        if isinstance(d, Mapping):
            if all(isinstance(k, str) for k in d.keys()):
                if elem.generics[0].origin == str:
                    return {k: elem.generics[1].parse_value(v) for k, v in d.items()}
                return {elem.generics[0].parse_value(json.loads(k)): elem.generics[1].parse_value(v)
                        for k, v in d.items()}
            else:
                return {elem.generics[0].parse_value(k): elem.generics[1].parse_value(v)
                        for k, v in d.items()}
        raise cls._parse_error(val, elem, f"could not be parsed as a dictionary.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        if len(elem.generics) == 0:
            return dict(parsed)
        if elem.generics[0].origin == str:
            return {k: elem.generics[1].dump_value(v) for k, v in parsed.items()}
        return {json.dumps(elem.generics[0].dump_value(k)): elem.generics[1].dump_value(v)
                for k, v in parsed.items()}


class ModelType_Type(ModelType_Object):
    t = type

    @classmethod
    def is_valid(cls, val: SupportedUnion, elem: _BaseModelElem, **kwargs) -> bool:
        return (inspect.isclass(val) and
                (len(elem.generics) == 0 or ClassHelpers.check_subclass(val, elem.generics[0].annotated_type)))

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
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
                raise ModelElemError(elem, f"Unable to parse string value '{val}' as a type; "
                                           f"type is not found.")
        if not inspect.isclass(val):
            raise cls._parse_error(val, elem, f"could not be "
                                              f"interpreted as a type; is it an instance?", **kwargs)
        return val

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        return None if parsed is None else ClassHelpers.full_name(parsed)


class ModelType_Concrete(ModelType_Object, ABC):

    @classmethod
    def parse(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, elem.origin):
            return val
        else:
            return cls._convert(val, elem, **kwargs)

    @classmethod
    @abstractmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        ...


class ModelType_Basic(ModelType_Concrete):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return any(issubclass(elem.origin, x) for x in (str, int, float, bool))

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if issubclass(elem.origin, float) and isinstance(val, int):
            return float(val)
        raise cls._parse_error(val, elem, "as one of the basic types.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs)


class ModelType_Pattern(ModelType_Concrete):

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return issubclass(elem.origin, re.Pattern)

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, str):
            try:
                return re.compile(val)
            except:
                raise ModelElemError(elem, f"Unable to compile string as a regular expression.")
        raise cls._parse_error(val, elem, f"as a regular expression.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        return parsed.pattern


class ModelType_DateTime(ModelType_Concrete):
    t = datetime

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin == datetime

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        try:
            return TimeHelpers.parse_datetime(val)
        except ValueError:
            raise cls._parse_error(val, elem, "into a datetime.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return TimeHelpers.stringify_datetime(cls._parse_for_dump(val, elem, **kwargs))


class ModelType_Date(ModelType_Concrete):
    t = date

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin == date

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        try:
            return TimeHelpers.parse_date(val)
        except ValueError:
            raise cls._parse_error(val, elem, "into a date.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return TimeHelpers.stringify_date(cls._parse_for_dump(val, elem, **kwargs))


class ModelType_Time(ModelType_Concrete):
    t = time

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return elem.origin == time

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        try:
            return TimeHelpers.parse_time(val)
        except ValueError:
            raise cls._parse_error(val, elem, "into a time.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return TimeHelpers.stringify_time(cls._parse_for_dump(val, elem, **kwargs))


class ModelType_TimeDelta(ModelType_Concrete):
    t = timedelta

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
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
            raise ModelElemError(elem, f"Unable to parse timedelta string; format is invalid.")
        elif isinstance(val, int):
            return timedelta(seconds=val / 1000)
        elif isinstance(val, float):
            return timedelta(seconds=val)
        raise cls._parse_error(val, elem, "into a timedelta.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return int(cls._parse_for_dump(val, elem, **kwargs).total_seconds() * 1000)


class ModelType_IntFlag(ModelType_Concrete):
    t = IntFlag

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, int):
            try:
                return elem.origin(val)
            except ValueError as e:
                raise ModelElemError(elem, f"Unable to parse IntFlag: {e}")
        raise cls._parse_error(val, elem, "into an IntFlag.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs).value


class ModelType_IntEnum(ModelType_Concrete):
    t = IntEnum

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, int):
            try:
                return elem.origin(val)
            except ValueError:
                raise ModelElemError(elem, f"Unable to parse IntEnum from integer; "
                                           f"Unrecognized IntEnum value ({val}) for '{type(elem.origin).__name__}'.")
        elif isinstance(val, str):
            try:
                return elem.origin[val]
            except KeyError:
                raise ModelElemError(elem, f"Unable to parse IntEnum from string; "
                                           f"Unrecognized IntEnum value ({val}) for '{type(elem.origin).__name__}'.")

        raise cls._parse_error(val, elem, "into an IntEnum.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs).value


class ModelType_StrEnum(ModelType_Concrete):
    t = StrEnum

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, str):
            try:
                return elem.origin(val)
            except ValueError:
                raise ModelElemError(elem, f"Unable to parse StrEnum; "
                                           f"Unrecognized StrEnum value ({val}) for '{type(elem.origin).__name__}")
        raise cls._parse_error(val, elem, "into a StrEnum.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs).value


class ModelType_Enum(ModelType_Concrete):
    t = Enum

    @classmethod
    def test_origin(cls, elem: _BaseModelElem, **kwargs) -> bool:
        return issubclass(elem.origin, Enum) and not any(issubclass(elem.origin, x)
                                                         for x in (IntEnum, StrEnum, IntFlag))

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, str):
            try:
                return elem.origin[val]
            except KeyError:
                pass
        try:
            return elem.origin(val)
        except ValueError:
            raise cls._parse_error(val, elem, "into an Enum.", **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs).name


class ModelType_JSON(ModelType_Concrete):
    t = JSONConvertible

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, str):
            return elem.origin.from_json(json.loads(val))
        if ClassHelpers.check_generic_instance(val, dict, str, Any):
            return elem.origin.from_json(val)
        raise cls._parse_error(val, elem, f"into a JSON convertible object '{elem.origin.__name__}'.",
                               **kwargs)

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> JSONType:
        return cls._parse_for_dump(val, elem, **kwargs).to_json()


class ModelType_Bytes(ModelType_Concrete):
    t = bytes

    @classmethod
    def _convert(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        if isinstance(val, str):
            for alt in type(elem).__base64_altchars__:
                try:
                    return base64.b64decode(val, alt)
                except ValueError:
                    pass
            raise ModelElemError(elem, f"Unable to parse string to bytes; is not valid base-64")
        if ClassHelpers.check_generic_instance(val, Collection, int):
            if all(0 <= x <= 255 for x in val):
                return bytes(val)
            raise ModelElemError(elem, f"Given array of integers to parse as bytes has one or more values "
                                       f"outside the range of 0-255.")
        if ClassHelpers.check_generic_instance(val, Collection, str):
            try:
                parsed = [int(s, 16) for s in val]
            except ValueError:
                raise ModelElemError(elem, f"Given array of strings to parse as bytes has one or more invalid "
                                           f"hexadecimal strings.")
            if all(0 <= x <= 255 for x in parsed):
                return bytes(parsed)
            raise ModelElemError(elem, f"Given array of strings to parse as bytes has one or more hexadecimal "
                                       f"values outside the range of 0-255.")

    @classmethod
    def dump(cls, val: Any, elem: _BaseModelElem, **kwargs) -> type[SupportedUnion]:
        parsed = cls._parse_for_dump(val, elem, **kwargs)
        alts = type(elem).__base64_altchars__
        alt = alts[0] if len(alts) > 0 else None
        return base64.b64encode(parsed, alt).decode("ascii")
