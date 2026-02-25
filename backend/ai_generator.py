import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    MAX_ROUNDS = 2  # Maximum sequential tool-call rounds per query

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use `search_course_content` **only** for questions about specific course content or detailed educational materials
- Use `get_course_outline` for any question about a course's structure, lessons list, or topics covered — it returns the course title, course link, and numbered lesson list
- **You may make up to 2 sequential tool calls per query** if the first result informs a more precise second search
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives
- When presenting a course outline, always include: course title, course link, and each lesson as "Lesson N: <title>"

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports up to MAX_ROUNDS sequential tool calls.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Initial messages list — grows across tool rounds
        messages = [{"role": "user", "content": query}]

        # Prepare first API call
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content,
        }
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # First API call
        response = self.client.messages.create(**api_params)

        # Sequential tool-call loop — up to MAX_ROUNDS
        round_count = 0
        error_occurred = False

        while (
            round_count < self.MAX_ROUNDS
            and response.stop_reason == "tool_use"
            and tool_manager is not None
        ):
            round_count += 1
            tool_results = []

            for content_block in response.content:
                if content_block.type != "tool_use":
                    continue

                try:
                    result = tool_manager.execute_tool(
                        content_block.name, **content_block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": result,
                    })
                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Tool error: {e}",
                        "is_error": True,
                    })
                    error_occurred = True
                    break  # stop processing further tool calls this round

            # Append assistant turn and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            if error_occurred:
                break

            # Next API call — tools still available for potential second round
            response = self.client.messages.create(
                **self.base_params,
                messages=messages,
                system=system_content,
                tools=tools,
                tool_choice={"type": "auto"},
            )

        # Rounds exhausted but Claude still wants a tool call — make a final
        # no-tools call so Claude can synthesise what it has into a text answer.
        if response.stop_reason == "tool_use":
            response = self.client.messages.create(
                **self.base_params,
                messages=messages,
                system=system_content,
            )

        return response.content[0].text
