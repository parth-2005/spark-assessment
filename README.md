# Query Intelligence — FastAPI

This project implements a small async FastAPI service that accepts natural-language
research queries, runs an agentic loop using a configurable LLM (default: Gemma 4 26B),
grounds searches using Google Search, synthesizes structured intelligence JSON, and
persists results to SQLite.

### Key features
- Async, non-blocking FastAPI app using background tasks for LLM work
- SQLite persistence via `sqlmodel` and `aiosqlite`
- Provider abstraction (`LLM_PROVIDER`) to switch models
- Simple JSON output schema for downstream consumption

### Repository layout


```

.
├── agent/                # prompts, provider, agent loop
├── db/                   # async DB engine and models
├── routers/              # API endpoints
├── schemas/              # request/response Pydantic models
├── main.py               # FastAPI app and startup
├── requirements.txt
├── .env.example
└── README.md

```

### Architecture

- **POST /queries**: validate input, insert DB row with `status="processing"`,
  schedule an async background task to call the agent, immediately return 202 with the `id`.
- **Background task**: runs the agent (search grounding + synthesis), extracts structured JSON
  and grounding URLs, updates the DB row to `status="completed"` and stores results.
- **GET /queries/{id}**: returns stored intelligence (or 404 if not found).

### Note on Starter Code Deviation
The assessment prompt provided starter code using the `anthropic` SDK. However, I made the deliberate architectural decision to swap this for the `google-genai` SDK. The primary reason for this change was to leverage native **Google Search Grounding** (`tools=[{"google_search": {}}]`). For a corporate research platform, returning live, verifiable web sources alongside the intelligence is vastly more valuable than relying strictly on a model's internal weights. To support this while maintaining flexibility, I also introduced an `LLM_PROVIDER` abstraction.

### Data model (table `queries`)

- `id` (UUID string) — PK
- `raw_query` — original query text
- `status` — `processing | completed | failed`
- `llm_provider` — value of `LLM_PROVIDER` used
- `intent`, `entities`, `intelligence`, `sources` — stored as JSON strings
- timestamps: `created_at`, `completed_at`

### API

- **POST /queries**
    - Request JSON: `{ "query": "find battery technology startups in Southeast Asia" }`
    - Response: `202 Accepted` with `{ "id": "...", "status": "processing" }`

- **GET /queries/{id}**
    - Response: full stored result with `intelligence`, `sources`, timestamps.

### Environment and configuration

Copy the example `.env.example` and set your API key and optionally provider:

```bash
cp .env.example .env
# Edit .env: set GOOGLE_API_KEY and (optionally) LLM_PROVIDER

```

**Important variables**

* `GOOGLE_API_KEY` — required; used by the `google-genai` SDK
* `LLM_PROVIDER` — one of `gemma_26b` (default), `gemma_31b`, `gemini_flash`, `ollama`
* `DATABASE_URL` — DB connection string (defaults to `sqlite+aiosqlite:///./queries.db`)

### Installation

Windows example:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env to set GOOGLE_API_KEY
uvicorn main:app --reload

```

### Notes on async and non-blocking behavior

* The agent call uses the `google-genai` SDK which is synchronous. To avoid blocking
FastAPI's event loop, the synchronous call is executed in a threadpool via
`asyncio.get_running_loop().run_in_executor(...)` in `agent/loop.py`.
* Incoming POST requests are fast: they insert a DB row and schedule a background task
via `asyncio.create_task(...)`, returning immediately so the HTTP layer remains responsive.

### Development

* **DB models and migration**: The project uses SQLite for simplicity. On startup `main.py`
ensures tables are created with `create_db_and_tables()`.
* **Provider mapping** is in `agent/provider.py` — change `LLM_PROVIDER` to pick a different model.

### Troubleshooting

* If startup fails with `GOOGLE_API_KEY not set`, ensure `.env` contains the key (and
`python-dotenv` loads it). The app validates this on startup.
* If the model response cannot be parsed as JSON, the background task will mark the
query `status = failed` and save the exception text to the `error` column.

### Next steps / enhancements

* Convert background processing to a durable queue (Redis/RQ or Celery) for reliability.
* Add paginated listing endpoints and filtering by `status` or `intent`.
* Add unit+integration tests and CI config.
* Add streaming SSE for progress updates while agent runs.