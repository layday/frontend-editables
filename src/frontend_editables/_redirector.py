"""
This module is adapted from https://github.com/pfmoore/editables,
released under the MIT licence.
It's bundled here to avoid having to request the installation of an additional
dependency from the frontend during the course of the editable installation.
It is therefore not possible to share the redirector module between multiple
editable installations and a new copy is made at a unique location
on installation.
"""

from collections.abc import Sequence
import importlib.util
import sys


def install_redirector(redirections: "dict[str, str]") -> None:
    class RedirectingFinder:
        @staticmethod
        def find_spec(fullname: str, path: "Sequence[bytes | str] | None", target: object = None):
            if "." in fullname or path is not None or fullname not in redirections:
                return None
            maybe_spec = importlib.util.spec_from_file_location(fullname, redirections[fullname])
            return maybe_spec

    for finder in sys.meta_path:
        if finder is RedirectingFinder:
            break
    else:
        sys.meta_path.append(
            # Protocols don't support optional members and we do not implement ``find_module``.
            RedirectingFinder,  # type: ignore
        )
