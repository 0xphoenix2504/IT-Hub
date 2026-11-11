# IT Hub

IT Hub is a dashboard and launcher for the IT department. It shows statistics from other systems and links out to them. It does not store tickets, assets, or other business records.

The frontend and backend are separate projects. The frontend talks only to the Hub API. Authorization is enforced in the backend.

## Decisions for this build

- Interface language: English.
- Network monitor: adapter interface only. No product is selected.
- Ticketing and assets: adapter interfaces only. Their read APIs are not connected yet.
- Single sign-on into those systems: handoff interface only. Buttons are ordinary deep links, and only when a base URL is configured.
- Demo: run locally. Nothing is deployed.
- Active Directory groups: `executives` is fixed. The other four groups stay empty until an IT Manager maps them.
- Critical services: empty until an IT Manager adds them. Health stays empty until a monitor is connected.
- Confirmed access: Executive sees the summary only. System Admin sees servers. Network Admin sees network devices. Helpdesk sees ticket stats and end-user devices. IT Manager sees everything and settings. A person in several groups gets the union of those permissions.

Pages with no source connected show **No data connected yet**. They do not show placeholder numbers.

## Local setup

Requirements: Python 3.12+, Node.js 20+, and PostgreSQL. The Hub database holds accounts, sessions, group mappings, critical-service names, the audit log, and a short stats cache.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env`:

- `DATABASE_URL` — PostgreSQL connection string, for example `postgresql+psycopg://it_hub:password@localhost:5432/it_hub`
- `FIRST_ADMIN_USERNAME` and `FIRST_ADMIN_PASSWORD` — used once, to create the first IT Manager when that username does not exist. Password must be at least 10 characters. This is the only seed.
- `CORS_ORIGIN` — exact frontend origin, for example `http://localhost:5173`
- `AUTH_PROVIDER=local` for this demo
- Leave `COOKIE_SECURE` empty while you use HTTP locally. It turns on automatically when `APP_ENV=production`.

Create the database, then:

```powershell
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Leave `VITE_API_BASE_URL` empty so the dev server proxies `/api` and the session cookie stays on that origin. Do not put secrets in any `VITE_` variable.

Tests, from `backend`:

```powershell
python -m pytest
```

The tests use an in-memory SQLite database. The running app should use PostgreSQL.

## What each role sees

| Page | Who |
|---|---|
| Overview | Executive, IT Manager |
| Servers | System Admin, IT Manager |
| Network | Network Admin, IT Manager |
| Helpdesk | Helpdesk, IT Manager |
| Settings | IT Manager |

A directory user who is not in `executives` and not in a mapped group is rejected even with a correct password. Executive responses do not include IP addresses, hostnames, interface names, or logs.

## Settings an IT Manager can change

- Map Active Directory groups to IT Manager, System Admin, Network Admin, or Helpdesk.
- Name the critical services the executive page will request from a future monitor.
- Create local accounts while `AUTH_PROVIDER=local`.
- Read the audit log.

Secrets stay in the backend environment: database URL, the first-admin password, and the LDAPS bind password. The settings screen shows whether each adapter is configured. It does not edit secrets.

Deep links, when you want them:

- `TICKETING_APP_BASE_URL`
- `ASSETS_APP_BASE_URL`

Use `http` or `https` URLs with no username or password. Empty values hide the buttons.

## Move to the internal server

Keep the same code. Change configuration and run migrations.

1. Serve `frontend/dist` (`npm run build`) as static files from Nginx or Caddy.
2. Run the backend with `uvicorn app.main:app` as a service behind that proxy, on HTTPS.
3. Point `DATABASE_URL` at the local PostgreSQL and run `alembic upgrade head`.
4. Set `AUTH_PROVIDER=ldaps` and the `LDAPS_*` variables. The URL must start with `ldaps://`.
5. Set `CORS_ORIGIN` to the exact site origin, `APP_ENV=production`, and `COOKIE_SECURE=true`.
6. If the proxy sets `X-Forwarded-For` and you want that address in the audit log, set `TRUST_PROXY=true`.

Supabase, if used for the demo database, is only a PostgreSQL connection string. Do not enable Supabase Auth, Row Level Security, Storage, Realtime, or Edge Functions. Moving off it is a new `DATABASE_URL` plus migrations.

The frontend can be hosted as a static site, including on Vercel, by setting `VITE_API_BASE_URL` to the public API origin at build time. That value is not a secret. The API itself stays a long-running process so the same code runs on the internal server.

## Auth providers

`AUTH_PROVIDER=local` checks usernames and passwords stored by the Hub. `AUTH_PROVIDER=ldaps` binds to Active Directory, reads group membership, and assigns roles. Sessions are random tokens in an HTTP-only cookie. The cookie value is stored only as a hash. Failed sign-ins are rate limited in this process.
