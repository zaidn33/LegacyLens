# Phase 8 Notes: Authentication & Multi-User Deployment

LegacyLens has migrated from a single-user local tool to a multi-tenant application secured strictly via HttpOnly Cookies and ready for centralized Docker-based distribution.

## Architecture Boundaries
- **JWT & HttpOnly Cookies:** JWTs are minted upon login and issued strictly in `HttpOnly`, `SameSite=Lax` cookies. The frontend code NEVER stores or touches raw tokens in localStorage, preventing XSS token harvesting.
- **Frontend/Backend Unification via Proxy:** The Next.js server proxies requests from `localhost:3000/api/*` to FastAPI `http://backend:8000/api/v1/*` behind the scenes. This allows the Next.js fetch implementation to specify `Same-Origin` credential inclusion (cookie shipping) without triggering domain constraint failures or requiring fragile CORS `expose_header` setups.
- **Scoping & Ownership:** A strict authorization barrier via `get_current_user` evaluates the token natively. Every DB mutation and query filters natively on `user_id`. Attempting to request cross-tenant data (including artifacts) resolves strictly to 404 or 401.

## Security Posture
- **CSRF Resistance:** The current architecture relies on same-origin proxying plus `SameSite=Lax` cookies for baseline CSRF resistance in this phase. Dedicated CSRF tokens are not yet implemented.
- **Docker Deployment Limits:** Docker and docker-compose configurations are fully authored and structurally sound. However, live containerized runtime verification was not fully completed because Docker was unavailable on the host machine.

## Secrets
- Deployments must supply values in `.env` to operate securely.
- `JWT_SECRET` must be set for cryptographic token signing.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` can optionally be passed to safely initialize a seed user on application start, offering Day 0 access without needing open registration.
