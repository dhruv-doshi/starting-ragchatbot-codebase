# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Always use `uv` to run Python commands. Never use `pip`.

```bash
# Install dependencies
uv sync

# Run the server (from repo root)
./run.sh

# Or manually (must run from backend/ directory)
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Requires a `.env` file in the repo root with `ANTHROPIC_API_KEY=...` (see `.env.example`).

There are no tests in this codebase.

## Architecture

### Request flow

1. `POST /api/query` → `RAGSystem.query()` → `AIGenerator.generate_response()` (with tools)
2. Claude decides whether to call `search_course_content` tool
3. `CourseSearchTool.execute()` → `VectorStore.search()` → ChromaDB semantic search
4. Tool results returned to Claude → final answer generated
5. Exchange saved to `SessionManager` (in-memory, last 2 exchanges per session)

### Key design decisions

- **Tool-based RAG**: Retrieval is done via an Anthropic tool call, not pre-fetched context injection. Claude decides when and how to search.
- **Two ChromaDB collections**: `course_catalog` (one doc per course, for fuzzy name resolution) and `course_content` (chunked lesson text, for semantic search). Course name in a query is first resolved against `course_catalog`, then used as a metadata filter on `course_content`.
- **Chunking is sentence-aware**: `DocumentProcessor.chunk_text()` splits on sentence boundaries (not raw character count) and carries overlapping sentences (up to 100 chars) into the next chunk.
- **Session history is injected into the system prompt** as plain text, not as Anthropic `messages[]` history. Only the last `MAX_HISTORY=2` exchanges are kept.
- **ChromaDB is persistent** at `backend/chroma_db/`. Documents are deduplicated by course title on startup — already-loaded courses are skipped.

### Document format

Course `.txt` files in `docs/` must follow this structure:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: Introduction
Lesson Link: <url>
<lesson content...>

Lesson 1: Next Topic
Lesson Link: <url>
<lesson content...>
```

The course title is used as the unique ID in ChromaDB. The first chunk of each lesson is prefixed with `"Lesson N content: ..."` to preserve retrieval context.

### Adding a new tool

1. Create a class extending `Tool` (ABC in `search_tools.py`) implementing `get_tool_definition()` and `execute()`
2. Register it: `tool_manager.register_tool(your_tool)` in `RAGSystem.__init__`
3. If it needs to expose sources to the UI, add a `last_sources` list attribute — `ToolManager` picks it up automatically
