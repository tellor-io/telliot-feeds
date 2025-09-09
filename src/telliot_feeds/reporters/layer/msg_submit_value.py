# type: ignore
from terra_sdk.core.msg import Msg

from telliot_feeds.proto.layer.oracle import MsgSubmitValue as MsgSubmitValue_pb


__all__ = ["MsgSubmitValue"]

import attr


@attr.s
class MsgSubmitValue(Msg):
    """Submit oracle report revealing value from ``creator`` to ``query_data``.

    Args:
        creator (str): msg_sender
        query_data (str: query_data
        value (str): hex_value
    """

    type_amino = "layer/MsgSubmitValue"
    """"""
    type_url = "/layer.oracle.MsgSubmitValue"
    """"""
    action = "send"
    """"""
    prototype = MsgSubmitValue_pb
    """"""

    creator: str = attr.ib()
    query_data: bytes = attr.ib()
    value: str = attr.ib()

    def to_amino(self) -> dict:
        return {
            "type": self.type_amino,
            "value": {
                "creator": self.creator,
                "query_data": self.query_data,
                "value": self.value,
            },
        }

    @classmethod
    def from_data(cls, data: dict):
        return cls(
            creator=data["creator"],
            query_data=data["query_data"],
            value=data["value"],
        )

    def to_data(self) -> dict:
        return {
            "@type": self.type_url,
            "creator": self.creator,
            "query_data": self.query_data,
            "amount": self.amount.to_data(),
        }

    @classmethod
    def from_proto(cls, proto: MsgSubmitValue_pb):
        return cls(
            creator=proto.creator,
            query_data=proto.query_data,
            value=proto.value,
        )

    def to_proto(self) -> MsgSubmitValue_pb:
        proto = MsgSubmitValue_pb()
        proto.creator = self.creator
        proto.query_data = self.query_data
        proto.value = self.value
        return proto
