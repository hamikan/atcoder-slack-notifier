import base64
from datetime import date, datetime, time
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from icalendar import Calendar


JST = ZoneInfo("Asia/Tokyo")

CALENDARS = {
    "ABC": "https://calendar.google.com/calendar/u/0?cid=Y180MzA3MDIxZTE0ZDhhMzNlYzgzNjI5YmM1MWQ2OTEzMWMwNjMxOGJiNGQ1ZmRjOTYwODNlZDE2ODFmMGEwZWQ2QGdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20",
    "ARC": "https://calendar.google.com/calendar/u/0?cid=Y185NGJiMDZmYmI0MDA2NjEzM2VmOTlkNTQ2NDhiZjIzYjI4MTEwNzdjZjU0MWE0ZGMyZDJlYjFiODI1MmU2NmZhQGdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20",
}


def to_ics_url(calendar_url: str) -> str:
    query = parse_qs(urlparse(calendar_url).query)
    cid = query["cid"][0]

    padding = "=" * (-len(cid) % 4)
    calendar_id = base64.b64decode(cid + padding).decode()

    return (
        "https://calendar.google.com/calendar/ical/"
        f"{quote(calendar_id, safe='')}/public/basic.ics"
    )


def to_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=JST)
        return value.astimezone(JST)

    return datetime.combine(value, time.min, tzinfo=JST)


def get_upcoming_contests(calendar_url: str):
    with urlopen(to_ics_url(calendar_url), timeout=20) as response:
        calendar = Calendar.from_ical(response.read())

    now = datetime.now(JST)
    contests = []

    for event in calendar.walk("VEVENT"):
        start = to_datetime(event.decoded("DTSTART"))
        title = str(event.get("SUMMARY", ""))

        if start >= now:
            contests.append((start, title))

    return sorted(contests)


def main():
    for contest_type, calendar_url in CALENDARS.items():
        print(f"=== {contest_type} ===")

        contests = get_upcoming_contests(calendar_url)

        for start, title in contests[:3]:
            print(f"{start:%Y-%m-%d %H:%M}  {title}")

        print()


if __name__ == "__main__":
    main()