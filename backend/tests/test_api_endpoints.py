"""Tests for FastAPI endpoints: POST /api/query, GET /api/courses, DELETE /api/session."""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------


class TestQueryEndpoint:

    def test_valid_request_returns_200(self, app_client):
        client, _ = app_client
        response = client.post("/api/query", json={"query": "What is Python?"})
        assert response.status_code == 200

    def test_response_contains_required_fields(self, app_client):
        client, _ = app_client
        response = client.post("/api/query", json={"query": "What is Python?"})
        body = response.json()
        assert "answer" in body
        assert "sources" in body
        assert "session_id" in body

    def test_answer_reflects_rag_output(self, app_client):
        client, mock_rag = app_client
        mock_rag.query.return_value = ("Python is a versatile language.", [])
        response = client.post("/api/query", json={"query": "What is Python?"})
        assert response.json()["answer"] == "Python is a versatile language."

    def test_session_created_when_not_provided(self, app_client):
        client, mock_rag = app_client
        response = client.post("/api/query", json={"query": "test"})
        mock_rag.session_manager.create_session.assert_called()
        assert response.json()["session_id"] == "test-session-id"

    def test_provided_session_id_echoed_back(self, app_client):
        client, _ = app_client
        response = client.post(
            "/api/query", json={"query": "test", "session_id": "sess-abc"}
        )
        assert response.json()["session_id"] == "sess-abc"

    def test_sources_forwarded_from_rag(self, app_client):
        client, mock_rag = app_client
        mock_rag.query.return_value = (
            "answer",
            [{"label": "Intro", "url": "https://example.com"}],
        )
        response = client.post("/api/query", json={"query": "test"})
        assert response.json()["sources"] == [
            {"label": "Intro", "url": "https://example.com"}
        ]

    def test_missing_query_field_returns_422(self, app_client):
        client, _ = app_client
        response = client.post("/api/query", json={"session_id": "s1"})
        assert response.status_code == 422

    def test_rag_exception_returns_500(self, app_client):
        client, mock_rag = app_client
        mock_rag.query.side_effect = RuntimeError("DB unavailable")
        response = client.post("/api/query", json={"query": "test"})
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------


class TestCoursesEndpoint:

    def test_returns_200(self, app_client):
        client, _ = app_client
        response = client.get("/api/courses")
        assert response.status_code == 200

    def test_response_contains_required_fields(self, app_client):
        client, _ = app_client
        response = client.get("/api/courses")
        body = response.json()
        assert "total_courses" in body
        assert "course_titles" in body

    def test_reflects_analytics_data(self, app_client):
        client, mock_rag = app_client
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Python Basics", "Data Science", "Web Dev"],
        }
        response = client.get("/api/courses")
        body = response.json()
        assert body["total_courses"] == 3
        assert "Python Basics" in body["course_titles"]

    def test_analytics_exception_returns_500(self, app_client):
        client, mock_rag = app_client
        mock_rag.get_course_analytics.side_effect = RuntimeError("connection failed")
        response = client.get("/api/courses")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/session/{session_id}
# ---------------------------------------------------------------------------


class TestDeleteSessionEndpoint:

    def test_returns_200_with_ok_body(self, app_client):
        client, _ = app_client
        response = client.delete("/api/session/some-session")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_delegates_correct_id_to_session_manager(self, app_client):
        client, mock_rag = app_client
        client.delete("/api/session/my-session-123")
        mock_rag.session_manager.delete_session.assert_called_with("my-session-123")
