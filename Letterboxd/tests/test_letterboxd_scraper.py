from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from Film import Film
from letterboxd_scraper import (
    films_from_letterboxdpy_movies,
    letterboxdpy_movie_values,
    limit_films,
    parse_url,
    parse_year,
    save_films,
)


def test_film_values_accepts_direct_movies_dict() -> None:
    movie = {"name": "Basic Instinct", "year": 1992}

    assert letterboxdpy_movie_values({"51688": movie}) == [movie]


def test_film_values_accepts_jsonified_list_payload() -> None:
    movie = {"name": "Basic Instinct", "year": 1992}

    assert letterboxdpy_movie_values({"username": "chouann", "_movies": {"51688": movie}}) == [movie]


def test_film_values_ignores_non_dict_values() -> None:
    movie = {"name": "Basic Instinct", "year": 1992}

    assert letterboxdpy_movie_values({"username": "chouann", "51688": movie}) == [movie]


def test_film_values_returns_empty_list_for_invalid_movies_wrapper() -> None:
    assert letterboxdpy_movie_values({"_movies": "not a movie dict"}) == []


def test_films_from_letterboxdpy_movies_converts_direct_movies() -> None:
    films = films_from_letterboxdpy_movies(
        {
            "51688": {
                "slug": "basic-instinct",
                "name": "Basic Instinct",
                "year": 1992,
                "url": "https://letterboxd.com/film/basic-instinct/",
            }
        }
    )

    assert films == [
        Film(
            title="Basic Instinct",
            year=1992,
            url="https://letterboxd.com/film/basic-instinct/",
        )
    ]


def test_films_from_letterboxdpy_movies_converts_jsonified_list_payload() -> None:
    films = films_from_letterboxdpy_movies(
        {
            "username": "chouann",
            "slug": "2025",
            "title": "2025",
            "_movies": {
                "51688": {
                    "slug": "basic-instinct",
                    "name": "Basic Instinct",
                    "year": 1992,
                    "url": "https://letterboxd.com/film/basic-instinct/",
                }
            },
        }
    )

    assert films == [
        Film(
            title="Basic Instinct",
            year=1992,
            url="https://letterboxd.com/film/basic-instinct/",
        )
    ]


def test_films_from_letterboxdpy_movies_skips_missing_names() -> None:
    assert films_from_letterboxdpy_movies({"51688": {"year": 1992}}) == []


def test_parse_year_accepts_int_and_numeric_string() -> None:
    assert parse_year(1992) == 1992
    assert parse_year("1992") == 1992


def test_parse_year_rejects_blank_and_non_numeric_values() -> None:
    assert parse_year(None) is None
    assert parse_year("unknown") is None


def test_parse_url_accepts_http_urls() -> None:
    assert parse_url("https://letterboxd.com/film/basic-instinct/") == (
        "https://letterboxd.com/film/basic-instinct/"
    )


def test_parse_url_rejects_non_urls() -> None:
    assert parse_url(None) is None
    assert parse_url("basic-instinct") is None


def test_limit_films_returns_all_without_limit() -> None:
    films = [Film("A"), Film("B")]

    assert limit_films(films, None) == films


def test_limit_films_returns_prefix_with_limit() -> None:
    films = [Film("A"), Film("B")]

    assert limit_films(films, 1) == [Film("A")]


def test_save_films_writes_letterboxd_csv(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "films.csv"

    save_films(
        [Film("Basic Instinct", 1992, "https://letterboxd.com/film/basic-instinct/")],
        output,
    )

    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["Name", "Year", "Letterboxd URI"],
        ["Basic Instinct", "1992", "https://letterboxd.com/film/basic-instinct/"],
    ]
