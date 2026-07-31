# Letterboxd Film Picker

A small local CLI for choosing a film from your Letterboxd movie list.

## Browser Comparison Game

Start the local browser game from this directory:

```bash
cd Letterboxd
uv run python src/main.py web
```

Then open:

```text
http://127.0.0.1:8000
```

Use a public Letterboxd custom-list URL:

```text
https://letterboxd.com/your-username/list/your-list-slug/
```

The browser game flow is:

1. Paste the list URL.
2. Wait while the app fetches the full list.
3. Choose how many films to compare. The number must be from 2 through the loaded list length.
4. Pick between two films until one winner remains.
5. Review the winner and the matchup path that produced it.

The web game shows poster, title, year, and Letterboxd URL for each film when a poster is available. Use the buttons, or press Left Arrow / Right Arrow to choose the left or right film. Play again reuses the same fetched list and same game size; New list clears the in-memory list and returns to the URL form.

The browser game keeps fetched films, poster URLs, and game state in browser memory only. It does not intentionally write a CSV cache, image files, game state, or results to disk; refreshing or closing the tab clears the run.

Poster fetching works in two steps:

1. The app fetches the Letterboxd list first. The list data includes each film's title, year, and Letterboxd URL, but not its poster.
2. After you choose the game size, the app randomly samples the films for that game and asks Python to fetch poster URLs for only those selected films.

Poster URLs come from `letterboxdpy.movie.Movie`, which scrapes the individual Letterboxd film page and exposes the package's `poster` field. The app sends the poster URL to the browser and uses it as the image source; it does not need to store the image file locally. A browser may still use its own normal HTTP cache for remote images, but this app does not save poster files itself.

Use a different port if needed:

```bash
uv run python src/main.py web --port 8123
```

## Pick From A CSV

Export a Letterboxd list, watchlist, or watched films CSV, then run:

```bash
cd Letterboxd
uv run python src/main.py pick path/to/your-list.csv
```

You can also put a CSV at one of these paths and omit the file argument:

- `data/watchlist.csv`
- `data/watched.csv`
- `data/films.csv`
- `watchlist.csv`
- `watched.csv`
- `films.csv`

Examples:

```bash
uv run python src/main.py pick data/watchlist.csv
uv run python src/main.py pick data/watchlist.csv --count 3
uv run python src/main.py pick data/watchlist.csv --min-year 1990 --max-year 2020
uv run python src/main.py pick data/watchlist.csv --seed friday-night
```

The shorter old form still works:

```bash
uv run python src/main.py data/watchlist.csv --count 3
```

The CSV parser accepts common Letterboxd headers such as `Name`, `Title`, `Year`, and `Letterboxd URI`.

## Fetch With letterboxdpy

`letterboxdpy` can fetch public Letterboxd pages without developer credentials.

Fetch a public watchlist:

```bash
uv run python src/main.py scrape-watchlist your-username
uv run python src/main.py scrape-watchlist your-username --output data/watchlist.csv
uv run python src/main.py scrape-watchlist your-username --limit 100
```

Fetch a public custom list:

```bash
uv run python src/main.py scrape-list your-username your-list-slug
uv run python src/main.py scrape-list your-username your-list-slug --output data/list.csv
```

For a list URL like:

```text
https://letterboxd.com/your-username/list/movies-to-watch/
```

use:

```bash
uv run python src/main.py scrape-list your-username movies-to-watch
```

This project's current list can be fetched with:

```bash
uv run python src/main.py scrape-list username 2026 --output data/2026.csv
uv run python src/main.py pick data/2026.csv --count 3
```

Letterboxd may occasionally return a `403` IP/VPN block for scraper requests. If that happens, wait and retry later, or use a CSV export instead.

## Development

This project uses `uv` for dependency management. Run `uv sync` after cloning or after dependency changes.

Run tests with:

```bash
uv run pytest
```

Tests live under `tests/`.

Show all commands:

```bash
uv run python src/main.py --help
uv run python src/main.py pick --help
uv run python src/main.py scrape-watchlist --help
uv run python src/main.py scrape-list --help
uv run python src/main.py web --help
```