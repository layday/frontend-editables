from collections.abc import Iterable
from typing import Hashable, TypeVar

_T = TypeVar("_T", bound=Hashable)


class _GenericGetitemMeta(type):
    def __getitem__(self, value: object) -> None:
        ...


class GenericGetitem(metaclass=_GenericGetitemMeta):
    pass


def uniq(it: "Iterable[_T]") -> "list[_T]":
    return list(dict.fromkeys(it))
