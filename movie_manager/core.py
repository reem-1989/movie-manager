"""Core logic for the Movie Manager.

This module holds all the data handling (add, edit, delete, search,
save, load) so it can be shared by the graphical interface (gui.py)
and the command-line menu (cli.py).
"""

import json
from datetime import date
from pathlib import Path

MIN_YEAR = 1900
DEFAULT_FILE = "movies_file.json"

SAMPLE_MOVIES ={
    "IT": {
        "year": 2017,
        "genre": "Horror",
        "director": "Andy Muschietti",
        "actors": ["Bill Skarsgard", "Jaeden Martell"]
    },

    "Titanic": {
        "year": 1997,
        "genre": "Romance",
        "director": "James Cameron",
        "actors": ["Leonardo DiCaprio", "Kate Winslet"]
    },

    "Inception": {
        "year": 2010,
        "genre": "Sci-Fi",
        "director": "Christopher Nolan",
        "actors": ["Leonardo DiCaprio", "Tom Hardy"]
    },

    "The Conjuring": {
        "year": 2013,
        "genre": "Horror",
        "director": "James Wan",
        "actors": ["Vera Farmiga", "Patrick Wilson"]
    }
}


class MovieError(ValueError):
    """Raised when the user gives invalid movie data."""


def max_year():
    """Latest year allowed (next year, so upcoming releases can be added)."""
    return date.today().year + 1


def parse_year(value):
    """Turn user input into a valid year, or raise MovieError."""
    try:
        year = int(str(value).strip())
    except ValueError:
        raise MovieError("Year must be a number.") from None
    if not MIN_YEAR <= year <= max_year():
        raise MovieError(f"Year must be between {MIN_YEAR} and {max_year()}.")
    return year


def parse_actors(value):
    """Split actors on commas so full names like 'Heath Ledger' stay together."""
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(",")
    return [name.strip() for name in items if name.strip()]


class MovieCollection:
    """A collection of movies stored as {title: details}."""

    def __init__(self, movies=None):
        source = SAMPLE_MOVIES if movies is None else movies
        # Copy so we never modify the sample data by accident
        self.movies = {title: dict(details, actors=list(details["actors"]))
                       for title, details in source.items()}

    # ----- basic operations -------------------------------------------
    def add(self, title, year, genre, director, actors):
        title = title.strip()
        if not title:
            raise MovieError("Title cannot be empty.")
        if self.find_title(title):
            raise MovieError(f'"{title}" already exists. Use Edit instead.')
        self.movies[title] = {
            "year": parse_year(year),
            "genre": genre.strip(),
            "director": director.strip(),
            "actors": parse_actors(actors),
        }
        return title

    def edit(self, old_title, new_title, year, genre, director, actors):
        """Update a movie. The title can be changed too."""
        if old_title not in self.movies:
            raise MovieError("Movie not found.")
        new_title = new_title.strip()
        if not new_title:
            raise MovieError("Title cannot be empty.")
        existing = self.find_title(new_title)
        if existing and existing != old_title:
            raise MovieError(f'"{new_title}" already exists.')
        details = {
            "year": parse_year(year),
            "genre": genre.strip(),
            "director": director.strip(),
            "actors": parse_actors(actors),
        }
        del self.movies[old_title]
        self.movies[new_title] = details
        return new_title

    def delete(self, title):
        if title not in self.movies:
            raise MovieError("Movie not found.")
        del self.movies[title]

    # ----- searching --------------------------------------------------
    def find_title(self, title):
        """Return the stored title matching `title` (case-insensitive), or None."""
        wanted = title.strip().lower()
        for stored in self.movies:
            if stored.lower() == wanted:
                return stored
        return None

    def search(self, text="", field="all"):
        """Return {title: details} for movies matching `text`.

        field can be: all, title, genre, director, actors, year.
        Text matching is case-insensitive and allows partial matches.
        """
        text = str(text).strip().lower()
        if not text:
            return dict(self.movies)

        results = {}
        for title, d in self.movies.items():
            values = {
                "title": [title],
                "genre": [d["genre"]],
                "director": [d["director"]],
                "actors": d["actors"],
                "year": [str(d["year"])],
            }
            if field == "year":
                match = text == str(d["year"])
            else:
                fields = values.values() if field == "all" else [values[field]]
                match = any(text in v.lower() for group in fields for v in group)
            if match:
                results[title] = d
        return results

    # ----- saving / loading -------------------------------------------
    def save(self, path=DEFAULT_FILE):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.movies, file, indent=4, ensure_ascii=False)

    def load(self, path=DEFAULT_FILE):
        path = Path(path)
        if not path.exists():
            raise MovieError(f"File not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            raise MovieError("The file is not valid JSON.") from None
        if not isinstance(data, dict):
            raise MovieError("The file does not contain a movie list.")
        self.movies = data
