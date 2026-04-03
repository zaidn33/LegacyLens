# Phase 9: Turso Cloud Database Integration

This document serves as the guide for utilizing the newly implemented Turso (libSQL) database integration in LegacyLens. The platform is configured to transition smoothly between local SQLite environments and persistent remote Turso environments.

## 1. Turso Cloud Provisioning

To create a new Turso database and obtain credentials, use the Turso CLI:

1. **Create the production database:**
   ```bash
   turso db create legacylens
   ```
2. **Obtain the connection URL:**
   ```bash
   turso db show --url legacylens
   ```
3. **Generate an auth token:**
   ```bash
   turso db tokens create legacylens
   ```

Place both the URL and Token alongside `USE_TURSO=true` in your `.env` file.

## 2. Test Isolation Database

> [!IMPORTANT]
> Real-world testing requires isolation. Tests executed against Turso must not overlap with your production database.

1. **Create a dedicated test database:**
   ```bash
   turso db create legacylens-test
   turso db show --url legacylens-test
   ```

2. **Set the test URL in `.env`:**
   ```env
   TURSO_TEST_DATABASE_URL=libsql://legacylens-test-yourorg.turso.io
   ```

`TURSO_TEST_DATABASE_URL` is included in `.env.example` alongside the production `TURSO_DATABASE_URL`. When running `pytest` against Turso, point the test suite to this dedicated database to avoid wiping or corrupting production data.

## 3. Data Migration

To copy existing local SQLite job data to Turso, run the migration script:

```bash
python scripts/migrate_to_turso.py
```

**Requirements:** `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` must be set in the environment.

**Script behaviors:**
- Inserts records in strict foreign-key order: `users` → `jobs` → `pipeline_results` → `pipeline_errors`.
- Uses `INSERT OR IGNORE` for idempotency — safe to run repeatedly without creating duplicates.
- Initializes the remote schema before inserting data.

## 4. Local Fallback

When `USE_TURSO` is unset, missing, or set to `false`, the application uses local SQLite (`legacylens.db`) via Python's built-in `sqlite3` module. No Turso dependencies are loaded in this mode.

> [!CAUTION]
> **Fail-fast on misconfigured Turso credentials.**
> If `USE_TURSO=true` is set but the connection fails (missing URL, invalid token, unreachable host), the application raises a `RuntimeError` at startup and halts. It will never silently fall back to local SQLite while you believe writes are going to the cloud.

## 5. Known Limitations

- **Turso cloud tests were not executed.** The automated test suite (`pytest tests/`) was verified against local SQLite only. Running the full test suite against a live Turso database requires provisioned credentials (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`) and a dedicated test database (`TURSO_TEST_DATABASE_URL`). This is left as a manual verification step after Turso provisioning. The DBWrapper adapter ensures identical SQL behavior across both backends, so local-passing tests are expected to pass against Turso without modification.
- The `_TursoWrapper` adapter translates `libsql-client` response structures to emulate `sqlite3.Row` dict-like access. Low-level SQLite-specific binary features not covered by the DB-API specification may require explicit mapping if used in the future.
- The `executescript()` method on the Turso wrapper splits SQL by semicolons and issues a `batch()` call. Complex multi-statement scripts with embedded semicolons in string literals should be tested individually.

## 6. Unchanged System Components

The following are explicitly confirmed unchanged by Phase 9:

| Component | Status |
|---|---|
| Pipeline behavior (Analyst → Coder → Reviewer loop) | Unchanged |
| `contracts.py` (all typed contracts and fields) | Unchanged |
| Artifact file structure on disk (files remain on filesystem, DB holds metadata only) | Unchanged |
| Phase 8 authentication (JWT, HttpOnly cookies, user scoping) | Unchanged |
| All existing API endpoint contracts (paths, parameters, response shapes) | Unchanged |

Phase 9 modifies only the database connection layer (`backend/db.py`), environment configuration, and adds the migration script. No pipeline logic, contract definitions, artifact storage, auth flows, or API surfaces were altered.
