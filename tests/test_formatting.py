from datetime import datetime

import pytest

from scripts.check_contests import (
    JST,
    format_date,
    format_scores,
    get_contest_id,
    get_time_notice,
)


def test_get_contest_id():
    assert (
        get_contest_id("https://atcoder.jp/contests/abc474")
        == "ABC474"
    )


def test_get_contest_id_with_trailing_slash():
    assert (
        get_contest_id("https://atcoder.jp/contests/arc229/")
        == "ARC229"
    )


def test_time_notice_is_empty_at_21():
    start = datetime(2026, 9, 5, 21, 0, tzinfo=JST)

    assert get_time_notice(start) == ""


def test_time_notice_is_shown_at_different_time():
    start = datetime(2026, 9, 5, 21, 30, tzinfo=JST)

    assert (
        get_time_notice(start)
        == "普段と開始時刻が異なるので気をつけてください。"
    )


def test_format_scores():
    assert (
        format_scores([100, 200, 300, 400])
        == "100 - 200 - 300 - 400"
    )


def test_format_scores_when_unpublished():
    assert format_scores(None) == "未公開"


@pytest.mark.parametrize(
    ("day", "weekday"),
    [
        (7, "月"),
        (8, "火"),
        (9, "水"),
        (10, "木"),
        (11, "金"),
        (12, "土"),
        (13, "日"),
    ],
)
def test_format_date(day, weekday):
    dt = datetime(2026, 9, day, 21, 0, tzinfo=JST)

    assert format_date(dt) == f"9月{day}日（{weekday}）"
