# Phase 9: Turso Cloud Database Integration

This document serves as the guide for utilizing the newly implemented Turso (libSQL) database integration in LegacyLens. The platform is robustly configured to transition smoothly between local SQLite environments and persistent remote Turso environments.

## 1. Turso Cloud Provisioning

To create a new Turso database and obtain the requisite credentials, utilize the Turso CLI:

1. **Create the production database:**
   ```bash
   turso db create legacylens
   ```
2. **Obtain the Connection URL:**
   ```bash
   turso db show --url legacylens
   ```
3. **Generate an Auth Token:**
   ```bash
   turso db tokens create legacylens
   ```

*Place both the URL and Token alongside `USE_TURSO=true` in your `.env` file.*

## 2. Test Isolation Database

> [!IMPORTANT]
> Real-world testing requires isolation. Tests executed using Turso must **not** overlap with your production table or local SQLite schema.

1. **Create the test database:**
   ```bash
   turso db create legacylens-test
   turso db show --url legacylens-test
   ```
   
Supply this specific URL within the `.env` variable `TURSO_TEST_DATABASE_URL`. During Pytest integration validation involving a `TURSO_TEST_DATABASE_URL`, this ensures non-destructive validation behavior.

## 3. Data Migration Approach

To transport preexisting analytical data, sessions, and user records established on your local SQLite into the cloud, use the built-in migration script.

```bash
python scripts/migrate_to_turso.py
```

### Script Behaviors:
- Requires `.env` configuration for `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`. 
- Ensures **foreign key integrity** natively by inserting strictly hierarchically (`users` → `jobs` → `pipeline_results` → `pipeline_errors`).
- Highly **Idempotent**: It employs `INSERT OR IGNORE`. Running this script repeatedly will neither fault on duplicate constraints nor write degenerate entries.

## 4. Local Fallback

If `USE_TURSO` is missing, commented out, or explicitly set to `false`, the platform will default flawlessly to spinning up `legacylens.db` through standard local Python standard library `sqlite3` without invoking `libsql-client`.

> [!CAUTION]
> **Deliberate Configuration Check**
> If you configure your environment stating `USE_TURSO=true` inside your `.env`, but inadvertently pass missing or totally wrong Turso URLs or authentication tokens, the application's startup payload will **explicitly intentionally fault out** (Fail-fast behavior). It fundamentally aborts, protecting against silent and obfuscated down-shifting back into local persistence while you believe production writes are occurring. Expect a `RuntimeError`.

## 5. Known Limitations
- `libsql-client` implements batch queries asynchronously and resolves Python dictionary types inherently. Our unified `DBWrapper` translates these `Row` structures symmetrically over to emulate `sqlite3.Row` functionality. This avoids heavy codebase rewriting, but means any highly low-level binary `sqlite3` built-in features missing from DBAPI specifications may require explicit mapping.
- The `try ... except Exception as e:` catch logic correctly emulates `sqlite3.OperationalError` locally for handling iterative additive migrations.
