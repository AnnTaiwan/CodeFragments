from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from Film import Film
from main import (
    dedupe_films,
    film_from_row,
    filter_films,
    first_value,
    load_films,
    parse_args,
    parse_year,
    positive_int,
)


def test_parse_args_defaults_unknown_first_argument_to_pick_command() -> None:
    args = parse_args(["data/2026.csv", "--count", "3"])

    assert args.command == "pick"
    assert args.file == Path("data/2026.csv")
    assert args.count == 3


def test_parse_args_accepts_scrape_list_command() -> None:
    args = parse_args(["scrape-list", "ChouAnn", "2026", "--output", "data/2026.csv"])

    assert args.command == "scrape-list"
    assert args.username == "ChouAnn"
    assert args.slug == "2026"
    assert args.output == Path("data/2026.csv")


def test_positive_int_accepts_positive_numbers() -> None:
    assert positive_int("3") == 3


def test_positive_int_rejects_zero() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("0")


def test_load_films_reads_letterboxd_csv(tmp_path: Path) -> None:
    path = tmp_path / "films.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Year", "Letterboxd URI"])
        writer.writerow(["Basic Instinct", "1992", "https://letterboxd.com/film/basic-instinct/"])

    assert load_films(path) == [
        Film("Basic Instinct", 1992, "https://letterboxd.com/film/basic-instinct/")
    ]


def test_load_films_deduplicates_rows(tmp_path: Path) -> None:
    path = tmp_path / "films.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Year"])
        writer.writerow(["Basic Instinct", "1992"])
        writer.writerow(["basic instinct", "1992"])

    assert load_films(path) == [Film("Basic Instinct", 1992, None)]


def test_film_from_row_accepts_title_aliases() -> None:
    assert film_from_row({"Title": "Basic Instinct", "Release Year": "1992"}) == Film(
        "Basic Instinct",
        1992,
        None,
    )


def test_film_from_row_skips_missing_title() -> None:
    assert film_from_row({"Year": "1992"}) is None


def test_first_value_matches_keys_case_insensitively() -> None:
    assert first_value({" name ": " Basic Instinct "}, "Name") == "Basic Instinct"


def test_parse_year_returns_int_or_none() -> None:
    assert parse_year("1992") == 1992
    assert parse_year("unknown") is None
    assert parse_year(None) is None


def test_dedupe_films_uses_title_and_year() -> None:
    assert dedupe_films([Film("Basic Instinct", 1992), Film("basic instinct", 1992)]) == [
        Film("Basic Instinct", 1992)
    ]


def test_filter_films_keeps_unknown_years() -> None:
    films = [Film("Old", 1980), Film("Unknown"), Film("New", 2020)]

    assert filter_films(films, min_year=2000, max_year=None) == [Film("Unknown"), Film("New", 2020)]
