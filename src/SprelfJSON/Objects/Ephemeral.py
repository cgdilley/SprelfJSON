from __future__ import annotations

from typing import Generic, TypeVar, Any, Iterator, Iterable, Self
import copy
import functools

T = TypeVar('T')


#


class Ephemeral(Generic[T]):
    """
    This class is intended to be a wrapper over any kind of object, except that
    it will not be parsed or dumped as part of a JSONModel; it will only ever
    live in memory and then vanish.  As a result, the contents wrapped by this
    do not need to be JSON-serializable, as they will never interact with
    JSON, by design.

    It is intended that this wrapper mimics the functionality and identify
    of whatever it wraps, except for passing isinstance checks;
    for that, see Ephemeral.is_ephemeral()
    """
    __ephm_field__: str = "_ephm_value"
    __slots__ = (__ephm_field__,)
    __is_ephemeral__ = True

    def __new__(cls, value: T):
        return super().__new__(_build(value))

    def __init__(self, value: T):
        object.__setattr__(self, type(self).__ephm_field__, value)

    @property
    def value(self) -> T:
        return object.__getattribute__(self, type(self).__ephm_field__)

    @property
    def V(self) -> T:
        return self.value

    # Attribute delegation
    def __getattr__(self, name: str) -> Any:
        return getattr(self.value, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == type(self).__ephm_field__:
            object.__setattr__(self, name, value)
        else:
            setattr(self.value, name, value)

    def __delattr__(self, name: str) -> None:
        if name == type(self).__ephm_field__:
            raise AttributeError("Cannot delete Ephemeral internal state")
        delattr(self.value, name)

    def __dir__(self) -> list[str]:
        own = set(super().__dir__())
        try:
            other = set(dir(self.value))
        except Exception:
            other = set()
        return sorted(own | other)

    def __copy__(self) -> Ephemeral[T]:
        try:
            v = copy.copy(self.value)
        except Exception:
            v = self.value
        return type(self)(v)

    def __deepcopy__(self, memo) -> Ephemeral[T]:
        try:
            v = copy.deepcopy(self.value, memo)
        except Exception:
            v = self.value
        return type(self)(v)



    @classmethod
    def is_ephemeral(cls, obj: Any) -> bool:
        return isinstance(obj, cls) or getattr(obj, "__is_ephemeral__", False)

    @classmethod
    def unwrap(cls, o: Ephemeral[T] | T) -> T:
        return o.value if isinstance(o, Ephemeral) else o


def _build(value: T) -> type[Ephemeral[T]]:
    key = sorted((k
                  for k in ("__len__", "__iter__", "__contains__", "__enter__", "__exit__",
                            "__index__", "__int__", "__float__", "__complex__", "__bytes__",
                            "__hash__")
                  if hasattr(value, k)))
    new_cls: type[Ephemeral] = _get_proxy(tuple(key))
    return new_cls


@functools.cache
def _get_proxy(key: tuple[str, ...]) -> type[Ephemeral]:
    namespace: dict[str, Any] = {}

    namespace["__repr__"] = lambda self: f"{type(self).__name__}({self.value!r})"
    namespace["__str__"] = lambda self: f"{str(self.value)}"
    namespace["__bool__"] = lambda self: bool(self.value)

    namespace["__eq__"] = lambda self, other: self.value == (other.value if isinstance(other, Ephemeral) else other)
    namespace["__ne__"] = lambda self, other: self.value != (other.value if isinstance(other, Ephemeral) else other)
    namespace["__lt__"] = lambda self, other: self.value < (other.value if isinstance(other, Ephemeral) else other)
    namespace["__le__"] = lambda self, other: self.value <= (other.value if isinstance(other, Ephemeral) else other)
    namespace["__gt__"] = lambda self, other: self.value > (other.value if isinstance(other, Ephemeral) else other)
    namespace["__ge__"] = lambda self, other: self.value >= (other.value if isinstance(other, Ephemeral) else other)

    for dund in key:

        # namespace[dund] = lambda self: getattr(self.value, dund)()
        match dund:
            case "__len__":
                def __len__(self):
                    return len(self.value)

                namespace[dund] = __len__
            case "__iter__":
                def __iter__(self) -> Iterator:
                    return iter(self.value)

                namespace[dund] = __iter__
            case "__contains__":
                def __contains__(self, item: Any) -> bool:
                    return item in self.value

                namespace[dund] = __contains__
            case "__call__":
                def __call__(self, *args: Any, **kwargs: Any) -> Any:
                    return self.value(*args, **kwargs)

                namespace[dund] = __call__
            case "__enter__":
                def __enter__(self) -> Ephemeral[T]:
                    return self.value.__enter__()

                namespace[dund] = __enter__
            case "__exit__":
                def __exit__(self, *args: Any) -> Ephemeral[T]:
                    return self.value.__exit__(*args)

                namespace[dund] = __exit__
            case "__index__":
                def __index__(self) -> int:
                    return self.value.__index__()

                namespace[dund] = __index__
            case "__int__":
                def __int__(self) -> int:
                    return int(self.value)

                namespace[dund] = __int__
            case "__float__":
                def __float__(self) -> float:
                    return float(self.value)

                namespace[dund] = __float__
            case "__complex__":
                def __complex__(self) -> complex:
                    return complex(self.value)

                namespace[dund] = __complex__
            case "__bytes__":
                def __bytes__(self) -> bytes:
                    return bytes(self.value)

                namespace[dund] = __bytes__
            case "__hash__":
                def __hash__(self) -> int:
                    return hash(self.value)

                namespace[dund] = __hash__

    new_cls: type[Ephemeral] = type(f"EphmProxy[{','.join(key)}]", (Ephemeral,), namespace)
    return new_cls