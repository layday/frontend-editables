from collections.abc import Iterable
import hashlib
from typing import Hashable, TypeVar

_T = TypeVar("_T", bound=Hashable)


def uniq(it: "Iterable[_T]") -> "list[_T]":
    return list(dict.fromkeys(it))


def shasum(*values: object) -> str:
    return hashlib.sha256("".join(map(str, values)).encode()).hexdigest()[:32]
