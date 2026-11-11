from app.schemas import AssetStats, ExecutiveDashboard, ProblemStat, Section, ServiceHealth, TicketStats
from app.text import EMPTY_MESSAGE


def _stamp(section: Section) -> list[str]:
    if section.last_updated is None:
        return []
    return [f"Last updated: {section.last_updated.strftime('%Y-%m-%d %H:%M UTC')}"]


def _services(section: Section[list[ServiceHealth]]) -> list[str]:
    if section.status != "ok" or not section.data:
        return [EMPTY_MESSAGE if section.status != "error" else section.message or "Could not load this data."]
    lines = []
    for item in section.data:
        lines.append(f"{item.name}: {item.state}, {item.availability_30d:.1f}% over 30 days")
    return lines + _stamp(section)


def _tickets(section: Section[TicketStats]) -> list[str]:
    if section.status != "ok" or section.data is None:
        return [EMPTY_MESSAGE if section.status != "error" else section.message or "Could not load this data."]
    item = section.data
    lines = [
        f"Open now: {item.open_now}",
        f"Closed this month: {item.closed_this_month}",
        f"Closed last month: {item.closed_last_month}",
        f"Average resolution hours: {item.avg_resolution_hours:.1f}",
    ]
    if item.avg_resolution_hours_last_month is not None:
        lines.append(f"Average resolution hours last month: {item.avg_resolution_hours_last_month:.1f}")
    return lines + _stamp(section)


def _assets(section: Section[AssetStats]) -> list[str]:
    if section.status != "ok" or section.data is None:
        return [EMPTY_MESSAGE if section.status != "error" else section.message or "Could not load this data."]
    item = section.data
    lines = [
        f"Devices: {item.total_devices}",
        f"Servers: {item.total_servers}",
        f"Nearing end of warranty: {item.nearing_end_of_life}",
    ]
    return lines + _stamp(section)


def _problems(section: Section[list[ProblemStat]]) -> list[str]:
    if section.status != "ok" or not section.data:
        return [EMPTY_MESSAGE if section.status != "error" else section.message or "Could not load this data."]
    lines = [f"{item.label}: {item.count}" for item in section.data]
    return lines + _stamp(section)


def report_lines(board: ExecutiveDashboard) -> list[str]:
    generated = board.generated_at.strftime("%Y-%m-%d %H:%M UTC")
    lines = ["IT Hub", "Monthly report", f"Generated {generated}", "", "Service health"]
    lines.extend(_services(board.service_health))
    lines.extend(["", "Tickets"])
    lines.extend(_tickets(board.tickets))
    lines.extend(["", "Assets"])
    lines.extend(_assets(board.assets))
    lines.extend(["", "Most frequent problems"])
    lines.extend(_problems(board.top_problems))
    return lines


def render_pdf(lines: list[str]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=18)
    title = lines[0].encode("latin-1", "replace").decode("latin-1")
    pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for line in lines[1:]:
        safe = line.encode("latin-1", "replace").decode("latin-1")
        if not safe.strip():
            pdf.ln(4)
        else:
            pdf.multi_cell(0, 7, safe, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
