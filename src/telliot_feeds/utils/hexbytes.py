from typing import cast
from typing import Type
from typing import Union

from hexbytes import HexBytes


class CustomHexBytes(HexBytes):
    """HexBytes with stricter construction and 0x-prefixed hex() output.

    - Disallows construction from int/bool types to avoid ambiguity
    - Ensures hex() returns a 0x-prefixed string for compatibility
    """

    def __new__(cls: Type[bytes], val: Union[bytearray, bytes, str]) -> "CustomHexBytes":
        if isinstance(val, (int, bool)):
            raise ValueError("Invalid value")
        return cast(CustomHexBytes, super().__new__(cls, val))

    def hex(self) -> str:  # type: ignore[override]
        h = super().hex()
        if not h.startswith("0x"):
            return "0x" + h
        return h
