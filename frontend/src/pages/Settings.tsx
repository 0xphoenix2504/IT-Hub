import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { Card, Notice, PrimaryButton, Shell, formatTime, roleChoices } from "../components";
import { ROLE_LABELS } from "../types";
import type { AuditOut, ConnectionOut, MappingOut, Role, ServiceOut, UserOut } from "../types";

export function SettingsPage() {
  const { me } = useAuth();
  const [connections, setConnections] = useState<ConnectionOut[]>([]);
  const [mappings, setMappings] = useState<MappingOut[]>([]);
  const [services, setServices] = useState<ServiceOut[]>([]);
  const [users, setUsers] = useState<UserOut[]>([]);
  const [audit, setAudit] = useState<AuditOut[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    try {
      const [nextConnections, nextMappings, nextServices, nextUsers, nextAudit] = await Promise.all([
        api<ConnectionOut[]>("/api/settings/connections"),
        api<MappingOut[]>("/api/settings/mappings"),
        api<ServiceOut[]>("/api/settings/services"),
        api<UserOut[]>("/api/settings/users"),
        api<AuditOut[]>("/api/settings/audit"),
      ]);
      setConnections(nextConnections);
      setMappings(nextMappings);
      setServices(nextServices);
      setUsers(nextUsers);
      setAudit(nextAudit);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load settings.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <Shell title="Settings">
      <div className="space-y-4">
        {error ? <Notice>{error}</Notice> : null}
        {notice ? <p className="text-sm text-good">{notice}</p> : null}
        <Card title="Connections">
          {connections.length === 0 ? <p className="text-sm text-muted">Loading connections.</p> : null}
          <ul className="space-y-3">
            {connections.map((item) => (
              <li key={item.key} className="flex flex-wrap items-start justify-between gap-3 rounded-2xl bg-elevated px-4 py-3">
                <div>
                  <div className="font-medium">{item.label}</div>
                  <p className="mt-1 text-sm text-muted">{item.note}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.configured ? "bg-good text-pine" : "bg-white/10 text-muted"}`}>
                  {item.configured ? "Configured" : "Not configured"}
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <MappingForm
          mappings={mappings}
          onDone={async (message) => {
            setNotice(message);
            await load();
          }}
          onError={setError}
        />
        <ServiceForm
          services={services}
          onDone={async (message) => {
            setNotice(message);
            await load();
          }}
          onError={setError}
        />
        {me?.auth_provider === "local" ? (
          <UserForm
            users={users}
            onDone={async (message) => {
              setNotice(message);
              await load();
            }}
            onError={setError}
          />
        ) : (
          <Card title="Accounts">
            <p className="text-sm text-muted">Accounts are managed in Active Directory. Map their groups above.</p>
          </Card>
        )}
        <Card title="Audit log">
          {audit.length === 0 ? <p className="text-sm text-muted">No audit events yet.</p> : null}
          <ul className="space-y-2">
            {audit.map((item) => (
              <li key={item.id} className="grid gap-1 rounded-2xl bg-elevated px-4 py-3 text-sm md:grid-cols-[180px_1fr]">
                <span className="text-muted">{formatTime(item.created_at)}</span>
                <span>
                  <span className="font-semibold">{item.actor}</span> {item.action.replaceAll("_", " ")}
                  {item.detail ? ` — ${item.detail}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </Shell>
  );
}

function MappingForm({
  mappings,
  onDone,
  onError,
}: {
  mappings: MappingOut[];
  onDone: (message: string) => Promise<void>;
  onError: (message: string) => void;
}) {
  const [group, setGroup] = useState("");
  const [role, setRole] = useState<Role>("system_admin");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api("/api/settings/mappings", { method: "POST", body: JSON.stringify({ ad_group: group, role }) });
      setGroup("");
      await onDone("Group mapping saved.");
    } catch (caught) {
      onError(caught instanceof ApiError ? caught.message : "Could not save the mapping.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Directory groups">
      <p className="mb-4 text-sm text-muted">The group named executives always has the Executive role. Map the other IT groups here.</p>
      <ul className="mb-4 space-y-2">
        <li className="flex items-center justify-between rounded-2xl bg-elevated px-4 py-3 text-sm">
          <span>executives</span>
          <span>{ROLE_LABELS.executive}</span>
        </li>
        {mappings.map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-3 rounded-2xl bg-elevated px-4 py-3 text-sm">
            <span>
              {item.ad_group} · {ROLE_LABELS[item.role]}
            </span>
            <button
              type="button"
              className="text-sm text-muted underline"
              onClick={() =>
                void api(`/api/settings/mappings/${item.id}`, { method: "DELETE" })
                  .then(() => onDone("Group mapping removed."))
                  .catch((caught) => onError(caught instanceof Error ? caught.message : "Could not remove the mapping."))
              }
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={submit} className="flex flex-wrap gap-2">
        <input
          aria-label="Active Directory group"
          value={group}
          onChange={(event) => setGroup(event.target.value)}
          placeholder="Group name"
          className="min-w-48 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none"
          required
        />
        <select aria-label="Role" value={role} onChange={(event) => setRole(event.target.value as Role)} className="rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm">
          {roleChoices(false).map((item) => (
            <option key={item} value={item}>
              {ROLE_LABELS[item]}
            </option>
          ))}
        </select>
        <PrimaryButton type="submit" disabled={busy}>
          Add group
        </PrimaryButton>
      </form>
    </Card>
  );
}

function ServiceForm({
  services,
  onDone,
  onError,
}: {
  services: ServiceOut[];
  onDone: (message: string) => Promise<void>;
  onError: (message: string) => void;
}) {
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api("/api/settings/services", { method: "POST", body: JSON.stringify({ name, external_key: key }) });
      setName("");
      setKey("");
      await onDone("Critical service saved. Status stays empty until a monitor is connected.");
    } catch (caught) {
      onError(caught instanceof ApiError ? caught.message : "Could not save the service.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Critical services">
      <p className="mb-4 text-sm text-muted">These names appear on the executive page. Health stays empty until a network monitor is connected.</p>
      <ul className="mb-4 space-y-2">
        {services.map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-3 rounded-2xl bg-elevated px-4 py-3 text-sm">
            <span>
              {item.name} · {item.external_key}
            </span>
            <button
              type="button"
              className="text-sm text-muted underline"
              onClick={() =>
                void api(`/api/settings/services/${item.id}`, { method: "DELETE" })
                  .then(() => onDone("Critical service removed."))
                  .catch((caught) => onError(caught instanceof Error ? caught.message : "Could not remove the service."))
              }
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={submit} className="flex flex-wrap gap-2">
        <input aria-label="Service name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Service name" className="min-w-40 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none" required />
        <input aria-label="External key" value={key} onChange={(event) => setKey(event.target.value)} placeholder="External key" className="min-w-40 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none" required />
        <PrimaryButton type="submit" disabled={busy}>
          Add service
        </PrimaryButton>
      </form>
    </Card>
  );
}

function UserForm({
  users,
  onDone,
  onError,
}: {
  users: UserOut[];
  onDone: (message: string) => Promise<void>;
  onError: (message: string) => void;
}) {
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [roles, setRoles] = useState<Role[]>(["helpdesk"]);
  const [busy, setBusy] = useState(false);

  function toggle(role: Role) {
    setRoles((current) => (current.includes(role) ? current.filter((item) => item !== role) : [...current, role]));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api("/api/settings/users", {
        method: "POST",
        body: JSON.stringify({ username, password, display_name: displayName, roles }),
      });
      setUsername("");
      setDisplayName("");
      setPassword("");
      setRoles(["helpdesk"]);
      await onDone("Account created.");
    } catch (caught) {
      onError(caught instanceof ApiError ? caught.message : "Could not create the account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Local accounts">
      <ul className="mb-4 space-y-2">
        {users.map((user) => (
          <li key={user.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-elevated px-4 py-3 text-sm">
            <span>
              <span className="font-semibold">{user.display_name}</span>
              <span className="text-muted"> · {user.username}</span>
              <span className="mt-1 block text-muted">{user.roles.map((role) => ROLE_LABELS[role]).join(", ")}{user.is_active ? "" : " · inactive"}</span>
            </span>
            {user.provider === "local" ? (
              <button
                type="button"
                className="text-sm text-muted underline"
                onClick={() =>
                  void api(`/api/settings/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !user.is_active }) })
                    .then(() => onDone(user.is_active ? "Account deactivated." : "Account activated."))
                    .catch((caught) => onError(caught instanceof Error ? caught.message : "Could not update the account."))
                }
              >
                {user.is_active ? "Deactivate" : "Activate"}
              </button>
            ) : null}
          </li>
        ))}
      </ul>
      <form onSubmit={submit} className="grid gap-3">
        <div className="flex flex-wrap gap-2">
          <input aria-label="Username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" className="min-w-40 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none" required />
          <input aria-label="Display name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Display name" className="min-w-40 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none" />
          <input aria-label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" className="min-w-40 flex-1 rounded-full border border-white/10 bg-elevated px-4 py-2 text-sm outline-none" required />
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          {roleChoices(true).map((role) => (
            <label key={role} className="inline-flex items-center gap-2">
              <input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} />
              {ROLE_LABELS[role]}
            </label>
          ))}
        </div>
        <div>
          <PrimaryButton type="submit" disabled={busy || roles.length === 0}>
            Create account
          </PrimaryButton>
        </div>
      </form>
    </Card>
  );
}
