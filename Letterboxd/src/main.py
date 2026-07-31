from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path
from typing import Iterable

from Film import Film
from rich.console import Console
from rich.table import Table


DEFAULT_FILES = (
    Path("data/watchlist.csv"),
    Path("data/watched.csv"),
    Path("data/films.csv"),
    Path("watchlist.csv"),
    Path("watched.csv"),
    Path("films.csv"),
)

COMMANDS = {"pick", "scrape-watchlist", "scrape-list", "web", "-h", "--help"}

console = Console()


def main() -> None:
    args = parse_args(sys.argv[1:])

    if args.command == "scrape-watchlist":
        scrape_watchlist(args)
    elif args.command == "scrape-list":
        scrape_list(args)
    elif args.command == "web":
        run_web(args)
    else:
        pick_films(args)


def parse_args(argv: list[str]) -> argparse.Namespace:
    if argv and argv[0] not in COMMANDS:
        argv = ["pick", *argv]

    parser = argparse.ArgumentParser(
        description="Choose films from a CSV, or save public Letterboxd pages as CSV files."
    )
    subparsers = parser.add_subparsers(dest="command")

    add_pick_parser(subparsers)
    add_scrape_watchlist_parser(subparsers)
    add_scrape_list_parser(subparsers)
    add_web_parser(subparsers)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        raise SystemExit(0)

    return args


def add_pick_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "pick",
        help="choose films from a CSV",
        description="Choose films from a CSV file.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="CSV file to use. If omitted, the app looks for a default CSV.",
    )
    parser.add_argument("-n", "--count", type=positive_int, default=1, help="How many films to choose.")
    parser.add_argument("--min-year", type=int, help="Use films from this year or newer.")
    parser.add_argument("--max-year", type=int, help="Use films from this year or older.")
    parser.add_argument("--seed", type=str, help="Use the same random result again.")


def add_scrape_watchlist_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "scrape-watchlist",
        help="save a public watchlist as CSV",
        description="Save a public Letterboxd watchlist as a CSV file.",
    )
    parser.add_argument("username", help="Letterboxd username.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/watchlist.csv"),
        help="Where to save the CSV. Defaults to data/watchlist.csv.",
    )
    parser.add_argument("--limit", type=positive_int, help="Stop after this many films.")


def add_scrape_list_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "scrape-list",
        help="save a public list as CSV",
        description="Save a public Letterboxd list as a CSV file.",
    )
    parser.add_argument("username", help="Letterboxd username.")
    parser.add_argument("slug", help="List slug from the URL, like 2026 or movies-to-watch.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/list.csv"),
        help="Where to save the CSV. Defaults to data/list.csv.",
    )
    parser.add_argument("--limit", type=positive_int, help="Stop after this many films.")


def add_web_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "web",
        help="start the local browser game",
        description="Start the local browser-based Letterboxd comparison game.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=positive_int, default=8000, help="Port to bind. Defaults to 8000.")


def pick_films(args: argparse.Namespace) -> None:
    csv_path = args.file or find_default_file()
    films = filter_films(load_films(csv_path), min_year=args.min_year, max_year=args.max_year)

    if not films:
        raise SystemExit("No films matched those filters.")

    rng = random.Random(args.seed)
    picks = rng.sample(films, k=min(args.count, len(films)))

    render_picks(picks, total=len(films), csv_path=csv_path)


def scrape_watchlist(args: argparse.Namespace) -> None:
    from letterboxd_scraper import LetterboxdScraperError, fetch_watchlist, save_films

    try:
        films = fetch_watchlist(args.username, limit=args.limit)
    except LetterboxdScraperError as error:
        raise SystemExit(str(error)) from error

    save_films(films, args.output)
    console.print(f"Saved {len(films)} films to {args.output}")


def scrape_list(args: argparse.Namespace) -> None:
    from letterboxd_scraper import LetterboxdScraperError, fetch_list, save_films

    try:
        films = fetch_list(args.username, args.slug, limit=args.limit)
    except LetterboxdScraperError as error:
        raise SystemExit(str(error)) from error

    save_films(films, args.output)
    console.print(f"Saved {len(films)} films to {args.output}")


def run_web(args: argparse.Namespace) -> None:
    from web_app import run

    run(host=args.host, port=args.port)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def find_default_file() -> Path:
    for path in DEFAULT_FILES:
        if path.exists():
            return path

    options = ", ".join(str(path) for path in DEFAULT_FILES)
    raise SystemExit(f"No CSV file found. Pass a file path or add one of: {options}")


def load_films(path: Path) -> list[Film]:
    if not path.exists():
        raise SystemExit(f"CSV file not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise SystemExit(f"CSV file has no header row: {path}")

        films = [film for film in (film_from_row(row) for row in reader) if film]

    if not films:
        raise SystemExit(f"No films found in CSV file: {path}")

    return dedupe_films(films)


def film_from_row(row: dict[str, str]) -> Film | None:
    title = first_value(row, "Name", "Title", "Film", "Movie")
    if not title:
        return None

    return Film(
        title=title,
        year=parse_year(first_value(row, "Year", "Release Year")),
        url=first_value(row, "Letterboxd URI", "Letterboxd URL", "URL", "Url"),
    )


def first_value(row: dict[str, str], *keys: str) -> str | None:
    normalized = {key.strip().lower(): value.strip() for key, value in row.items() if key and value}
    for key in keys:
        value = normalized.get(key.lower())
        if value:
            return value
    return None


def parse_year(value: str | None) -> int | None:
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def dedupe_films(films: Iterable[Film]) -> list[Film]:
    seen: set[tuple[str, int | None]] = set()
    unique: list[Film] = []

    for film in films:
        key = (film.title.casefold(), film.year)
        if key in seen:
            continue
        seen.add(key)
        unique.append(film)

    return unique


def filter_films(films: list[Film], min_year: int | None, max_year: int | None) -> list[Film]:
    return [
        film
        for film in films
        if (min_year is None or film.year is None or film.year >= min_year)
        and (max_year is None or film.year is None or film.year <= max_year)
    ]


def render_picks(picks: list[Film], total: int, csv_path: Path) -> None:
    table = Table(title=f"Choosing from {total} films in {csv_path}")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Film", style="bold")
    table.add_column("Year", justify="right")
    table.add_column("Letterboxd")

    for index, film in enumerate(picks, start=1):
        table.add_row(str(index), film.title, str(film.year or ""), film.url or "")

    console.print(table)


if __name__ == "__main__":
    main()
