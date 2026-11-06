import pytest

from bcsfe import core


@pytest.mark.parametrize("value", [0, 1, 127, 128, 300, 16383, 16384, 2**21, 2**27 - 1])
def test_variable_length_int_round_trip(value: int) -> None:
    data = core.Data()
    data.write_variable_length_int(value)
    data.reset_pos()
    assert data.read_variable_length_int() == value
    assert data.get_pos() == len(data)


def test_typed_round_trip() -> None:
    data = core.Data()
    data.write_int(-5)
    data.write_short(-2)
    data.write_byte(-1)
    data.write_bool(True)
    data.write_double(1.5)
    data.write_string("にゃんこ")
    data.write_int_list([1, 2, 3])
    data.reset_pos()
    assert data.read_int() == -5
    assert data.read_short() == -2
    assert data.read_byte() == -1
    assert data.read_bool() is True
    assert data.read_double() == 1.5
    assert data.read_string() == "にゃんこ"
    assert data.read_int_list() == [1, 2, 3]


def test_read_past_end_raises() -> None:
    data = core.Data(b"\x01\x00")
    with pytest.raises(core.EndOfDataError, match="offset 0"):
        data.read_int()


def test_negative_length_raises() -> None:
    data = core.Data(b"\x00" * 8)
    data.set_pos(4)
    with pytest.raises(core.EndOfDataError):
        data.read_to_end(remaining_data=8)


def test_timestamp_helpers_round_trip() -> None:
    from bcsfe.core.io.save import from_timestamp, to_timestamp

    for ts in [0.0, 86400.0, 1_700_000_000.0]:
        assert to_timestamp(from_timestamp(ts)) == ts
