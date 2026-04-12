"""About and Keyboard Shortcuts dialogs."""

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize

from core.config import Config, resource_path


def show_about_dialog(window):
    dlg = QDialog(window)
    dlg.setWindowTitle(
        QCoreApplication.translate("MainWindow", "About")
        + " — "
        + "Desktop Icon Backup Manager"
    )
    dlg.setFixedSize(420, 340)

    root = QVBoxLayout(dlg)
    root.setSpacing(0)
    root.setContentsMargins(0, 0, 0, 0)

    # ── Top banner ────────────────────────────────────────────────────
    banner = QWidget()
    banner.setStyleSheet("background: #0078D7;")
    banner.setFixedHeight(90)
    banner_lay = QHBoxLayout(banner)
    banner_lay.setContentsMargins(24, 0, 24, 0)
    banner_lay.setSpacing(16)

    icon_lbl = QLabel()
    pix = QPixmap(resource_path("icon.png"))
    if not pix.isNull():
        icon_lbl.setPixmap(
            pix.scaled(
                QSize(52, 52),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    icon_lbl.setStyleSheet("background: transparent;")
    banner_lay.addWidget(icon_lbl)

    title_col = QVBoxLayout()
    title_col.setSpacing(2)
    app_name = QLabel("Desktop Icon Backup Manager")
    app_name.setStyleSheet(
        "font-size: 16px; font-weight: bold; color: #ffffff;"
        " background: transparent;"
    )
    title_col.addWidget(app_name)
    banner_lay.addLayout(title_col)
    banner_lay.addStretch()
    root.addWidget(banner)

    # ── Body ──────────────────────────────────────────────────────────
    body = QVBoxLayout()
    body.setSpacing(14)
    body.setContentsMargins(24, 20, 24, 16)

    desc = QLabel(
        QCoreApplication.translate(
            "MainWindow",
            "A simple yet powerful tool to save and restore "
            "Windows desktop icon positions.",
        )
    )
    desc.setWordWrap(True)
    desc.setStyleSheet("font-size: 13px;")
    body.addWidget(desc)

    # ── Info grid ─────────────────────────────────────────────────────
    info_grid = QVBoxLayout()
    info_grid.setSpacing(6)

    for label, value, color in [
        (
            QCoreApplication.translate("MainWindow", "Version:"),
            Config.VERSION,
            "palette(text)",
        ),
        (
            QCoreApplication.translate("MainWindow", "Development:"),
            "mapi68",
            "palette(text)",
        ),
    ]:
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(f"<b>{label}</b>")
        lbl.setFixedWidth(100)
        lbl.setStyleSheet("font-size: 12px; color: palette(placeholderText);")
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 12px; color: {color};")
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        info_grid.addLayout(row)

    body.addLayout(info_grid)
    body.addStretch()

    # ── Bottom buttons ────────────────────────────────────────────────
    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    kofi_btn = QPushButton(QCoreApplication.translate("MainWindow", "Support on Ko-fi"))
    kofi_btn.setStyleSheet(
        "QPushButton { background: #FF5E5B; color: white; border: none;"
        " border-radius: 4px; padding: 7px 16px; font-size: 12px;"
        " font-weight: bold; }"
        "QPushButton:hover { background: #E54542; }"
    )
    kofi_btn.clicked.connect(window.open_kofi)

    close_btn = QPushButton(QCoreApplication.translate("MainWindow", "Close"))
    close_btn.setMinimumHeight(32)
    close_btn.clicked.connect(dlg.accept)

    btn_row.addWidget(kofi_btn)
    btn_row.addStretch()
    btn_row.addWidget(close_btn)
    body.addLayout(btn_row)

    root.addLayout(body)
    dlg.exec()


def show_shortcuts_dialog(window):
    pal = window.palette()
    _c = lambda role: pal.color(role).name()
    c_header_bg = _c(pal.ColorRole.Dark)
    c_header_fg = _c(pal.ColorRole.BrightText)
    c_border = _c(pal.ColorRole.Mid)
    c_row_even = _c(pal.ColorRole.AlternateBase)
    c_row_odd = _c(pal.ColorRole.Base)
    c_text = _c(pal.ColorRole.Text)
    c_dim = _c(pal.ColorRole.PlaceholderText)

    shortcuts_text = f"""
    <h2>{QCoreApplication.translate("MainWindow", "Keyboard Shortcuts")}</h2>
    <table style='width:100%; border-collapse: collapse;'>
        <tr style='background-color: {c_header_bg}; color: {c_header_fg};'>
            <th style='padding: 8px; text-align: left; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Shortcut")}</th>
            <th style='padding: 8px; text-align: left; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Action")}</th>
        </tr>
        <tr style='background-color: {c_row_odd}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>Ctrl+S</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Quick Save current layout")}</td>
        </tr>
        <tr style='background-color: {c_row_even}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>Ctrl+M</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Open") + " Backup Manager"}</td>
        </tr>
        <tr style='background-color: {c_row_odd}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>Ctrl+H</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Show/Hide Desktop Icons")}</td>
        </tr>
        <tr style='background-color: {c_row_even}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>Ctrl+,</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Open Settings menu")}</td>
        </tr>
        <tr style='background-color: {c_row_odd}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>F1</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Open Online User Manual")}</td>
        </tr>
        <tr style='background-color: {c_row_even}; color: {c_text};'>
            <td style='padding: 8px; border: 1px solid {c_border};'><b>Ctrl+Q</b></td>
            <td style='padding: 8px; border: 1px solid {c_border};'>{QCoreApplication.translate("MainWindow", "Exit Application")}</td>
        </tr>
    </table>
    <br>
    <p style='color: {c_dim}; font-size: 11px;'>{QCoreApplication.translate("MainWindow", "Tip: Hover over buttons to see additional shortcuts in tooltips.")}</p>
    """

    dialog = QDialog(window)
    dialog.setWindowTitle(
        QCoreApplication.translate("MainWindow", "Keyboard Shortcuts")
    )
    dialog.setMinimumWidth(Config.SHORTCUTS_DIALOG_MIN_WIDTH)
    dialog.setMinimumHeight(Config.SHORTCUTS_DIALOG_MIN_HEIGHT)

    layout = QVBoxLayout(dialog)

    text_browser = QTextEdit()
    text_browser.setReadOnly(True)
    text_browser.setHtml(shortcuts_text)
    layout.addWidget(text_browser)

    btn_close = QPushButton(QCoreApplication.translate("MainWindow", "Close"))
    btn_close.clicked.connect(dialog.accept)
    layout.addWidget(btn_close)

    dialog.exec()
