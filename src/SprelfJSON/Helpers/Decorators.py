from __future__ import annotations

import functools
from typing import Callable, TypeVar, Hashable, Iterable


THash = TypeVar('THash', bound=Hashable)


def yield_unique(func: Callable[..., Iterable[THash]]) -> Callable[..., Iterable[THash]]:

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Iterable[THash]:
        s = set()
        for x in func(*args, **kwargs):
            if x not in s:
                s.add(x)
                yield x

    return wrapper
