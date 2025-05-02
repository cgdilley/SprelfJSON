from __future__ import annotations

from abc import ABCMeta, ABC, abstractmethod
from typing import Any, Hashable, Self, Mapping, dataclass_transform
import typing
import itertools
import inspect

import typing_inspect

from SprelfJSON.JSONModel.ModelElem import ModelElem, ModelElemError, SupportedTypeMap, AlternateModelElem
from SprelfJSON.JSONDefinitions import JSONObject, JSONType, JSONConvertible
from SprelfJSON.JSONModel.JSONModelError import JSONModelError
from SprelfJSON.Helpers import ClassHelpers


#


@dataclass_transform(kw_only_default=True, field_specifiers=(ModelElem,))
class JSONModelMeta(ABCMeta):
    _ANNO = '__annotations__'
    _FIELDS = "_fields"
    _JSON_MODEL = "__json_model__"
    __json_model__: dict[str, ModelElem]
    __name_field_required__: bool = True
    __exclusions__: list[str] = []
    __eval_context__ = {**globals(),
                        **SupportedTypeMap,
                        **typing.__dict__,
                        ModelElem.__name__: ModelElem,
                        AlternateModelElem.__name__: AlternateModelElem}

    #

    class Glue:
        pass

    #

    def __new__(mcls: type[JSONModelMeta],
                name: str,
                bases: tuple[type, ...],
                namespace: dict[str, Any],
                **kwargs) -> type:
        if name == "JSONModel" or not any(isinstance(base, JSONModelMeta) for base in bases) \
                or any(base == JSONModelMeta.Glue for base in bases):
            new_cls = super().__new__(mcls, name, bases, namespace)
            return new_cls

        given_anno: dict[str, Any] = {}
        defaults: dict[str, Any] = {}

        for base in reversed(bases):
            if hasattr(base, mcls._ANNO):
                given_anno.update(base.__annotations__)
                defaults.update(getattr(base, "__defaults__", {}))

        given_anno.update(namespace.get(mcls._ANNO, {}))

        defaults.update({key: namespace[key] for key in given_anno.keys() if key in namespace})
        defaults.update({key: elem.default for key, elem in given_anno.items()
                         if isinstance(elem, ModelElem) and elem.has_default()})
        given_anno = {k: v for k, v in given_anno.items() if not k.startswith("_")}
        defaults = {k: v for k, v in defaults.items() if not k.startswith("_")}

        for field in given_anno.keys():
            if hasattr(mcls, field):
                defaults[field] = getattr(mcls, field)

        eval_context = {**JSONModelMeta.__eval_context__,
                        **{sc.__name__: sc for sc in ClassHelpers.all_subclasses(JSONModel)}}

        def _eval(_s: Any):
            if inspect.isclass(_s) or typing_inspect.is_generic_type(_s) or typing_inspect.is_union_type(_s) or \
                    typing_inspect.is_optional_type(_s):
                return _s
            try:
                return eval(_s, eval_context)
            except:
                return ClassHelpers.locate_class(_s)

        clean_anno = {k: v.annotated_type if isinstance(v, ModelElem) else _eval(v)
                      for k, v in given_anno.items()}
        full_anno = {k: v if isinstance(v, ModelElem) else ModelElem(_eval(v), default=defaults.get(k, ()))
                     for k, v in given_anno.items()}
        required = [n for n in clean_anno.keys() if n not in defaults]

        def __init__(self, **_kwargs):
            JSONModel.__init__(self, **_kwargs)
            if hasattr(self, '__post_init__'):
                self.__post_init__()

        constructor_anno = {k: given_anno[k] for k in clean_anno.keys()}
        __init__.__annotations__ = constructor_anno
        __init__.__kwdefaults__ = dict(defaults)

        def __repr__(self):
            parts = ", ".join(f"{k}={getattr(self, k)!r}" for k in given_anno.keys())
            return f"{name}({parts})"

        namespace = {
            **namespace,
            "__defaults__": defaults,
            "__slots__": required,
            "_fields": tuple(given_anno.keys()),
            "__annotations__": given_anno,
            "__json_model__": full_anno,
            "__init__": __init__,
            "__repr__": __repr__
        }

        glue_name = f"_{name}_Glue"

        glue_cls = super().__new__(mcls, glue_name, bases + (JSONModelMeta.Glue,), namespace)

        new_cls = super().__new__(mcls, name, (glue_cls,), {})
        __init__.__annotations__.update({"return": new_cls})

        return new_cls

    #

    #

    #


class JSONModel(JSONConvertible, ABC, metaclass=JSONModelMeta):
    _MODEL_CACHE: dict[tuple[Hashable, JSONModelMeta], JSONModelMeta] = dict()

    def __init__(self, **kwargs):
        model = type(self).get_model()
        validated = type(self).validate_model(model=model, values=kwargs, ignore_extra=False)
        for k, v in validated.items():
            setattr(self, k, v)

    @classmethod
    def from_json(cls, o: JSONObject, **kwargs) -> Self:
        return cls._from_json_meta(o, **kwargs)

    def to_json(self, **kwargs) -> JSONObject:
        return {}

    @classmethod
    def get_model(cls) -> dict[str, ModelElem]:
        return {k: v for k, v in getattr(cls, cls._JSON_MODEL, {}).items()
                if k not in cls.__exclusions__}

    @classmethod
    def _from_json_meta(cls, o: JSONObject, **kwargs):
        copy = {k: v for k, v in o.items()}
        subclass = cls._extract_subclass(copy)
        return subclass(**subclass.parse_json(o))

    @classmethod
    def parse_json(cls, o: JSONObject):
        return {k: elem.parse_value(o[k])
                for k, elem in getattr(cls, cls._JSON_MODEL, {}).items()
                if k in o}

    @classmethod
    def _name_field(cls) -> str:
        return "__name"

    @classmethod
    def model_identity(cls) -> JSONType:
        return cls.__name__

    @classmethod
    def _pop_name_from_name_field(cls, o: JSONObject) -> JSONType:
        name_field = cls._name_field()
        if name_field not in o:
            if cls.__name_field_required__:
                raise JSONModelError(f"Object is missing name field '{name_field}'; cannot "
                                     f"determine class to instantiate.")
            return cls.model_identity()

        return o.pop(name_field)

    @classmethod
    def _subclass_match(cls, value: JSONType, subclass: type[Self]) -> bool:
        return value == subclass.model_identity()

    @classmethod
    def _extract_subclass(cls, o: JSONObject) -> type[Self]:
        name = cls._pop_name_from_name_field(o)
        return cls._extract_subclass_by_name(name)

    @classmethod
    def _extract_subclass_by_name(cls, name: str) -> type[Self]:
        if isinstance(name, Hashable):
            _id = (name, cls)
            if _id in JSONModel._MODEL_CACHE:
                return JSONModel._MODEL_CACHE[_id]

        for subclass in itertools.chain((cls,), ClassHelpers.all_subclasses(cls)):
            if JSONModelMeta.Glue not in subclass.__bases__ and cls._subclass_match(name, subclass):
                if isinstance(name, Hashable):
                    JSONModel._MODEL_CACHE[(name, cls)] = subclass
                return subclass

        raise JSONModelError(f"Unable to find suitable subclass for '{cls.__name__}' matching "
                             f"the name '{name}'; cannot parse JSONModel.")

    #

    #

    @classmethod
    def validate_model(cls, model: Mapping[str, ModelElem],
                       values: Mapping[str, Any],
                       ignore_extra: bool = False) -> dict[str, Any]:
        return cls._validate_model(model, values, ignore_extra)

    @classmethod
    def _validate_model(cls, model: Mapping[str, ModelElem],
                        values: Mapping[str, Any],
                        ignore_extra: bool) -> dict[str, Any]:
        result: dict[str, Any] = dict()
        values = {**values}
        for k, m in model.items():
            if k not in values:
                if not m.has_default():
                    raise JSONModelError(f"Missing required key '{k}' on '{cls.__name__}'.")
                val = m.default
            else:
                val = values.pop(k)
            try:
                val = m.validate(val)
            except ModelElemError as e:
                raise JSONModelError(f"Model error on key '{k}' of '{cls.__name__}': {str(e)}")

            result[k] = val

        if not ignore_extra and any(k for k in values.keys() if k not in cls.__exclusions__):
            raise JSONModelError(f"The following keys are not found in the model for '{cls.__name__}': "
                                 f"{','.join(values.keys())}")

        return result
