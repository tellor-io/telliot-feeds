import os
import unittest.mock

import pytest

from telliot_feeds.utils.input_timeout import input_timeout
from telliot_feeds.utils.input_timeout import TimeoutOccurred


# Fixure to prevent pytest from capturing the input and producing a different error.
# Using "with capsys.disabled():" didn't work. It doesn't do the same as adding the "-s" flag, which is
# what we need. But this fixture works:
@pytest.fixture(scope="class")
def suspend_capture(pytestconfig):
    class suspend_guard:
        def __init__(self):
            self.capmanager = pytestconfig.pluginmanager.getplugin("capturemanager")

        def __enter__(self):
            self.capmanager.suspend_global_capture(in_=True)
            pass

        def __exit__(self, _1, _2, _3):
            self.capmanager.resume_global_capture()

    yield suspend_guard()


def is_ci_environment():
    """Check if running in a CI environment."""
    return os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")


def test_input_timeout(suspend_capture) -> None:
    """Test input_timeout() function."""
    if is_ci_environment():
        pytest.skip("This test fails in CI environments: PermissionError: [Errno 1] Operation not permitted")
    with suspend_capture:
        with pytest.raises(TimeoutOccurred):
            input_timeout(prompt="sup", timeout=0)


def test_input_timeout_ci() -> None:
    if not is_ci_environment():
        pytest.skip("This test is only relevant in CI environments")

    with unittest.mock.patch("telliot_feeds.utils.input_timeout.input_timeout_func") as mock_input:
        mock_input.side_effect = TimeoutOccurred()
        with pytest.raises(TimeoutOccurred):
            input_timeout(prompt="sup", timeout=0)
