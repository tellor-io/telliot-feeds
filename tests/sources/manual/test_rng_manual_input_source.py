from unittest import mock

import pytest

from telliot_feeds.sources.manual.tellor_rng_manual_source import TellorRNGManualInputSource


@pytest.mark.asyncio
async def test_rng_valid_input(capsys):
    with mock.patch(
        "telliot_feeds.utils.input_timeout.InputTimeout.__call__",
        side_effect=["0x2b563420722cbcfc84857129bef775e0dc5f1401", ""],
    ):
        result, _ = await TellorRNGManualInputSource().fetch_new_datapoint()
        expected = "TellorRNG value to be submitted on chain: 2b563420722cbcfc84857129bef775e0dc5f1401\nPress [ENTER] to continue"  # noqa: E501
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
        assert result == bytes.fromhex("2b563420722cbcfc84857129bef775e0dc5f1401")


@pytest.mark.asyncio
async def test_rng_invalid_input(capsys):
    with mock.patch(
        "telliot_feeds.utils.input_timeout.InputTimeout.__call__",
        side_effect=["exit", "0x2b563420722cbcfc84857129bef775e0dc5f1401", ""],
    ):
        _, _ = await TellorRNGManualInputSource().fetch_new_datapoint()
        expected = "Invalid input! Enter hex string value (32 byte size)"
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()


@pytest.mark.asyncio
async def test_rng_non_input(capsys):
    with mock.patch(
        "telliot_feeds.utils.input_timeout.InputTimeout.__call__",
        side_effect=["", "0x2b563420722cbcfc84857129bef775e0dc5f1401", ""],
    ):
        _, _ = await TellorRNGManualInputSource().fetch_new_datapoint()
        expected = "Invalid input! Not enough characters, Enter a hex string (example: 0x2b563420722cbcfc84857129bef775e0dc5f1401"  # noqa: E501
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()


@pytest.mark.asyncio
async def test_rng_non_bytes32_input(capsys):
    with mock.patch(
        "telliot_feeds.utils.input_timeout.InputTimeout.__call__",
        side_effect=[
            "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000954656c6c6f72524e470000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004d2",  # noqa: E501
            "0x2b563420722cbcfc84857129bef775e0dc5f1401",
            "",
        ],
    ):
        _, _ = await TellorRNGManualInputSource().fetch_new_datapoint()
        expected = "Invalid input! Exceeds total byte size for bytes32 encoding"
        captured_output = capsys.readouterr()
        assert expected in captured_output.out.strip()
