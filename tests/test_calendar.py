from datetime import datetime, timedelta
from urllib.error import URLError

import pytest

import scripts.check_contests as cc
from scripts.check_contests import (
    JST,
    Contest,
    get_all_contests,
    get_contest_type,
    get_contests,
    get_ics_url,
)


@pytest.mark.parametrize(
    ("calendar_type", "name", "expected"),
    [
        ("ABC", "AtCoder Beginner Contest 474", "ABC"),
        ("ARC", "AtCoder Regular Contest 229", "ARC"),
        ("ARC", "AtCoder Regular Contest-- 229", "ARC--"),
        ("ARC", "AtCoder Regular Contest++ 229", "ARC++"),
    ],
)
def test_get_contest_type(calendar_type, name, expected):
    assert get_contest_type(calendar_type, name) == expected


def test_get_ics_url():
    url = get_ics_url("abc+def@example.com")

    assert url == (
        "https://calendar.google.com/calendar/ical/"
        "abc%2Bdef%40example.com/public/basic.ics"
    )


def test_get_contests(monkeypatch, make_ics, fake_response):
    ics = make_ics(
        """
        BEGIN:VEVENT
        UID:test@example.com
        DTSTART:20260905T120000Z
        DTEND:20260905T140000Z
        STATUS:CONFIRMED
        SUMMARY:AtCoder Regular Contest 229
        DESCRIPTION:https://atcoder.jp/contests/arc229
        END:VEVENT
        """
    )

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda url, timeout: fake_response(ics),
    )

    contests = get_contests("ARC", "calendar@example.com")

    assert contests == [
        Contest(
            contest_type="ARC",
            name="AtCoder Regular Contest 229",
            start=datetime(2026, 9, 5, 21, 0, tzinfo=JST),
            end=datetime(2026, 9, 5, 23, 0, tzinfo=JST),
            url="https://atcoder.jp/contests/arc229",
        )
    ]


def test_get_contests_detects_arc_minus_minus(
    monkeypatch,
    make_ics,
    fake_response,
):
    ics = make_ics(
        """
        BEGIN:VEVENT
        UID:test@example.com
        DTSTART:20260906T120000Z
        DTEND:20260906T140000Z
        STATUS:CONFIRMED
        SUMMARY:AtCoder Regular Contest-- 229
        DESCRIPTION:https://atcoder.jp/contests/arc229
        END:VEVENT
        """
    )

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda url, timeout: fake_response(ics),
    )

    contests = get_contests("ARC", "calendar@example.com")

    assert len(contests) == 1
    assert contests[0].contest_type == "ARC--"


def test_get_contests_ignores_arc_plus_plus(
    monkeypatch,
    make_ics,
    fake_response,
):
    ics = make_ics(
        """
        BEGIN:VEVENT
        UID:test@example.com
        DTSTART:20260906T120000Z
        DTEND:20260906T143000Z
        STATUS:CONFIRMED
        SUMMARY:AtCoder Regular Contest++ 230
        DESCRIPTION:https://atcoder.jp/contests/arc230
        END:VEVENT
        """
    )

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda url, timeout: fake_response(ics),
    )

    assert get_contests("ARC", "calendar@example.com") == []


@pytest.mark.parametrize(
    "event",
    [
        """
        BEGIN:VEVENT
        DTSTART:20260905T120000Z
        DTEND:20260905T140000Z
        STATUS:CANCELLED
        SUMMARY:Test
        DESCRIPTION:https://atcoder.jp/contests/abc999
        END:VEVENT
        """,
        """
        BEGIN:VEVENT
        DTEND:20260905T140000Z
        STATUS:CONFIRMED
        SUMMARY:Test
        DESCRIPTION:https://atcoder.jp/contests/abc999
        END:VEVENT
        """,
        """
        BEGIN:VEVENT
        DTSTART:20260905T120000Z
        STATUS:CONFIRMED
        SUMMARY:Test
        DESCRIPTION:https://atcoder.jp/contests/abc999
        END:VEVENT
        """,
        """
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20260905
        DTEND;VALUE=DATE:20260906
        STATUS:CONFIRMED
        SUMMARY:Test
        DESCRIPTION:https://atcoder.jp/contests/abc999
        END:VEVENT
        """,
        """
        BEGIN:VEVENT
        DTSTART:20260905T140000Z
        DTEND:20260905T120000Z
        STATUS:CONFIRMED
        SUMMARY:Test
        DESCRIPTION:https://atcoder.jp/contests/abc999
        END:VEVENT
        """,
        """
        BEGIN:VEVENT
        DTSTART:20260905T120000Z
        DTEND:20260905T140000Z
        STATUS:CONFIRMED
        SUMMARY:Test
        DESCRIPTION:https://example.com/abc999
        END:VEVENT
        """,
    ],
)
def test_get_contests_ignores_invalid_events(
    monkeypatch,
    make_ics,
    fake_response,
    event,
):
    ics = make_ics(event)

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda url, timeout: fake_response(ics),
    )

    assert get_contests("ABC", "calendar@example.com") == []


def test_get_contests_propagates_network_error(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError("network error")

    monkeypatch.setattr(cc, "urlopen", fail)

    with pytest.raises(URLError):
        get_contests("ABC", "calendar@example.com")


def test_get_all_contests(monkeypatch, make_contest):
    start = datetime(2026, 9, 5, 21, 0, tzinfo=JST)

    abc = make_contest("ABC", start)
    arc = make_contest("ARC", start + timedelta(days=1))

    calls = []

    def fake_get_contests(contest_type, calendar_id):
        calls.append((contest_type, calendar_id))

        if contest_type == "ABC":
            return [abc]

        return [arc]

    monkeypatch.setattr(cc, "get_contests", fake_get_contests)

    assert get_all_contests() == [abc, arc]

    assert calls == [
        ("ABC", cc.CALENDARS["ABC"]),
        ("ARC", cc.CALENDARS["ARC"]),
    ]