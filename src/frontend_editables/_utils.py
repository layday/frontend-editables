from collections.abc import Iterable
from typing import Hashable, TypeVar

_T = TypeVar("_T", bound=Hashable)


def uniq(it: "Iterable[_T]") -> "list[_T]":
    return list(dict.fromkeys(it))
