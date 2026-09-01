from urllib.error import URLError

import pytest

import scripts.check_contests as cc
from scripts.check_contests import get_scores


def test_get_scores(monkeypatch, fake_response):
    html = """
        <html>
            <h3>配点</h3>
            <table>
                <tbody>
                    <tr><td>A</td><td>100</td></tr>
                    <tr><td>B</td><td>200</td></tr>
                    <tr><td>C</td><td>300</td></tr>
                </tbody>
            </table>
        </html>
    """.encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return fake_response(html)

    monkeypatch.setattr(cc, "urlopen", fake_urlopen)

    assert get_scores("https://atcoder.jp/contests/abc999") == [
        100,
        200,
        300,
    ]

    assert captured["url"] == (
        "https://atcoder.jp/contests/abc999?lang=ja"
    )


def test_get_scores_returns_none_when_unpublished(
    monkeypatch,
    fake_response,
):
    html = b"<html><body>Not published</body></html>"

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda request, timeout: fake_response(html),
    )

    assert get_scores("https://atcoder.jp/contests/abc999") is None


def test_get_scores_returns_none_when_table_is_missing(
    monkeypatch,
    fake_response,
):
    html = "<html><h3>配点</h3></html>".encode()

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda request, timeout: fake_response(html),
    )

    assert get_scores("https://atcoder.jp/contests/abc999") is None


def test_get_scores_skips_malformed_rows(
    monkeypatch,
    fake_response,
):
    html = """
        <html>
            <h3>配点</h3>
            <table>
                <tbody>
                    <tr><td>invalid</td></tr>
                    <tr><td>A</td><td>100</td></tr>
                </tbody>
            </table>
        </html>
    """.encode()

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda request, timeout: fake_response(html),
    )

    assert get_scores(
        "https://atcoder.jp/contests/abc999"
    ) == [100]


def test_get_scores_returns_none_for_invalid_score(
    monkeypatch,
    fake_response,
):
    html = """
        <html>
            <h3>配点</h3>
            <table>
                <tbody>
                    <tr><td>A</td><td>100 points</td></tr>
                </tbody>
            </table>
        </html>
    """.encode()

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda request, timeout: fake_response(html),
    )

    assert get_scores("https://atcoder.jp/contests/abc999") is None


def test_get_scores_returns_none_when_table_is_empty(
    monkeypatch,
    fake_response,
):
    html = """
        <html>
            <h3>配点</h3>
            <table>
                <tbody></tbody>
            </table>
        </html>
    """.encode()

    monkeypatch.setattr(
        cc,
        "urlopen",
        lambda request, timeout: fake_response(html),
    )

    assert get_scores("https://atcoder.jp/contests/abc999") is None


@pytest.mark.parametrize(
    "error",
    [
        URLError("network error"),
        TimeoutError("timeout"),
    ],
)
def test_get_scores_returns_none_on_network_error(
    monkeypatch,
    error,
):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(cc, "urlopen", fail)

    assert get_scores("https://atcoder.jp/contests/abc999") is None