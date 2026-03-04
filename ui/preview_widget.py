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


# ── _DiffCanvas ───────────────────────────────────────────────────────────────
class _DiffCanvas(QWidget):
    # Grid color computed at paint time from system palette

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(Config.PREVIEW_HEIGHT)
        self._saved: Dict[str, Tuple[int, int]] = {}
        self._current: Dict[str, Tuple[int, int]] = {}
        self._res: Tuple[int, int] = (1920, 1080)
        self.setMouseTracking(True)

    def set_data(self, saved, current, res):
        self._saved = saved
        self._current = current
        self._res = res if res else (1920, 1080)
        self.update()

    def _sx(self):
        return self.width() / self._res[0]

    def _sy(self):
        return self.height() / self._res[1]

    def _clamp(self, px: float, py: float) -> Tuple[int, int]:
        m = _MARGIN
        return (
            int(max(m, min(px, self.width() - m))),
            int(max(m, min(py, self.height() - m))),
        )

    @staticmethod
    def _eq(a, b, tol=4):
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Use system palette so canvas respects light/dark theme
        pal = self.palette()
        bg = pal.color(pal.ColorRole.Base)
        grid_color = pal.color(pal.ColorRole.AlternateBase)
        border_color = pal.color(pal.ColorRole.Mid)
        p.fillRect(0, 0, W, H, bg)

        # Subtle grid
        p.setPen(QPen(grid_color, 1))
        for x in range(0, W, 60):
            p.drawLine(x, 0, x, H)
        for y in range(0, H, 60):
            p.drawLine(0, y, W, y)

        # Border
        p.setPen(QPen(border_color, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(1, 1, W - 2, H - 2, 4, 4)

        if not self._saved:
            p.setPen(pal.color(pal.ColorRole.PlaceholderText))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                self.tr("No Preview Available"),
            )
            return

        sx, sy = self._sx(), self._sy()

        # Pass 1: arrows (drawn below dots)
        for name, sp in self._saved.items():
            if name not in self._current:
                continue
            tx, ty = self._clamp(sp[0] * sx, sp[1] * sy)
            cx, cy = self._clamp(
                self._current[name][0] * sx, self._current[name][1] * sy
            )
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
            tx, ty = self._clamp(sp[0] * sx, sp[1] * sy)
            if name in self._current:
                cx, cy = self._clamp(
                    self._current[name][0] * sx, self._current[name][1] * sy
                )
                if self._eq((tx, ty), (cx, cy)):
                    p.setBrush(QColor(255, 255, 255, 25))
                    p.drawEllipse(
                        tx - _DOT_R - 2, ty - _DOT_R - 2, _DOT_D + 4, _DOT_D + 4
                    )
                    p.setBrush(_C_BLUE)
                    p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)
                else:
                    p.setBrush(_C_ORANGE)
                    p.drawEllipse(cx - _DOT_R, cy - _DOT_R, _DOT_D, _DOT_D)
                    p.setBrush(_C_RED)
                    p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)
            else:
                p.setBrush(_C_GREEN)
                p.drawEllipse(tx - _DOT_R, ty - _DOT_R, _DOT_D, _DOT_D)

    def mouseMoveEvent(self, ev):
        if not self._saved:
            return
        sx, sy = self._sx(), self._sy()
        ex, ey = ev.position().x(), ev.position().y()
        hit = (_DOT_R + 5) ** 2
        for name, sp in self._saved.items():
            tx, ty = self._clamp(sp[0] * sx, sp[1] * sy)
            if (ex - tx) ** 2 + (ey - ty) ** 2 < hit:
                if name in self._current:
                    cx, cy = self._clamp(
                        self._current[name][0] * sx, self._current[name][1] * sy
                    )
                    st = (
                        self.tr("✓ already in place")
                        if self._eq((tx, ty), (cx, cy))
                        else self.tr("↕ will move")
                    )
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

    _ROW_H = 26  # uniform row height (px)

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
        self.setStyleSheet("""
            QFrame#LegendPanel {
                border: 1px solid palette(mid);
                border-radius: 7px;
            }
            QLabel {
                background: transparent;
                border: none;
                font-family: 'Segoe UI';
                font-size: 11px;
            }
        """)

        grid = QGridLayout(self)
        grid.setContentsMargins(12, 8, 16, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(0)
        # Column 0: icon zone — wide enough for _ArrowIcon (64 px)
        grid.setColumnMinimumWidth(0, _ArrowIcon._W)
        grid.setColumnStretch(1, 1)

        for row_idx, (icon_fn, label_key) in enumerate(self._ROWS):
            icon_w = icon_fn()
            # Every icon widget is the same height — the grid rows are all equal
            icon_w.setFixedHeight(self._ROW_H)
            icon_w.setStyleSheet("background: transparent; border: none;")

            lbl = QLabel(self.tr(label_key))
            lbl.setFixedHeight(self._ROW_H)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            grid.addWidget(icon_w, row_idx, 0, Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl, row_idx, 1, Qt.AlignmentFlag.AlignVCenter)


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

    def update_preview(self, saved, current, res):
        self._canvas.set_data(saved, current, res)


# ── IconPreviewWidget (simple single-backup dot-map) ─────────────────────────
class IconPreviewWidget(QWidget):
    """Standard dot-map preview for a single backup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(Config.PREVIEW_WIDTH, Config.PREVIEW_HEIGHT)
        self.icons: Dict[str, Tuple[int, int]] = {}
        self.screen_res: Tuple[int, int] = (1920, 1080)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QWidget {
                background-color: palette(base);
                border: 2px solid palette(mid);
                border-radius: 4px;
            }
            QToolTip {
                font-family: 'Segoe UI'; font-size: 12px;
            }
        """)

    def update_preview(self, icons: Dict, res_tuple: Tuple[int, int]):
        self.icons = icons
        self.screen_res = res_tuple if res_tuple else (1920, 1080)
        self.update()

    def _scale(self):
        return self.width() / self.screen_res[0], self.height() / self.screen_res[1]

    def _clamp(self, px, py):
        m = _MARGIN
        return (max(m, min(px, self.width() - m)), max(m, min(py, self.height() - m)))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.icons:
            p.setPen(self.palette().color(self.palette().ColorRole.PlaceholderText))
            p.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                self.tr("No Preview Available"),
            )
            return
        sx, sy = self._scale()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_C_BLUE)
        for pos in self.icons.values():
            px, py = self._clamp(int(pos[0] * sx), int(pos[1] * sy))
            p.drawEllipse(px - _DOT_R, py - _DOT_R, _DOT_D, _DOT_D)

    def mouseMoveEvent(self, ev):
        if not self.icons:
            return
        sx, sy = self._scale()
        for name, pos in self.icons.items():
            ix, iy = int(pos[0] * sx), int(pos[1] * sy)
            dx = ev.position().x() - ix
            dy = ev.position().y() - iy
            if dx * dx + dy * dy < 144:
                QToolTip.showText(ev.globalPosition().toPoint(), name, self)
                return
        QToolTip.hideText()


def make_legend_widget(parent=None) -> _LegendPanel:
    """Return a standalone _LegendPanel for use outside the canvas."""
    return _LegendPanel(parent)
