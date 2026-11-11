import type { Me } from "./types";

const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function detail(body: unknown, fallback: string) {
  if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
    return body.detail;
  }
  return fallback;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { ...init, headers, credentials: "include" });
  } catch {
    throw new ApiError(0, "Could not reach the hub.");
  }
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, detail(body, "Could not complete that request."));
  return body as T;
}

export async function downloadReport() {
  let response: Response;
  try {
    response = await fetch(`${base}/api/reports/executive.pdf`, { credentials: "include" });
  } catch {
    throw new ApiError(0, "Could not reach the hub.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, detail(body, "Could not export the report."));
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "it-hub-monthly-report.pdf";
  link.click();
  URL.revokeObjectURL(url);
}

export function homeFor(roles: Me["roles"]) {
  return navFor(roles)[0]?.to ?? "/login";
}

export function navFor(roles: Me["roles"]) {
  const manager = roles.includes("it_manager");
  const items: { to: string; label: string }[] = [];
  if (manager || roles.includes("executive")) items.push({ to: "/", label: "Overview" });
  if (manager || roles.includes("system_admin")) items.push({ to: "/servers", label: "Servers" });
  if (manager || roles.includes("network_admin")) items.push({ to: "/network", label: "Network" });
  if (manager || roles.includes("helpdesk")) items.push({ to: "/helpdesk", label: "Helpdesk" });
  if (manager) items.push({ to: "/settings", label: "Settings" });
  return items;
}
