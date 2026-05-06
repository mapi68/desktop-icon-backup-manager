"""Icon Preview Widget and Diff Preview Widget"""

import math
from typing import Dict, Tuple

from PyQt6.QtWidgets import (
    QWidget,
    QToolTip,
    QSizePolicy,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize, QCoreApplication


# Alias for marking strings extractable by lupdate without translating at import time.
def QT_TR_NOOP(s: str) -> str:  # noqa: N802
    return s


from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QFont,
    QPolygonF,
)

from core.config import Config

# ── Palette ───────────────────────────────────────────────────────────────────
_C_BLUE = QColor("#0078D7")
_C_ORANGE = QColor("#FF9800")
_C_RED = QColor("#F44336")
_C_GREEN = QColor("#4CAF50")

_DOT_R = 5
_DOT_D = _DOT_R * 2
_ARR_H = 7
_MARGIN = 10


# ── _ColorDot ─────────────────────────────────────────────────────────────────
class _ColorDot(QWidget):
    """
    Fixed 16×16 widget, draws an antialiased filled circle centred exactly.
    Used in the legend so every icon occupies the same column width.
    """

    _S = 16  # widget size
    _R = 6  # circle radius

    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(self._S, self._S)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        c = self._S // 2
        p.drawEllipse(c - self._R, c - self._R, self._R * 2, self._R * 2)


# ── _ArrowIcon ────────────────────────────────────────────────────────────────
class _ArrowIcon(QWidget):
    """
    Compact orange-dot ──▶ red-dot icon, 64 px wide x 16 px tall.
    Fits entirely in column 0 of the legend grid alongside _ColorDot.
    """

    _W = 64  # total widget width
    _H = 16  # height
    _R = 6  # dot radius (matches _ColorDot._R)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._W, self._H)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        cy = self._H // 2
        r = self._R

        # Orange dot — left
        ox = r + 2
        p.setBrush(_C_ORANGE)
        p.drawEllipse(ox - r, cy - r, r * 2, r * 2)

        # Red dot — right
        rx = self._W - r - 2
        p.setBrush(_C_RED)
        p.drawEllipse(rx - r, cy - r, r * 2, r * 2)

        # Dashed line between dots
        x0 = ox + r + 3
        x1 = rx - r - 7  # stop before arrowhead
        pen = QPen(_C_RED, 1, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 3])
        p.setPen(pen)
        p.drawLine(x0, cy, x1, cy)

        # Arrowhead just before red dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_C_RED)
        tip = rx - r - 1
        p.drawPolygon(
            QPolygonF(
                [
                    QPointF(tip, cy),
                    QPointF(tip - 6, cy - 3.5),
                    QPointF(tip - 6, cy + 3.5),
                ]
            )
        )


# ── Canvas helpers ────────────────────────────────────────────────────────────
def _draw_arrowhead(
    p: QPainter, x1: float, y1: float, x2: float, y2: float, color: QColor
) -> None:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 6:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    bx = x2 - ux * _ARR_H * 1.8
    by = y2 - uy * _ARR_H * 1.8
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawPolygon(
        QPolygonF(
            [
                QPointF(x2, y2),
                QPointF(bx + px * _ARR_H, by + py * _ARR_H),
                QPointF(bx - px * _ARR_H, by - py * _ARR_H),
            ]
        )
    )


# ── Windows 11 taskbar mock-up ────────────────────────────────────────────────
def _draw_win11_taskbar(
    p: QPainter,
    ox: int,
    oy: int,
    sw: int,
    sh: int,
    res_h: int,
    palette,
    clock_time: str = "12:34",
    clock_date: str = "17/04/2026",
) -> int:
    """
    Paint a stylised Windows 11 taskbar along the bottom edge of the virtual
    screen rectangle (ox, oy, sw, sh). Returns the taskbar's top-y in widget
    coordinates (so callers know where the usable desktop ends).

    The taskbar is 48 real screen-pixels tall on Windows 11 at 100% DPI;
    the height scales proportionally with the virtual-screen's sh/res_h.
    Icons inside are drawn schematically — enough to be recognisable at
    preview sizes without pretending to be pixel-accurate.

    clock_time / clock_date: two-line clock display on the right side of the
    system tray. Callers pass the backup's own timestamp so the taskbar
    reflects the moment the snapshot was taken.
    """
    TASKBAR_PX = 48  # Win11 default taskbar height in physical pixels
    res_h = res_h if res_h > 0 else 1080
    # Proportional height, but enforce a readable minimum so the Start
    # button, tray icons, and clock are actually visible at small preview
    # sizes. Purely proportional scaling gives ~9px on a typical 800×220
    # preview, which is too cramped to see anything.
    proportional = int(sh * TASKBAR_PX / res_h) * 2
    bar_h = max(44, proportional)
    # Cap at ~20% of the screen height so we never swallow the desktop area
    bar_h = min(bar_h, max(44, sh // 5))
    bar_y = oy + sh - bar_h

    # Theme-adaptive fill: use Window colour blended toward Shadow for depth
    win = palette.color(palette.ColorRole.Window)
    shadow = palette.color(palette.ColorRole.Shadow)
    # 65% Window + 35% Shadow — gives a denser bar in both light and dark themes
    mix = QColor(
        int(win.red() * 0.65 + shadow.red() * 0.35),
        int(win.green() * 0.65 + shadow.green() * 0.35),
        int(win.blue() * 0.65 + shadow.blue() * 0.35),
    )
    # Detect dark theme from Window luminance
    lum = 0.299 * win.red() + 0.587 * win.green() + 0.114 * win.blue()
    dark_theme = lum < 128

    # Fill + subtle top separator
    p.fillRect(ox, bar_y, sw, bar_h, mix)
    p.setPen(QPen(shadow, 1))
    p.drawLine(ox, bar_y, ox + sw, bar_y)

    # Only decorate if there's enough room
    if bar_h < 10:
        return bar_y, bar_h

    icon_color = QColor("#E6E6E6") if dark_theme else QColor("#2B2B2B")
    accent = QColor("#0078D4")  # Windows accent blue

    # Icon metrics
    ic_size = int(bar_h * 0.55)
    ic_size = max(6, ic_size)
    gap = max(4, int(bar_h * 0.30))
    cy = bar_y + bar_h // 2

    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # ── Centered cluster: Start, Search, Task view ──────────────────────────
    n_icons = 3
    cluster_w = n_icons * ic_size + (n_icons - 1) * gap
    cx_start = ox + (sw - cluster_w) // 2
    slot_step = ic_size + gap

    def _slot(i: int) -> tuple[int, int]:
        return cx_start + i * slot_step, cy

    # 0: Start button — 4-square logo
    sx, sy = _slot(0)
    quarter = max(2, (ic_size - 3) // 2)
    q_gap = max(1, ic_size // 10)
    top = sy - ic_size // 2
    left = sx
    # top-left, top-right, bottom-left, bottom-right
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(accent)
    for dx, dy in (
        (0, 0),
        (quarter + q_gap, 0),
        (0, quarter + q_gap),
        (quarter + q_gap, quarter + q_gap),
    ):
        p.drawRoundedRect(left + dx, top + dy, quarter, quarter, 1, 1)

    # 1: Search — magnifier (circle + tail)
    sx, sy = _slot(1)
    p.setPen(QPen(icon_color, max(1, ic_size // 8)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    r = ic_size // 3
    p.drawEllipse(sx - r + ic_size // 4, sy - r - 1, r * 2, r * 2)
    # tail
    from math import cos, sin, pi

    a = pi / 4
    tail_start_x = sx + ic_size // 4 + int(r * cos(a))
    tail_start_y = sy - 1 + int(r * sin(a))
    p.drawLine(tail_start_x, tail_start_y, sx + ic_size - 2, sy + ic_size // 2 - 2)

    # 2: Task view — two overlapping rounded rectangles
    sx, sy = _slot(2)
    p.setPen(QPen(icon_color, max(1, ic_size // 10)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    rw = int(ic_size * 0.7)
    rh = int(ic_size * 0.55)
    p.drawRoundedRect(sx + ic_size // 2 - rw, sy - rh // 2 - 1, rw, rh, 2, 2)
    p.drawRoundedRect(sx + ic_size // 2 - rw // 2, sy - rh // 2 + 2, rw, rh, 2, 2)

    # (No accent underline: on the real Win11 taskbar that small line only
    # appears under the currently-active foreground app, never under Start.)

    # ── System tray (right side): Wi-Fi, volume, battery, clock ──────────────
    tray_right = ox + sw - max(6, int(bar_h * 0.3))
    tray_gap = max(3, int(bar_h * 0.22))
    tray_icon_size = max(5, int(bar_h * 0.42))

    # Two-line clock: HH:MM on top, DD/MM/YYYY below — matches how Win11
    # shows the tray clock, and here carries the backup's real timestamp
    # so the user sees when the snapshot was taken.
    time_font = QFont("Segoe UI", max(6, int(bar_h * 0.24)))
    date_font = QFont("Segoe UI", max(6, int(bar_h * 0.20)))
    p.setFont(time_font)
    fm_t = p.fontMetrics()
    p.setFont(date_font)
    fm_d = p.fontMetrics()
    time_w = fm_t.horizontalAdvance(clock_time)
    date_w = fm_d.horizontalAdvance(clock_date)
    clock_w = max(time_w, date_w)
    # Vertical layout: stack the two lines and centre them on cy
    line_gap = max(1, bar_h // 24)
    total_h = fm_t.height() + fm_d.height() + line_gap
    top_y = cy - total_h // 2
    p.setPen(icon_color)
    p.setFont(time_font)
    p.drawText(
        tray_right - clock_w + (clock_w - time_w) // 2,
        top_y + fm_t.ascent(),
        clock_time,
    )
    p.setFont(date_font)
    p.drawText(
        tray_right - clock_w + (clock_w - date_w) // 2,
        top_y + fm_t.height() + line_gap + fm_d.ascent(),
        clock_date,
    )
    cursor_x = tray_right - clock_w - tray_gap * 2

    # Battery — horizontal rounded rect with a little nub and a fill
    bat_w = int(tray_icon_size * 1.6)
    bat_h = int(tray_icon_size * 0.75)
    bat_x = cursor_x - bat_w
    bat_y = cy - bat_h // 2
    p.setPen(QPen(icon_color, 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(bat_x, bat_y, bat_w, bat_h, 1, 1)
    # nub
    nub_w = max(1, bat_w // 12)
    p.fillRect(bat_x + bat_w, bat_y + bat_h // 4, nub_w, bat_h // 2, icon_color)
    # fill (~75%)
    pad = 2
    fill_w = int((bat_w - pad * 2) * 0.75)
    p.fillRect(bat_x + pad, bat_y + pad, fill_w, bat_h - pad * 2, icon_color)
    cursor_x = bat_x - tray_gap

    # Volume — speaker trapezoid + one sound arc
    spk_w = tray_icon_size
    spk_h = tray_icon_size
    spk_x = cursor_x - spk_w
    spk_y = cy - spk_h // 2
    p.setPen(QPen(icon_color, max(1, tray_icon_size // 8)))
    p.setBrush(icon_color)
    # trapezoid body
    speaker = QPolygonF(
        [
            QPointF(spk_x, spk_y + spk_h * 0.35),
            QPointF(spk_x + spk_w * 0.35, spk_y + spk_h * 0.35),
            QPointF(spk_x + spk_w * 0.6, spk_y + spk_h * 0.1),
            QPointF(spk_x + spk_w * 0.6, spk_y + spk_h * 0.9),
            QPointF(spk_x + spk_w * 0.35, spk_y + spk_h * 0.65),
            QPointF(spk_x, spk_y + spk_h * 0.65),
        ]
    )
    p.drawPolygon(speaker)
    # sound arc
    p.setBrush(Qt.BrushStyle.NoBrush)
    arc_x = spk_x + int(spk_w * 0.65)
    arc_y = spk_y + int(spk_h * 0.2)
    arc_s = int(spk_h * 0.6)
    from PyQt6.QtCore import QRect as _QR

    p.drawArc(_QR(arc_x, arc_y, arc_s, arc_s), -60 * 16, 120 * 16)
    cursor_x = spk_x - tray_gap

    # Wi-Fi — three stacked arcs (or a filled fan shape)
    wf_size = tray_icon_size
    wf_x = cursor_x - wf_size
    wf_y = cy - wf_size // 2
    p.setPen(QPen(icon_color, max(1, tray_icon_size // 8)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # three concentric arcs opening downward — draw as arc segments centred
    # at the bottom-middle of the wifi icon box
    cx_wf = wf_x + wf_size // 2
    cy_wf = wf_y + wf_size - 1
    for k in (3, 2, 1):
        radius = int(wf_size * k / 3.2)
        rect = _QR(cx_wf - radius, cy_wf - radius, radius * 2, radius * 2)
        p.drawArc(rect, 30 * 16, 120 * 16)
    # dot
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(icon_color)
    dot_r = max(1, wf_size // 10)
    p.drawEllipse(cx_wf - dot_r, cy_wf - dot_r, dot_r * 2, dot_r * 2)

    return bar_y, bar_h


# ── _DiffCanvas ───────────────────────────────────────────────────────────────
class _DiffCanvas(QWidget):
    """
    Draws the saved-vs-current icon diff on a virtual "screen" rectangle
    that preserves the aspect ratio of the saved resolution.

    The virtual screen is letterboxed inside the widget (empty bands on the
    sides or top/bottom as needed) so that proportions match the real monitor
    and icons never get squashed onto the widget's edges.

    Icons whose saved coordinates fall outside the declared resolution are
    NOT silently clamped: they are rendered with a distinctive marker on the
    nearest edge of the virtual screen, so the user can see that something
    is off (typical symptom of a DPI-aware mismatch between an old backup
    and the current environment).
    """

    # Grid color computed at paint time from system palette

    # Inner padding around the virtual-screen rectangle, so dots near the
    # edges don't get cut off against the widget's outer border and the
    # top row of icons gets visual breathing room.
    _PAD = 12
    # Extra vertical breathing room, enforced even when aspect-ratio
    # letterboxing would otherwise give zero space at top/bottom (wide but
    # short widget). The top row of real icons tends to sit near y≈30 of
    # the desktop, which in a cramped canvas ends up glued to the border;
    # reserving this margin guarantees visible padding above it.
    _MIN_VSPACE = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(Config.PREVIEW_HEIGHT)
        self._saved: Dict[str, Tuple[int, int]] = {}
        self._current: Dict[str, Tuple[int, int]] = {}
        self._res: Tuple[int, int] = (1920, 1080)
        self._clock_time: str = "12:34"
        self._clock_date: str = "17/04/2026"
        self._bar_h: int = 0  # set each paint from _draw_win11_taskbar
        self.setMouseTracking(True)

    def set_data(self, saved, current, res, clock_time=None, clock_date=None):
        self._saved = saved
        self._current = current
        self._res = res if res else (1920, 1080)
        if clock_time is not None:
            self._clock_time = clock_time
        if clock_date is not None:
            self._clock_date = clock_date
        self.update()

    # ── Aspect-ratio-preserving projection ────────────────────────────────────
    def _screen_rect(self) -> Tuple[int, int, int, int]:
        """
        Return (ox, oy, sw, sh): the top-left origin and the size of the
        virtual-screen rectangle inside the widget, preserving the aspect
        ratio of self._res.

        Guarantees at least _MIN_VSPACE pixels above and below the rectangle
        even when the widget is wider than tall in aspect — this keeps the
        top row of icons from being glued to the canvas border.
        """
        rw, rh = self._res
        if rw <= 0 or rh <= 0:
            rw, rh = 1920, 1080

        # Available area after outer padding and forced vertical margins.
        avail_w = max(1, self.width() - 2 * self._PAD)
        avail_h = max(1, self.height() - 2 * max(self._PAD, self._MIN_VSPACE))

        s = min(avail_w / rw, avail_h / rh)
        sw = int(rw * s)
        sh = int(rh * s)
        ox = self._PAD + (avail_w - sw) // 2
        oy = max(self._PAD, self._MIN_VSPACE) + (avail_h - sh) // 2
        return ox, oy, sw, sh

    def _project(self, x: float, y: float) -> Tuple[int, int, bool]:
        """
        Project (x, y) from screen-pixel space into widget-pixel space.

        Returns (px, py, out_of_range). When out_of_range is True, the point
        has been snapped to the nearest edge of the virtual screen and should
        be drawn with the out-of-range marker instead of the normal dot.

        Y is projected onto the usable canvas height (sh - _bar_h) mapped to
        the usable screen height (rh - TASKBAR_PX_REAL), so that icons near
        the bottom of the desktop are not rendered inside the taskbar mock-up.
        """
        _TASKBAR_PX_REAL = 48  # Win11 default taskbar height in physical pixels
        ox, oy, sw, sh = self._screen_rect()
        rw, rh = self._res
        rw = rw if rw > 0 else 1
        rh = rh if rh > 0 else 1

        # Usable heights: exclude the taskbar from both domains so the
        # mapping stays proportionally correct.
        sh_usable = max(1, sh - self._bar_h)
        rh_usable = max(1, rh - _TASKBAR_PX_REAL)

        # Tolerance: a few pixels in screen space, to avoid false positives
        # from rounding/quantization right at the edge.
        tol_x = max(2, int(rw * 0.002))
        tol_y = max(2, int(rh * 0.002))
        out = (x < -tol_x) or (y < -tol_y) or (x > rw + tol_x) or (y > rh + tol_y)

        # Always clamp to the drawable rectangle (needed for both regular
        # drawing and the out-of-range marker).
        cx = max(0.0, min(float(x), float(rw)))
        cy = max(0.0, min(float(y), float(rh_usable)))
        px = int(ox + cx * sw / rw)
        py = int(oy + cy * sh_usable / rh_usable)
        return px, py, out

    @staticmethod
    def _eq(a, b, tol=4):
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

    def _draw_out_of_range_marker(self, p: QPainter, x: int, y: int, color: QColor):
        """Small filled triangle with a thin outline — signals clamped icon."""
        r = _DOT_R + 1
        tri = QPolygonF(
            [
                QPointF(x, y - r),
                QPointF(x - r, y + r * 0.7),
                QPointF(x + r, y + r * 0.7),
            ]
        )
        p.setBrush(color)
        p.setPen(QPen(QColor(0, 0, 0, 160), 1))
        p.drawPolygon(tri)
        p.setPen(Qt.PenStyle.NoPen)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Use system palette so canvas respects light/dark theme
        pal = self.palette()
        bg = pal.color(pal.ColorRole.Base)
        grid_color = pal.color(pal.ColorRole.AlternateBase)
        border_color = pal.color(pal.ColorRole.Mid)
        # Fill the whole widget with a slightly dimmer background so the
        # virtual-screen rectangle stands out.
        widget_bg = pal.color(pal.ColorRole.Window)
        p.fillRect(0, 0, W, H, widget_bg)

        # ── Virtual screen rectangle (letterboxed, aspect-ratio preserved) ──
        ox, oy, sw, sh = self._screen_rect()

        # Visual background extends beyond the logical screen rectangle at
        # the top, left, and right — this way icons near the screen edges
        # (especially the top row at y≈30) sit INSIDE the grid area instead
        # of being plastered onto its border. The bottom edge stays exact
        # because the taskbar already gives a clear boundary there.
        bleed_top = 24
        bleed_side = 12
        bg_x = max(0, ox - bleed_side)
        bg_y = max(0, oy - bleed_top)
        bg_w = min(W, ox + sw + bleed_side) - bg_x
        bg_h = (oy + sh) - bg_y

        # Screen background
        p.fillRect(bg_x, bg_y, bg_w, bg_h, bg)

        # Subtle grid, drawn across the extended visual rectangle.
        # Grid lines are anchored to the logical screen origin (ox, oy) so
        # vertical lines align with the logical x=0..rw columns.
        p.setPen(QPen(grid_color, 1))
        # Vertical lines
        x = ox
        while x <= bg_x + bg_w:
            p.drawLine(x, bg_y, x, bg_y + bg_h)
            x += 60
        x = ox - 60
        while x >= bg_x:
            p.drawLine(x, bg_y, x, bg_y + bg_h)
            x -= 60
        # Horizontal lines
        y = oy
        while y <= bg_y + bg_h:
            p.drawLine(bg_x, y, bg_x + bg_w, y)
            y += 60
        y = oy - 60
        while y >= bg_y:
            p.drawLine(bg_x, y, bg_x + bg_w, y)
            y -= 60

        # Border around the extended visual rectangle
        p.setPen(QPen(border_color, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(bg_x, bg_y, bg_w, bg_h, 4, 4)

        # ── Windows 11 taskbar mock-up along the bottom of the screen ───────
        # Drawn BEFORE icons so they render on top when their Y falls inside
        # the taskbar area (which is precisely the case we want to surface —
        # those icons will be hidden behind the real taskbar after restore).
        # Pass the *extended* visual rect (bg_x, bg_w) so the taskbar fill
        # reaches the same left/right edges as the grid background — no
        # mismatched strips on the sides.
        _, self._bar_h = _draw_win11_taskbar(
            p,
            bg_x,
            oy,
            bg_w,
            sh,
            self._res[1],
            pal,
            clock_time=self._clock_time,
            clock_date=self._clock_date,
        )

        if not self._saved:
            p.setPen(pal.color(pal.ColorRole.PlaceholderText))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(
                QRectF(ox, oy, sw, sh),
                int(Qt.AlignmentFlag.AlignCenter),
                self.tr("No Preview Available"),
            )
            return

        # Pass 1: arrows (drawn below dots)
        for name, sp in self._saved.items():
            if name not in self._current:
                continue
            tx, ty, t_out = self._project(sp[0], sp[1])
            cp = self._current[name]
            cx, cy, c_out = self._project(cp[0], cp[1])
            # Skip arrows involving out-of-range endpoints — the marker already
            # tells the story and drawing an arrow to the border would be noise.
            if t_out or c_out:
                continue
            if self._eq((tx, ty), (cx, cy)):
                continue
            pen = QPen(_C_RED, 1, Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 3])
            p.setPen(pen)
            p.drawLine(cx, cy, tx, ty)
            _draw_arrowhead(p, cx, cy, tx, ty, _C_RED)

        # Pass 2: dots (on top)
        p.setPen(Qt.PenStyle.NoPen)
        for name, sp in self._saved.items():
            tx, ty, t_out = self._project(sp[0], sp[1])
            if name in self._current:
                cp = self._current[name]
                cx, cy, c_out = self._project(cp[0], cp[1])
                same = (not t_out) and (not c_out) and self._eq((tx, ty), (cx, cy))
                if same:
                    p.setBrush(QColor(255, 255, 255, 25))
                    p.drawEllipse(
                        tx - _DOT_R - 2, ty - _DOT_R - 2, _DOT_D + 4, _DOT_D + 4
                    )
                    p.setBrush(_C_BLUE)
                    p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)
                else:
                    # Current position (orange)
                    if c_out:
                        self._draw_out_of_range_marker(p, cx, cy, _C_ORANGE)
                    else:
                        p.setBrush(_C_ORANGE)
                        p.drawEllipse(cx - _DOT_R, cy - _DOT_R, _DOT_D, _DOT_D)
                    # Saved/target position (red)
                    if t_out:
                        self._draw_out_of_range_marker(p, tx, ty, _C_RED)
                    else:
                        p.setBrush(_C_RED)
                        p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)
            else:
                if t_out:
                    self._draw_out_of_range_marker(p, tx, ty, _C_GREEN)
                else:
                    p.setBrush(_C_GREEN)
                    p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)

    def mouseMoveEvent(self, ev):
        if not self._saved:
            return
        ex, ey = ev.position().x(), ev.position().y()
        hit = (_DOT_R + 5) ** 2
        for name, sp in self._saved.items():
            tx, ty, t_out = self._project(sp[0], sp[1])
            if (ex - tx) ** 2 + (ey - ty) ** 2 < hit:
                if name in self._current:
                    cp = self._current[name]
                    cx, cy, c_out = self._project(cp[0], cp[1])
                    same = (not t_out) and (not c_out) and self._eq((tx, ty), (cx, cy))
                    if same:
                        st = self.tr("✓ already in place")
                    else:
                        st = self.tr("↕ will move")
                else:
                    st = self.tr("⚠ not on desktop")
                QToolTip.showText(ev.globalPosition().toPoint(), f"{name}\n{st}", self)
                return
        QToolTip.hideText()


# ── _LegendPanel ──────────────────────────────────────────────────────────────
class _LegendPanel(QFrame):
    """
    Overlay legend panel, anchored bottom-right on the canvas.

    Uses a strict QGridLayout with:
      • column 0 — fixed-width icon zone (exactly _ColorDot._S px = 16 px)
      • column 1 — text label (stretches)

    Every row has setFixedHeight(_ROW_H) so Qt cannot vary the spacing.
    The _ArrowIcon is drawn with its orange dot centred in the same 16 px
    zone as every _ColorDot, so all icons in column 0 are on the same axis.

    Row layout:
        row 0:  [● blue  ] "Already in place — will not move"
        row 1:  [●──▶●   ] "Will move  (orange = now,  red = target)"
        row 2:  [● green ] "In backup — not on desktop"
    """

    _ROW_H = 22  # uniform row height (px)

    # (icon_factory, source_string) — strings are marked here for lupdate extraction.
    # Translation happens at instance creation time via self.tr() in __init__.
    _ROWS = [
        (lambda: _ColorDot(_C_BLUE), QT_TR_NOOP("Already in place, will not move")),
        (lambda: _ArrowIcon(), QT_TR_NOOP("Will move  (orange = now,  red = target)")),
        (lambda: _ColorDot(_C_GREEN), QT_TR_NOOP("In backup, not on desktop")),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LegendPanel")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Styles loaded from styles/theme.qss via QFrame#LegendPanel selector

        grid = QGridLayout(self)
        grid.setContentsMargins(12, 8, 16, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        # Column 0: icon zone — wide enough for _ArrowIcon (64 px)
        grid.setColumnMinimumWidth(0, _ArrowIcon._W)
        grid.setColumnStretch(1, 1)

        for row_idx, (icon_fn, label_key) in enumerate(self._ROWS):
            icon_w = icon_fn()
            icon_w.setFixedHeight(self._ROW_H)
            icon_w.setStyleSheet("background: transparent; border: none;")

            lbl = QLabel(self.tr(label_key))
            lbl.setFixedHeight(self._ROW_H)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            grid.addWidget(icon_w, row_idx, 0, Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl, row_idx, 1, Qt.AlignmentFlag.AlignVCenter)

        # Stretch row: absorbs extra vertical space so items stay packed at top
        grid.setRowStretch(len(self._ROWS), 1)


# ── DiffPreviewWidget ─────────────────────────────────────────────────────────
class DiffPreviewWidget(QWidget):
    """
    Canvas fills the entire widget. Legend is now external to this widget.

    ┌──────────────────────────────────────┐
    │                                      │
    │           _DiffCanvas                │
    │                                      │
    └──────────────────────────────────────┘
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._canvas = _DiffCanvas(self)
        self._canvas.setGeometry(self.rect())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._canvas.setGeometry(self.rect())

    def update_preview(self, saved, current, res, clock_time=None, clock_date=None):
        self._canvas.set_data(
            saved, current, res, clock_time=clock_time, clock_date=clock_date
        )


# ── IconPreviewWidget (simple single-backup dot-map) ─────────────────────────
class IconPreviewWidget(QWidget):
    """Standard dot-map preview for a single backup."""

    _PAD = 12
    _MIN_VSPACE = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IconPreviewWidget")
        self.setFixedSize(Config.PREVIEW_WIDTH, Config.PREVIEW_HEIGHT)
        self.icons: Dict[str, Tuple[int, int]] = {}
        self.screen_res: Tuple[int, int] = (1920, 1080)
        self._bar_h: int = 0  # set each paint from _draw_win11_taskbar
        self.setMouseTracking(True)
        # Styles loaded from styles/theme.qss via IconPreviewWidget selector

    def update_preview(self, icons: Dict, res_tuple: Tuple[int, int]):
        self.icons = icons
        self.screen_res = res_tuple if res_tuple else (1920, 1080)
        self.update()

    def _screen_rect(self) -> Tuple[int, int, int, int]:
        rw, rh = self.screen_res
        if rw <= 0 or rh <= 0:
            rw, rh = 1920, 1080
        avail_w = max(1, self.width() - 2 * self._PAD)
        avail_h = max(1, self.height() - 2 * max(self._PAD, self._MIN_VSPACE))
        s = min(avail_w / rw, avail_h / rh)
        sw = int(rw * s)
        sh = int(rh * s)
        ox = self._PAD + (avail_w - sw) // 2
        oy = max(self._PAD, self._MIN_VSPACE) + (avail_h - sh) // 2
        return ox, oy, sw, sh

    def _project(self, x: float, y: float) -> Tuple[int, int, bool]:
        _TASKBAR_PX_REAL = 48
        ox, oy, sw, sh = self._screen_rect()
        rw, rh = self.screen_res
        rw = rw if rw > 0 else 1
        rh = rh if rh > 0 else 1
        sh_usable = max(1, sh - self._bar_h)
        rh_usable = max(1, rh - _TASKBAR_PX_REAL)
        tol_x = max(2, int(rw * 0.002))
        tol_y = max(2, int(rh * 0.002))
        out = (x < -tol_x) or (y < -tol_y) or (x > rw + tol_x) or (y > rh + tol_y)
        cx = max(0.0, min(float(x), float(rw)))
        cy = max(0.0, min(float(y), float(rh_usable)))
        px = int(ox + cx * sw / rw)
        py = int(oy + cy * sh_usable / rh_usable)
        return px, py, out

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()

        ox, oy, sw, sh = self._screen_rect()
        # Extended visual rectangle (see _DiffCanvas.paintEvent rationale)
        W, H = self.width(), self.height()
        bleed_top = max(18, self._MIN_VSPACE - 4)
        bleed_side = 12
        bg_x = max(0, ox - bleed_side)
        bg_y = max(0, oy - bleed_top)
        bg_w = min(W, ox + sw + bleed_side) - bg_x
        bg_h = (oy + sh) - bg_y
        # Screen background
        p.fillRect(bg_x, bg_y, bg_w, bg_h, pal.color(pal.ColorRole.Base))
        # Border
        p.setPen(QPen(pal.color(pal.ColorRole.Mid), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(bg_x, bg_y, bg_w, bg_h, 4, 4)
        # Windows 11 taskbar mock-up
        _, self._bar_h = _draw_win11_taskbar(p, ox, oy, sw, sh, self.screen_res[1], pal)

        if not self.icons:
            p.setPen(pal.color(pal.ColorRole.PlaceholderText))
            p.drawText(
                QRectF(ox, oy, sw, sh),
                int(Qt.AlignmentFlag.AlignCenter),
                self.tr("No Preview Available"),
            )
            return

        p.setPen(Qt.PenStyle.NoPen)
        for pos in self.icons.values():
            px, py, out = self._project(pos[0], pos[1])
            if out:
                # Out-of-range marker — same triangle as in _DiffCanvas
                r = _DOT_R + 1
                tri = QPolygonF(
                    [
                        QPointF(px, py - r),
                        QPointF(px - r, py + r * 0.7),
                        QPointF(px + r, py + r * 0.7),
                    ]
                )
                p.setBrush(_C_RED)
                p.setPen(QPen(QColor(0, 0, 0, 160), 1))
                p.drawPolygon(tri)
                p.setPen(Qt.PenStyle.NoPen)
            else:
                p.setBrush(_C_BLUE)
                p.drawEllipse(px - _DOT_R, py - _DOT_R, _DOT_D, _DOT_D)

    def mouseMoveEvent(self, ev):
        if not self.icons:
            return
        ex, ey = ev.position().x(), ev.position().y()
        hit = (_DOT_R + 5) ** 2
        for name, pos in self.icons.items():
            ix, iy, out = self._project(pos[0], pos[1])
            dx = ex - ix
            dy = ey - iy
            if dx * dx + dy * dy < hit:
                QToolTip.showText(ev.globalPosition().toPoint(), name, self)
                return
        QToolTip.hideText()


def make_legend_widget(parent=None) -> _LegendPanel:
    """Return a standalone _LegendPanel for use outside the canvas."""
    return _LegendPanel(parent)
