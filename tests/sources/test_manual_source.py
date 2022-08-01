import pytest

from telliot_feeds.dtypes.float_type import UnsignedFloatType
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.sources.manual_sources.numeric_response import ManualSource


class FakeQuery(AbiQuery):

    value: str = ""

    @property
    def value_type(self) -> UnsignedFloatType:
        """Data type returned for a DailyVolatility query. Returns a volitility index in decimals.

        - abi_type: ufixed256x18 (18 decimals of precision)
        - packed: false

        """
        return UnsignedFloatType(abi_type=self.value, packed=False)


query = FakeQuery()
source = ManualSource(query)


@pytest.mark.asyncio
async def test_one_number_response(monkeypatch):
    query.value = "(fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "[1]")
    result, _ = await source.fetch_new_datapoint()
    assert result == [1]


@pytest.mark.asyncio
async def test_two_number_response(monkeypatch):
    query.value = "(fixed256x18,fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "1,2")
    result, _ = await source.fetch_new_datapoint()
    assert result == [1, 2]


@pytest.mark.asyncio
async def test_three_number_response(monkeypatch):
    query.value = "(fixed256x18,fixed256x18,fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "[-1,2,3]")
    result, _ = await source.fetch_new_datapoint()
    assert result == [-1, 2, 3]


@pytest.mark.asyncio
async def test_four_number_response(monkeypatch):
    query.value = "(fixed256x18[],fixed256x18,fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "[(1,2,3),2,3]")
    result, _ = await source.fetch_new_datapoint()
    assert result == [(1, 2, 3), 2, 3]


@pytest.mark.asyncio
async def test_five_number_response(monkeypatch):
    query.value = "(fixed256x18[],fixed256x18,fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "[(1,i,3),2,3]")
    result, _ = await source.fetch_new_datapoint()
    assert result is None


@pytest.mark.asyncio
async def test_six_number_response(monkeypatch):
    query.value = "(fixed256x18[])"
    monkeypatch.setattr("builtins.input", lambda _: "[1,2,3]")
    result, _ = await source.fetch_new_datapoint()
    assert result == [(1, 2, 3)]


@pytest.mark.asyncio
async def test_7_number_response(monkeypatch):
    query.value = "fixed256x18[]"
    monkeypatch.setattr("builtins.input", lambda _: "1,2,3")
    result, _ = await source.fetch_new_datapoint()
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_8_number_response(monkeypatch):
    query.value = "fixed256x18[]"
    monkeypatch.setattr("builtins.input", lambda _: "1")
    result, _ = await source.fetch_new_datapoint()
    assert result == [1]


@pytest.mark.asyncio
async def test_9_number_response(monkeypatch):
    query.value = "fixed256x18"
    monkeypatch.setattr("builtins.input", lambda _: "(1)")
    result, _ = await source.fetch_new_datapoint()
    assert result is None


@pytest.mark.asyncio
async def test_10_number_response(monkeypatch):
    query.value = "(fixed256x18[],fixed256x18,fixed256x18)"
    monkeypatch.setattr("builtins.input", lambda _: "[2,(1,2,3),3]")
    result, _ = await source.fetch_new_datapoint()
    assert result is None
