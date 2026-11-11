import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { homeFor, navFor } from "./api";
import { useAuth } from "./auth";
import { EMPTY_MESSAGE, ROLE_LABELS } from "./types";
import type { Role } from "./types";

export function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function Frame({ children }: { children: ReactNode }) {
  return <div className="app-frame">{children}</div>;
}

export function Shell({ title, children }: { title: string; children: ReactNode }) {
  const { me, logout } = useAuth();
  const items = me ? navFor(me.roles) : [];
  const home = me ? homeFor(me.roles) : "/login";
  return (
    <Frame>
      <div className="px-4 py-4 md:px-8 md:py-6">
        <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-full focus:bg-lime focus:px-3 focus:py-2 focus:text-ink">
          Skip to content
        </a>
        <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-lime text-sm font-bold text-ink">IT</span>
            <span className="text-sm font-semibold tracking-wide">IT Hub</span>
          </div>
          <nav className="flex gap-1 overflow-x-auto rounded-full bg-black/30 p-1" aria-label="Primary">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold ${isActive ? "bg-lime text-ink" : "text-white/85 hover:bg-white/5"}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            {me ? (
              <div className="text-right">
                <div className="text-sm font-semibold">{me.display_name}</div>
                <div className="text-xs text-muted">{me.roles.map((role) => ROLE_LABELS[role]).join(", ")}</div>
              </div>
            ) : null}
            <button type="button" className="rounded-full border border-white/15 px-4 py-2 text-sm" onClick={() => void logout()}>
              Sign out
            </button>
          </div>
        </header>
        <div className="mt-8 flex items-center gap-3">
          {home !== window.location.pathname ? (
            <NavLink to={home} className="grid h-10 w-10 place-items-center rounded-full border border-white/15 text-lg" aria-label="Back">
              ←
            </NavLink>
          ) : null}
          <h1 className="text-4xl font-semibold tracking-tight">{title}</h1>
        </div>
        <main id="content" className="mt-6">
          {children}
        </main>
      </div>
    </Frame>
  );
}

export function Card({
  title,
  lastUpdated,
  action,
  children,
}: {
  title: string;
  lastUpdated?: string | null;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-card p-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {lastUpdated ? <p className="mt-1 text-sm text-muted">Last updated {formatTime(lastUpdated)}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ message = EMPTY_MESSAGE }: { message?: string | null }) {
  return <p className="text-sm leading-6 text-muted">{message || EMPTY_MESSAGE}</p>;
}

export function ErrorState({ message }: { message?: string | null }) {
  return <p className="text-sm leading-6 text-bad">{message || "Could not load this data."}</p>;
}

export function LoadingBlock() {
  return <div className="h-12 w-40 animate-pulse rounded-2xl bg-white/10" aria-label="Loading" />;
}

export function SectionBody({
  status,
  message,
  children,
}: {
  status: "loading" | "ok" | "not_configured" | "error";
  message?: string | null;
  children: ReactNode;
}) {
  if (status === "loading") return <LoadingBlock />;
  if (status === "error") return <ErrorState message={message} />;
  if (status !== "ok") return <EmptyState message={message} />;
  return children;
}

export function KpiCard({
  label,
  value,
  hint,
  hintTone,
  status,
  message,
}: {
  label: string;
  value?: string;
  hint?: string;
  hintTone?: "good" | "bad" | "muted";
  status: "loading" | "ok" | "not_configured" | "error";
  message?: string | null;
}) {
  const tone = hintTone === "good" ? "text-good" : hintTone === "bad" ? "text-bad" : "text-muted";
  return (
    <div className="rounded-[24px] bg-elevated p-5">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{label}</div>
      <SectionBody status={status === "ok" && value === undefined ? "not_configured" : status} message={message}>
        <div className="mt-3 text-4xl font-semibold tracking-tight">{value}</div>
        {hint ? <div className={`mt-2 text-sm ${tone}`}>{hint}</div> : null}
      </SectionBody>
    </div>
  );
}

const CHIP = {
  up: "bg-good text-pine",
  degraded: "bg-warn text-pine",
  down: "bg-bad text-pine",
  unknown: "bg-[#d5dde3] text-pine",
};

const CHIP_LABEL = { up: "Running", degraded: "Degraded", down: "Down", unknown: "Unknown" };

export function StatusChip({ status }: { status: keyof typeof CHIP }) {
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${CHIP[status]}`}>{CHIP_LABEL[status]}</span>;
}

export function PillTabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: T; label: string; count?: number }[];
  active: T;
  onChange: (id: T) => void;
}) {
  return (
    <div className="inline-flex flex-wrap gap-1 rounded-full bg-black/30 p-1" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={tab.id === active}
          className={`rounded-full px-4 py-2 text-sm font-semibold ${tab.id === active ? "bg-lime text-ink" : "text-white/85"}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.count !== undefined ? ` ${tab.count}` : ""}
        </button>
      ))}
    </div>
  );
}

export type DataRow = {
  id: string;
  title: string;
  meta: string;
  trailing?: string;
  status?: keyof typeof CHIP;
};

export function DataList({
  rows,
  selectedId,
  onSelect,
}: {
  rows: DataRow[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <ul className="space-y-2">
      {rows.map((row) => {
        const selected = row.id === selectedId;
        return (
          <li key={row.id}>
            <button
              type="button"
              aria-pressed={selected}
              className={`flex w-full items-center gap-3 rounded-[22px] px-3 py-3 text-left ${selected ? "bg-pine text-white" : "text-pine hover:bg-black/5"}`}
              onClick={() => onSelect(row.id)}
            >
              <span className="min-w-0 flex-1">
                <span className="block truncate font-semibold">{row.title}</span>
                <span className={`mt-1 block truncate text-sm ${selected ? "text-white/75" : "text-pine/70"}`}>{row.meta}</span>
              </span>
              {row.status ? <StatusChip status={row.status} /> : null}
              {row.trailing ? <span className="text-sm font-semibold">{row.trailing}</span> : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export function FilterRow({
  query,
  status,
  onQuery,
  onStatus,
}: {
  query: string;
  status: string;
  onQuery: (value: string) => void;
  onStatus: (value: string) => void;
}) {
  const count = Number(query.trim().length > 0) + Number(status !== "any");
  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <div className="inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 text-sm">
        Active filters
        <span className="grid h-6 min-w-6 place-items-center rounded-full bg-lime px-2 font-semibold text-ink">{count}</span>
      </div>
      <select
        aria-label="Status"
        value={status}
        onChange={(event) => onStatus(event.target.value)}
        className="rounded-full border border-white/10 bg-card px-4 py-2 text-sm"
      >
        <option value="any">Any status</option>
        <option value="up">Running</option>
        <option value="degraded">Degraded</option>
        <option value="down">Down</option>
        <option value="unknown">Unknown</option>
      </select>
      <input
        type="search"
        value={query}
        aria-label="Search"
        placeholder="Search"
        onChange={(event) => onQuery(event.target.value)}
        className="min-w-48 flex-1 rounded-full border border-white/10 bg-card px-4 py-2 text-sm outline-none"
      />
    </div>
  );
}

export function PrimaryButton({
  children,
  type = "button",
  disabled,
  onClick,
}: {
  children: ReactNode;
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className="rounded-full bg-lime px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
    >
      {children}
    </button>
  );
}

export function Notice({ children }: { children: ReactNode }) {
  return <p className="rounded-2xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm text-bad">{children}</p>;
}

export function roleChoices(includeExecutive: boolean): Role[] {
  const roles: Role[] = ["it_manager", "system_admin", "network_admin", "helpdesk"];
  if (includeExecutive) roles.push("executive");
  return roles;
}
