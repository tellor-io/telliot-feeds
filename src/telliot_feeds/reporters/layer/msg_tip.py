# type: ignore
from terra_sdk.core import Coin
from terra_sdk.core.msg import Msg

from telliot_feeds.proto.layer.oracle import MsgTip as MsgTip_pb
from telliot_feeds.reporters.layer.msg_submit_value import MsgSubmitValue


__all__ = ["MsgSubmitValue", "MsgTip"]

import attr


@attr.s
class MsgTip(Msg):
    """tip ``amount`` from ``tipper`` to ``query_data``.

    Args:
        tipper (str): msg_sender
        query_data (str): query_data
        amount (str): "__cosmos_base_v1_beta1__.Coin"
    """

    type_amino = "layer/MsgTip"
    """"""
    type_url = "/layer.oracle.MsgTip"
    """"""
    action = "send"
    """"""
    prototype = MsgTip_pb
    """"""

    tipper: str = attr.ib()
    query_data: bytes = attr.ib()
    amount: Coin = attr.ib(converter=Coin.parse)

    def to_amino(self) -> dict:
        return {
            "type": self.type_amino,
            "value": {
                "tipper": self.tipper,
                "query_data": self.query_data,
                "amount": self.amount.to_amino(),
            },
        }

    @classmethod
    def from_data(cls, data: dict):
        return cls(
            tipper=data["tipper"],
            query_data=data["query_data"],
            amount=Coin.from_data(data["amount"]),
        )

    def to_data(self) -> dict:
        return {
            "@type": self.type_url,
            "tipper": self.tipper,
            "query_data": self.query_data,
            "amount": self.amount.to_data(),
        }

    @classmethod
    def from_proto(cls, proto: MsgTip_pb):
        return cls(
            tipper=proto.tipper,
            query_data=proto.query_data,
            amount=Coin.from_proto(proto.amount),
        )

    def to_proto(self) -> MsgTip_pb:
        proto = MsgTip_pb()
        proto.tipper = self.tipper
        proto.query_data = self.query_data
        proto.amount = self.amount.to_proto()
        return proto
