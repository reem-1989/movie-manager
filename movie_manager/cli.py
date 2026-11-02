"""Command-line version of the Movie Manager (the original text menu)."""

from .core import DEFAULT_FILE, MovieCollection, MovieError

MENU = """
===== Movie Manager =====
1. Add a movie
2. Edit a movie
3. Delete a movie
4. View all movies
5. Search movies
6. Save movies to file
7. Load movies from file
8. Exit
"""


def print_movies(movies):
    if not movies:
        print("No movies found.")
        return
    for title, d in movies.items():
        print(f"\n{title} ({d['year']})")
        print(f"  Genre:    {d['genre']}")
        print(f"  Director: {d['director']}")
        print(f"  Actors:   {', '.join(d['actors'])}")


def ask_movie_details(current=None):
    """Ask for movie details. Press Enter to keep the current value when editing."""
    current = current or {}

    def ask(label, key):
        old = current.get(key, "")
        if isinstance(old, list):
            old = ", ".join(old)
        hint = f" [{old}]" if old != "" else ""
        answer = input(f"{label}{hint}: ").strip()
        return answer if answer else str(old)

    return {
        "year": ask("Year", "year"),
        "genre": ask("Genre", "genre"),
        "director": ask("Director", "director"),
        "actors": ask("Actors (comma separated)", "actors"),
    }


def main():
    collection = MovieCollection()

    while True:
        print(MENU)
        choice = input("Please enter a number from the list: ").strip()

        try:
            if choice == "1":
                title = input("Title: ")
                collection.add(title, **ask_movie_details())
                print("Movie added.")

            elif choice == "2":
                title = collection.find_title(input("Title of the movie to edit: "))
                if not title:
                    print("Movie not found.")
                    continue
                print("Press Enter to keep the current value.")
                new_title = input(f"Title [{title}]: ").strip() or title
                details = ask_movie_details(collection.movies[title])
                collection.edit(title, new_title, **details)
                print("Movie updated.")

            elif choice == "3":
                title = collection.find_title(input("Title of the movie to delete: "))
                if not title:
                    print("Movie not found.")
                    continue
                collection.delete(title)
                print("Movie deleted.")

            elif choice == "4":
                print_movies(collection.movies)

            elif choice == "5":
                field = input("Search in (all, title, genre, director, actors, year) [all]: ")
                field = field.strip().lower() or "all"
                if field not in ("all", "title", "genre", "director", "actors", "year"):
                    print("Invalid field.")
                    continue
                print_movies(collection.search(input("Search for: "), field))

            elif choice == "6":
                collection.save(DEFAULT_FILE)
                print(f"Saved to {DEFAULT_FILE}.")

            elif choice == "7":
                collection.load(DEFAULT_FILE)
                print(f"Loaded {len(collection.movies)} movies from {DEFAULT_FILE}.")

            elif choice == "8":
                print("Goodbye!")
                break

            else:
                print("Please choose a number from 1 to 8.")

        except MovieError as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    main()
