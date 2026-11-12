import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Card, DataList, EmptyState, ErrorState, FilterRow, KpiCard, LoadingBlock, Notice, PillTabs, SectionBody, Shell, StatusChip } from "../components";
import { useI18n } from "../i18n";
import type { DeviceRecord, TechnicalDashboard } from "../types";

export function TechnicalPage({
  title,
  path,
  noun,
}: {
  title: string;
  path: "servers" | "network" | "helpdesk";
  noun: string;
}) {
  const { t } = useI18n();
  const [board, setBoard] = useState<TechnicalDashboard | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"devices" | "issues">("devices");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("any");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const kindLabels: Record<string, string> = {
    server: t("tech.servers_noun"),
    network: t("tech.network_noun"),
    endpoint: t("tech.helpdesk_noun"),
  };

  const pageNoun =
    path === "servers"
      ? t("tech.servers_noun")
      : path === "network"
      ? t("tech.network_noun")
      : path === "helpdesk"
      ? t("tech.helpdesk_noun")
      : noun;

  const pageTitle =
    path === "servers"
      ? t("nav.servers")
      : path === "network"
      ? t("nav.network")
      : path === "helpdesk"
      ? t("nav.helpdesk")
      : title;

  function countTrend(current: number, previous: number, higherIsBetter: boolean) {
    if (current === previous) return { text: t("exec.trend.same"), tone: "muted" as const };
    const up = current > previous;
    const good = higherIsBetter ? up : !up;
    return { text: t(up ? "exec.trend.up" : "exec.trend.down"), tone: good ? ("good" as const) : ("bad" as const) };
  }

  useEffect(() => {
    setBoard(null);
    setError("");
    setSelectedId(null);
    api<TechnicalDashboard>(`/api/dashboard/${path}`)
      .then(setBoard)
      .catch((caught) => setError(caught instanceof Error ? caught.message : t("error.could_not_load")));
  }, [path, t]);

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
    <Shell title={pageTitle}>
      {error ? <Notice>{error}</Notice> : null}
      {!board && !error ? <LoadingBlock /> : null}
      {board ? (
        <>
          <div className="mb-4">
            <PillTabs
              active={tab}
              onChange={setTab}
              tabs={[
                { id: "devices", label: pageNoun, count: board.devices.status === "ok" ? devices.length : undefined },
                { id: "issues", label: t("tech.issues"), count: board.tickets.status === "ok" ? board.tickets.data?.open_now : undefined },
              ]}
            />
          </div>
          {tab === "issues" ? (
            <div className="grid gap-4 xl:grid-cols-2">
              <Card title={t("exec.tickets")} lastUpdated={board.tickets.last_updated}>
                <div className="grid gap-3 sm:grid-cols-2">
                  <KpiCard label={t("exec.open_now")} status={board.tickets.status} message={board.tickets.message} value={tickets ? String(tickets.open_now) : undefined} />
                  <KpiCard
                    label={t("exec.closed_this_month")}
                    status={board.tickets.status}
                    message={board.tickets.message}
                    value={tickets ? String(tickets.closed_this_month) : undefined}
                    hint={tickets ? countTrend(tickets.closed_this_month, tickets.closed_last_month, true).text : undefined}
                    hintTone={tickets ? countTrend(tickets.closed_this_month, tickets.closed_last_month, true).tone : undefined}
                  />
                  <KpiCard
                    label={t("exec.avg_resolution")}
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
                  <KpiCard label={t("exec.closed_last_month")} status={board.tickets.status} message={board.tickets.message} value={tickets ? String(tickets.closed_last_month) : undefined} />
                </div>
              </Card>
              <Card title={t("exec.top_problems")} lastUpdated={board.problems.last_updated}>
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
                    <EmptyState message={t("empty.none_reported")} />
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
                    <EmptyState message={devices.length === 0 ? t("empty.none_reported") : t("empty.no_devices_match")} />
                  </div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-[320px_1fr]">
                    <DataList
                      rows={filtered.map((device) => ({
                        id: device.id,
                        title: device.name,
                        meta: [device.hostname, device.ip].filter(Boolean).join(" · ") || kindLabels[device.kind],
                        status: device.status,
                      }))}
                      selectedId={selectedId}
                      onSelect={setSelectedId}
                    />
                    <DeviceDetail device={selected} links={board.links} kindLabels={kindLabels} />
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

function DeviceDetail({
  device,
  links,
  kindLabels,
}: {
  device: DeviceRecord | null;
  links: TechnicalDashboard["links"];
  kindLabels: Record<string, string>;
}) {
  const { t } = useI18n();
  if (!device) {
    return <div className="rounded-[22px] bg-white p-6 text-sm text-pine/70">{t("empty.select_device")}</div>;
  }
  return (
    <div className="rounded-[22px] bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">{device.name}</h2>
          <p className="mt-1 text-sm text-pine/70">{kindLabels[device.kind] || device.kind}</p>
        </div>
        <StatusChip status={device.status} />
      </div>
      <dl className="mt-6 space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-pine/70">{t("tech.hostname")}</dt>
          <dd className="font-medium">{device.hostname || t("tech.not_provided")}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-pine/70">{t("tech.ip_address")}</dt>
          <dd className="font-medium">{device.ip || t("tech.not_provided")}</dd>
        </div>
      </dl>
      <div className="mt-6 flex flex-wrap gap-2">
        {links.ticketing ? (
          <a className="rounded-full bg-lime px-4 py-2 text-sm font-semibold text-ink" href={links.ticketing} target="_blank" rel="noreferrer">
            {t("tech.open_ticketing")}
          </a>
        ) : null}
        {links.assets ? (
          <a className="rounded-full border border-pine/15 px-4 py-2 text-sm font-semibold" href={links.assets} target="_blank" rel="noreferrer">
            {t("tech.open_assets")}
          </a>
        ) : null}
        {!links.ticketing && !links.assets ? <p className="text-sm text-pine/70">{t("tech.no_deep_link")}</p> : null}
      </div>
    </div>
  );
}
