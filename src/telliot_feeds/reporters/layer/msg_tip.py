from terra_sdk.core.coins import Coin
from terra_sdk.core.msg import Msg

from telliot_feeds.proto.layer.oracle import MsgTip as MsgTip_pb


__all__ = ["MsgTip"]

import attr


@attr.s
class MsgTip(Msg):
    """Tips the amount from ``tipper`` to ``query_data``.
    (layerd tx oracle tip [tipper] [query_data] [amount] [flags])
    Args:
        tipper (str): msg_sender
        query_data (str: query_data
        amount (Coin): (denom, amount)
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
    amount: Coin = attr.ib()

    def to_amino(self) -> dict:
        return {
            "type": self.type_amino,
            "value": {
                "tipper": self.tipper,
                "query_data": self.query_data,
                "amount": self.amount,
            },
        }

    @classmethod
    def from_data(cls, data: dict):
        return cls(
            tipper=data["tipper"],
            query_data=data["query_data"],
            amount=data["amount"],
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
            amount=proto.amount,
        )

    def to_proto(self) -> MsgTip_pb:
        proto = MsgTip_pb()
        proto.tipper = self.tipper
        proto.query_data = self.query_data
        proto.amount = self.amount
        return proto
