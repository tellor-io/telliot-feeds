# type: ignore
from __future__ import annotations

from asyncio import AbstractEventLoop
from asyncio import get_event_loop
from json import JSONDecodeError
from typing import List
from typing import Optional
from typing import Union

import nest_asyncio
from aiohttp import ClientSession
from multidict import CIMultiDict

from telliot_feeds._vendor.terra_sdk.client.lcd.api.auth import AsyncAuthAPI
from telliot_feeds._vendor.terra_sdk.client.lcd.api.auth import AuthAPI
from telliot_feeds._vendor.terra_sdk.client.lcd.api.tx import AsyncTxAPI
from telliot_feeds._vendor.terra_sdk.client.lcd.api.tx import TxAPI
from telliot_feeds._vendor.terra_sdk.client.lcd.params import APIParams
from telliot_feeds._vendor.terra_sdk.client.lcd.wallet import AsyncWallet
from telliot_feeds._vendor.terra_sdk.client.lcd.wallet import Wallet
from telliot_feeds._vendor.terra_sdk.core import Coins
from telliot_feeds._vendor.terra_sdk.core import Dec
from telliot_feeds._vendor.terra_sdk.core import Numeric
from telliot_feeds._vendor.terra_sdk.exceptions import LCDResponseError
from telliot_feeds._vendor.terra_sdk.key.key import Key
from telliot_feeds._vendor.terra_sdk.util.json import dict_to_data
from telliot_feeds._vendor.terra_sdk.util.url import urljoin


class AsyncLCDClient:
    def __init__(
        self,
        url: str,
        chain_id: Optional[str] = None,
        gas_prices: Optional[Coins.Input] = None,
        gas_adjustment: Optional[Numeric.Input] = None,
        loop: Optional[AbstractEventLoop] = None,
        _create_session: bool = True,
    ):
        if loop is None:
            loop = get_event_loop()
        self.loop = loop
        if _create_session:
            self.session = ClientSession(headers={"Accept": "application/json"}, loop=self.loop)

        self.chain_id = chain_id
        self.url = url
        self.last_request_height = None

        self.gas_prices = Coins(gas_prices) if gas_prices else Coins.from_str("0.000025loya")
        self.gas_adjustment = gas_adjustment if gas_adjustment else Numeric.parse(1.75)

        # Only the LCD modules the layer reporter actually uses are wired up:
        # auth (account number / sequence) and tx (fee estimation, broadcast).
        self.auth = AsyncAuthAPI(self)
        self.tx = AsyncTxAPI(self)

    def wallet(self, key: Key) -> AsyncWallet:
        """Creates a :class:`AsyncWallet` object from a key.

        Args:
            key (Key): key implementation
        """
        return AsyncWallet(self, key)

    async def _get(
        self,
        endpoint: str,
        params: Optional[Union[APIParams, CIMultiDict, list, dict]] = None,
        # raw: bool = False
    ):
        if params and hasattr(params, "to_dict") and callable(getattr(params, "to_dict")):  # noqa
            params = params.to_dict()

        async with self.session.get(urljoin(self.url, endpoint), params=params) as response:
            try:
                result = await response.json(content_type=None)
            except JSONDecodeError:
                raise LCDResponseError(message=str(response.reason), response=response)
            if not 200 <= response.status < 299:
                raise LCDResponseError(message=str(result), response=response)
        self.last_request_height = result.get("height") if result else self.last_request_height
        return result  # if raw else result["result"]

    async def _post(self, endpoint: str, data: Optional[dict] = None):  # , raw: bool = False
        async with self.session.post(urljoin(self.url, endpoint), json=data and dict_to_data(data)) as response:
            try:
                result = await response.json(content_type=None)
            except JSONDecodeError:
                raise LCDResponseError(message=str(response.reason), response=response)
            if not 200 <= response.status < 299:
                raise LCDResponseError(message=result.get("message"), response=response)
        self.last_request_height = result.get("height") if result else self.last_request_height
        return result  # if raw else result["result"]

    async def _search(
        self,
        events: List[list],
        params: Optional[Union[APIParams, CIMultiDict, list, dict]] = None,
        # raw: bool = False
    ):

        actual_params: CIMultiDict = CIMultiDict()

        for event in events:
            if event[0] == "tx.height":
                actual_params.add("events", f"{event[0]}={event[1]}")
            else:
                actual_params.add("events", f"{event[0]}='{event[1]}'")
        if params:
            for p in params:
                actual_params.add(p, params[p])

        async with self.session.get(urljoin(self.url, "/cosmos/tx/v1beta1/txs"), params=actual_params) as response:
            try:
                result = await response.json(content_type=None)
            except JSONDecodeError:
                raise LCDResponseError(message=str(response.reason), response=response)
            if not 200 <= response.status < 299:
                raise LCDResponseError(message=str(result), response=response)
        self.last_request_height = result.get("height") if result else self.last_request_height
        return result  # if raw else result["result"]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()


class LCDClient(AsyncLCDClient):
    """An object representing a connection to a node running the Terra LCD server."""

    url: str
    """URL endpoint of LCD server."""

    chain_id: str
    """Chain ID of blockchain network connecting to."""

    gas_prices: Coins.Input
    """Gas prices to use for automatic fee estimation."""

    gas_adjustment: Union[str, float, int, Dec]
    """Gas adjustment factor for automatic fee estimation."""

    last_request_height: Optional[int]  # type: ignore
    """Height of response of last-made made LCD request."""

    auth: AuthAPI
    """:class:`AuthAPI<terra_sdk.client.lcd.api.auth.AuthAPI>`."""

    tx: TxAPI
    """:class:`TxAPI<terra_sdk.client.lcd.api.tx.TxAPI>`."""

    def __init__(
        self,
        url: str,
        chain_id: str = None,
        gas_prices: Optional[Coins.Input] = None,
        gas_adjustment: Optional[Numeric.Input] = None,
    ):
        super().__init__(
            url,
            chain_id,
            gas_prices,
            gas_adjustment,
            _create_session=False,
            loop=nest_asyncio.apply(get_event_loop()),
        )

        self.auth = AuthAPI(self)
        self.tx = TxAPI(self)

    async def __aenter__(self):
        raise NotImplementedError("async context manager not implemented - you probably want AsyncLCDClient")

    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError("async context manager not implemented - you probably want AsyncLCDClient")

    def wallet(self, key: Key) -> Wallet:  # type: ignore
        """Creates a :class:`Wallet` object from a key for easy transaction creating and
        signing.

        Args:
            key (Key): key implementation
        """
        return Wallet(self, key)

    async def _get(self, *args, **kwargs):
        # session has to be manually created and torn down for each HTTP request in a
        # synchronous client
        self.session = ClientSession(headers={"Accept": "application/json"}, loop=self.loop)
        try:
            result = await super()._get(*args, **kwargs)
        finally:
            await self.session.close()
        return result

    async def _post(self, *args, **kwargs):
        # session has to be manually created and torn down for each HTTP request in a
        # synchronous client
        self.session = ClientSession(headers={"Accept": "application/json"}, loop=self.loop)
        try:
            result = await super()._post(*args, **kwargs)
        finally:
            await self.session.close()
        return result

    async def _search(self, *args, **kwargs):
        # session has to be manually created and torn down for each HTTP request in a
        # synchronous client
        self.session = ClientSession(headers={"Accept": "application/json"}, loop=self.loop)
        try:
            result = await super()._search(*args, **kwargs)
        finally:
            await self.session.close()
        return result
