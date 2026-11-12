import { useEffect, useState } from "react";
import { ApiError, downloadReport } from "../api";
import { useAuth } from "../auth";
import { Card, EmptyState, KpiCard, LoadingBlock, Notice, PrimaryButton, SectionBody, Shell, StatusChip, formatTime } from "../components";
import { useI18n } from "../i18n";
import type { ExecutiveDashboard } from "../types";
import { api } from "../api";

function TicketCards({ section }: { section: ExecutiveDashboard["tickets"] | "loading" }) {
  const { t } = useI18n();

  function countTrend(current: number, previous: number, higherIsBetter: boolean) {
    if (current === previous) return { text: t("exec.trend.same"), tone: "muted" as const };
    const up = current > previous;
    const good = higherIsBetter ? up : !up;
    return { text: t(up ? "exec.trend.up" : "exec.trend.down"), tone: good ? ("good" as const) : ("bad" as const) };
  }

  if (section === "loading") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <KpiCard label={t("exec.open_now")} status="loading" />
        <KpiCard label={t("exec.closed_this_month")} status="loading" />
        <KpiCard label={t("exec.avg_resolution")} status="loading" />
        <KpiCard label={t("exec.closed_last_month")} status="loading" />
      </div>
    );
  }
  const data = section.data;
  const closed = data ? countTrend(data.closed_this_month, data.closed_last_month, true) : undefined;
  const speed =
    data && data.avg_resolution_hours_last_month !== null
      ? countTrend(data.avg_resolution_hours, data.avg_resolution_hours_last_month, false)
      : undefined;
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <KpiCard label={t("exec.open_now")} status={section.status} message={section.message} value={data ? String(data.open_now) : undefined} />
      <KpiCard
        label={t("exec.closed_this_month")}
        status={section.status}
        message={section.message}
        value={data ? String(data.closed_this_month) : undefined}
        hint={closed?.text}
        hintTone={closed?.tone}
      />
      <KpiCard
        label={t("exec.avg_resolution")}
        status={section.status}
        message={section.message}
        value={data ? `${data.avg_resolution_hours.toFixed(1)} h` : undefined}
        hint={speed?.text}
        hintTone={speed?.tone}
      />
      <KpiCard label={t("exec.closed_last_month")} status={section.status} message={section.message} value={data ? String(data.closed_last_month) : undefined} />
    </div>
  );
}

export function ExecutivePage() {
  const { me } = useAuth();
  const { t, lang } = useI18n();
  const [board, setBoard] = useState<ExecutiveDashboard | null>(null);
  const [error, setError] = useState("");
  const [exportError, setExportError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<ExecutiveDashboard>("/api/dashboard/executive")
      .then(setBoard)
      .catch((caught) => setError(caught instanceof Error ? caught.message : t("error.could_not_load")));
  }, [t]);

  async function exportPdf() {
    setBusy(true);
    setExportError("");
    try {
      await downloadReport();
    } catch (caught) {
      setExportError(caught instanceof ApiError ? caught.message : t("error.could_not_load"));
    } finally {
      setBusy(false);
    }
  }

  const allEmpty =
    board &&
    [board.service_health, board.tickets, board.assets, board.top_problems].every((section) => section.status === "not_configured");

  return (
    <Shell title={t("exec.title")}>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm leading-6 text-muted">
          {board ? `${t("time.checked")} ${formatTime(board.generated_at, lang)}.` : t("loading.checking")}{" "}
          {allEmpty ? t("exec.sources_unconnected") : null}
        </p>
        {me?.roles.includes("executive") || me?.roles.includes("it_manager") ? (
          <PrimaryButton disabled={busy} onClick={() => void exportPdf()}>
            {busy ? t("exec.preparing_report") : t("exec.monthly_report")}
          </PrimaryButton>
        ) : null}
      </div>
      {exportError ? (
        <div className="mb-4">
          <Notice>{exportError}</Notice>
        </div>
      ) : null}
      {error ? <Notice>{error}</Notice> : null}
      {!board && !error ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Card title={t("exec.service_health")}>
            <LoadingBlock />
          </Card>
          <Card title={t("exec.tickets")}>
            <TicketCards section="loading" />
          </Card>
        </div>
      ) : null}
      {board ? (
        <div className="grid gap-4 xl:grid-cols-2">
          <Card title={t("exec.service_health")} lastUpdated={board.service_health.last_updated}>
            <SectionBody status={board.service_health.status} message={board.service_health.message}>
              {board.service_health.data && board.service_health.data.length > 0 ? (
                <ul className="space-y-5">
                  {board.service_health.data.map((service) => (
                    <li key={service.name}>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <span className="font-medium">{service.name}</span>
                        <StatusChip status={service.state} />
                      </div>
                      <div className="mb-2 text-sm text-muted">{service.availability_30d.toFixed(1)}% {t("exec.availability_30d")}</div>
                      <div className="h-1.5 rounded-full bg-white/10">
                        <div
                          className={`h-1.5 rounded-full ${service.state === "up" ? "bg-good" : service.state === "degraded" ? "bg-warn" : "bg-bad"}`}
                          style={{ width: `${Math.max(0, Math.min(100, service.availability_30d))}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState message={t("empty.none_reported")} />
              )}
            </SectionBody>
          </Card>
          <Card title={t("exec.tickets")} lastUpdated={board.tickets.last_updated}>
            <TicketCards section={board.tickets} />
          </Card>
          <Card title={t("exec.assets")} lastUpdated={board.assets.last_updated}>
            <div className="grid gap-3 sm:grid-cols-3">
              <KpiCard
                label={t("exec.devices")}
                status={board.assets.status}
                message={board.assets.message}
                value={board.assets.data ? String(board.assets.data.total_devices) : undefined}
              />
              <KpiCard
                label={t("exec.servers")}
                status={board.assets.status}
                message={board.assets.message}
                value={board.assets.data ? String(board.assets.data.total_servers) : undefined}
              />
              <KpiCard
                label={t("exec.warranty_end")}
                status={board.assets.status}
                message={board.assets.message}
                value={board.assets.data ? String(board.assets.data.nearing_end_of_life) : undefined}
              />
            </div>
          </Card>
          <Card title={t("exec.top_problems")} lastUpdated={board.top_problems.last_updated}>
            <SectionBody status={board.top_problems.status} message={board.top_problems.message}>
              {board.top_problems.data && board.top_problems.data.length > 0 ? (
                <ul className="space-y-4">
                  {board.top_problems.data.map((item) => {
                    const max = Math.max(...board.top_problems.data!.map((problem) => problem.count), 1);
                    return (
                      <li key={item.label}>
                        <div className="mb-2 flex justify-between gap-3 text-sm">
                          <span>{item.label}</span>
                          <span className="font-semibold">{item.count}</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-white/10">
                          <div className="h-1.5 rounded-full bg-lime" style={{ width: `${(item.count / max) * 100}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <EmptyState message={t("empty.none_reported")} />
              )}
            </SectionBody>
          </Card>
        </div>
      ) : null}
    </Shell>
  );
}
