
# IT Hub

IT Hub is a dashboard and launcher for the IT department. It shows statistics from other systems and links out to them. It does not store tickets, assets, or other business records.

The frontend and backend are separate projects. The frontend talks only to the Hub API. Authorization is enforced in the backend.

## Decisions for this build

- Interface language: English and Arabic (bilingual with instant LTR/RTL toggle in the header).
- Network monitor: adapter interface + HTTP implementation with fallback empty state.
- Ticketing and assets: adapter interfaces + HTTP implementations.
- Single sign-on into those systems: handoff interface only. Buttons are ordinary deep links, and only when a base URL is configured.
- Deployment: Vercel-ready for both Frontend (static) and Serverless Fullstack, plus on-premise systemd/uvicorn instructions.
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

## Deploying to Vercel (Online Demo)

IT Hub is fully configured for deployment on Vercel. You can deploy it in either of two ways:

### Option 1: Full-Stack on Vercel (Root Deployment)
1. Import the repository into Vercel and leave the **Root Directory** as `./`.
2. Vercel automatically uses `vercel.json`:
   - Builds the frontend via `cd frontend && npm install && npm run build` -> `frontend/dist`.
   - Serves API routes (`/api/*`) via serverless Python (`api/index.py`).
3. In your Vercel Project Settings -> **Environment Variables**, add:
   - `DATABASE_URL`: Your Supabase connection string (e.g. `postgresql+psycopg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres` or pooled port 6543)
   - `AUTH_PROVIDER`: `local`
   - `FIRST_ADMIN_USERNAME`: `admin`
   - `FIRST_ADMIN_PASSWORD`: `<strong-password-at-least-10-chars>`
   - `FIRST_ADMIN_DISPLAY_NAME`: `Hub Administrator`
   - `CORS_ORIGIN`: `https://<your-project>.vercel.app` (or comma-separated with `http://localhost:5173`)
   - `COOKIE_SECURE`: `true`
   - `COOKIE_SAMESITE`: `lax`
4. Click **Deploy**. On initial startup, tables are automatically verified and the initial admin user is bootstrapped.

### Option 2: Frontend-Only on Vercel (Static)
1. Import the repository into Vercel and set the **Root Directory** to `frontend`.
2. Add the environment variable:
   - `VITE_API_BASE_URL`: URL of your backend API (e.g. `https://api.yourdomain.com`).
3. Deploy! `frontend/vercel.json` ensures all client-side routes (`/servers`, `/network`, `/settings`, etc.) route properly without 404 errors.

## Auth providers

`AUTH_PROVIDER=local` checks usernames and passwords stored by the Hub. `AUTH_PROVIDER=ldaps` binds to Active Directory, reads group membership, and assigns roles. Sessions are random tokens in an HTTP-only cookie. The cookie value is stored only as a hash. Failed sign-ins are rate limited in this process.
