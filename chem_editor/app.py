"""Application bootstrap."""

from __future__ import annotations

import sys

from .chemistry_services.factory import create_chemistry_service


def main() -> int:
    """Start the desktop application."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise SystemExit(
            "PySide6 is required to run this app. Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    from .commands.stack import EditorCommandStack
    from .ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Chem Drawing Smiles")
    app.setOrganizationName("chem-drawing-smiles")

    chemistry_service = create_chemistry_service()
    command_stack = EditorCommandStack()
    window = MainWindow(
        chemistry_service=chemistry_service,
        command_stack=command_stack,
    )
    window.show()
    return app.exec()
