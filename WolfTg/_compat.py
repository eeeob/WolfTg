"""Backports for the Python versions below the ones that ship these natively.

Kept in one place so the rest of the package imports these unconditionally.
Drop this module (and its imports) once the supported floor reaches 3.11.
"""

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
    from typing import Never, Self
else:
    from enum import Enum

    from typing_extensions import Never, Self

    class StrEnum(str, Enum):
        """`enum.StrEnum` backport (3.11+).

        The `_generate_next_value_` override is the load-bearing part: a plain
        `class X(str, Enum)` turns `auto()` into "1", "2", ... instead of the
        lowercased member name, which would silently change every enum value
        sent over the wire.
        """

        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            return name.lower()

        def __str__(self) -> str:
            return str(self.value)


__all__ = (
    "Never",
    "Self",
    "StrEnum",
)
