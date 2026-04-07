# LegacyLens

LegacyLens is an AI-powered agentic modernization pipeline designed to translate complex legacy enterprise systems (e.g., COBOL) into modern, well-structured Python endpoints. It extracts business logic constraints, resolves multi-file dependencies, checks for logic parity through an LLM reflection loop, and persists the pipeline results securely with multi-tenant isolation.

## Technical Details

Supported Python Version: 3.11-slim
Frontend Stack: Next.js 16.2.1, React 19.2.4, TypeScript, Prism
LLM Pipeline: LangGraph, Google Gemini (1.5 Pro/Flash), IBM Granite support
Persistence: SQLite / Turso (LibSQL)
Authentication: JWT (JSON Web Tokens), bcrypt hashing (passlib)

## Getting Started

### Local Setup (Development)

Ensure you have Python installed. LegacyLens natively supports backwards compatibility up to Python 3.14.3 with targeted upstream warnings safely handled. 

1. Install backend dependencies:
```bash
pip install -r requirements.txt
```

2. Generate a `.env` file from the example and configure:
```bash
cp .env.example .env
```

3. Boot the FastAPI Backend:
```bash
python -m uvicorn backend.server:app --reload --port 8000
```

4. Boot the Next.js Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Running via Docker (Production)

LegacyLens includes a fully isolated `docker-compose.yml` environment, perfect for deployment without requiring local Python environments.

```bash
docker-compose up --build -d
```

Access the frontend via `http://localhost:3000` and the backend metrics via `http://localhost:8000`. Stop the environment at any time using `docker-compose down`.

## Environment Variables

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Secret key used to cryptographically trace cookie ownership. Needs to be replaced with a secure random key when deployed. |
| `USE_TURSO` | Determines SQLite strategy. `false` defaults to local filesystem DB (`legacylens.db`). `true` enforces remote connection. |
| `TURSO_DATABASE_URL` | Remote `libsql://` address for production data. Only required if `USE_TURSO=true`. |
| `TURSO_TEST_DATABASE_URL` | Dedicated isolated testing environment URL to prevent test suite from modifying production tables. |
| `TURSO_AUTH_TOKEN` | Bearer token allowing client access to the Turso provider. |

## Known Limitations

- **Cloud Testing Scope:** The automated test suite executes fully against local SQLite. Execution against Turso requires active provisioned credentials via `TURSO_DATABASE_URL` and `TURSO_TEST_DATABASE_URL`. Running `pytest` with `USE_TURSO=true` without set credentials immediately fails securely by design instead of silently degrading.
- **Upstream Pydantic Warnings:** Running under Python 3.14 emits upstream `UserWarning: Pydantic V1` compatibility flags. This stems from internal langchain-core implementations, not LegacyLens source code, and does not alter pipeline efficiency.
- **Provider API:** Testing limits via MockProvider ensures localized determinism. To evaluate IBM Granite endpoints, ensure `WATSONX_APIKEY` is added to your local environment file.
