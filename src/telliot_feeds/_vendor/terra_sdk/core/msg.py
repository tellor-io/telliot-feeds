from __future__ import annotations

from betterproto.lib.google.protobuf import Any as Any_pb

from telliot_feeds._vendor.terra_sdk.util.base import BaseTerraData


class Msg(BaseTerraData):
    def to_proto(self):
        raise NotImplementedError

    def pack_any(self) -> Any_pb:
        return Any_pb(type_url=self.type_url, value=bytes(self.to_proto()))

    # telliot: terra_sdk.util.parse_msg (the registry of every Cosmos message
    # type) is not vendored, so generic Msg deserialization is unavailable.
    # Concrete subclasses (MsgSubmitValue, MsgTip) implement their own.
    _NOT_VENDORED = "terra_sdk.util.parse_msg is not vendored; use from_data/from_proto on the concrete Msg subclass"

    @staticmethod
    def from_data(data: dict) -> Msg:
        raise NotImplementedError(Msg._NOT_VENDORED)

    @staticmethod
    def from_proto(proto: any) -> Msg:
        raise NotImplementedError(Msg._NOT_VENDORED)

    @staticmethod
    def unpack_any(any_pb: Any_pb) -> Msg:
        raise NotImplementedError(Msg._NOT_VENDORED)
