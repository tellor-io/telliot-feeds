""" :mod:`telliot_feeds.dtypes.float_type`

"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from telliot_feeds.dtypes.value_type import ValueType


@dataclass
class UnsignedFloatType(ValueType):
    """Unsigned Float Type

    This class specifies the a floating point value
    using an ABI data type.  It also provides encoding/decoding
    to/from floating point values.

    """

    #: ABI Encoding for Unsigned Float value (default = ufixed256x6)
    abi_type: str = "ufixed256x6"

    @property
    def decimals(self) -> int:
        """Get precision from abi type"""
        mxn = self.abi_type[6:]
        m, n = mxn.split("x")
        return int(n)

    @property
    def nbits(self) -> int:
        """Get number of bits from abi type"""
        mxn = self.abi_type[6:]
        m, n = mxn.split("x")
        return int(m)

    def encode(self, value: float) -> bytes:
        """An encoder for float values

        This encoder converts a float value to the SpotPrice ABI
        data type.
        """

        decimal_value = Decimal(value).quantize(Decimal(10) ** -self.decimals)

        return super().encode(decimal_value)

    def decode(self, bytes_val: bytes) -> Any:
        """A decoder for float values

        This decoder converts from the SpotPrice ABI data type to
        a floating point value.
        """
        nbytes = self.nbits / 8

        if self.packed:
            if len(bytes_val) != nbytes:
                raise ValueError(f"Value must be {nbytes} bytes")

        intval = int.from_bytes(bytes_val, "big", signed=False)

        return intval / 10.0**self.decimals
