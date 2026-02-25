"""Tests for CourseSearchTool.execute()"""

import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search_tools import CourseSearchTool
from vector_store import SearchResults
import config as cfg

# ---------------------------------------------------------------------------
# Unit tests — VectorStore is mocked
# ---------------------------------------------------------------------------


class TestCourseSearchToolUnit:

    def test_execute_returns_formatted_results_on_success(
        self, mock_vector_store, sample_search_results_success
    ):
        mock_vector_store.search.return_value = sample_search_results_success
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="python")

        assert result != ""
        assert "Introduction to Python" in result
        assert "Python" in result

    def test_execute_returns_error_string_when_search_has_error(
        self, mock_vector_store, sample_search_results_error
    ):
        mock_vector_store.search.return_value = sample_search_results_error
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="python")

        assert result == "Search error: n_results must be a positive integer"

    def test_execute_returns_no_results_message_when_empty(
        self, mock_vector_store, sample_search_results_empty
    ):
        mock_vector_store.search.return_value = sample_search_results_empty
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="python")

        assert result.startswith("No relevant content found")

    def test_execute_passes_course_filter_to_vector_store(
        self, mock_vector_store, sample_search_results_success
    ):
        mock_vector_store.search.return_value = sample_search_results_success
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="foo", course_name="MCP")

        mock_vector_store.search.assert_called_once_with(
            query="foo",
            course_name="MCP",
            lesson_number=None,
        )

    def test_execute_passes_lesson_filter_to_vector_store(
        self, mock_vector_store, sample_search_results_success
    ):
        mock_vector_store.search.return_value = sample_search_results_success
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="foo", lesson_number=2)

        mock_vector_store.search.assert_called_once_with(
            query="foo",
            course_name=None,
            lesson_number=2,
        )

    def test_last_sources_populated_after_successful_search(
        self, mock_vector_store, sample_search_results_success
    ):
        mock_vector_store.search.return_value = sample_search_results_success
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="python")

        assert len(tool.last_sources) > 0
        for source in tool.last_sources:
            assert "label" in source


# ---------------------------------------------------------------------------
# Integration test — real ChromaDB
# ---------------------------------------------------------------------------


class TestCourseSearchToolIntegration:

    def test_execute_against_real_vector_store(self, real_vector_store):
        """Fails when MAX_RESULTS=0 because ChromaDB rejects n_results=0."""
        tool = CourseSearchTool(real_vector_store)

        result = tool.execute(query="python")

        assert not result.startswith(
            "Search error:"
        ), f"Search failed — likely caused by MAX_RESULTS=0 in config.py. Got: {result}"
