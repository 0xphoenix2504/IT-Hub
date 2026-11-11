import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Card, DataList, EmptyState, ErrorState, FilterRow, KpiCard, LoadingBlock, Notice, PillTabs, SectionBody, Shell, StatusChip } from "../components";
import type { DeviceRecord, TechnicalDashboard } from "../types";

const KIND_LABEL = { server: "Server", network: "Network device", endpoint: "End-user device" };

function countTrend(current: number, previous: number, higherIsBetter: boolean) {
  if (current === previous) return { text: "Same as last month", tone: "muted" as const };
  const up = current > previous;
  const good = higherIsBetter ? up : !up;
  return { text: `${up ? "Up" : "Down"} from last month`, tone: good ? ("good" as const) : ("bad" as const) };
}

export function TechnicalPage({
  title,
  path,
  noun,
}: {
  title: string;
  path: "servers" | "network" | "helpdesk";
  noun: string;
}) {
  const [board, setBoard] = useState<TechnicalDashboard | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"devices" | "issues">("devices");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("any");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    setBoard(null);
    setError("");
    setSelectedId(null);
    api<TechnicalDashboard>(`/api/dashboard/${path}`)
      .then(setBoard)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load this data."));
  }, [path]);

  const devices = board?.devices.data ?? [];
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return devices.filter((device) => {
      const matchesStatus = status === "any" || device.status === status;
      const haystack = [device.name, device.hostname, device.ip].filter(Boolean).join(" ").toLowerCase();
      return matchesStatus && (!needle || haystack.includes(needle));
    });
  }, [devices, query, status]);

  useEffect(() => {
    if (selectedId && !filtered.some((device) => device.id === selectedId)) setSelectedId(null);
  }, [filtered, selectedId]);

  const selected = filtered.find((device) => device.id === selectedId) ?? null;
  const tickets = board?.tickets.data;

  return (
    <Shell title={title}>
      {error ? <Notice>{error}</Notice> : null}
      {!board && !error ? <LoadingBlock /> : null}
      {board ? (
        <>
          <div className="mb-4">
            <PillTabs
              active={tab}
              onChange={setTab}
              tabs={[
                { id: "devices", label: noun, count: board.devices.status === "ok" ? devices.length : undefined },
                { id: "issues", label: "Issues", count: board.tickets.status === "ok" ? board.tickets.data?.open_now : undefined },
              ]}
            />
          </div>
          {tab === "issues" ? (
            <div className="grid gap-4 xl:grid-cols-2">
              <Card title="Ticket stats" lastUpdated={board.tickets.last_updated}>
                <div className="grid gap-3 sm:grid-cols-2">
                  <KpiCard label="Open now" status={board.tickets.status} message={board.tickets.message} value={tickets ? String(tickets.open_now) : undefined} />
                  <KpiCard
                    label="Closed this month"
                    status={board.tickets.status}
                    message={board.tickets.message}
                    value={tickets ? String(tickets.closed_this_month) : undefined}
                    hint={tickets ? countTrend(tickets.closed_this_month, tickets.closed_last_month, true).text : undefined}
                    hintTone={tickets ? countTrend(tickets.closed_this_month, tickets.closed_last_month, true).tone : undefined}
                  />
                  <KpiCard
                    label="Average resolution"
                    status={board.tickets.status}
                    message={board.tickets.message}
                    value={tickets ? `${tickets.avg_resolution_hours.toFixed(1)} h` : undefined}
                    hint={
                      tickets && tickets.avg_resolution_hours_last_month !== null
                        ? countTrend(tickets.avg_resolution_hours, tickets.avg_resolution_hours_last_month, false).text
                        : undefined
                    }
                    hintTone={
                      tickets && tickets.avg_resolution_hours_last_month !== null
                        ? countTrend(tickets.avg_resolution_hours, tickets.avg_resolution_hours_last_month, false).tone
                        : undefined
                    }
                  />
                  <KpiCard label="Closed last month" status={board.tickets.status} message={board.tickets.message} value={tickets ? String(tickets.closed_last_month) : undefined} />
                </div>
              </Card>
              <Card title="Most frequent problems" lastUpdated={board.problems.last_updated}>
                <SectionBody status={board.problems.status} message={board.problems.message}>
                  {board.problems.data && board.problems.data.length > 0 ? (
                    <ul className="space-y-3">
                      {board.problems.data.map((item) => (
                        <li key={item.label} className="flex items-center justify-between gap-3 text-sm">
                          <span>{item.label}</span>
                          <span className="font-semibold">{item.count}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <EmptyState message="None reported." />
                  )}
                </SectionBody>
              </Card>
            </div>
          ) : (
            <>
              <FilterRow query={query} status={status} onQuery={setQuery} onStatus={setStatus} />
              <section className="rounded-[28px] bg-panel p-3 text-pine md:p-4">
                {board.devices.status === "error" ? (
                  <div className="p-4">
                    <ErrorState message={board.devices.message} />
                  </div>
                ) : board.devices.status !== "ok" ? (
                  <div className="p-4">
                    <EmptyState message={board.devices.message} />
                  </div>
                ) : filtered.length === 0 ? (
                  <div className="p-4">
                    <EmptyState message={devices.length === 0 ? "None reported." : "No devices match these filters."} />
                  </div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-[320px_1fr]">
                    <DataList
                      rows={filtered.map((device) => ({
                        id: device.id,
                        title: device.name,
                        meta: [device.hostname, device.ip].filter(Boolean).join(" · ") || KIND_LABEL[device.kind],
                        status: device.status,
                      }))}
                      selectedId={selectedId}
                      onSelect={setSelectedId}
                    />
                    <DeviceDetail device={selected} links={board.links} />
                  </div>
                )}
              </section>
            </>
          )}
        </>
      ) : null}
    </Shell>
  );
}

function DeviceDetail({ device, links }: { device: DeviceRecord | null; links: TechnicalDashboard["links"] }) {
  if (!device) {
    return <div className="rounded-[22px] bg-white p-6 text-sm text-pine/70">Select a device.</div>;
  }
  return (
    <div className="rounded-[22px] bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">{device.name}</h2>
          <p className="mt-1 text-sm text-pine/70">{KIND_LABEL[device.kind]}</p>
        </div>
        <StatusChip status={device.status} />
      </div>
      <dl className="mt-6 space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-pine/70">Hostname</dt>
          <dd className="font-medium">{device.hostname || "Not provided"}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-pine/70">IP address</dt>
          <dd className="font-medium">{device.ip || "Not provided"}</dd>
        </div>
      </dl>
      <div className="mt-6 flex flex-wrap gap-2">
        {links.ticketing ? (
          <a className="rounded-full bg-lime px-4 py-2 text-sm font-semibold text-ink" href={links.ticketing} target="_blank" rel="noreferrer">
            Open in ticketing system
          </a>
        ) : null}
        {links.assets ? (
          <a className="rounded-full border border-pine/15 px-4 py-2 text-sm font-semibold" href={links.assets} target="_blank" rel="noreferrer">
            Open in assets
          </a>
        ) : null}
        {!links.ticketing && !links.assets ? <p className="text-sm text-pine/70">No deep link is configured.</p> : null}
      </div>
    </div>
  );
}
