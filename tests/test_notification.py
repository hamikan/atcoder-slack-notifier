import json
from datetime import datetime
from urllib.error import URLError

import pytest

import scripts.check_contests as cc
from scripts.check_contests import (
    JST,
    Contest,
    send_slack_notification,
)


def test_send_slack_notification(
    monkeypatch,
    fake_response,
):
    contest = Contest(
        contest_type="ARC",
        name="AtCoder Regular Contest 229",
        start=datetime(2026, 9, 5, 21, 30, tzinfo=JST),
        end=datetime(2026, 9, 5, 23, 30, tzinfo=JST),
        url="https://atcoder.jp/contests/arc229",
    )

    monkeypatch.setenv(
        "SLACK_WORKFLOW_WEBHOOK_URL",
        "https://example.com/webhook",
    )
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123456789")
    monkeypatch.setattr(
        cc,
        "get_scores",
        lambda url: [400, 500, 600],
    )

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return fake_response(b'{"ok":true}')

    monkeypatch.setattr(cc, "urlopen", fake_urlopen)

    send_slack_notification(contest)

    request = captured["request"]
    payload = json.loads(request.data.decode())

    assert request.get_method() == "POST"

    assert payload == {
        "channel_id": "C123456789",
        "contest_type": "ARC",
        "contest_id": "ARC229",
        "contest_name": "AtCoder Regular Contest 229",
        "contest_date": "9月5日（土）",
        "start_time": "21:30",
        "end_time": "23:30",
        "duration": "120分",
        "contest_url": "https://atcoder.jp/contests/arc229",
        "scores": "400 - 500 - 600",
        "time_notice": "普段と開催日時が異なるので気をつけてください。",
    }


def test_send_slack_notification_propagates_network_error(
    monkeypatch,
    make_contest,
):
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 5, 21, 0, tzinfo=JST),
    )

    monkeypatch.setenv(
        "SLACK_WORKFLOW_WEBHOOK_URL",
        "https://example.com/webhook",
    )
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123456789")
    monkeypatch.setattr(cc, "get_scores", lambda url: None)

    def fail(*args, **kwargs):
        raise URLError("network error")

    monkeypatch.setattr(cc, "urlopen", fail)

    with pytest.raises(URLError):
        send_slack_notification(contest)


def test_main_sends_selected_contest(
    monkeypatch,
    make_contest,
):
    contest = make_contest(
        "ABC",
        datetime(2026, 9, 6, 21, 0, tzinfo=JST),
    )

    contests = [contest]

    monkeypatch.setenv("FORCE_NEXT_CONTEST", "true")
    monkeypatch.setattr(cc, "get_all_contests", lambda: contests)

    def fake_get_next_contest(
        received,
        now,
        force_next_contest,
    ):
        assert received == contests
        assert force_next_contest is True
        return contest

    monkeypatch.setattr(
        cc,
        "get_next_contest",
        fake_get_next_contest,
    )

    sent = []

    monkeypatch.setattr(
        cc,
        "send_slack_notification",
        sent.append,
    )

    cc.main()

    assert sent == [contest]


def test_main_does_not_send_when_no_contest(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("FORCE_NEXT_CONTEST", raising=False)
    monkeypatch.setattr(cc, "get_all_contests", lambda: [])

    def fake_get_next_contest(
        contests,
        now,
        force_next_contest,
    ):
        assert force_next_contest is False
        return None

    monkeypatch.setattr(
        cc,
        "get_next_contest",
        fake_get_next_contest,
    )

    def fail_if_called(contest):
        pytest.fail("Slack notification should not be sent")

    monkeypatch.setattr(
        cc,
        "send_slack_notification",
        fail_if_called,
    )

    cc.main()

    assert "No contest to notify." in capsys.readouterr().out
