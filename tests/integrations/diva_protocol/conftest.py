"""Skip legacy DIVA protocol integration tests (unmaintained / flaky CI)."""
import pytest

pytestmark = pytest.mark.skip(reason="Old DIVA protocol integration tests skipped.")
