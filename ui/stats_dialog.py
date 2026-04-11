"""Statistics Dashboard Dialog for Desktop Icon Backup Manager."""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QWidget,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPainter, QColor, QFont

from core.config import Config
from core.stats import compute_all, format_bytes

# ── Tiny bar-chart widget ─────────────────────────────────────────────────────


class _BarChart(QWidget):
    """Minimal vertical bar chart drawn with QPainter."""

    _BAR_COLOR = QColor("#378ADD")
    _BAR_COLOR_LIGHT = QColor("#5BA0D9")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, int]] = []
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, int]]):
        self._data = data
        self.update()

    def paintEvent(self, _):
        if not self._data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        label_h = 18
        chart_h = H - label_h - 4
        max_val = max(v for _, v in self._data) or 1
        n = len(self._data)
        gap = 6
        bar_w = max(8, (W - gap * (n + 1)) // n)

        pal = self.palette()
        text_color = pal.color(pal.ColorRole.Text)

        for i, (label, val) in enumerate(self._data):
            x = gap + i * (bar_w + gap)
            bar_h = max(4, int((val / max_val) * chart_h))
            y = chart_h - bar_h

            is_max = val == max_val
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._BAR_COLOR if is_max else self._BAR_COLOR_LIGHT)
            p.drawRoundedRect(x, y, bar_w, bar_h, 3, 3)

            # Value on top of bar
            p.setPen(text_color)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(x, y - 2, bar_w, 14, Qt.AlignmentFlag.AlignHCenter, str(val))

            # Label below
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(
                x - 4,
                chart_h + 2,
                bar_w + 8,
                label_h,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                label,
            )
        p.end()


# ── Progress-bar-style row ────────────────────────────────────────────────────


def _make_progress_row(label: str, pct: float, color: QColor, parent=None) -> QWidget:
    """A single horizontal progress row: label — bar — percentage."""
    row = QWidget(parent)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    lbl = QLabel(label)
    lbl.setFixedWidth(90)
    lbl.setStyleSheet("font-size: 12px;")
    lay.addWidget(lbl)

    bar_bg = QFrame()
    bar_bg.setFixedHeight(6)
    bar_bg.setStyleSheet("background: palette(mid); border-radius: 3px;")
    bar_bg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    bar_fill = QFrame(bar_bg)
    bar_fill.setFixedHeight(6)
    bar_fill.setStyleSheet(f"background: {color.name()}; border-radius: 3px;")
    fill_w = max(2, int(pct))
    bar_fill.setFixedWidth(fill_w)
    lay.addWidget(bar_bg, stretch=1)

    pct_lbl = QLabel(f"{pct:.0f}%")
    pct_lbl.setFixedWidth(36)
    pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    pct_lbl.setStyleSheet("font-size: 12px; color: palette(placeholderText);")
    lay.addWidget(pct_lbl)

    return row


# ── Stat card ─────────────────────────────────────────────────────────────────


def _make_stat_card(
    title: str, value: str, accent: str = "#378ADD", parent=None
) -> QFrame:
    card = QFrame(parent)
    card.setStyleSheet(
        f"QFrame {{ background: palette(button); border: 1px solid palette(mid);"
        f" border-left: 3px solid {accent};"
        f" border-radius: 8px; padding: 10px; }}"
    )
    lay = QVBoxLayout(card)
    lay.setContentsMargins(12, 10, 12, 10)
    lay.setSpacing(2)

    t = QLabel(title)
    t.setAlignment(Qt.AlignmentFlag.AlignCenter)
    t.setStyleSheet(
        "font-size: 11px; color: palette(placeholderText);"
        " background: transparent; border: none;"
    )
    lay.addWidget(t)

    v = QLabel(value)
    v.setAlignment(Qt.AlignmentFlag.AlignCenter)
    v.setStyleSheet(
        f"font-size: 22px; font-weight: bold; color: {accent};"
        f" background: transparent; border: none;"
    )
    lay.addWidget(v)

    return card


# ── Ranked list item ──────────────────────────────────────────────────────────


def _section_title(text: str, color: str = "#378ADD") -> QLabel:
    """Section title with a small colored dot prefix."""
    lbl = QLabel(f"<span style='color:{color};'>●</span>&nbsp; {text}")
    lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: palette(text);")
    return lbl


_RANK_COLORS = [
    ("#E8A817", "#FFF3D0"),  # 1st — gold
    ("#7B8894", "#E8ECF0"),  # 2nd — silver
    ("#B5713F", "#F5E6D8"),  # 3rd — bronze
]


def _make_ranked_item(rank: int, name: str, detail: str, parent=None) -> QWidget:
    row = QWidget(parent)
    row.setFixedHeight(28)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 2, 0, 2)
    lay.setSpacing(8)

    if rank <= len(_RANK_COLORS):
        fg, bg = _RANK_COLORS[rank - 1]
    else:
        fg, bg = "palette(text)", "palette(button)"

    badge = QLabel(str(rank))
    badge.setFixedSize(22, 22)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setStyleSheet(
        f"font-size: 11px; font-weight: bold; border-radius: 11px;"
        f" background: {bg}; color: {fg};"
    )
    lay.addWidget(badge)

    n = QLabel(name)
    n.setStyleSheet("font-size: 13px; color: palette(text);")
    lay.addWidget(n, stretch=1)

    d = QLabel(detail)
    d.setStyleSheet("font-size: 12px; color: palette(placeholderText);")
    lay.addWidget(d)

    return row


# ── Main Dialog ───────────────────────────────────────────────────────────────


class StatsDialog(QDialog):
    """Statistics Dashboard — shows aggregated backup data."""

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Statistics Dashboard"))
        self.setMinimumSize(700, 560)
        self.resize(740, 600)

        self._settings = settings

        # ── Compute stats ─────────────────────────────────────────────────
        data = compute_all(Config.BACKUP_DIR)

        total_restores = settings.value("stats/total_restores_performed", 0, type=int)
        total_scrambles = settings.value("stats/total_scrambles", 0, type=int)
        total_saves = settings.value("stats/total_saves_performed", 0, type=int)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(18, 18, 18, 18)

        # ── Top stat cards ────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        cards_row.addWidget(
            _make_stat_card(
                self.tr("Total backups"), str(data["file_count"]), accent="#00A65A"
            )
        )
        cards_row.addWidget(
            _make_stat_card(self.tr("Restores"), str(total_restores), accent="#0078D7")
        )
        cards_row.addWidget(
            _make_stat_card(self.tr("Saves"), str(total_saves), accent="#00C853")
        )
        cards_row.addWidget(
            _make_stat_card(
                self.tr("Disk usage"),
                format_bytes(data["total_bytes"]),
                accent="#E8A817",
            )
        )
        cards_row.addWidget(
            _make_stat_card(
                self.tr("Avg icons"), str(data["avg_icons"]), accent="#9C27B0"
            )
        )
        root.addLayout(cards_row)

        # ── Middle row: bar chart + resolutions ───────────────────────────
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        # Bar chart
        chart_box = QVBoxLayout()
        chart_box.addWidget(_section_title(self.tr("Backups per month"), "#378ADD"))

        self._chart = _BarChart()
        chart_data = []
        for month_key, count in data["backups_per_month"]:
            try:
                from datetime import datetime as _dt

                label = _dt.strptime(month_key, "%Y-%m").strftime("%b")
            except ValueError:
                label = month_key
            chart_data.append((label, count))
        self._chart.set_data(chart_data)
        chart_box.addWidget(self._chart, stretch=1)
        mid_row.addLayout(chart_box, stretch=2)

        # Resolutions
        res_box = QVBoxLayout()
        res_box.addWidget(_section_title(self.tr("Top resolutions"), "#5BA0D9"))

        total_res = sum(c for _, c in data["top_resolutions"]) or 1
        colors = [QColor("#378ADD"), QColor("#5BA0D9"), QColor("#85B7EB")]
        for i, (res_str, count) in enumerate(data["top_resolutions"][:3]):
            pct = (count / total_res) * 100
            color = colors[min(i, len(colors) - 1)]
            res_box.addWidget(_make_progress_row(res_str, pct, color))

        res_box.addStretch(1)
        mid_row.addLayout(res_box, stretch=1)

        root.addLayout(mid_row, stretch=1)

        # ── Bottom row: most moved + activity ─────────────────────────────
        bot_row = QHBoxLayout()
        bot_row.setSpacing(14)

        # Most moved icons
        moved_box = QVBoxLayout()
        moved_box.addWidget(_section_title(self.tr("Most moved icons"), "#E8A817"))

        if data["most_moved_icons"]:
            for rank, (name, times) in enumerate(data["most_moved_icons"], 1):
                detail = self.tr("moved %1×").replace("%1", str(times))
                moved_box.addWidget(_make_ranked_item(rank, name, detail))
        else:
            empty_lbl = QLabel(self.tr("Not enough data (need 2+ backups)"))
            empty_lbl.setStyleSheet("font-size: 12px; color: palette(placeholderText);")
            moved_box.addWidget(empty_lbl)

        moved_box.addStretch(1)
        bot_row.addLayout(moved_box, stretch=1)

        # Activity summary
        act_box = QVBoxLayout()
        act_box.addWidget(_section_title(self.tr("Activity"), "#00A65A"))

        activity_items = [
            (self.tr("First backup"), data["first_date"]),
            (self.tr("Last backup"), data["last_date"]),
            (self.tr("Saves"), str(total_saves)),
            (self.tr("Scrambles"), str(total_scrambles)),
        ]

        if data["top_tags"]:
            top_tag = data["top_tags"][0][0]
            activity_items.append((self.tr("Most used tag"), top_tag))

        for label, value in activity_items:
            r = QHBoxLayout()
            r.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 13px; color: palette(placeholderText);")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            val = QLabel(value)
            val.setStyleSheet("font-size: 13px; color: palette(text);")
            val.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            r.addWidget(lbl)
            r.addStretch(1)
            r.addWidget(val)

            container = QWidget()
            container.setFixedHeight(28)
            container.setLayout(r)
            act_box.addWidget(container)

        act_box.addStretch(1)
        bot_row.addLayout(act_box, stretch=1)

        root.addLayout(bot_row, stretch=1)

        # ── Close button ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton(self.tr("Close"))
        btn_close.setMinimumHeight(34)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)
