from datetime import datetime

from scripts.check_contests import JST, get_next_contest


def test_morning_selects_contest_before_13(make_contest):
    now = datetime(2026, 9, 6, 9, 0, tzinfo=JST)
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 6, 12, 30, tzinfo=JST),
    )

    assert get_next_contest([contest], now, False) == contest


def test_morning_does_not_select_contest_at_13(make_contest):
    now = datetime(2026, 9, 6, 9, 0, tzinfo=JST)
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 6, 13, 0, tzinfo=JST),
    )

    assert get_next_contest([contest], now, False) is None


def test_noon_selects_contest_at_13(make_contest):
    now = datetime(2026, 9, 6, 12, 0, tzinfo=JST)
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 6, 13, 0, tzinfo=JST),
    )

    assert get_next_contest([contest], now, False) == contest


def test_started_contest_is_not_selected(make_contest):
    now = datetime(2026, 9, 6, 13, 0, tzinfo=JST)
    contest = make_contest("ABC", now)

    assert get_next_contest([contest], now, False) is None


def test_contest_on_another_day_is_not_selected(make_contest):
    now = datetime(2026, 9, 6, 12, 0, tzinfo=JST)
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 7, 21, 0, tzinfo=JST),
    )

    assert get_next_contest([contest], now, False) is None


def test_selects_earliest_contest(make_contest):
    now = datetime(2026, 9, 6, 12, 0, tzinfo=JST)

    earlier = make_contest(
        "ARC",
        datetime(2026, 9, 6, 20, 0, tzinfo=JST),
    )
    later = make_contest(
        "ABC",
        datetime(2026, 9, 6, 21, 0, tzinfo=JST),
    )

    assert get_next_contest([later, earlier], now, False) == earlier


def test_abc_is_preferred_when_abc_and_arc_start_at_same_time(
    make_contest,
):
    now = datetime(2026, 9, 6, 12, 0, tzinfo=JST)
    start = datetime(2026, 9, 6, 21, 0, tzinfo=JST)

    abc = make_contest("ABC", start)
    arc = make_contest("ARC", start)

    assert get_next_contest([arc, abc], now, False) == abc


def test_force_next_contest_selects_nearest_future_contest(
    make_contest,
):
    now = datetime(2026, 9, 6, 12, 0, tzinfo=JST)

    later = make_contest(
        "ABC",
        datetime(2026, 9, 12, 21, 0, tzinfo=JST),
    )
    next_contest = make_contest(
        "ARC",
        datetime(2026, 9, 7, 21, 0, tzinfo=JST),
    )

    assert get_next_contest(
        [later, next_contest],
        now,
        True,
    ) == next_contest


def test_force_next_contest_does_not_select_started_contest(
    make_contest,
):
    now = datetime(2026, 9, 6, 21, 0, tzinfo=JST)
    contest = make_contest("ABC", now)

    assert get_next_contest([contest], now, True) is None