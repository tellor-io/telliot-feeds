from tkinter.tix import Tree
import pytest
from telliot_feeds.utils.log import get_logger
from telliot_feeds.feeds.snapshot_feed import snapshot_feed

logger = get_logger(__name__)

@pytest.mark.asyncio
async def test_snapshot_zero_response(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda : "0")
    (value, _) = await snapshot_feed.source.fetch_new_datapoint()
    assert type(value) is bool
    assert value is False

@pytest.mark.asyncio
async def test_snapshot_one_response(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda : "1")
    (value, _) = await snapshot_feed.source.fetch_new_datapoint()
    assert type(value) is bool
    assert value is True
    

@pytest.mark.asyncio
async def test_snapshot_false_response(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda : "false")
    (value, _) = await snapshot_feed.source.fetch_new_datapoint()
    assert type(value) is bool
    assert value is False

@pytest.mark.asyncio
async def test_snapshot_true_response(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda : "true")
    (value, _) = await snapshot_feed.source.fetch_new_datapoint()
    assert type(value) is bool
    assert value is True

@pytest.mark.asyncio
async def test_snapshot_error_response(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda : "5")
    monkeypatch.setattr("builtins.input", lambda : "0")
    (value, _) = await snapshot_feed.source.fetch_new_datapoint()
    
    assert type(value) is bool
    assert value is False