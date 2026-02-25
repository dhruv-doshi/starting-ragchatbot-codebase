import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure backend/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vector_store import SearchResults


@pytest.fixture
def sample_course_chunk_metadata():
    """List of (doc, metadata) pairs for mocking search results."""
    return [
        (
            "Python is a high-level programming language.",
            {
                "course_title": "Introduction to Python",
                "lesson_number": 1,
                "chunk_index": 0,
            },
        ),
        (
            "Functions in Python are defined using the def keyword.",
            {
                "course_title": "Introduction to Python",
                "lesson_number": 2,
                "chunk_index": 1,
            },
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


class _DummyStaticFiles:
    """Minimal ASGI stub replacing StaticFiles during API tests.

    Avoids the directory-existence check in StaticFiles.__init__ and
    provides a valid ASGI callable so app.mount() doesn't complain.
    Any request that falls through to this mount returns 404.
    """

    def __init__(self, *args, **kwargs):
        pass

    async def __call__(self, scope, receive, send):
        await send({"type": "http.response.start", "status": 404, "headers": []})
        await send({"type": "http.response.body", "body": b""})


@pytest.fixture
def app_client():
    """TestClient for the FastAPI app with RAGSystem and StaticFiles mocked.

    Patches are applied *before* importing app.py so that:
    - RAGSystem(config) returns mock_rag instead of touching ChromaDB/Anthropic.
    - StaticFiles(directory="../frontend") never checks the filesystem.

    The app module is popped from sys.modules before each test to guarantee a
    fresh import, giving each test its own isolated mock_rag instance.
    """
    from fastapi.testclient import TestClient

    mock_rag = MagicMock()
    mock_rag.query.return_value = ("Test answer", [])
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    mock_rag.session_manager.create_session.return_value = "test-session-id"
    mock_rag.add_course_folder.return_value = (0, 0)

    sys.modules.pop("app", None)

    with patch("rag_system.RAGSystem", return_value=mock_rag), patch(
        "fastapi.staticfiles.StaticFiles", _DummyStaticFiles
    ):
        import app as app_module  # noqa: PLC0415

    # Explicitly override the module-level rag_system so route handlers use
    # our mock regardless of what RAGSystem(config) captured at import time.
    app_module.rag_system = mock_rag

    with TestClient(app_module.app) as client:
        yield client, mock_rag

    sys.modules.pop("app", None)


@pytest.fixture
def real_vector_store():
    """VectorStore pointing at backend/chroma_db, always uses max_results=5."""
    from vector_store import VectorStore
    import config as cfg

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    chroma_path = os.path.join(backend_dir, "chroma_db")
    return VectorStore(chroma_path, cfg.config.EMBEDDING_MODEL, max_results=5)
