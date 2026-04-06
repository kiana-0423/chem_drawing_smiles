"""Main application window."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QFileDialog, QDockWidget, QInputDialog, QMainWindow, QMessageBox, QToolBar

from chem_editor.chemistry_services import ChemistryServiceError
from chem_editor.chemistry_services.base import ChemistryService
from chem_editor.commands.stack import EditorCommandStack
from chem_editor.core.models import MoleculeDocument
from chem_editor.editor import ALL_TOOLS, EditorCanvas

from .inspector_panel import InspectorPanel
from .status_panel import StatusPanel
from .tool_panel import ToolPanel


class MainWindow(QMainWindow):
    """Top-level desktop shell for the native editor scaffold."""

    def __init__(self, chemistry_service: ChemistryService, command_stack: EditorCommandStack) -> None:
        super().__init__()
        self._chemistry_service = chemistry_service
        self._command_stack = command_stack
        self._document = MoleculeDocument()
        self._canvas = EditorCanvas(command_stack=command_stack)
        self._tool_panel = ToolPanel()
        self._inspector_panel = InspectorPanel(chemistry_service=chemistry_service, document=self._document)
        self._status_panel = StatusPanel()
        self._tool_actions: dict[str, QAction] = {}
        self._build_window()
        self._connect_signals()
        self._log_startup()

    def _build_window(self) -> None:
        self.setWindowTitle("Chem Drawing Smiles")
        self.resize(1280, 840)
        self.setCentralWidget(self._canvas)
        self._build_docks()
        self._build_menu_bar()
        self._build_toolbar()
        self.statusBar().showMessage("Application ready.")

    def _build_docks(self) -> None:
        left_dock = QDockWidget("Tools", self)
        left_dock.setWidget(self._tool_panel)
        left_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        right_dock = QDockWidget("Inspector", self)
        right_dock.setWidget(self._inspector_panel)
        right_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        bottom_dock = QDockWidget("Status", self)
        bottom_dock.setWidget(self._status_panel)
        bottom_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        clear_action = QAction("Clear Canvas", self)
        clear_action.triggered.connect(self._canvas.clear_canvas)
        file_menu.addAction(clear_action)
        file_menu.addSeparator()

        export_mol_action = QAction("Export MOL...", self)
        export_mol_action.triggered.connect(self._export_mol)
        file_menu.addAction(export_mol_action)

        export_pdb_action = QAction("Export PDB...", self)
        export_pdb_action.triggered.connect(self._export_pdb)
        file_menu.addAction(export_pdb_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        undo_action = self._command_stack.create_undo_action(self, "Undo")
        redo_action = self._command_stack.create_redo_action(self, "Redo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()

        delete_action = QAction("Delete Selected", self)
        delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        delete_action.triggered.connect(self._canvas.delete_selected)
        edit_menu.addAction(delete_action)

        view_menu = self.menuBar().addMenu("&View")
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._canvas.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._canvas.zoom_out)
        view_menu.addAction(zoom_out_action)

        tool_menu = self.menuBar().addMenu("&Tools")
        for tool_name in ALL_TOOLS:
            action = QAction(tool_name, self)
            action.triggered.connect(lambda checked=False, name=tool_name: self._set_active_tool(name))
            tool_menu.addAction(action)

        chemistry_menu = self.menuBar().addMenu("&Chemistry")
        import_smiles_action = QAction("Import From SMILES...", self)
        import_smiles_action.triggered.connect(self._prompt_and_load_smiles)
        chemistry_menu.addAction(import_smiles_action)

        generate_smiles_action = QAction("Generate SMILES", self)
        generate_smiles_action.triggered.connect(self._generate_smiles)
        chemistry_menu.addAction(generate_smiles_action)

        chemistry_menu.addSeparator()

        export_sdf_action = QAction("Export SDF...", self)
        export_sdf_action.triggered.connect(self._export_sdf)
        chemistry_menu.addAction(export_sdf_action)

        backend_action = QAction("Backend Status", self)
        backend_action.triggered.connect(self._show_backend_status)
        chemistry_menu.addAction(backend_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        for tool_name in ALL_TOOLS:
            action = QAction(tool_name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=tool_name: self._set_active_tool(name))
            toolbar.addAction(action)
            tool_group.addAction(action)
            self._tool_actions[tool_name] = action

        self._tool_actions["Select"].setChecked(True)
        toolbar.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._canvas.delete_selected)
        toolbar.addAction(delete_action)

        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._canvas.clear_canvas)
        toolbar.addAction(clear_action)

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self._canvas.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self._canvas.zoom_out)
        toolbar.addAction(zoom_out_action)

        backend_action = QAction("Backend", self)
        backend_action.triggered.connect(self._show_backend_status)
        toolbar.addAction(backend_action)

    def _connect_signals(self) -> None:
        self._tool_panel.tool_selected.connect(self._set_active_tool)
        self._canvas.status_message.connect(self._handle_status_message)
        self._canvas.document_changed.connect(self._handle_document_changed)
        self._canvas.selection_summary_changed.connect(self._inspector_panel.update_selection)
        self._inspector_panel.load_smiles_requested.connect(self._load_smiles)
        self._inspector_panel.generate_smiles_requested.connect(self._generate_smiles)
        self._inspector_panel.export_mol_requested.connect(self._export_mol)
        self._inspector_panel.export_pdb_requested.connect(self._export_pdb)

    def _set_active_tool(self, tool_name: str) -> None:
        self._tool_panel.set_active_tool(tool_name)
        self._canvas.set_active_tool(tool_name)
        self._inspector_panel.set_active_tool(tool_name)
        action = self._tool_actions.get(tool_name)
        if action is not None:
            action.setChecked(True)

    def _handle_status_message(self, message: str) -> None:
        self.statusBar().showMessage(message, 3000)
        self._status_panel.append_message(message)

    def _handle_document_changed(self, document: MoleculeDocument) -> None:
        self._document = document
        self._inspector_panel.update_document(document)

    def _show_backend_status(self) -> None:
        QMessageBox.information(
            self,
            "Chemistry Backend",
            self._chemistry_service.describe(),
        )

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Chem Drawing Smiles\n\nNative Python scaffold for a future chemical structure editor.",
        )

    def _log_startup(self) -> None:
        self._status_panel.append_message("Starter editor window initialized.")
        self._status_panel.append_message(
            "Available MVP tools: selection, atom placement, bond placement, delete, clear, zoom, undo/redo."
        )
        self._status_panel.append_message(self._chemistry_service.describe())

    def _prompt_and_load_smiles(self) -> None:
        smiles, accepted = QInputDialog.getText(
            self,
            "Import From SMILES",
            "SMILES:",
            text=self._inspector_panel.smiles_text(),
        )
        if not accepted:
            return
        self._inspector_panel.set_smiles_text(smiles)
        self._load_smiles(smiles)

    def _load_smiles(self, smiles: str) -> None:
        try:
            document = self._chemistry_service.import_smiles(smiles)
            canonical_smiles = self._chemistry_service.export_smiles(document)
        except ChemistryServiceError as exc:
            self._show_chemistry_error("SMILES Import Failed", str(exc))
            return

        self._command_stack.clear()
        self._canvas.load_document(document, fit_view=True)
        self._inspector_panel.set_smiles_text(canonical_smiles)
        self._handle_status_message(
            f"Loaded structure from SMILES with {document.atom_count} atoms and {document.bond_count} bonds."
        )

    def _generate_smiles(self) -> None:
        try:
            smiles = self._chemistry_service.export_smiles(self._document)
        except ChemistryServiceError as exc:
            self._show_chemistry_error("SMILES Export Failed", str(exc))
            return

        self._inspector_panel.set_smiles_text(smiles)
        self._handle_status_message("Generated canonical SMILES from the current drawing.")
        self._status_panel.append_message(f"SMILES: {smiles}")

    def _export_mol(self) -> None:
        self._save_chemistry_export(
            title="Export MOL",
            default_suffix=".mol",
            file_filter="MDL Mol (*.mol);;All Files (*)",
            exporter=lambda molecule_name: self._chemistry_service.export_mol(
                self._document,
                molecule_name=molecule_name,
            ),
        )

    def _export_sdf(self) -> None:
        self._save_chemistry_export(
            title="Export SDF",
            default_suffix=".sdf",
            file_filter="Structure Data File (*.sdf);;All Files (*)",
            exporter=lambda molecule_name: self._chemistry_service.export_sdf(
                self._document,
                molecule_name=molecule_name,
            ),
        )

    def _export_pdb(self) -> None:
        self._save_chemistry_export(
            title="Export PDB",
            default_suffix=".pdb",
            file_filter="Protein Data Bank (*.pdb);;All Files (*)",
            exporter=lambda molecule_name: self._chemistry_service.export_pdb(
                self._document,
                molecule_name=molecule_name,
            ),
        )

    def _save_chemistry_export(
        self,
        *,
        title: str,
        default_suffix: str,
        file_filter: str,
        exporter: Callable[[str], str],
    ) -> None:
        if self._document.atom_count == 0:
            self._show_chemistry_error(f"{title} Failed", "The current drawing is empty.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            f"structure{default_suffix}",
            file_filter,
        )
        if not file_path:
            return

        output_path = Path(file_path)
        if not output_path.suffix:
            output_path = output_path.with_suffix(default_suffix)

        try:
            exported_text = exporter(output_path.stem)
            output_path.write_text(exported_text, encoding="utf-8")
        except ChemistryServiceError as exc:
            self._show_chemistry_error(f"{title} Failed", str(exc))
            return
        except OSError as exc:
            QMessageBox.warning(self, f"{title} Failed", f"Could not write the file:\n{exc}")
            return

        self._handle_status_message(f"Exported structure to {output_path.name}.")

    def _show_chemistry_error(self, title: str, message: str) -> None:
        self._handle_status_message(message)
        QMessageBox.warning(self, title, message)
