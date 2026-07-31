from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Film:
    title: str
    year: int | None = None
    url: str | None = None

    def display(self) -> str:
        year = f" ({self.year})" if self.year else ""
        url = f"\n   {self.url}" if self.url else ""
        return f"{self.title}{year}{url}"
