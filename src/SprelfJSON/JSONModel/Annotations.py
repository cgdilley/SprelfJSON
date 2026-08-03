from __future__ import annotations

from abc import ABC
from typing import Callable, Any, TypeVar, Generic, Iterable, Iterator
from dataclasses import dataclass

T = TypeVar("T")
TAlt = TypeVar("TAlt")


class AnnotationMetadata(ABC):

    def __repr__(self) -> str:
        return str(self)


class Description(AnnotationMetadata):
    def __init__(self, text: str):
        self.text = text

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.text!r})"


class DefaultFactory(AnnotationMetadata, Generic[T]):
    def __init__(self, factory: Callable[[], T]):
        self.factory = factory

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.factory!r})"


class Alternate(AnnotationMetadata, Generic[T, TAlt]):
    def __init__(self,
                 alt_type: type[TAlt],
                 transformer: Callable[[TAlt], T],
                 jsonifier: Callable[[T], TAlt] | None = None,
                 forced: bool = False):
        self.alt_type = alt_type
        self.transformer = transformer
        self.jsonifier = jsonifier
        self.forced = forced

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.alt_type.__name__})"


class Ignored(AnnotationMetadata):

    def __str__(self) -> str:
        return f"{type(self).__name__}()"


class Enumerated(AnnotationMetadata, Generic[T]):
    def __init__(self, values: list[T]):
        self.values = values

    def __str__(self) -> str:
        return f"{type(self).__name__}({','.join(map(str, self.values))})"


#


class AnnotationMetadataSet(Iterable[AnnotationMetadata]):

    def __init__(self, metadata: Iterable[AnnotationMetadata]):
        self.metadata = list(metadata)

    def __contains__(self, anno_type: type[AnnotationMetadata]) -> bool:
        return any(isinstance(anno, anno_type) for anno in self.metadata)

    def __getitem__(self, metadata_type: type[T]) -> T:
        for md in self.metadata:
            if isinstance(md, metadata_type):
                return md
        raise KeyError(f"No annotation of type '{metadata_type.__name__}' found in group")

    def get(self, anno_type: type[T]) -> T | None:
        for md in self.metadata:
            if isinstance(md, anno_type):
                return md
        return None

    def get_all(self, metadata_type: type[T]) -> list[T]:
        return [md for md in self.metadata if isinstance(md, metadata_type)]

    def __len__(self) -> int:
        return len(self.metadata)

    def __iter__(self) -> Iterator[AnnotationMetadata]:
        return iter(self.metadata)
