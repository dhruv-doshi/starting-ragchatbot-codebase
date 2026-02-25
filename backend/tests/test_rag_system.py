"""Integration tests for RAGSystem.query() — pinpoints config bugs."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config as cfg
from vector_store import VectorStore, SearchResults
from rag_system import RAGSystem


# ---------------------------------------------------------------------------
# Mock response helpers (same pattern as test_ai_generator)
# ---------------------------------------------------------------------------

def _text_response(text="Test response"):
    response = MagicMock()
    response.stop_reason = "end_turn"
    block = MagicMock()
    block.type = "text"
    block.text = text
    response.content = [block]
    return response


def _tool_use_response(tool_name="search_course_content", tool_input=None, tool_id="toolu_abc"):
    if tool_input is None:
        tool_input = {"query": "python"}
    response = MagicMock()
    response.stop_reason = "tool_use"
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = tool_id
    block.input = tool_input
    response.content = [block]
    return response


# ---------------------------------------------------------------------------
# Config sanity
# ---------------------------------------------------------------------------

class TestRAGSystemConfig:

    def test_config_max_results_is_positive(self):
        """FAILS immediately when MAX_RESULTS=0, making the root bug obvious."""
        assert cfg.config.MAX_RESULTS > 0, (
            f"config.MAX_RESULTS={cfg.config.MAX_RESULTS}. "
            "ChromaDB requires n_results > 0; every search silently fails."
        )


# ---------------------------------------------------------------------------
# VectorStore with zero results
# ---------------------------------------------------------------------------

class TestVectorStoreWithZeroResults:

    def test_vector_store_search_n_results_zero_returns_error(self):
        """Proves MAX_RESULTS=0 makes every search return an error SearchResult."""
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        chroma_path = os.path.join(backend_dir, "chroma_db")
        vs = VectorStore(chroma_path, cfg.config.EMBEDDING_MODEL, max_results=0)

        result = vs.search("python")

        assert result.error is not None, (
            "Expected an error SearchResults when max_results=0, but got none."
        )
        assert "Search error" in result.error, (
            f"Unexpected error format: {result.error}"
        )


# ---------------------------------------------------------------------------
# RAGSystem integration (mocked Anthropic API)
# ---------------------------------------------------------------------------

class TestRAGSystemIntegration:

    def _make_rag(self, mock_client, max_results=5):
        """Build a RAGSystem with patched Anthropic and overridden MAX_RESULTS."""
        test_config = cfg.Config()
        test_config.MAX_RESULTS = max_results
        rag = RAGSystem(test_config)
        # Replace the already-created client inside AIGenerator
        rag.ai_generator.client = mock_client
        return rag

    def test_query_returns_response_and_sources_with_mock_api(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _text_response("Python is great.")

        with patch("anthropic.Anthropic", return_value=mock_client):
            rag = self._make_rag(mock_client)
            result = rag.query("What is Python?")

        assert isinstance(result, tuple) and len(result) == 2
        response_text, sources = result
        assert isinstance(response_text, str)
        assert isinstance(sources, list)

    def test_query_content_question_triggers_tool_call_with_mock_api(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            _tool_use_response(tool_input={"query": "python"}),
            _text_response("Final answer about Python."),
        ]

        with patch("anthropic.Anthropic", return_value=mock_client):
            rag = self._make_rag(mock_client)
            with patch.object(
                rag.search_tool, "execute", wraps=rag.search_tool.execute
            ) as spy:
                response, sources = rag.query("Tell me about Python.")
                spy.assert_called_once()

        assert response == "Final answer about Python."

    def test_query_with_fixed_max_results_does_not_error(self):
        """Uses real ChromaDB with max_results=5; skipped if DB is empty."""
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        chroma_path = os.path.join(backend_dir, "chroma_db")
        vs = VectorStore(chroma_path, cfg.config.EMBEDDING_MODEL, max_results=5)

        if vs.get_course_count() == 0:
            pytest.skip("ChromaDB is empty — no courses loaded to query")

        result = vs.search("python")

        assert result.error is None, (
            f"Unexpected search error with max_results=5: {result.error}"
        )
