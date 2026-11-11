# IT Hub: Project Spec for the Coding Agent

Read this whole file before writing any code. If something is unclear or missing, **ask. Do not guess and do not invent.**

---

## 1. Hard rules (non-negotiable)

1. **NO sample, mock, fake, or demo data. Anywhere.** No seed scripts with fake tickets, assets, devices, users, or statistics. No hardcoded numbers in charts. No "Lorem ipsum" values. When there is no real data, the UI shows a clear **empty state** ("No data connected yet"), never placeholder numbers. The only allowed seed is creating the first admin account from environment variables.
2. **Frontend and backend are separate projects**, deployed separately.
3. **The frontend holds no important data and no secrets.** See section 6.
4. **Keep it lightweight and simple.** Low RAM/CPU, few dependencies, no over-engineering. No microservices, no message queues, no Redis, no Kubernetes unless explicitly requested.
5. **All authorization is enforced in the backend.** Hiding a button in the UI is never security.
6. **Do not build vendor lock-in into Supabase or Vercel.** They are only the temporary demo hosting (section 7). The app must move to an internal server by changing configuration only.
7. **UI follows the visual reference in section 13** (`ui-reference.png`). It is a style reference only. Never copy its branding, text, numbers, names, or photos.

---

## 2. What this system is

A **centralized IT Hub** for the IT department. It is a **dashboard + launcher**:

- **Shows** aggregated data and statistics collected from other systems.
- **Links out** (deep links) to those systems, where the real work is done.
- The Hub does **not** store business data (tickets, assets). It reads them from the source systems.

Final deployment is **on-premise on an internal server**, authenticating users through **LDAPS** against the company Active Directory. Only the IT team and the executives can log in. **Regular employees have no access at all.**

### Connected systems

| System | Where | Role of the Hub |
|---|---|---|
| **Ticketing + Assets system** | Separate system on another local machine. The team owns it and **can modify it freely**. | Read statistics via an internal read-only API; deep-link into it. |
| **Network monitor** | **Not decided yet** (Zabbix, PRTG, LibreNMS, etc. possible). | Read device/server status through a **swappable adapter**. |
| **Active Directory** | Company domain servers | Authentication (LDAPS) and group-to-role mapping. |

---

## 3. Roles and permissions (RBAC)

Five roles. Each user sees **only** what their role allows. Role is derived from AD group membership.

| Role | AD group | Can see |
|---|---|---|
| **Executive** | `executives` | Only the simplified executive dashboard (section 4). Read-only. No technical details. |
| **IT Manager** | *(to be confirmed)* | Everything, including overall reports, and manages settings and group mappings. |
| **System Admin** | *(to be confirmed)* | Servers: their assets, status from monitor, server-related ticket stats. |
| **Network Admin** | *(to be confirmed)* | Network devices: their assets, status from monitor, network-related ticket stats. |
| **Helpdesk** | *(to be confirmed)* | Ticket stats and end-user devices only. No servers, no network devices. |

Rules:
- A user **not in any approved group is denied**, even with a correct password.
- If a user is in several groups, they get the **union** of permissions (highest role wins for settings).
- Group names, other than `executives`, **must be configurable**, not hardcoded.
- Every permission check happens server-side. Every response is filtered by role **before** it leaves the backend.
- The Executive role must never receive technical fields (IPs, hostnames, interface names, logs) in API responses, not just hide them in the UI.

> The per-role scope above is the current assumption. Confirm with the owner before finalizing.

---

## 4. Executive dashboard

Audience: 3-5 senior managers, **non-technical**. Goal: understand IT health at a glance.

- **One page.** No complex filters. Works well on **mobile and tablet**.
- Simple wording (e.g. "Services running", "Open issues"), clear green / yellow / red status.
- **Every number comes from a real source system.** No manual or estimated figures. Show **"last updated"** time next to the data.

Content, in order of importance:
1. **Service health now**: green/yellow/red per critical service + availability % over the last 30 days. *(The list of critical services is TBD and must be configurable.)*
2. **Tickets**: open now, closed this month, average resolution time, comparison with last month (up/down).
3. **Assets**: total devices and servers, and how many are near end of warranty/life.
4. **Most frequent problems**: top 3-5 types.
5. **Monthly PDF report export.**

---

## 5. Recommended tech stack (lightweight)

Chosen for **low runtime, low resource use, and minimal complexity**.

### Backend: Python + FastAPI
- Small memory footprint, single process, easy to run as a service on an internal server.
- `ldap3` for LDAPS.
- `SQLAlchemy` + `Alembic` for the database and migrations, talking to **plain PostgreSQL**.
- `httpx` for calling the ticketing/assets system and the monitor.
- Runs locally with `uvicorn` behind a reverse proxy (Nginx or Caddy).

### Frontend: React + Vite + TypeScript (static build)
- Builds to plain static files, so no server runtime is needed in production.
- Tailwind CSS for styling, a small chart library (e.g. Recharts or Chart.js).
- Must support **RTL and Arabic** if requested (ask the owner, see open questions).

### Database: PostgreSQL
- Supabase **is** PostgreSQL, so the same schema moves to a local PostgreSQL unchanged.
- The Hub database is **small**. It holds only: users/sessions metadata, AD-group-to-role mapping, adapter settings, audit log, and an optional stats cache. **No business data.**

### Auth
- Production: **LDAPS** against AD, with group-to-role mapping.
- Session in an **httpOnly, Secure, SameSite cookie** (or short-lived JWT in such a cookie). Never in localStorage.
- Implement auth behind an interface: `AUTH_PROVIDER=ldaps | local`. The demo uses `local` (see section 7).

### Integration layer (adapters)
- Each external system sits behind its own adapter interface:
  - `TicketingAdapter` / `AssetsAdapter` for the ticketing and assets system.
  - `MonitorAdapter` for the network monitor. **Product is undecided, so build only the interface now** and one concrete implementation once the product is chosen.
- Adapters return a **unified internal format**. Swapping a monitor product must not change the rest of the app.
- An adapter without configuration returns "not configured", and the UI shows an empty state. It never returns fake data.

---

## 6. Frontend security rules (keep important data out of the frontend)

- The frontend **never** talks directly to Supabase, the database, AD, the monitor, or the ticketing system. It talks **only to the Hub backend API**.
- **No secrets** in the frontend: no API keys, no service keys, no tokens in env vars prefixed for the client (`VITE_*`), nothing in the repo that ships in the bundle.
- **No important data in the bundle or in browser storage**: no localStorage/sessionStorage of business data, no hardcoded lists of devices, users, or IPs.
- Data is fetched per page, per role, from the backend, and held in memory only.
- Backend CORS allows **only the frontend's exact origin**.
- Rate limiting and lockout on login. Audit-log every login and sensitive action.
- Secrets live **only** in backend environment variables. `.env` files are git-ignored; provide `.env.example` with **empty** values.

---

## 7. Deployment plan

### Phase 1: Online demo
- **Frontend** on **Vercel** (static).
- **Backend** deployed separately (Vercel serverless functions as a separate project, or any simple host the owner prefers). Keep the code runnable as a normal long-running `uvicorn` app too, so it moves on-prem without changes.
- **Database** on **Supabase**, used **only as managed PostgreSQL** via a connection string. **Do not use** Supabase Auth, Row Level Security, Storage, Realtime, or Edge Functions. Auth and authorization are in the backend.
- Authentication in the demo: the internal AD is not reachable from the internet, so use `AUTH_PROVIDER=local` with accounts created by an admin. Only the first admin is bootstrapped from env vars. Do not create fake users.
- Because there is no real data and no sample data, pages will mostly show **empty states** until real adapters are connected. That is expected and correct.

### Phase 2: On-premise
- Frontend: static files served by Nginx/Caddy on the internal server.
- Backend: `uvicorn` as a systemd service (or Docker if the owner prefers).
- Database: local PostgreSQL. **Migrating = changing `DATABASE_URL` and running migrations.** Document this.
- Auth: switch to `AUTH_PROVIDER=ldaps` and set the AD settings.
- Everything runs inside the internal network only.

---

## 8. Suggested project structure

```
it-hub/
├── frontend/        # React + Vite (separate project, separate deploy)
│   └── .env.example
├── backend/         # FastAPI (separate project, separate deploy)
│   ├── app/
│   │   ├── api/         # routes, role-filtered responses
│   │   ├── auth/        # ldaps + local providers
│   │   ├── adapters/    # ticketing, assets, monitor (interfaces first)
│   │   ├── models/      # SQLAlchemy models
│   │   └── core/        # config, security, audit
│   ├── alembic/
│   └── .env.example
├── docs/
│   └── ui-reference.png # visual reference for the UI (section 13)
└── README.md        # setup, deploy to Vercel/Supabase, move to on-prem
```

---

## 9. Non-functional requirements

- **Capacity**: the source systems track roughly 500-1000 employees and their devices/tickets. The Hub itself has **very few concurrent users** (IT team + 3-5 executives). Keep the Hub fast with caching of stats, not with heavy infrastructure.
- Dashboards should load fast (cache stats briefly in the backend).
- Production traffic over **HTTPS only**.
- Clear logging and an audit trail.

---

## 10. Out of scope

- Employee-facing portal or any employee login.
- Creating or editing tickets/assets **inside the Hub** (done in the ticketing/assets system).
- Storing tickets or assets in the Hub database.
- Any sample/demo/mock data.
- Choosing the network monitor product (interface only for now).

---

## 11. Open questions (the agent must ask, not assume)

1. Which services count as **critical** for the executive dashboard?
2. Which network monitor product will be used?
3. Exact AD group names for the four IT roles (only `executives` is fixed).
4. Does the ticketing/assets system already expose an API, or should one be added to it? (The team can modify it.)
5. Should the Hub log users into the ticketing system automatically (SSO via the same LDAPS)?
6. Interface language: Arabic, English, or both (RTL needed)?
7. Where should the demo backend be hosted?

---

## 12. Definition of done (per phase)

**Phase 1 (demo):**
- Frontend on Vercel, backend and Supabase DB connected, login works, role-based pages work.
- Zero fake data anywhere; empty states render correctly.
- Security checklist in section 6 verified (no secrets or data in the bundle).

**Phase 2 (on-prem):**
- Runs on the internal server with LDAPS login and AD-group role mapping.
- Executive dashboard shows only real numbers with "last updated".
- Switching from the demo needs configuration changes only.

---

## 13. UI design reference

The file **`ui-reference.png`** (put it in `docs/` and view it before building any UI) is the **visual style reference** for the whole system. Match its look and feel, not its content.

### What to take from it

- **Dark theme by default**: deep navy / near-black background with slightly lighter rounded cards on top.
- **One neon lime-green accent color** for the active tab, primary buttons, highlights, and progress bars. Everything else stays neutral (white, greys). Define the colors as design tokens (CSS variables / Tailwind theme) in one place, not scattered in components.
- **Big rounded cards** (large border radius, soft subtle borders, light glass/gradient feel) grouping related information.
- **Big, bold numbers with small muted labels above them** for KPIs (this is the core pattern for the executive dashboard).
- **Floating pill-shaped top navigation** with icon buttons; the active item is a lime pill. The page title is large, with a back arrow.
- **Segmented pill tabs with counters** (e.g. "All / Draft 3 / Unpaid 5") for switching views.
- **Thin horizontal progress bars** for ratios and time ranges.
- **Filter row** above lists (dropdowns, date range, search box) with an "active filters" counter. Use it on technical pages only, **not** on the executive page.
- **Master-detail layout on technical pages**: a list on the left, details of the selected row on the right, inside a contrasting light panel.
- Tablet-friendly proportions and generous spacing. Must stay clean on mobile.
- Clean modern sans-serif font. If the UI is Arabic, pick a good Arabic font to pair with it and mirror the layout (RTL).

### How to adapt it to this project

- **Executive page**: the top KPI cards pattern. Big numbers for open tickets, service availability %, total assets, and average resolution time, each with a small trend indicator and "last updated". Use **green / yellow / red** status colors for service health, and keep lime as the brand accent.
- **Technical pages** (System Admin, Network Admin, Helpdesk): list + detail layout for devices/servers/ticket stats, with status chips.
- The Hub is **read-only**. Replace any "action" buttons from the reference (like "Pay out now" or "Create an invoice") with **"Open in ticketing system"** or **"Open in assets"** deep-link buttons.
- Replace the reference's money/invoice concepts entirely with IT concepts. No finance wording.

### Do not copy

- The Salesforce logo or any brand name, the company/customer names, the avatars and photos, the invoice numbers, and every number in the image. They are **sample data**, which is forbidden by rule 1.
- Avatar stacks only appear when a real user/technician list exists. Otherwise omit them.

### Quality bar

- Consistent spacing, radius, and typography across all pages (build a small shared component library first: Card, KpiCard, StatusChip, PillTabs, DataList).
- Sufficient text contrast on the dark background (accessibility).
- Every card has loading, error, and **empty** states.
