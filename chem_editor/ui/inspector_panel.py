"""Right-side inspector placeholder."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chem_editor.chemistry_services.base import ChemistryService
from chem_editor.core.models import MoleculeDocument


class InspectorPanel(QWidget):
    """Displays high-level state for the current document and backend."""

    load_smiles_requested = Signal(str)
    generate_smiles_requested = Signal()
    export_mol_requested = Signal()
    export_pdb_requested = Signal()

    def __init__(self, chemistry_service: ChemistryService, document: MoleculeDocument | None = None) -> None:
        super().__init__()
        self._document = document or MoleculeDocument()
        self._backend_value = QLabel(chemistry_service.name)
        self._backend_status_value = QLabel(chemistry_service.describe())
        self._tool_value = QLabel("Select")
        self._document_value = QLabel(self._format_document_summary(self._document))
        self._selection_value = QLabel("0 atoms, 0 bonds")
        self._smiles_input = QLineEdit()
        self._build_ui()

    def set_active_tool(self, tool_name: str) -> None:
        """Update the displayed active tool."""
        self._tool_value.setText(tool_name)

    def update_document(self, document: MoleculeDocument) -> None:
        """Update the displayed document summary."""
        self._document = document
        self._document_value.setText(self._format_document_summary(document))

    def update_selection(self, atom_count: int, bond_count: int) -> None:
        """Update the displayed selection summary."""
        self._selection_value.setText(f"{atom_count} atoms, {bond_count} bonds")

    def set_smiles_text(self, smiles: str) -> None:
        """Update the SMILES text field."""
        self._smiles_input.setText(smiles)

    def smiles_text(self) -> str:
        """Return the current SMILES input text."""
        return self._smiles_input.text()

    def _build_ui(self) -> None:
        self._backend_status_value.setWordWrap(True)
        self._document_value.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Backend:", self._backend_value)
        form.addRow("Backend status:", self._backend_status_value)
        form.addRow("Active tool:", self._tool_value)
        form.addRow("Document:", self._document_value)
        form.addRow("Selection:", self._selection_value)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addLayout(form)
        layout.addWidget(self._build_structure_io_group())
        layout.addStretch(1)

    @staticmethod
    def _format_document_summary(document: MoleculeDocument) -> str:
        return f"{document.atom_count} atoms, {document.bond_count} bonds"

    def _build_structure_io_group(self) -> QGroupBox:
        group = QGroupBox("Structure I/O")
        layout = QVBoxLayout(group)

        self._smiles_input.setPlaceholderText("Enter SMILES and press Load")
        self._smiles_input.returnPressed.connect(self._emit_load_smiles)
        layout.addWidget(QLabel("SMILES"))
        layout.addWidget(self._smiles_input)

        load_row = QHBoxLayout()
        load_button = QPushButton("Load SMILES")
        load_button.clicked.connect(self._emit_load_smiles)
        generate_button = QPushButton("Generate SMILES")
        generate_button.clicked.connect(self.generate_smiles_requested)
        load_row.addWidget(load_button)
        load_row.addWidget(generate_button)
        layout.addLayout(load_row)

        export_row = QHBoxLayout()
        export_mol_button = QPushButton("Export MOL")
        export_mol_button.clicked.connect(self.export_mol_requested)
        export_pdb_button = QPushButton("Export PDB")
        export_pdb_button.clicked.connect(self.export_pdb_requested)
        export_row.addWidget(export_mol_button)
        export_row.addWidget(export_pdb_button)
        layout.addLayout(export_row)

        hint = QLabel("SMILES import/export uses the chemistry service layer rather than editor widgets directly.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return group

    def _emit_load_smiles(self) -> None:
        self.load_smiles_requested.emit(self._smiles_input.text())
