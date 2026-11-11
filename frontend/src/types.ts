export type Role = "it_manager" | "system_admin" | "network_admin" | "helpdesk" | "executive";

export type Me = {
  username: string;
  display_name: string;
  roles: Role[];
  auth_provider: string;
};

export type Section<T> = {
  status: "ok" | "not_configured" | "error";
  message: string | null;
  last_updated: string | null;
  data: T | null;
};

export type ServiceHealth = {
  name: string;
  state: "up" | "degraded" | "down";
  availability_30d: number;
};

export type TicketStats = {
  open_now: number;
  closed_this_month: number;
  closed_last_month: number;
  avg_resolution_hours: number;
  avg_resolution_hours_last_month: number | null;
};

export type AssetStats = {
  total_devices: number;
  total_servers: number;
  nearing_end_of_life: number;
};

export type ProblemStat = {
  label: string;
  count: number;
};

export type DeviceRecord = {
  id: string;
  name: string;
  kind: "server" | "network" | "endpoint";
  status: "up" | "degraded" | "down" | "unknown";
  ip: string | null;
  hostname: string | null;
};

export type ExecutiveDashboard = {
  generated_at: string;
  service_health: Section<ServiceHealth[]>;
  tickets: Section<TicketStats>;
  assets: Section<AssetStats>;
  top_problems: Section<ProblemStat[]>;
};

export type TechnicalDashboard = {
  generated_at: string;
  tickets: Section<TicketStats>;
  problems: Section<ProblemStat[]>;
  devices: Section<DeviceRecord[]>;
  links: { ticketing: string | null; assets: string | null };
};

export type UserOut = {
  id: number;
  username: string;
  display_name: string;
  provider: string;
  is_active: boolean;
  roles: Role[];
};

export type MappingOut = { id: number; ad_group: string; role: Role };
export type ServiceOut = { id: number; name: string; external_key: string; sort_order: number };
export type AuditOut = { id: number; created_at: string; actor: string; action: string; detail: string; ip: string | null };
export type ConnectionOut = { key: string; label: string; configured: boolean; note: string };

export const ROLE_LABELS: Record<Role, string> = {
  it_manager: "IT Manager",
  system_admin: "System Admin",
  network_admin: "Network Admin",
  helpdesk: "Helpdesk",
  executive: "Executive",
};

export const EMPTY_MESSAGE = "No data connected yet";
