from __future__ import annotations

import typing_inspect
from typing import Iterable, TypeAlias, get_origin, get_args, Any, TypeVar, Iterator, Sequence, Collection
from types import ModuleType
import collections
import typing
import types
import inspect
import pydoc
import builtins
import sys

from SprelfJSON.Helpers.Decorators import yield_unique


T = TypeVar('T')


def analyze_type(t: type) -> tuple[type, tuple[type, ...]]:
    o = get_origin(t) or t
    a = get_args(t)
    return o, a


def check_subclass(check: Any, expected: Any) -> bool:
    origin, args = analyze_type(expected)
    return check_generic_subclass(check, origin, *args)


def check_generic_subclass(check: Any, expected_origin: Any, *expected_args: Any) -> bool:
    if not isinstance(check, type):
        return False

    if expected_origin == Any:
        return True

    origin, args = analyze_type(check)

    if typing_inspect.is_union_type(expected_origin):
        return any(check_subclass(check, a) for a in expected_args)

    if not issubclass(origin, expected_origin):
        return False

    if len(expected_args) != len(args):
        return False

    if len(expected_args) == 0:
        return True

    return all(check_subclass(c, e) for c, e in zip(args, expected_args))


def check_instance(check: Any, expected: Any) -> bool:
    origin, args = analyze_type(expected)
    return check_generic_instance(check, origin, *args)


def check_generic_instance(check: Any, expected_origin: Any, *expected_args: Any) -> bool:
    if typing_inspect.is_union_type(expected_origin):
        return any(check_instance(check, a) for a in expected_args)

    if expected_origin == Any:
        return True

    if not isinstance(check, expected_origin):
        return False

    if len(expected_args) == 0:
        return True

    if expected_origin in (Iterable, Iterator, Sequence, Collection):
        return all(check_instance(x, expected_args[0]) for x in check)

    if issubclass(expected_origin, type):
        return inspect.isclass(check) and check_subclass(check, expected_args[0])

    if issubclass(expected_origin, tuple) and isinstance(check, collections.abc.Collection):
        if len(expected_args) == 2 and expected_args[1] is Ellipsis:
            return all(check_instance(x, expected_args[0]) for x in check)
        elif len(expected_args) != len(check):
            return False
        return all(check_instance(x, a) for x, a in zip(check, expected_args))

    if issubclass(expected_origin, Iterable) and isinstance(check, Iterable):
        return all(check_instance(x, expected_args[0]) for x in check)

    elif issubclass(expected_origin, collections.abc.Mapping) and isinstance(check, collections.abc.Mapping):
        key_type, val_type = expected_args
        return all(check_instance(k, key_type) and check_instance(v, val_type)
                   for k, v in check.items())

    return False


#


def as_generic(origin: Any, *generics: Any) -> Any:
    if len(generics) == 0:
        return origin
    try:
        return origin[generics]
    except TypeError:
        if origin == types.UnionType:
            return typing.Union[generics]

        # fallback to typing equivalents if needed
        origin_names = (origin.__name__, origin.__name__.capitalize())
        for origin_name in origin_names:
            for module in (typing, types):
                typing_origin = getattr(module, origin_name, None)
                if typing_origin:
                    return typing_origin[generics]
        raise

#


def type_as_string(t: type) -> str:
    origin, args = analyze_type(t)

    if origin is None:
        return t.__name__

    base_name = origin.__name__
    if len(args) == 0:
        return base_name

    arg_str = ", ".join(type_as_string(a) for a in args)
    return f"{base_name}[{arg_str}]"


#


@yield_unique
def all_subclasses(t: type) -> Iterable[type]:
    for c in t.__subclasses__():
        yield c
        yield from all_subclasses(c)


def get_module(t: type | ModuleType) -> ModuleType:
    return inspect.getmodule(t)


def full_name(t: type) -> str:
    return get_module(t).__name__ + "." + t.__name__


def locate_class(name: str) -> type | None:
    # Try pydoc.locate first (handles fully qualified names)
    obj = pydoc.locate(name)
    if isinstance(obj, type):
        return obj

    # Split the name (in case it's like "module.Class")
    split = name.split(".")
    if len(split) > 1:
        module_path = ".".join(split[:-1])
        class_name = split[-1]

        module = pydoc.locate(module_path)
        if isinstance(module, ModuleType):
            return getattr(module, class_name, None)

    # Try builtins
    if hasattr(builtins, name):
        obj = getattr(builtins, name)
        if isinstance(obj, type):
            return obj

    # Search through all currently loaded modules
    for mod in sys.modules.values():
        if mod and isinstance(mod, ModuleType) and hasattr(mod, name):
            obj = getattr(mod, name)
            if isinstance(obj, type):
                return obj

    # Optionally: scan local and global scopes in the call stack
    for frame_info in inspect.stack():
        frame = frame_info.frame
        if name in frame.f_locals:
            obj = frame.f_locals[name]
            if isinstance(obj, type):
                return obj
        if name in frame.f_globals:
            obj = frame.f_globals[name]
            if isinstance(obj, type):
                return obj

    # Not found
    return None
