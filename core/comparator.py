"""BackupComparator - moved from icon_manager.py into its own module"""

import json
import logging
from typing import Optional

from PyQt6.QtCore import QCoreApplication

logger = logging.getLogger("dibm")


class BackupComparator:
    """Compare two backup files to find differences"""

    @staticmethod
    def compare(file1_path: str, file2_path: str) -> Optional[str]:
        """Compare two backup files and return a coloured-text report, or None on error."""
        try:
            with open(file1_path, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            icons1 = data1.get("icons", data1) if isinstance(data1, dict) else data1

            with open(file2_path, "r", encoding="utf-8") as f:
                data2 = json.load(f)
            icons2 = data2.get("icons", data2) if isinstance(data2, dict) else data2

            names1 = set(icons1.keys())
            names2 = set(icons2.keys())

            added = names2 - names1
            removed = names1 - names2
            moved = [name for name in names1 & names2 if icons1[name] != icons2[name]]

            num_added = len(added)
            num_removed = len(removed)
            num_moved = len(moved)
            num_unchanged = len(names1 & names2) - len(moved)

            report = (
                QCoreApplication.translate(
                    "BackupComparator", "=== COMPARISON RESULTS ==="
                )
                + "\n\n"
            )
            report += (
                QCoreApplication.translate(
                    "BackupComparator", "Icon(s) Added: %n", None, num_added
                )
                + "\n"
            )
            report += (
                QCoreApplication.translate(
                    "BackupComparator", "Icon(s) Removed: %n", None, num_removed
                )
                + "\n"
            )
            report += (
                QCoreApplication.translate(
                    "BackupComparator", "Icon(s) Moved: %n", None, num_moved
                )
                + "\n"
            )
            report += (
                QCoreApplication.translate(
                    "BackupComparator", "Icon(s) Unchanged: %n", None, num_unchanged
                )
                + "\n\n"
            )

            if added:
                report += (
                    QCoreApplication.translate(
                        "BackupComparator", "--- ADDED ICONS ---"
                    )
                    + "\n"
                )
                for name in sorted(added):
                    report += f"  + {name}\n"
                report += "\n"

            if removed:
                report += (
                    QCoreApplication.translate(
                        "BackupComparator", "--- REMOVED ICONS ---"
                    )
                    + "\n"
                )
                for name in sorted(removed):
                    report += f"  - {name}\n"
                report += "\n"

            if moved:
                report += (
                    QCoreApplication.translate(
                        "BackupComparator", "--- MOVED ICONS ---"
                    )
                    + "\n"
                )
                for name in sorted(moved):
                    report += f"  ↔ {name}\n"

            if not added and not removed and not moved:
                report += (
                    QCoreApplication.translate(
                        "BackupComparator",
                        "✓ No differences - backups are identical!",
                    )
                    + "\n"
                )

            return report

        except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("BackupComparator.compare failed: %s", e)
            return None
