"""Desktop Icon Backup Manager - Main Entry Point"""

import sys
import os
import argparse
import ctypes
from pathlib import Path


# ── DPI awareness (must run BEFORE creating QApplication) ─────────────────────
# Without this, on Windows with display scaling > 100% (typical on 2K / 4K
# monitors), Qt reports a logical, DPI-scaled screen resolution while Win32
# LVM_GETITEMPOSITION returns physical pixel coordinates. The mismatch makes
# some icons — especially those near the bottom edge — appear to be "missing"
# in the Backup Manager preview because they get clamped onto the canvas
# border. Declaring the process as Per-Monitor-v2 DPI-aware aligns Qt's
# reported geometry with Win32's pixel coordinates.
def _enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    # Per-Monitor v2 (Windows 10 1703+)
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except (AttributeError, OSError):
        pass
    # System DPI Aware (Windows 8.1+)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    except (AttributeError, OSError):
        pass
    # Vista+ fallback
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


_enable_dpi_awareness()


from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QSystemTrayIcon,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QCheckBox,
)
from PyQt6.QtCore import (
    QSettings,
    QTranslator,
    QLocale,
    QCoreApplication,
    QTimer,
    QLibraryInfo,
)
from PyQt6.QtGui import QIcon, QPalette, QColor

from core.config import Config, resource_path
from core.icon_manager import DesktopIconManager
from ui.main_window import MainWindow
from utils.single_instance import ensure_single_instance
from utils.logging_config import init_logging

_LOCALE_NAMES = {
    "": "English",
    "ar_SA": "Arabic (العربية)",
    "zh_CN": "Chinese Simplified (中文 简体)",
    "zh_TW": "Chinese Traditional (中文 繁體)",
    "cs_CZ": "Czech (Čeština)",
    "da_DK": "Danish (Dansk)",
    "nl_NL": "Dutch (Nederlands)",
    "fi_FI": "Finnish (Suomi)",
    "fr_FR": "French (Français)",
    "de_DE": "German (Deutsch)",
    "el_GR": "Greek (Ελληνικά)",
    "hi_IN": "Hindi (हिन्दी)",
    "it_IT": "Italian (Italiano)",
    "ja_JP": "Japanese (日本語)",
    "ko_KR": "Korean (한국어)",
    "nb_NO": "Norwegian (Norsk bokmål)",
    "pl_PL": "Polish (Polski)",
    "pt_BR": "Portuguese BR (Português BR)",
    "pt_PT": "Portuguese PT (Português PT)",
    "ro_RO": "Romanian (Română)",
    "ru_RU": "Russian (Русский)",
    "sl_SI": "Slovenian (Slovenščina)",
    "es_ES": "Spanish (Español)",
    "sv_SE": "Swedish (Svenska)",
    "tr_TR": "Turkish (Türkçe)",
    "uk_UA": "Ukrainian (Українська)",
}


def _display_name(locale: str) -> str:
    """Return a human-readable name for a locale string."""
    return _LOCALE_NAMES.get(locale, locale)


# ── Discover available .qm files ──────────────────────────────────────────────
def _available_locales() -> list[str]:
    """
    Scan the i18n folder and return a sorted list of locale strings
    for which a .qm file exists, plus "" (English built-in).
    E.g. ["", "it_IT"]
    """
    locales = [""]  # English always available
    i18n_dir = Path(resource_path("i18n"))
    if i18n_dir.is_dir():
        for qm in sorted(i18n_dir.glob("*.qm")):
            locale = qm.stem  # e.g. "it_IT"
            if locale not in locales:
                locales.append(locale)
    return locales


# ── Auto-detect best locale ───────────────────────────────────────────────────
def _autodetect_locale(available: list[str]) -> str:
    """
    Try to match the system locale to an available .qm file.
    Tries exact match first (e.g. "it_IT"), then language-only (e.g. "it").
    Returns "" (English) if nothing matches.
    """
    sys_locale = QLocale.system()
    # Candidates in order of preference
    candidates = [
        sys_locale.name(),  # e.g. "it_IT"
        sys_locale.name().split("_")[0],  # e.g. "it"
    ]
    available_lower = {a.lower(): a for a in available if a}
    for c in candidates:
        if c in available:
            return c
        if c.lower() in available_lower:
            return available_lower[c.lower()]
    return ""


# ── Language loader ───────────────────────────────────────────────────────────
def load_language(app: QApplication, locale: str) -> QTranslator:
    """Install a translator for *locale* ("" = English, no file needed)."""
    translator = QTranslator()
    if locale:
        translator.load(locale, resource_path("i18n"))
    app.installTranslator(translator)

    # Also load Qt's own base translations so standard buttons
    # (Yes/No/OK/Cancel/Close/…) appear in the chosen language.
    if locale:
        qt_translator = QTranslator()
        lang_short = locale.split("_")[0]  # e.g. "it" from "it_IT"

        # When running from a PyInstaller bundle, qtbase_*.qm files are
        # bundled in the "qt_translations" subfolder next to the exe.
        # In a dev environment they live in Qt's system translations path.
        search_paths = [
            resource_path("qt_translations"),
            QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
        ]
        loaded = False
        for path in search_paths:
            if qt_translator.load(f"qtbase_{locale}", path):
                loaded = True
                break
            if qt_translator.load(f"qtbase_{lang_short}", path):
                loaded = True
                break
        if loaded:
            app.installTranslator(qt_translator)

    return translator


# ── Language picker dialog ────────────────────────────────────────────────────
class LanguageDialog(QDialog):
    """Shown only when the system locale has no matching .qm or --choose-lang is passed."""

    def __init__(self, available: list[str], current_lang: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Language")
        self.setFixedWidth(280)
        self.setObjectName("LanguageDialog")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Select language:"))

        self.combo = QComboBox()
        english = [loc for loc in available if loc == ""]
        others = sorted([loc for loc in available if loc != ""], key=_display_name)
        for locale in english + others:
            self.combo.addItem(_display_name(locale), locale)

        # Pre-select current language
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == current_lang:
                self.combo.setCurrentIndex(i)
                break

        layout.addWidget(self.combo)
        self.combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        self.remember_cb = QCheckBox("Remember this choice")
        self.remember_cb.setChecked(True)
        layout.addWidget(self.remember_cb)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    @property
    def selected_locale(self) -> str:
        return self.combo.currentData()

    @property
    def remember(self) -> bool:
        return self.remember_cb.isChecked()


# ── Theme helpers ─────────────────────────────────────────────────────────────


def _build_light_palette() -> QPalette:
    """Return a QPalette that reproduces a clean light appearance."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(0xF0, 0xF0, 0xF0))
    p.setColor(QPalette.ColorRole.WindowText, QColor(0x00, 0x00, 0x00))
    p.setColor(QPalette.ColorRole.Base, QColor(0xFF, 0xFF, 0xFF))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(0xE8, 0xE8, 0xE8))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(0xFF, 0xFF, 0xDC))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(0x00, 0x00, 0x00))
    p.setColor(QPalette.ColorRole.Text, QColor(0x00, 0x00, 0x00))
    p.setColor(QPalette.ColorRole.Button, QColor(0xE0, 0xE0, 0xE0))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(0x00, 0x00, 0x00))
    p.setColor(QPalette.ColorRole.BrightText, QColor(0xFF, 0x00, 0x00))
    p.setColor(QPalette.ColorRole.Link, QColor(0x00, 0x78, 0xD7))
    p.setColor(QPalette.ColorRole.Highlight, QColor(0x00, 0x78, 0xD7))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0xFF, 0xFF, 0xFF))
    p.setColor(QPalette.ColorRole.Mid, QColor(0xA0, 0xA0, 0xA0))
    p.setColor(QPalette.ColorRole.Midlight, QColor(0xD0, 0xD0, 0xD0))
    p.setColor(QPalette.ColorRole.Dark, QColor(0x80, 0x80, 0x80))
    p.setColor(QPalette.ColorRole.Shadow, QColor(0x60, 0x60, 0x60))
    return p


def _build_dark_palette() -> QPalette:
    """Return a QPalette that reproduces a dark appearance."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(0x2B, 0x2B, 0x2B))
    p.setColor(QPalette.ColorRole.WindowText, QColor(0xF0, 0xF0, 0xF0))
    p.setColor(QPalette.ColorRole.Base, QColor(0x1E, 0x1E, 0x1E))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(0x35, 0x35, 0x35))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(0x2B, 0x2B, 0x2B))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(0xF0, 0xF0, 0xF0))
    p.setColor(QPalette.ColorRole.Text, QColor(0xF0, 0xF0, 0xF0))
    p.setColor(QPalette.ColorRole.Button, QColor(0x3C, 0x3C, 0x3C))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(0xF0, 0xF0, 0xF0))
    p.setColor(QPalette.ColorRole.BrightText, QColor(0xFF, 0x60, 0x60))
    p.setColor(QPalette.ColorRole.Link, QColor(0x4E, 0xB0, 0xFF))
    p.setColor(QPalette.ColorRole.Highlight, QColor(0x00, 0x78, 0xD7))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0xFF, 0xFF, 0xFF))
    p.setColor(QPalette.ColorRole.Mid, QColor(0x55, 0x55, 0x55))
    p.setColor(QPalette.ColorRole.Midlight, QColor(0x45, 0x45, 0x45))
    p.setColor(QPalette.ColorRole.Dark, QColor(0x18, 0x18, 0x18))
    p.setColor(QPalette.ColorRole.Shadow, QColor(0x0A, 0x0A, 0x0A))
    return p


def apply_theme(app: QApplication, mode: str) -> None:
    """Apply a colour palette according to *mode* ("system" | "light" | "dark").

    "system" leaves the palette untouched so Qt inherits the OS setting.
    "light" and "dark" force the corresponding hand-crafted palette.
    """
    if mode == "dark":
        app.setPalette(_build_dark_palette())
    elif mode == "light":
        app.setPalette(_build_light_palette())
    # "system" → do nothing; Qt already uses the system palette by default


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    app_path = Path(os.path.abspath(sys.argv[0])).parent
    settings_file_path = app_path / "settings.ini"
    settings = QSettings(str(settings_file_path), QSettings.Format.IniFormat)

    # ── Structured logging ────────────────────────────────────────────────────
    init_logging(app_path / "history.log", console=True)

    # ── Load centralized theme ────────────────────────────────────────────────
    _theme_path = resource_path(os.path.join("styles", "theme.qss"))
    try:
        with open(_theme_path, "r", encoding="utf-8") as _f:
            app.setStyleSheet(_f.read())
    except OSError:
        pass  # theme file missing — fall back to Qt defaults

    # ── Apply colour-mode (system / light / dark) ─────────────────────────────
    # Must run after setStyleSheet and before any window is created so that
    # the palette is already set when widgets compute their geometry.
    _theme_mode = settings.value("theme_mode", Config.THEME_MODE_DEFAULT)
    apply_theme(app, _theme_mode)

    # ── Determine language ────────────────────────────────────────────────────
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--lang", type=str, default=None)
    pre_parser.add_argument("--choose-lang", action="store_true")
    pre_args, _ = pre_parser.parse_known_args()

    available = _available_locales()  # ["", "it_IT", ...]
    saved_lang = settings.value("language", None)  # None = never explicitly chosen

    if pre_args.lang is not None:
        # --lang en  or  --lang it_IT  — one-shot, not saved
        chosen_locale = "" if pre_args.lang == "en" else pre_args.lang
        remember = False

    elif pre_args.choose_lang:
        # --choose-lang: always show the dialog
        dlg = LanguageDialog(available, current_lang=saved_lang or "")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            chosen_locale = dlg.selected_locale
            remember = dlg.remember
        else:
            chosen_locale = saved_lang or _autodetect_locale(available)
            remember = False

    elif saved_lang is not None:
        # User already made a choice in a previous session — honour it silently
        chosen_locale = saved_lang
        remember = False

    else:
        # First run: show dialog pre-selecting the autodetected locale
        autodetected = _autodetect_locale(available)
        dlg = LanguageDialog(available, current_lang=autodetected)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            chosen_locale = dlg.selected_locale
            remember = dlg.remember
        else:
            chosen_locale = autodetected
            remember = False

    if remember:
        settings.setValue("language", chosen_locale)

    translator = load_language(app, chosen_locale)

    # ── Single instance guard (after translator is installed) ─────────────────
    _instance_lock = ensure_single_instance(app)
    if _instance_lock is None:
        sys.exit(0)

    # ── CLI argument parsing ──────────────────────────────────────────────────
    parser = argparse.ArgumentParser(description="Desktop Icon Backup Manager CLI")
    parser.add_argument(
        "--backup",
        action="store_true",
        help=QCoreApplication.translate("CLI", "Perform a backup"),
    )
    parser.add_argument(
        "--restore",
        type=str,
        metavar="FILENAME",
        help=QCoreApplication.translate("CLI", "Restore a specific backup or latest"),
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help=QCoreApplication.translate("CLI", "Run without showing the GUI"),
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        help="Set UI language for this session (e.g. en, it_IT)",
    )
    parser.add_argument(
        "--choose-lang",
        action="store_true",
        help="Show language picker at startup",
    )

    args, unknown = parser.parse_known_args()

    if args.silent or args.backup or args.restore:
        manager = DesktopIconManager()
        app.setQuitOnLastWindowClosed(True)

        def silent_log(msg):
            prefix = QCoreApplication.translate("CLI", "[SILENT]")
            print(f"{prefix} {msg}")

        if args.backup:
            cleanup_limit = settings.value("cleanup_limit", 0, type=int)
            print(QCoreApplication.translate("CLI", "Starting silent backup..."))
            success = manager.save(
                silent_log,
                description=QCoreApplication.translate("CLI", "Silent CLI Backup"),
                max_backup_count=cleanup_limit,
            )
            sys.exit(0 if success else 1)

        elif args.restore:
            enable_scaling = settings.value(
                "adaptive_scaling_enabled", False, type=bool
            )
            filename = None
            if args.restore.lower() == "latest":
                filename = manager.get_latest_backup_filename()
                if not filename:
                    print(
                        QCoreApplication.translate(
                            "CLI", "Error: No backup files found for latest restore."
                        )
                    )
                    sys.exit(1)
            else:
                filename = args.restore

            msg_restore = QCoreApplication.translate(
                "CLI", "Starting silent restore from: %1"
            ).replace("%1", filename)
            print(msg_restore)

            success, _ = manager.restore(
                silent_log, filename=filename, enable_scaling=enable_scaling
            )
            sys.exit(0 if success else 1)

        if args.silent:
            sys.exit(0)

    # ── GUI startup ───────────────────────────────────────────────────────────
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    start_minimized = settings.value("start_minimized", False, type=bool)

    try:
        window = MainWindow()

        if start_minimized:
            window.hide()
            window.tray_icon.showMessage(
                window.tr("Desktop Icon Manager"),
                window.tr("Application started minimized to system tray."),
                QSystemTrayIcon.MessageIcon.Information,
                Config.TRAY_NOTIFICATION_DURATION,
            )
        else:
            from ui.splash_screen import SplashScreen, SPLASH_DURATION_MS

            splash = SplashScreen()
            splash.center_on_window(window)
            splash.show()
            QApplication.processEvents()

            def _show_main():
                splash.finish(window)
                window.show()

            QTimer.singleShot(SPLASH_DURATION_MS, _show_main)

        sys.exit(app.exec())
    except Exception as e:
        error_title = QCoreApplication.translate("Main", "Critical Error")
        error_msg = QCoreApplication.translate(
            "Main", "Failed to start application:\n%1"
        ).replace("%1", str(e))
        QMessageBox.critical(None, error_title, error_msg)
        sys.exit(1)
