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
from PyQt6.QtCore import Qt, QRect, QCoreApplication

from core.config import Config, resource_path

# Duration in milliseconds
SPLASH_DURATION_MS = 1500


class SplashScreen(QSplashScreen):
    """Splash screen shown at application startup."""

    SPLASH_W = 460
    SPLASH_H = 340

    # Design palette — Windows light theme
    _C_BG_TOP = QColor("#D6DCE8")
    _C_BG_BOT = QColor("#C8D0E0")
    _C_CARD = QColor(0, 0, 0, 6)
    _C_BORDER = QColor(0, 0, 0, 45)
    _C_ACCENT = QColor("#0058A8")
    _C_ACCENT2 = QColor("#0078D7")
    _C_WHITE = QColor("#0A0A14")
    _C_DIM = QColor("#2D3748")
    _C_RULE = QColor(0, 0, 0, 120)

    def __init__(self):
        self._base_canvas = self._build_canvas()  # pixmap senza barra
        super().__init__(self._base_canvas.copy())
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

        # ── Background: near-black gradient
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.0, self._C_BG_TOP)
        bg.setColorAt(1.0, self._C_BG_BOT)
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, W, H, 12, 12)

        # ── Subtle radial glow behind icon area (blue)
        glow = QRadialGradient(W // 2, 118, 110)
        glow.setColorAt(0.0, QColor(0, 120, 215, 45))
        glow.setColorAt(1.0, QColor(0, 120, 215, 0))
        p.setBrush(glow)
        p.drawRect(0, 0, W, H)

        # ── Fine horizontal scan-lines for texture (very subtle)
        p.setPen(QPen(QColor(0, 0, 0, 6), 1))
        for y in range(0, H, 3):
            p.drawLine(0, y, W, y)

        # ── Outer border
        p.setPen(QPen(self._C_BORDER, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, W - 1, H - 1, 12, 12)

        # ── Top accent stripe (electric blue → cyan)
        p.setPen(Qt.PenStyle.NoPen)
        stripe = QLinearGradient(0, 0, W, 0)
        stripe.setColorAt(0.0, self._C_ACCENT)
        stripe.setColorAt(1.0, self._C_ACCENT2)
        p.setBrush(stripe)
        p.drawRoundedRect(0, 0, W, 4, 2, 2)

        # ══════════════════════════════════════════
        # ICON — centred in the top portion
        # ══════════════════════════════════════════
        ICON = 80
        ix = (W - ICON) // 2
        iy = 26
        scaled = source.scaled(
            ICON,
            ICON,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Soft drop-shadow behind icon
        p.setPen(Qt.PenStyle.NoPen)
        shadow = QRadialGradient(ix + ICON // 2, iy + ICON // 2 + 6, ICON // 2 + 8)
        shadow.setColorAt(0.0, QColor(0, 120, 215, 60))
        shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(shadow)
        p.drawEllipse(ix - 12, iy - 4, ICON + 24, ICON + 20)
        p.drawPixmap(ix, iy, scaled)

        # ══════════════════════════════════════════
        # APP NAME — two-line, centred
        # ══════════════════════════════════════════
        name_y = iy + ICON + 14

        p.setPen(self._C_WHITE)
        f_title = QFont("Segoe UI", 17, QFont.Weight.Bold)
        f_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        p.setFont(f_title)
        p.drawText(
            QRect(0, name_y, W, 30),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Desktop Icon",
        )

        p.setPen(self._C_ACCENT2)
        f_sub = QFont("Segoe UI", 17, QFont.Weight.Bold)
        f_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        p.setFont(f_sub)
        p.drawText(
            QRect(0, name_y + 28, W, 30),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Backup Manager",
        )

        # ══════════════════════════════════════════
        # THIN HORIZONTAL RULE
        # ══════════════════════════════════════════
        rule_y = name_y + 68
        rule_margin = 40
        rule_grad = QLinearGradient(rule_margin, 0, W - rule_margin, 0)
        rule_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        rule_grad.setColorAt(0.3, self._C_RULE)
        rule_grad.setColorAt(0.7, self._C_RULE)
        rule_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(QPen(rule_grad, 1))
        p.drawLine(rule_margin, rule_y, W - rule_margin, rule_y)

        # ══════════════════════════════════════════
        # VERSION  +  DEVELOPMENT  — two columns
        # ══════════════════════════════════════════
        meta_y = rule_y + 14
        col_w = W // 2

        f_label = QFont("Segoe UI", 7, QFont.Weight.Bold)
        f_label.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.8)
        f_value = QFont("Segoe UI", 9)

        # Left: VERSION
        p.setFont(f_label)
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(0, meta_y, col_w, 16),
            Qt.AlignmentFlag.AlignHCenter,
            QCoreApplication.translate("SplashScreen", "VERSION"),
        )
        p.setFont(f_value)
        p.setPen(self._C_WHITE)
        p.drawText(
            QRect(0, meta_y + 17, col_w, 18),
            Qt.AlignmentFlag.AlignHCenter,
            Config.VERSION,
        )

        # Vertical divider between columns
        p.setPen(QPen(self._C_RULE, 1))
        p.drawLine(col_w, meta_y, col_w, meta_y + 35)

        # Right: DEVELOPMENT
        p.setFont(f_label)
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(col_w, meta_y, col_w, 16),
            Qt.AlignmentFlag.AlignHCenter,
            QCoreApplication.translate("SplashScreen", "DEVELOPMENT"),
        )
        p.setFont(f_value)
        p.setPen(self._C_WHITE)
        p.drawText(
            QRect(col_w, meta_y + 17, col_w, 18),
            Qt.AlignmentFlag.AlignHCenter,
            "mapi68",
        )

        # ══════════════════════════════════════════
        # LOADING LABEL at the bottom
        # ══════════════════════════════════════════
        label_margin = 32
        label_w = W - label_margin * 2
        label_y = H - 22

        # "Loading…" label left-aligned at the bottom
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(label_margin, label_y - 14, label_w, 14),
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
            self._C_DIM,
        )
        QApplication.processEvents()
