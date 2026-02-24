"""Splash Screen for Desktop Icon Backup Manager"""

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QLinearGradient,
    QRadialGradient,
    QPen,
)
from PyQt6.QtCore import Qt, QRect, QTimer, QCoreApplication

from core.config import Config, resource_path

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
        from PyQt6.QtGui import QPen, QRadialGradient

        W, H = self.SPLASH_W, self.SPLASH_H

        source = QPixmap(resource_path("icon.png"))
        canvas = QPixmap(W, H)
        canvas.fill(Qt.GlobalColor.transparent)

        p = QPainter(canvas)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # ── Background: deep space blue — diagonal gradient
        bg = QLinearGradient(0, 0, W * 0.6, H)
        bg.setColorAt(0.0, QColor("#060D1F"))
        bg.setColorAt(0.55, QColor("#0B1A3B"))
        bg.setColorAt(1.0, QColor("#0E2255"))
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, W, H, 14, 14)

        # ── Radial glow top-right (cyan)
        glow_tr = QRadialGradient(W, 0, 200)
        glow_tr.setColorAt(0.0, QColor(0, 229, 255, 55))
        glow_tr.setColorAt(1.0, QColor(0, 229, 255, 0))
        p.setBrush(glow_tr)
        p.drawRoundedRect(0, 0, W, H, 14, 14)

        # ── Radial glow bottom-left (violet)
        glow_bl = QRadialGradient(60, H + 30, 160)
        glow_bl.setColorAt(0.0, QColor(120, 40, 255, 40))
        glow_bl.setColorAt(1.0, QColor(120, 40, 255, 0))
        p.setBrush(glow_bl)
        p.drawRoundedRect(0, 0, W, H, 14, 14)

        # ── Subtle grid lines
        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        for x in range(0, W, 40):
            p.drawLine(x, 0, x, H)
        for y in range(0, H, 40):
            p.drawLine(0, y, W, y)

        # ── Top accent bar: vivid cyan → electric blue → violet
        p.setPen(Qt.PenStyle.NoPen)
        accent = QLinearGradient(0, 0, W, 0)
        accent.setColorAt(0.0, QColor("#00E5FF"))
        accent.setColorAt(0.45, QColor("#2979FF"))
        accent.setColorAt(1.0, QColor("#AA00FF"))
        p.setBrush(accent)
        p.drawRoundedRect(0, 0, W, 5, 3, 3)

        # ── Bottom accent bar: reversed, slightly dimmer
        accent2 = QLinearGradient(0, 0, W, 0)
        accent2.setColorAt(0.0, QColor(170, 0, 255, 140))
        accent2.setColorAt(0.55, QColor(41, 121, 255, 140))
        accent2.setColorAt(1.0, QColor(0, 229, 255, 140))
        p.setBrush(accent2)
        p.drawRoundedRect(0, H - 4, W, 4, 3, 3)

        # ── App icon (left)
        ICON = 96
        ix, iy = 28, (H - ICON) // 2 - 10
        scaled = source.scaled(
            ICON,
            ICON,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        p.drawPixmap(ix, iy, scaled)

        # ── Title line 1: pure white
        tx = ix + ICON + 24
        tw = W - tx - 22
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold))
        p.drawText(
            QRect(tx, iy, tw, 38),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Desktop Icon",
        )

        # ── Title line 2: vivid cyan (stands out from line 1)
        p.setPen(QColor("#00E5FF"))
        p.drawText(
            QRect(tx, iy + 37, tw, 38),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Backup Manager",
        )

        # ── Separator line: full gradient
        sep = QLinearGradient(tx, 0, tx + tw, 0)
        sep.setColorAt(0.0, QColor("#00E5FF"))
        sep.setColorAt(0.5, QColor("#2979FF"))
        sep.setColorAt(1.0, QColor("#AA00FF"))
        p.setPen(QPen(sep, 1.5))
        p.drawLine(tx, iy + 83, tx + tw, iy + 83)

        # ── Version — bright cyan
        p.setPen(QColor("#40D4FF"))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        p.drawText(
            QRect(tx, iy + 91, tw, 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QCoreApplication.translate("SplashScreen", "Version: %1").replace(
                "%1", Config.VERSION
            ),
        )

        # ── Author — light steel blue
        p.setPen(QColor("#7BB8E8"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(
            QRect(tx, iy + 111, tw, 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QCoreApplication.translate("SplashScreen", "Development: mapi68"),
        )

        # ── Translator credit (shown only if translated)
        translator_line = QCoreApplication.translate("Common", "Translation: %1")
        if translator_line != "Translation: %1":
            p.setPen(QColor("#B380FF"))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(
                QRect(tx, iy + 131, tw, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                translator_line,
            )

        # ── Status dot + text at bottom
        dot_x, dot_y = 22, H - 18
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#00E5FF"))
        p.drawEllipse(dot_x, dot_y - 3, 6, 6)

        p.setPen(QColor("#3A8FC4"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(
            QRect(dot_x + 12, H - 26, W - dot_x - 32, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QCoreApplication.translate("SplashScreen", "Loading\u2026"),
        )

        p.end()
        return canvas

    def set_status(self, message: str):
        """Update the loading message at the bottom."""
        self.showMessage(
            message,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            QColor("#3A8FC4"),
        )
        QApplication.processEvents()
