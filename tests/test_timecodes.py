from interview_review.timecodes import format_range, format_timestamp, parse_timestamp


def test_format_timestamp() -> None:
    assert format_timestamp(4280.9) == "01:11:21"


def test_parse_timestamp() -> None:
    assert parse_timestamp("01:11:20") == 4280
    assert parse_timestamp("11:20") == 680


def test_format_range_collapses_equal_values() -> None:
    assert format_range(10.1, 10.4) == "00:00:10"

