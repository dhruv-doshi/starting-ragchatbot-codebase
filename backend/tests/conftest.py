import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure backend/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vector_store import SearchResults


@pytest.fixture
def sample_course_chunk_metadata():
    """List of (doc, metadata) pairs for mocking search results."""
    return [
        (
            "Python is a high-level programming language.",
            {"course_title": "Introduction to Python", "lesson_number": 1, "chunk_index": 0},
        ),
        (
            "Functions in Python are defined using the def keyword.",
            {"course_title": "Introduction to Python", "lesson_number": 2, "chunk_index": 1},
        ),
    ]


@pytest.fixture
def sample_search_results_success(sample_course_chunk_metadata):
    """SearchResults with real documents/metadata."""
    docs = [pair[0] for pair in sample_course_chunk_metadata]
    metas = [pair[1] for pair in sample_course_chunk_metadata]
    distances = [0.1, 0.2]
    return SearchResults(documents=docs, metadata=metas, distances=distances)


@pytest.fixture
def sample_search_results_empty():
    """SearchResults with empty docs and no error."""
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def sample_search_results_error():
    """SearchResults carrying an error message."""
    return SearchResults.empty("Search error: n_results must be a positive integer")


@pytest.fixture
def mock_vector_store(sample_search_results_success):
    """Mock VectorStore with .search() and .get_lesson_link() pre-configured."""
    mock = MagicMock()
    mock.search.return_value = sample_search_results_success
    mock.get_lesson_link.return_value = "https://example.com/lesson/1"
    return mock


@pytest.fixture
def temp_course_file(tmp_path):
    """Write a minimal valid course .txt to a temp directory."""
    content = """\
Course Title: Test Python Course
Course Link: https://example.com/course
Course Instructor: Test Instructor

Lesson 0: Introduction
Lesson Link: https://example.com/lesson/0
This is the introduction to the course. Python is a versatile programming language.

Lesson 1: Variables
Lesson Link: https://example.com/lesson/1
Variables in Python are dynamically typed. You can assign any value to a variable.
"""
    course_file = tmp_path / "test_course.txt"
    course_file.write_text(content)
    return str(course_file)


@pytest.fixture
def real_vector_store():
    """VectorStore pointing at backend/chroma_db, always uses max_results=5."""
    from vector_store import VectorStore
    import config as cfg

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    chroma_path = os.path.join(backend_dir, "chroma_db")
    return VectorStore(chroma_path, cfg.config.EMBEDDING_MODEL, max_results=5)
