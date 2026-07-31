from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from Film import Film


def test_display_includes_title_year_and_url() -> None:
    film = Film(
        title="Basic Instinct",
        year=1992,
        url="https://letterboxd.com/film/basic-instinct/",
    )

    assert film.display() == "Basic Instinct (1992)\n   https://letterboxd.com/film/basic-instinct/"


def test_display_omits_missing_year_and_url() -> None:
    assert Film(title="Unknown Film").display() == "Unknown Film"
