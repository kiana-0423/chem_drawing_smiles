"""Left-side editor tool panel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from chem_editor.editor.tools import ALL_TOOLS


class ToolPanel(QWidget):
    """Simple tool chooser for the starter editor shell."""

    tool_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._buttons: dict[str, QToolButton] = {}
        self._build_ui()

    def set_active_tool(self, tool_name: str) -> None:
        """Synchronize the selected tool button."""
        button = self._buttons.get(tool_name)
        if button is not None:
            button.setChecked(True)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Tools")
        layout.addWidget(title)

        for tool_name in ALL_TOOLS:
            button = QToolButton()
            button.setText(tool_name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=tool_name: self.tool_selected.emit(name))
            self._button_group.addButton(button)
            self._buttons[tool_name] = button
            layout.addWidget(button)

        self._buttons["Select"].setChecked(True)
        layout.addStretch(1)

        hint = QLabel("Select and delete items, place atoms, and draw simple bonds.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
