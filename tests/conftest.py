from datetime import datetime, timedelta
from textwrap import dedent

import pytest

from scripts.check_contests import Contest


class FakeResponse:
    def __init__(self, body: bytes = b""):
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def fake_response():
    return FakeResponse


@pytest.fixture
def make_contest():
    def _make(
        contest_type: str,
        start: datetime,
        end: datetime | None = None,
    ) -> Contest:
        if end is None:
            end = start + timedelta(hours=2)

        contest_id = "abc999" if contest_type == "ABC" else "arc999"

        return Contest(
            contest_type=contest_type,
            name=f"Test {contest_type}",
            start=start,
            end=end,
            url=f"https://atcoder.jp/contests/{contest_id}",
        )

    return _make


@pytest.fixture
def make_ics():
    def _make(*events: str) -> bytes:
        body = "\n".join(dedent(event).strip() for event in events)

        return (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//test//EN\n"
            f"{body}\n"
            "END:VCALENDAR\n"
        ).encode()

    return _make