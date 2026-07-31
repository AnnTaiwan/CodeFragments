from __future__ import annotations

import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from Film import Film
from letterboxd_scraper import LetterboxdScraperError, fetch_list


WEB_DIR = Path(__file__).resolve().parents[1] / "web"


class LetterboxdListUrlError(ValueError):
    pass


class LetterboxdFilmUrlError(ValueError):
    pass


def parse_letterboxd_list_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())
    parts = [part for part in parsed.path.split("/") if part]

    if parsed.scheme != "https" or parsed.netloc.lower() != "letterboxd.com":
        raise LetterboxdListUrlError("Enter a Letterboxd list URL.")

    if len(parts) != 3 or parts[1] != "list":
        raise LetterboxdListUrlError("Expected https://letterboxd.com/{username}/list/{slug}/")

    username, _, slug = parts
    return username, slug


def parse_letterboxd_film_slug(url: str) -> str:
    parsed = urlparse(url.strip())
    parts = [part for part in parsed.path.split("/") if part]

    if parsed.scheme != "https" or parsed.netloc.lower() != "letterboxd.com":
        raise LetterboxdFilmUrlError("Expected a Letterboxd film URL.")

    if len(parts) != 2 or parts[0] != "film":
        raise LetterboxdFilmUrlError("Expected https://letterboxd.com/film/{slug}/")

    return parts[1]


def fetch_poster_url(film_url: str) -> str | None:
    from letterboxdpy.movie import Movie

    slug = parse_letterboxd_film_slug(film_url)
    poster = Movie(slug).poster
    return poster if isinstance(poster, str) and poster.startswith("http") else None


def film_to_json(film: Film) -> dict[str, Any]:
    return asdict(film)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), LetterboxdWebHandler)
    print(f"Serving Letterboxd game at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Letterboxd game server.")
    finally:
        server.server_close()


class LetterboxdWebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            self.serve_file(WEB_DIR / "index.html", "text/html; charset=utf-8")
            return

        if self.path == "/styles.css":
            self.serve_file(WEB_DIR / "styles.css", "text/css; charset=utf-8")
            return

        if self.path == "/app.js":
            self.serve_file(WEB_DIR / "app.js", "application/javascript; charset=utf-8")
            return

        self.send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/letterboxd-list":
            self.fetch_letterboxd_list()
            return

        if self.path == "/api/posters":
            self.fetch_posters()
            return

        self.send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def fetch_letterboxd_list(self) -> None:
        payload = self.read_json()
        if not isinstance(payload, dict):
            self.send_json({"error": "Request body must be JSON."}, status=HTTPStatus.BAD_REQUEST)
            return

        url = payload.get("url")
        if not isinstance(url, str):
            self.send_json({"error": "Letterboxd list URL is required."}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            username, slug = parse_letterboxd_list_url(url)
            films = fetch_list(username, slug)
        except LetterboxdListUrlError as error:
            self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return
        except LetterboxdScraperError as error:
            self.send_json({"error": str(error)}, status=HTTPStatus.BAD_GATEWAY)
            return

        self.send_json({"films": [film_to_json(film) for film in films]})

    def fetch_posters(self) -> None:
        payload = self.read_json()
        if not isinstance(payload, dict):
            self.send_json({"error": "Request body must be JSON."}, status=HTTPStatus.BAD_REQUEST)
            return

        films = payload.get("films")
        if not isinstance(films, list):
            self.send_json({"error": "Films are required."}, status=HTTPStatus.BAD_REQUEST)
            return

        posters: dict[str, str | None] = {}
        for film in films:
            if not isinstance(film, dict):
                continue

            url = film.get("url")
            if not isinstance(url, str) or url in posters:
                continue

            try:
                posters[url] = fetch_poster_url(url)
            except Exception:
                posters[url] = None

        self.send_json({"posters": posters})

    def serve_file(self, path: Path, content_type: str) -> None:
        try:
            content = path.read_bytes()
        except FileNotFoundError:
            self.send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def read_json(self) -> Any:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        return
