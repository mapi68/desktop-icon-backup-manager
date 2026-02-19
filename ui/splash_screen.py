"""Splash Screen for Desktop Icon Backup Manager"""

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtCore import Qt, QRect, QTimer

from config import Config, resource_path

# Duration in milliseconds
SPLASH_DURATION_MS = 2000


class SplashScreen(QSplashScreen):
    """Splash screen shown at application startup."""

    SPLASH_W = 480
    SPLASH_H = 280

    def __init__(self):
        canvas = self._build_canvas()
        super().__init__(canvas)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

    def center_on_window(self, window):
        """Position the splash at the center of the given main window."""
        geo = window.geometry()
        x = geo.x() + (geo.width() - self.SPLASH_W) // 2
        y = geo.y() + (geo.height() - self.SPLASH_H) // 2
        self.move(x, y)

    def _build_canvas(self) -> QPixmap:
        W, H = self.SPLASH_W, self.SPLASH_H

        source = QPixmap(resource_path("icon.png"))
        canvas = QPixmap(W, H)
        canvas.fill(Qt.GlobalColor.transparent)

        p = QPainter(canvas)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Background gradient
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.0, QColor("#0f1923"))
        bg.setColorAt(1.0, QColor("#1a2d3f"))
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, W, H, 14, 14)

        # Top accent bar
        accent = QLinearGradient(0, 0, W, 0)
        accent.setColorAt(0.0, QColor("#0078D7"))
        accent.setColorAt(1.0, QColor("#00B4D8"))
        p.setBrush(accent)
        p.drawRoundedRect(0, 0, W, 5, 2, 2)

        # App icon (left)
        ICON = 96
        ix, iy = 28, (H - ICON) // 2 - 12
        scaled = source.scaled(
            ICON,
            ICON,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        p.drawPixmap(ix, iy, scaled)

        # Title text
        tx = ix + ICON + 22
        tw = W - tx - 20
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        p.drawText(
            QRect(tx, iy, tw, 36),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Desktop Icon",
        )
        p.drawText(
            QRect(tx, iy + 34, tw, 36),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Backup Manager",
        )

        # Separator line
        p.setPen(QColor("#0078D7"))
        p.drawLine(tx, iy + 76, tx + tw, iy + 76)

        # Version / author
        p.setPen(QColor("#7AAECB"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(
            QRect(tx, iy + 84, tw, 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"Version {Config.VERSION}  \u00b7  by mapi68",
        )

        # Bottom status
        p.setPen(QColor("#3A6A8A"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(
            QRect(20, H - 32, W - 40, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Loading\u2026",
        )

        # Bottom border
        p.setPen(QColor("#0078D7"))
        p.drawLine(0, H - 1, W, H - 1)

        p.end()
        return canvas

    def set_status(self, message: str):
        """Update the loading message at the bottom."""
        self.showMessage(
            message,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            QColor("#3A6A8A"),
        )
        QApplication.processEvents()
