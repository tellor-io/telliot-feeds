"""Legacy DIVA datafeed tests.

Previously exercised Mumbai + DIVA pool assembly; that flow is no longer
maintained. The module is kept so CI can collect it without syntax/import
errors; all tests here are skipped.
"""
import pytest

pytestmark = pytest.mark.skip(reason="Old DIVA feed integration tests skipped; no longer maintained.")


def test_diva_feed_legacy_skipped() -> None:
    """Placeholder so this module reports as skipped rather than empty."""
    assert True
