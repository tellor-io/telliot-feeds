from telliot_feeds.utils.decode import bytes_from_string


def test_bytes_from_string():
    """Test successfully casting string to bytes"""
    status, result = bytes_from_string("0x0000000000000000000000000000000000000000000000000000000000000040", "")

    assert status.ok
    assert (
        result
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40"  # noqa: E501
    )

    status, result = bytes_from_string("0000000000000000000000000000000000000000000000000000000000000040", "test")

    assert status.ok
    assert (
        result
        == b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40"  # noqa: E501
    )


def test_bytes_from_string_fail(capfd):
    """Test failing to cast string to bytes"""
    status, result = bytes_from_string("invalidstring", "bazinga", print)

    assert not status.ok
    assert result is None
    assert "Error('Non-hexadecimal digit found')" in status.error
    assert "bazinga" in capfd.readouterr().out
