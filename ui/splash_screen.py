"""Splash Screen for Desktop Icon Backup Manager"""

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QFont,
    QLinearGradient,
    QPen,
    QPainterPath,
    QBrush,
)
from PyQt6.QtCore import Qt, QRect, QRectF, QCoreApplication

from core.config import Config, resource_path

# Duration in milliseconds
SPLASH_DURATION_MS = 1500


class SplashScreen(QSplashScreen):
    """Splash screen shown at application startup."""

    SPLASH_W = 480
    SPLASH_H = 300
    RADIUS = 16

    # ── Colour palette ───────────────────────────────────────────────────────
    _G_TOP = QColor("#1E3A5F")  # deep navy
    _G_MID = QColor("#2E5F8A")  # mid blue
    _G_BOT = QColor("#1A3050")  # dark slate

    _C_TEXT = QColor("#E8EDF4")  # near-white
    _C_SUB = QColor("#5BA8E5")  # sky blue
    _C_DIM = QColor("#7A9BB5")  # muted blue-grey
    _C_RULE = QColor(255, 255, 255, 90)
    _C_BORDER = QColor(255, 255, 255, 28)

    _DOT_SPACING = 18
    _DOT_ALPHA = 22
    _DOT_RADIUS = 1.0

    def __init__(self):
        self._base_canvas = self._build_canvas()
        super().__init__(self._base_canvas)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setMask(self._base_canvas.mask())

    def center_on_window(self, window):
        geo = window.geometry()
        x = geo.x() + (geo.width() - self.SPLASH_W) // 2
        y = geo.y() + (geo.height() - self.SPLASH_H) // 2
        self.move(x, y)

    def _build_canvas(self) -> QPixmap:
        W, H, R = self.SPLASH_W, self.SPLASH_H, self.RADIUS

        img = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)

        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Clip to rounded rect
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, W, H), R, R)
        p.setClipPath(clip)

        # 2. Background gradient
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.00, self._G_TOP)
        bg.setColorAt(0.45, self._G_MID)
        bg.setColorAt(1.00, self._G_BOT)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawRect(0, 0, W, H)

        # 3. Diagonal teal wash
        wash = QLinearGradient(0, 0, W * 0.7, H * 0.6)
        wash.setColorAt(0.0, QColor(0, 180, 220, 30))
        wash.setColorAt(1.0, QColor(0, 180, 220, 0))
        p.setBrush(QBrush(wash))
        p.drawRect(0, 0, W, H)

        # 4. Dot-grid texture
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, self._DOT_ALPHA))
        dr = self._DOT_RADIUS
        sp = self._DOT_SPACING
        for row in range(0, H // sp + 2):
            for col in range(0, W // sp + 2):
                cx = col * sp + (sp // 2 if row % 2 else 0)
                cy = row * sp
                p.drawEllipse(QRectF(cx - dr, cy - dr, dr * 2, dr * 2))

        # 5. Vignette
        vig = QLinearGradient(0, 0, 0, H)
        vig.setColorAt(0.0, QColor(0, 0, 0, 60))
        vig.setColorAt(0.3, QColor(0, 0, 0, 0))
        vig.setColorAt(0.7, QColor(0, 0, 0, 0))
        vig.setColorAt(1.0, QColor(0, 0, 0, 80))
        p.setBrush(QBrush(vig))
        p.drawRect(0, 0, W, H)

        # 6. Border
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(self._C_BORDER, 1.0))
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), R - 0.5, R - 0.5)

        # 7. Icon
        ICON = 72
        ix = (W - ICON) // 2
        iy = 22
        src = QPixmap(resource_path("icon.png"))
        scaled = src.scaled(
            ICON,
            ICON,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPixmap(ix, iy, scaled)

        # 8. App name
        name_y = iy + ICON + 12

        f_title = QFont("Segoe UI", 16, QFont.Weight.Bold)
        f_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.4)
        p.setFont(f_title)
        p.setPen(self._C_TEXT)
        p.drawText(
            QRect(0, name_y, W, 28),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Desktop Icon",
        )

        f_sub = QFont("Segoe UI", 16, QFont.Weight.Bold)
        f_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.4)
        p.setFont(f_sub)
        p.setPen(self._C_SUB)
        p.drawText(
            QRect(0, name_y + 26, W, 28),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Backup Manager",
        )

        # 9. Rule
        rule_y = name_y + 64
        rm = 44
        rule_g = QLinearGradient(rm, 0, W - rm, 0)
        rule_g.setColorAt(0.0, QColor(255, 255, 255, 0))
        rule_g.setColorAt(0.3, self._C_RULE)
        rule_g.setColorAt(0.7, self._C_RULE)
        rule_g.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(QPen(QBrush(rule_g), 1.0))
        p.drawLine(rm, rule_y, W - rm, rule_y)

        # 10. Meta row
        meta_y = rule_y + 14
        col_w = W // 2
        f_lbl = QFont("Segoe UI", 7, QFont.Weight.Bold)
        f_lbl.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.8)
        f_val = QFont("Segoe UI", 9)

        p.setFont(f_lbl)
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(0, meta_y, col_w, 15),
            Qt.AlignmentFlag.AlignHCenter,
            QCoreApplication.translate("SplashScreen", "VERSION"),
        )
        p.setFont(f_val)
        p.setPen(self._C_TEXT)
        p.drawText(
            QRect(0, meta_y + 16, col_w, 17),
            Qt.AlignmentFlag.AlignHCenter,
            Config.VERSION,
        )

        p.setPen(QPen(self._C_RULE, 1.0))
        p.drawLine(col_w, meta_y, col_w, meta_y + 33)

        p.setFont(f_lbl)
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(col_w, meta_y, col_w, 15),
            Qt.AlignmentFlag.AlignHCenter,
            QCoreApplication.translate("SplashScreen", "DEVELOPMENT"),
        )
        p.setFont(f_val)
        p.setPen(self._C_TEXT)
        p.drawText(
            QRect(col_w, meta_y + 16, col_w, 17),
            Qt.AlignmentFlag.AlignHCenter,
            "mapi68",
        )

        # 11. Loading
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(self._C_DIM)
        p.drawText(
            QRect(32, H - 28, W - 64, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QCoreApplication.translate("SplashScreen", "Loading\u2026"),
        )

        p.end()
        return QPixmap.fromImage(img)

    def set_status(self, message: str):
        self.showMessage(
            message,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            self._C_DIM,
        )
        QApplication.processEvents()
