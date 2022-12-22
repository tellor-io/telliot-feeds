from unittest import mock

import pytest

from telliot_feeds.sources.manual.string_query_manual_source import StringQueryManualSource


@pytest.mark.asyncio
async def test_string_query_input(capsys):
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["hello", ""]):
        result, _ = await StringQueryManualSource().fetch_new_datapoint()
        expected = "String query response to be submitted to oracle->: hello"
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert result == "hello"


@pytest.mark.asyncio
async def test_string_query_empty_input(capsys):
    with mock.patch("telliot_feeds.utils.input_timeout.InputTimeout.__call__", side_effect=["", ""]):
        result, _ = await StringQueryManualSource().fetch_new_datapoint()
        expected = "String query response to be submitted to oracle->: "
        captured_output = capsys.readouterr()
        assert result == ""
        assert expected in captured_output.out.strip()
