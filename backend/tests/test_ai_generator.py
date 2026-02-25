"""Tests for AIGenerator — all API calls are mocked."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai_generator import AIGenerator
import config as cfg


# ---------------------------------------------------------------------------
# Mock response helpers
# ---------------------------------------------------------------------------

def _text_response(text="Hello, this is a test response."):
    response = MagicMock()
    response.stop_reason = "end_turn"
    block = MagicMock()
    block.type = "text"
    block.text = text
    response.content = [block]
    return response


def _tool_use_response(
    tool_name="search_course_content",
    tool_input=None,
    tool_id="toolu_123",
):
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
# Tests
# ---------------------------------------------------------------------------

class TestAIGenerator:

    # -- existing tests (single-round behaviour) ----------------------------

    def test_generate_response_returns_direct_text_when_no_tool_use(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = _text_response("Direct answer")

            generator = AIGenerator(api_key="test-key", model="claude-test")
            result = generator.generate_response(query="What is Python?")

        assert result == "Direct answer"

    def test_tool_executed_with_correct_name_and_args(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(
                    tool_name="search_course_content",
                    tool_input={"query": "python"},
                ),
                _text_response("Final answer"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.return_value = "Search results"

            generator = AIGenerator(api_key="test-key", model="claude-test")
            generator.generate_response(
                query="What is Python?",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="python"
        )

    def test_second_api_call_contains_tool_result_block(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(),
                _text_response("Final"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.return_value = "Tool result content"

            generator = AIGenerator(api_key="test-key", model="claude-test")
            generator.generate_response(
                query="test",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

            second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
            messages = second_call_kwargs["messages"]

            tool_result_found = any(
                isinstance(msg.get("content"), list)
                and any(
                    isinstance(block, dict) and block.get("type") == "tool_result"
                    for block in msg["content"]
                )
                for msg in messages
            )
            assert tool_result_found, "No tool_result block found in second API call messages"

    def test_generate_response_returns_final_text_after_tool_execution(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(),
                _text_response("This is the final text response"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.return_value = "Tool results"

            generator = AIGenerator(api_key="test-key", model="claude-test")
            result = generator.generate_response(
                query="test",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        assert result == "This is the final text response"

    def test_model_name_not_invalid_format(self):
        model = cfg.config.ANTHROPIC_MODEL
        assert model, "ANTHROPIC_MODEL is empty"
        assert model.startswith("claude-"), (
            f"ANTHROPIC_MODEL='{model}' does not start with 'claude-'. "
            "This is likely an invalid model ID that will cause API errors."
        )
        print(f"\nDiagnostic: ANTHROPIC_MODEL = '{model}'")

    # -- new tests (multi-round behaviour) ----------------------------------

    def test_generate_response_single_api_call_when_no_tool_use(self):
        """No tool call → exactly one API call made."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = _text_response("Only answer")

            generator = AIGenerator(api_key="test-key", model="claude-test")
            result = generator.generate_response(query="What is 2+2?")

        assert result == "Only answer"
        assert mock_client.messages.create.call_count == 1

    def test_generate_response_two_api_calls_on_one_tool_use(self):
        """One tool call → 2 API calls; tools present in 2nd call."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(),
                _text_response("Final"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.return_value = "Search result"

            generator = AIGenerator(api_key="test-key", model="claude-test")
            result = generator.generate_response(
                query="test",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        assert result == "Final"
        assert mock_client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1
        # Tools must still be in the second call
        second_kwargs = mock_client.messages.create.call_args_list[1][1]
        assert "tools" in second_kwargs

    def test_generate_response_two_sequential_tool_calls(self):
        """Two sequential tool calls → 3 API calls, 2 tool executions, 5-entry messages."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(tool_id="t1"),
                _tool_use_response(tool_id="t2"),
                _text_response("Done"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.side_effect = ["Result A", "Result B"]

            generator = AIGenerator(api_key="test-key", model="claude-test")
            result = generator.generate_response(
                query="Compare courses",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        assert result == "Done"
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2
        # Third call's messages list: user + (assistant+user)*2 = 5 entries
        third_kwargs = mock_client.messages.create.call_args_list[2][1]
        assert len(third_kwargs["messages"]) == 5

    def test_generate_response_tools_available_in_round_2(self):
        """Tools must be included in every in-loop API call, not stripped after round 1."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(tool_id="t1"),
                _tool_use_response(tool_id="t2"),
                _text_response("Done"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.side_effect = ["Result A", "Result B"]

            generator = AIGenerator(api_key="test-key", model="claude-test")
            generator.generate_response(
                query="test",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        call_args = mock_client.messages.create.call_args_list
        # Both in-loop calls (indices 1 and 2) must carry tools
        assert "tools" in call_args[1][1], "tools missing from round-2 API call"
        assert "tools" in call_args[2][1], "tools missing from round-3 API call"

    def test_generate_response_tool_error_breaks_loop(self):
        """execute_tool raising an exception: loop exits, is_error:True in messages, no propagation."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = [
                _tool_use_response(),
                _text_response("Recovered"),
            ]
            mock_tool_manager = MagicMock()
            mock_tool_manager.execute_tool.side_effect = RuntimeError("boom")

            generator = AIGenerator(api_key="test-key", model="claude-test")
            # Must not raise
            result = generator.generate_response(
                query="test",
                tools=[{"name": "search_course_content"}],
                tool_manager=mock_tool_manager,
            )

        assert result == "Recovered"
        # Verify is_error:True was set in the tool_result message
        second_kwargs = mock_client.messages.create.call_args_list[1][1]
        tool_result_block = next(
            block
            for msg in second_kwargs["messages"]
            if isinstance(msg.get("content"), list)
            for block in msg["content"]
            if isinstance(block, dict) and block.get("type") == "tool_result"
        )
        assert tool_result_block.get("is_error") is True
