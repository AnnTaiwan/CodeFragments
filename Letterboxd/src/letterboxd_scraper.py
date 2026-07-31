from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from letterboxdpy.list import List
from letterboxdpy.watchlist import Watchlist

from Film import Film


class LetterboxdScraperError(RuntimeError):
    pass


def fetch_watchlist(username: str, *, limit: int | None = None) -> list[Film]:
    try:
        movies = Watchlist(username).movies
    except Exception as error:
        raise LetterboxdScraperError(f"Could not fetch watchlist for {username}: {error}") from error

    return limit_films(films_from_letterboxdpy_movies(movies), limit)


def fetch_list(username: str, slug: str, *, limit: int | None = None) -> list[Film]:
    try:
        movies = List(username, slug).movies
    except Exception as error:
        raise LetterboxdScraperError(
            f"Could not fetch list {username}/list/{slug}: {error}"
        ) from error

    return limit_films(films_from_letterboxdpy_movies(movies), limit)


def save_films(films: list[Film], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Year", "Letterboxd URI"])
        for film in films:
            writer.writerow([film.title, film.year or "", film.url or ""])


def films_from_letterboxdpy_movies(movies: dict[str, Any]) -> list[Film]:
    films: list[Film] = []

    for movie in letterboxdpy_movie_values(movies):
        name = movie.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        films.append(
            Film(
                title=name.strip(),
                year=parse_year(movie.get("year")),
                url=parse_url(movie.get("url")),
            )
        )

    return films


def letterboxdpy_movie_values(movies: dict[str, Any]) -> list[dict[str, Any]]:
    raw_movies = movies.get("_movies", movies)
    if not isinstance(raw_movies, dict):
        return []

    return [movie for movie in raw_movies.values() if isinstance(movie, dict)]


def parse_year(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return None


def parse_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("http"):
        return value
    return None


def limit_films(films: list[Film], limit: int | None) -> list[Film]:
    if limit is None:
        return films
    return films[:limit]
