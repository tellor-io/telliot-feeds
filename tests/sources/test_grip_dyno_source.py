from unittest.mock import patch

import pytest

from src.telliot_feeds.sources.manual.grip_dyno_manual_source import gripDynoManualSource
from telliot_feeds.utils.input_timeout import TimeoutOccurred


class TestGripDynoManualSource(pytest.TestCase):
    @patch("src.telliot_feeds.sources.manual.grip_dyno_manual_source.input_timeout")
    def test_parse_user_vals(self, mock_input):
        # Simulate user input
        mock_input.side_effect = [
            "w",  # Women's dataset
            "123.5",  # Right hand strength
            "134.5",  # Left hand strength
            "user_x_handle",  # X handle
            "user_github",  # Github username
            "7",  # Hours of sleep
        ]

        source = gripDynoManualSource()
        result = source.parse_user_vals()

        expected_result = (
            1,  # Women's dataset
            int(123.5 * 1e18),  # Right hand strength
            int(134.5 * 1e18),  # Left hand strength
            "user_x_handle",  # X handle
            "user_github",  # Github username
            7,  # Hours of sleep
        )

        self.assertEqual(result, expected_result)

    @patch("src.telliot_feeds.sources.manual.grip_dyno_manual_source.input_timeout")
    def test_parse_user_vals_defaults(self, mock_input):
        # Simulate user input with timeouts
        mock_input.side_effect = TimeoutOccurred

        source = gripDynoManualSource()
        result = source.parse_user_vals()

        expected_result = (
            0,  # Default to Men's dataset
            0,  # Default right hand strength
            0,  # Default left hand strength
            "@eth_denver_tellor_fan_2025",  # Default X handle
            "tellor_dev",  # Default Github username
            6,  # Default hours of sleep
        )

        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    pytest.main()
