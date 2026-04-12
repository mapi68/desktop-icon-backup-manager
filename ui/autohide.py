"""Auto-Hide Desktop Icons timer logic."""

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QDialogButtonBox,
)

from utils.threads import IconWorker


def toggle_autohide(window, checked: bool):
    """Enable or disable the auto-hide timer."""
    window.settings.setValue("autohide_enabled", checked)
    # Keep both menu and tray checkmarks in sync
    window.action_autohide_enabled.setChecked(checked)
    window.action_tray_autohide.setChecked(checked)
    if checked:
        total_sec = window.settings.value("autohide_seconds", 300, type=int)
        window.log(
            QCoreApplication.translate(
                "MainWindow", "Auto-Hide enabled: icons will be hidden after %1."
            ).replace("%1", format_duration(window, total_sec))
        )
        # Start only if icons are currently visible
        if window.visibility_manager.get_current_visibility_state():
            start_autohide_timer(window)
    else:
        stop_autohide_timer(window)
        window.log(QCoreApplication.translate("MainWindow", "Auto-Hide disabled."))


def set_autohide_seconds(window, seconds: int):
    """Change the auto-hide interval (in seconds)."""
    window.settings.setValue("autohide_seconds", seconds)
    update_autohide_time_menu_check(window, seconds)
    window.log(
        QCoreApplication.translate(
            "MainWindow", "Auto-Hide interval set to %1."
        ).replace("%1", format_duration(window, seconds))
    )
    # Restart the timer if auto-hide is active
    if window.settings.value("autohide_enabled", False, type=bool):
        if window.visibility_manager.get_current_visibility_state():
            start_autohide_timer(window)


def update_autohide_time_menu_check(window, current_seconds: int):
    """Update checkmarks in the auto-hide interval submenu."""
    is_preset = False
    for seconds, action in window.autohide_time_actions.items():
        matched = seconds == current_seconds
        action.setChecked(matched)
        if matched:
            is_preset = True
    # If no preset matched, the value is custom
    window.action_autohide_custom.setChecked(not is_preset)
    if not is_preset:
        window.action_autohide_custom.setText(
            QCoreApplication.translate("MainWindow", "Custom (%1)").replace(
                "%1", format_duration(window, current_seconds)
            )
        )
    else:
        window.action_autohide_custom.setText(
            QCoreApplication.translate("MainWindow", "Custom...")
        )


def ask_custom_autohide_time(window):
    """Show a dialog with minutes + seconds spin boxes for custom interval."""
    current = window.settings.value("autohide_seconds", 300, type=int)
    cur_m, cur_s = divmod(current, 60)

    dlg = QDialog(window)
    dlg.setWindowTitle(
        QCoreApplication.translate("MainWindow", "Custom Auto-Hide Interval")
    )
    dlg.setFixedWidth(320)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)
    layout.setContentsMargins(20, 20, 20, 20)

    layout.addWidget(
        QLabel(QCoreApplication.translate("MainWindow", "Hide desktop icons after:"))
    )

    row = QHBoxLayout()

    spin_min = QSpinBox()
    spin_min.setRange(0, 60)
    spin_min.setValue(cur_m)
    spin_min.setSuffix(f"  {QCoreApplication.translate("MainWindow", 'minutes')}")
    spin_min.setMinimumWidth(110)
    row.addWidget(spin_min)

    spin_sec = QSpinBox()
    spin_sec.setRange(0, 59)
    spin_sec.setValue(cur_s)
    spin_sec.setSuffix(f"  {QCoreApplication.translate("MainWindow", 'seconds')}")
    spin_sec.setMinimumWidth(90)
    row.addWidget(spin_sec)

    layout.addLayout(row)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        total = spin_min.value() * 60 + spin_sec.value()
        if total < 10:
            total = 10  # minimum 10 seconds
        set_autohide_seconds(window, total)


def format_duration(window, seconds: int) -> str:
    """Format seconds as translatable 'X minutes Y seconds' etc."""
    m, s = divmod(seconds, 60)
    if m and s:
        return (
            QCoreApplication.translate("MainWindow", "%n minute(s)", "duration", m)
            + " "
            + QCoreApplication.translate("MainWindow", "%n second(s)", "duration", s)
        )
    elif m:
        return QCoreApplication.translate("MainWindow", "%n minute(s)", "duration", m)
    else:
        return QCoreApplication.translate("MainWindow", "%n second(s)", "duration", s)


def start_autohide_timer(window):
    """Start (or restart) the auto-hide countdown."""
    if not window.settings.value("autohide_enabled", False, type=bool):
        return
    total_sec = window.settings.value("autohide_seconds", 300, type=int)
    window._autohide_remaining_sec = total_sec
    window.autohide_timer.start(total_sec * 1000)
    window.autohide_tick_timer.start()
    update_tray_autohide_tooltip(window)


def stop_autohide_timer(window):
    """Stop the auto-hide countdown and reset the tray tooltip."""
    window.autohide_timer.stop()
    window.autohide_tick_timer.stop()
    window._autohide_remaining_sec = 0
    update_tray_autohide_tooltip(window)


def on_autohide_tick(window):
    """Called every second to update the countdown tooltip."""
    if window._autohide_remaining_sec > 0:
        window._autohide_remaining_sec -= 1
    update_tray_autohide_tooltip(window)


def update_tray_autohide_tooltip(window):
    """Update the tray icon tooltip with auto-hide status."""
    base = "Desktop Icon Backup Manager"
    if not window.settings.value("autohide_enabled", False, type=bool):
        window.tray_icon.setToolTip(base)
        return

    is_visible = window.visibility_manager.get_current_visibility_state()
    if not is_visible:
        window.tray_icon.setToolTip(
            f"{base}\n{QCoreApplication.translate("MainWindow", 'Desktop icons are hidden')}"
        )
        return

    remaining = window._autohide_remaining_sec
    if remaining > 0:
        mins, secs = divmod(remaining, 60)
        window.tray_icon.setToolTip(
            f"{base}\n{QCoreApplication.translate("MainWindow", 'Auto-Hide in %1').replace('%1', f'{mins}:{secs:02d}')}"
        )
    else:
        window.tray_icon.setToolTip(base)


def on_autohide_timeout(window):
    """Called when the auto-hide timer expires — hide the desktop icons."""
    window.autohide_tick_timer.stop()
    window._autohide_remaining_sec = 0

    # Optional backup before hiding — run asynchronously via IconWorker
    if window.settings.value("autohide_backup_before_hide", True, type=bool):
        window.log(
            QCoreApplication.translate(
                "MainWindow", "Auto-Hide: creating backup before hiding icons..."
            )
        )
        cleanup_limit = window.settings.value("cleanup_limit", 0, type=int)
        window._autohide_worker = IconWorker(
            "save",
            description=QCoreApplication.translate("MainWindow", "Auto-Hide Backup"),
            max_backup_count=cleanup_limit,
            manager=window.manager,
        )
        window._autohide_worker.log_signal.connect(lambda msg: window.log(f"  {msg}"))
        window._autohide_worker.finished_signal.connect(
            lambda ok, meta: on_autohide_backup_done(window, ok, meta)
        )
        window._autohide_worker.start()
    else:
        do_autohide_icons(window)


def on_autohide_backup_done(window, success: bool, metadata):
    """Called when the pre-autohide backup finishes."""
    window._autohide_worker = None
    do_autohide_icons(window)


def do_autohide_icons(window):
    """Actually hide the desktop icons (called after optional backup)."""
    window.log(
        QCoreApplication.translate("MainWindow", "Auto-Hide: hiding desktop icons now.")
    )
    window.visibility_manager.hide_icons(window.log)
    update_tray_autohide_tooltip(window)


def restart_autohide_if_icons_visible(window):
    """Convenience: restart the auto-hide timer when icons become visible."""
    if window.settings.value("autohide_enabled", False, type=bool):
        if window.visibility_manager.get_current_visibility_state():
            start_autohide_timer(window)
        else:
            stop_autohide_timer(window)
