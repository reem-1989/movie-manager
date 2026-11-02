import pytest

from movie_manager.core import MovieCollection, MovieError


@pytest.fixture
def movies():
    return MovieCollection()


def test_sample_movies_loaded(movies):
    assert "Inception" in movies.movies
    assert len(movies.movies) == 2


def test_add_movie_keeps_full_actor_names(movies):
    movies.add("Interstellar", "2014", "Sci-Fi", "Christopher Nolan",
               "Matthew McConaughey, Anne Hathaway")
    assert movies.movies["Interstellar"]["actors"] == ["Matthew McConaughey", "Anne Hathaway"]
    assert movies.movies["Interstellar"]["year"] == 2014


@pytest.mark.parametrize("year", ["abc", "1800", "3000", ""])
def test_add_rejects_bad_year(movies, year):
    with pytest.raises(MovieError):
        movies.add("Bad", year, "Drama", "Someone", "A, B")


def test_add_rejects_duplicates_case_insensitive(movies):
    with pytest.raises(MovieError):
        movies.add("inception", "2010", "Sci-Fi", "Nolan", "")


def test_edit_and_rename(movies):
    movies.edit("Inception", "Inception (2010)", 2010, "Thriller", "Christopher Nolan", "Leo")
    assert "Inception" not in movies.movies
    assert movies.movies["Inception (2010)"]["genre"] == "Thriller"


def test_delete(movies):
    movies.delete("Inception")
    assert "Inception" not in movies.movies
    with pytest.raises(MovieError):
        movies.delete("Inception")


def test_search(movies):
    assert set(movies.search("nolan")) == {"The Dark Knight", "Inception"}
    assert set(movies.search("heath", "actors")) == {"The Dark Knight"}
    assert set(movies.search("2010", "year")) == {"Inception"}
    assert movies.search("comedy", "genre") == {}
    assert len(movies.search("")) == 2


def test_save_and_load(tmp_path, movies):
    path = tmp_path / "movies.json"
    movies.add("Up", 2009, "Animation", "Pete Docter", "Ed Asner")
    movies.save(path)

    other = MovieCollection(movies={})
    other.load(path)
    assert other.movies == movies.movies


def test_load_missing_file(tmp_path, movies):
    with pytest.raises(MovieError):
        movies.load(tmp_path / "nope.json")
