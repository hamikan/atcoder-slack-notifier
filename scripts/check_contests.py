import json
import os
from dataclasses import dataclass
from datetime import datetime
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from icalendar import Calendar


JST = ZoneInfo("Asia/Tokyo")

CALENDARS = {
    "ABC": "c_4307021e14d8a33ec83629bc51d69131c06318bb4d5fdc96083ed1681f0a0ed6@group.calendar.google.com",
    "ARC": "c_94bb06fbb40066133ef99d54648bf23b2811077cf541a4dc2d2eb1b8252e66fa@group.calendar.google.com",
}

EARLY_THRESHOLD_HOUR = 13

WEEKDAYS = "月火水木金土日"


@dataclass(frozen=True)
class Contest:
    contest_type: str
    name: str
    start: datetime
    end: datetime
    url: str


def get_ics_url(calendar_id: str) -> str:
    return (
        "https://calendar.google.com/calendar/ical/"
        f"{quote(calendar_id, safe='')}/public/basic.ics"
    )


def get_contests(contest_type: str, calendar_id: str) -> list[Contest]:
    with urlopen(get_ics_url(calendar_id), timeout=20) as response:
        calendar = Calendar.from_ical(response.read())

    contests = []

    for event in calendar.walk("VEVENT"):
        status = str(event.get("STATUS", ""))

        if status != "CONFIRMED":
            continue

        if event.get("DTSTART") is None or event.get("DTEND") is None:
            continue

        start = event.decoded("DTSTART")
        end = event.decoded("DTEND")

        if not isinstance(start, datetime) or not isinstance(end, datetime):
            continue

        start = start.astimezone(JST)
        end = end.astimezone(JST)

        if end <= start:
            continue

        url = str(event.get("DESCRIPTION", "")).strip()

        if not url.startswith("https://atcoder.jp/contests/"):
            continue

        contests.append(
            Contest(
                contest_type=contest_type,
                name=str(event.get("SUMMARY", "")),
                start=start,
                end=end,
                url=url,
            )
        )

    return contests


def get_all_contests() -> list[Contest]:
    contests = []

    for contest_type, calendar_id in CALENDARS.items():
        contests.extend(get_contests(contest_type, calendar_id))

    return contests


def get_next_contest(
    contests: list[Contest],
    now: datetime,
    force_next_contest: bool,
) -> Contest | None:
    if force_next_contest:
        candidates = [
            contest
            for contest in contests
            if now < contest.start
        ]
    elif now.hour < 12:
        candidates = [
            contest
            for contest in contests
            if contest.start.date() == now.date()
            and now < contest.start
            and contest.start.hour < EARLY_THRESHOLD_HOUR
        ]
    else:
        candidates = [
            contest
            for contest in contests
            if contest.start.date() == now.date()
            and now < contest.start
            and contest.start.hour >= EARLY_THRESHOLD_HOUR
        ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda contest: (
            contest.start,
            contest.contest_type != "ABC",
        ),
    )


def get_contest_id(contest_url: str) -> str:
    return contest_url.rstrip("/").split("/")[-1].upper()


def get_scores(contest_url: str) -> list[int] | None:
    request = Request(
        f"{contest_url}?lang=ja",
        headers={"User-Agent": "atcoder-slack-notifier"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            soup = BeautifulSoup(response.read(), "html.parser")
    except (URLError, TimeoutError) as error:
        print(f"Failed to get scores: {error}")
        return None

    heading = soup.find("h3", string="配点")
    if heading is None:
        return None

    table = heading.find_next("table")
    if table is None:
        return None

    scores = []

    for row in table.select("tbody tr"):
        cells = row.find_all("td")

        if len(cells) != 2:
            continue

        score = cells[1].get_text(strip=True)

        if not score.isdigit():
            return None

        scores.append(int(score))

    return scores or None


def get_time_notice(start: datetime) -> str:
    if start.hour == 21 and start.minute == 0:
        return ""

    return "普段と開始時刻が異なるので気をつけてください。"


def format_scores(scores: list[int] | None) -> str:
    if scores is None:
        return "未公開"

    return " - ".join(map(str, scores))


def format_date(dt: datetime) -> str:
    weekday = WEEKDAYS[dt.weekday()]
    return f"{dt.month}月{dt.day}日（{weekday}）"


def send_slack_notification(contest: Contest) -> None:
    webhook_url = os.environ["SLACK_WORKFLOW_WEBHOOK_URL"]

    scores = get_scores(contest.url)
    duration = int((contest.end - contest.start).total_seconds() // 60)

    payload = {
        "channel_id": os.environ["SLACK_CHANNEL_ID"],
        "contest_type": contest.contest_type,
        "contest_id": get_contest_id(contest.url),
        "contest_name": contest.name,
        "contest_date": format_date(contest.start),
        "start_time": contest.start.strftime("%H:%M"),
        "end_time": contest.end.strftime("%H:%M"),
        "duration": f"{duration}分",
        "contest_url": contest.url,
        "scores": format_scores(scores),
        "time_notice": get_time_notice(contest.start),
    }

    request = Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=20) as response:
        print(response.read().decode())


def main() -> None:
    now = datetime.now(JST)
    force_next_contest = os.environ.get("FORCE_NEXT_CONTEST") == "true"

    contests = get_all_contests()
    contest = get_next_contest(contests, now, force_next_contest)

    if contest is None:
        print("No contest to notify.")
        return

    print(
        f"Notify: "
        f"{contest.contest_type} "
        f"{contest.name}"
    )

    send_slack_notification(contest)


if __name__ == "__main__":
    main()