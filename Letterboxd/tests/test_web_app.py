from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from Film import Film
from web_app import (
    LetterboxdFilmUrlError,
    LetterboxdListUrlError,
    film_to_json,
    parse_letterboxd_film_slug,
    parse_letterboxd_list_url,
)


def test_parse_letterboxd_list_url_accepts_canonical_url() -> None:
    assert parse_letterboxd_list_url("https://letterboxd.com/ChouAnn/list/2026/") == (
        "ChouAnn",
        "2026",
    )


def test_parse_letterboxd_list_url_accepts_missing_trailing_slash() -> None:
    assert parse_letterboxd_list_url("https://letterboxd.com/ChouAnn/list/2026") == (
        "ChouAnn",
        "2026",
    )


def test_parse_letterboxd_list_url_preserves_username_and_slug() -> None:
    assert parse_letterboxd_list_url(
        "https://letterboxd.com/ChouAnn/list/Movies-To-Watch/"
    ) == ("ChouAnn", "Movies-To-Watch")


def test_parse_letterboxd_list_url_rejects_watchlist() -> None:
    with pytest.raises(LetterboxdListUrlError):
        parse_letterboxd_list_url("https://letterboxd.com/ChouAnn/watchlist/")


def test_parse_letterboxd_list_url_rejects_non_letterboxd_url() -> None:
    with pytest.raises(LetterboxdListUrlError):
        parse_letterboxd_list_url("https://example.com/ChouAnn/list/2026/")


def test_parse_letterboxd_film_slug_accepts_film_url() -> None:
    assert parse_letterboxd_film_slug("https://letterboxd.com/film/50-50/") == "50-50"


def test_parse_letterboxd_film_slug_accepts_missing_trailing_slash() -> None:
    assert parse_letterboxd_film_slug("https://letterboxd.com/film/50-50") == "50-50"


def test_parse_letterboxd_film_slug_rejects_non_film_url() -> None:
    with pytest.raises(LetterboxdFilmUrlError):
        parse_letterboxd_film_slug("https://letterboxd.com/ChouAnn/list/2026/")


def test_film_to_json_serializes_film() -> None:
    assert film_to_json(Film("50/50", 2011, "https://letterboxd.com/film/50-50/")) == {
        "title": "50/50",
        "year": 2011,
        "url": "https://letterboxd.com/film/50-50/",
    }
