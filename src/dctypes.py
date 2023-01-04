from typing import TypeAlias, TypeVar

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
HTML: TypeAlias = str
T = TypeVar("T")
