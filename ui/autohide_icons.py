"""Icons used by the Auto-Hide UI.

Kept separate from the main window so the QtGui paint machinery is only
imported when actually needed.
"""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QIcon, QPixmap


def make_stop_icon(
    size: int = 16, fg: QColor | None = None, bg: QColor | None = None
) -> QIcon:
    """Create a 'stop' icon: a small rounded square inside a thin ring."""
    if fg is None:
        fg = QColor("#CC0000")
    if bg is None:
        bg = QColor(0, 0, 0, 0)  # transparent

    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Outer ring
    ring_pen = QPen(fg, max(1, size // 12))
    p.setPen(ring_pen)
    p.setBrush(QBrush(bg))
    margin = max(1, size // 10)
    ring_rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    p.drawEllipse(ring_rect)

    # Inner filled square
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(fg))
    inner = size * 0.42
    cx = size / 2
    cy = size / 2
    square = QRectF(cx - inner / 2, cy - inner / 2, inner, inner)
    radius = inner * 0.18
    p.drawRoundedRect(square, radius, radius)
    p.end()

    return QIcon(pm)
