"""Auto-Hide Desktop Icons timer logic."""

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QDialogButtonBox,
    QSystemTrayIcon,
)

from utils.threads import IconWorker

# Tray notifications are emitted when the remaining time crosses these values.
NOTIFY_THRESHOLDS = (60, 10)


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
        # Always start the countdown on manual enable — the user's intent is
        # clear. The actual hide action still checks icon visibility when it
        # fires, so this is safe even if icons are currently hidden.
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
    window._autohide_total_sec = total_sec
    window._autohide_notified = set()
    window.autohide_timer.start(total_sec * 1000)
    window.autohide_tick_timer.start()
    update_tray_autohide_tooltip(window)
    update_statusbar_countdown(window)


def stop_autohide_timer(window):
    """Stop the auto-hide countdown and reset the tray tooltip."""
    window.autohide_timer.stop()
    window.autohide_tick_timer.stop()
    window._autohide_remaining_sec = 0
    window._autohide_total_sec = 0
    window._autohide_notified = set()
    update_tray_autohide_tooltip(window)
    update_statusbar_countdown(window)


def on_autohide_tick(window):
    """Called every second to update the countdown indicators."""
    if window._autohide_remaining_sec > 0:
        window._autohide_remaining_sec -= 1
    update_tray_autohide_tooltip(window)
    update_statusbar_countdown(window)
    maybe_notify_threshold(window)


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


def update_statusbar_countdown(window):
    """Refresh the countdown row in the main window.

    Three possible states, in priority order:
      1. Timer running               -> label + progress bar + stop button
      2. Enabled but icons hidden    -> "Auto-Hide armed" hint + stop button
      3. Disabled or not applicable  -> row hidden
    """
    frame = getattr(window, "autohide_status_frame", None)
    label = getattr(window, "autohide_status_label", None)
    bar = getattr(window, "autohide_status_bar", None)
    stop_btn = getattr(window, "autohide_status_stop_btn", None)
    if frame is None or label is None or bar is None:
        return

    enabled = window.settings.value("autohide_enabled", False, type=bool)
    if not enabled:
        frame.setVisible(False)
        return

    remaining = getattr(window, "_autohide_remaining_sec", 0)
    total = getattr(window, "_autohide_total_sec", 0) or 0

    # Case 1 — timer currently running
    if remaining > 0 and total > 0:
        mins, secs = divmod(remaining, 60)
        text = QCoreApplication.translate("MainWindow", "⏱ Auto-Hide in %1").replace(
            "%1", f"{mins}:{secs:02d}"
        )
        label.setText(text)
        bar.setMaximum(total)
        bar.setValue(remaining)
        bar.setVisible(True)
        if stop_btn is not None:
            stop_btn.setVisible(True)
        frame.setVisible(True)
        return

    # Case 2 — enabled but the timer is not ticking (e.g. initial state at
    # startup if the feature was persisted as enabled). Show an "armed" hint.
    configured = window.settings.value("autohide_seconds", 300, type=int)
    text = QCoreApplication.translate("MainWindow", "⏱ Auto-Hide armed (%1)").replace(
        "%1", format_duration(window, configured)
    )
    label.setText(text)
    bar.setVisible(False)
    if stop_btn is not None:
        stop_btn.setVisible(True)
    frame.setVisible(True)


def maybe_notify_threshold(window):
    """Emit a tray balloon when the remaining time crosses a threshold.

    Each threshold fires at most once per timer cycle (the bookkeeping
    set is reset in ``start_autohide_timer``).
    """
    if not window.settings.value("autohide_notify_enabled", True, type=bool):
        return
    if not window.settings.value("autohide_enabled", False, type=bool):
        return
    if not window.visibility_manager.get_current_visibility_state():
        return

    tray = getattr(window, "tray_icon", None)
    if tray is None:
        return

    notified = getattr(window, "_autohide_notified", None)
    if notified is None:
        notified = set()
        window._autohide_notified = notified

    remaining = window._autohide_remaining_sec
    for threshold in NOTIFY_THRESHOLDS:
        if remaining == threshold and threshold not in notified:
            notified.add(threshold)
            mins, secs = divmod(threshold, 60)
            when = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"
            title = QCoreApplication.translate("MainWindow", "Auto-Hide")
            message = QCoreApplication.translate(
                "MainWindow", "Desktop icons will be hidden in %1."
            ).replace("%1", when)
            try:
                tray.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    4000,
                )
            except Exception:
                # Tray messages are best-effort; never block the tick.
                pass


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
    update_statusbar_countdown(window)


def restart_autohide_if_icons_visible(window):
    """Convenience: restart the auto-hide timer when icons become visible."""
    if window.settings.value("autohide_enabled", False, type=bool):
        if window.visibility_manager.get_current_visibility_state():
            start_autohide_timer(window)
        else:
            stop_autohide_timer(window)
