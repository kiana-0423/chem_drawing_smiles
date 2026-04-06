"""Molecule editor scene and document mutation logic."""

from __future__ import annotations

from copy import deepcopy
from math import hypot

from PySide6.QtCore import QPointF, Signal
from PySide6.QtWidgets import QGraphicsScene

from chem_editor.commands.editor_commands import (
    AddAtomCommand,
    AddBondCommand,
    ClearCanvasCommand,
    DeleteSelectionCommand,
)
from chem_editor.commands.stack import EditorCommandStack
from chem_editor.core.models import Atom, Bond, MoleculeDocument

from .items import AtomItem, BondItem
from .tools import EditorTool

GRID_SIZE = 25.0
DEFAULT_ELEMENT = "C"
DEFAULT_BOND_LENGTH = 50.0


class MoleculeScene(QGraphicsScene):
    """Scene responsible for editor state, interactions, and undoable mutations."""

    document_changed = Signal(object)
    selection_summary_changed = Signal(int, int)
    status_message = Signal(str)

    def __init__(self, command_stack: EditorCommandStack) -> None:
        super().__init__()
        self._command_stack = command_stack
        self._document = MoleculeDocument()
        self._active_tool = EditorTool.SELECT
        self._pending_bond_atom_id: int | None = None
        self._atom_items: dict[int, AtomItem] = {}
        self._bond_items: dict[int, BondItem] = {}
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def active_tool(self) -> str:
        """Return the active editor tool label."""
        return self._active_tool.value

    def set_active_tool(self, tool_name: str) -> None:
        """Switch the active editor tool."""
        self._active_tool = EditorTool(tool_name)
        if self._active_tool is not EditorTool.BOND:
            self._pending_bond_atom_id = None

    def document_snapshot(self) -> MoleculeDocument:
        """Return a detached snapshot of the document."""
        return self._document.clone()

    def is_empty(self) -> bool:
        """Return whether the scene currently has any chemistry items."""
        return self._document.atom_count == 0 and self._document.bond_count == 0

    def post_status(self, message: str) -> None:
        """Emit an editor status message."""
        self.status_message.emit(message)

    def handle_primary_click(self, scene_pos: QPointF) -> bool:
        """Process a left-click according to the active tool."""
        if self._active_tool is EditorTool.SELECT:
            return False

        if self._active_tool is EditorTool.ATOM:
            if self._atom_item_at(scene_pos) is not None:
                self.post_status("Click empty space to place a new atom.")
                return True
            snapped = self.snap_to_grid(scene_pos)
            self._command_stack.push(AddAtomCommand(self, snapped, element=DEFAULT_ELEMENT))
            return True

        if self._active_tool is EditorTool.BOND:
            self._handle_bond_click(scene_pos)
            return True

        if self._active_tool is EditorTool.DELETE:
            target_item = self._pick_deletable_item(scene_pos)
            if target_item is None:
                self.post_status("Nothing to delete at this position.")
                return True
            self.clearSelection()
            target_item.setSelected(True)
            self.delete_selected()
            return True

        return False

    def delete_selected(self) -> None:
        """Delete the currently selected atoms and bonds."""
        atom_ids, bond_ids = self.selected_ids()
        if not atom_ids and not bond_ids:
            self.post_status("Nothing selected to delete.")
            return

        fragment = self.capture_fragment(atom_ids, bond_ids)
        self._command_stack.push(DeleteSelectionCommand(self, fragment))

    def clear_document(self) -> None:
        """Clear the full canvas with undo support."""
        if self.is_empty():
            self.post_status("Canvas is already empty.")
            return
        self._command_stack.push(ClearCanvasCommand(self, self.document_snapshot()))

    def add_atom(
        self,
        position: QPointF,
        element: str = DEFAULT_ELEMENT,
        preferred_atom_id: int | None = None,
        select_created: bool = False,
    ) -> Atom:
        """Create an atom in the document and scene."""
        snapped = self.snap_to_grid(position)
        atom = Atom(
            atom_id=self._document.allocate_atom_id(preferred_atom_id),
            element=element,
            x=snapped.x(),
            y=snapped.y(),
        )
        self._document.add_atom(atom)
        atom_item = AtomItem(atom)
        self.addItem(atom_item)
        self._atom_items[atom.atom_id] = atom_item

        if select_created:
            self.clearSelection()
            atom_item.setSelected(True)

        self._emit_document_changed()
        return atom

    def add_bond(
        self,
        atom_a_id: int,
        atom_b_id: int,
        preferred_bond_id: int | None = None,
        select_created: bool = False,
    ) -> Bond:
        """Create a bond between two existing atoms."""
        atom_a = self._document.get_atom(atom_a_id)
        atom_b = self._document.get_atom(atom_b_id)
        if atom_a is None or atom_b is None:
            raise RuntimeError("Cannot create a bond without two atoms.")
        if self._document.has_bond_between(atom_a_id, atom_b_id):
            raise RuntimeError("A bond between these atoms already exists.")

        bond = Bond(
            bond_id=self._document.allocate_bond_id(preferred_bond_id),
            atom_a_id=atom_a_id,
            atom_b_id=atom_b_id,
        )
        self._document.add_bond(bond)
        bond_item = BondItem(
            bond=bond,
            start_point=QPointF(atom_a.x, atom_a.y),
            end_point=QPointF(atom_b.x, atom_b.y),
        )
        self.addItem(bond_item)
        self._bond_items[bond.bond_id] = bond_item

        if select_created:
            self.clearSelection()
            bond_item.setSelected(True)

        self._emit_document_changed()
        return bond

    def remove_atom(self, atom_id: int) -> Atom | None:
        """Remove an atom item and its domain record."""
        atom_item = self._atom_items.pop(atom_id, None)
        if atom_item is not None:
            self.removeItem(atom_item)
        atom = self._document.remove_atom(atom_id)
        if self._pending_bond_atom_id == atom_id:
            self._pending_bond_atom_id = None
        self._emit_document_changed()
        return atom

    def remove_bond(self, bond_id: int) -> Bond | None:
        """Remove a bond item and its domain record."""
        bond_item = self._bond_items.pop(bond_id, None)
        if bond_item is not None:
            self.removeItem(bond_item)
        bond = self._document.remove_bond(bond_id)
        self._emit_document_changed()
        return bond

    def load_document(self, document: MoleculeDocument) -> None:
        """Replace the current document and rebuild the scene."""
        self._pending_bond_atom_id = None
        self.clearSelection()
        super().clear()
        self._atom_items.clear()
        self._bond_items.clear()
        self._document = document.clone()

        for atom in sorted(self._document.atoms.values(), key=lambda item: item.atom_id):
            atom_item = AtomItem(atom)
            self.addItem(atom_item)
            self._atom_items[atom.atom_id] = atom_item

        for bond in sorted(self._document.bonds.values(), key=lambda item: item.bond_id):
            atom_a = self._document.get_atom(bond.atom_a_id)
            atom_b = self._document.get_atom(bond.atom_b_id)
            if atom_a is None or atom_b is None:
                continue
            bond_item = BondItem(
                bond=bond,
                start_point=QPointF(atom_a.x, atom_a.y),
                end_point=QPointF(atom_b.x, atom_b.y),
            )
            self.addItem(bond_item)
            self._bond_items[bond.bond_id] = bond_item

        self._emit_document_changed()

    def capture_fragment(self, atom_ids: list[int], bond_ids: list[int]) -> MoleculeDocument:
        """Capture a restorable fragment for deletion commands."""
        fragment = MoleculeDocument(
            next_atom_id=self._document.next_atom_id,
            next_bond_id=self._document.next_bond_id,
        )

        expanded_atom_ids = {atom_id for atom_id in atom_ids if self._document.get_atom(atom_id) is not None}
        expanded_bond_ids = {bond_id for bond_id in bond_ids if self._document.get_bond(bond_id) is not None}

        for atom_id in expanded_atom_ids:
            expanded_bond_ids.update(self._document.bond_ids_for_atom(atom_id))

        for atom_id in sorted(expanded_atom_ids):
            atom = self._document.get_atom(atom_id)
            if atom is not None:
                fragment.add_atom(deepcopy(atom))

        for bond_id in sorted(expanded_bond_ids):
            bond = self._document.get_bond(bond_id)
            if bond is not None:
                fragment.add_bond(deepcopy(bond))

        return fragment

    def delete_fragment(self, fragment: MoleculeDocument) -> None:
        """Delete a previously captured fragment from the scene."""
        if self._pending_bond_atom_id in fragment.atoms:
            self._pending_bond_atom_id = None

        for bond_id in list(fragment.bonds):
            self.remove_bond(bond_id)
        for atom_id in list(fragment.atoms):
            self.remove_atom(atom_id)

        self.clearSelection()
        self._emit_document_changed()

    def restore_fragment(self, fragment: MoleculeDocument) -> None:
        """Restore a previously deleted fragment."""
        for atom in sorted(fragment.atoms.values(), key=lambda item: item.atom_id):
            self.add_atom(
                position=QPointF(atom.x, atom.y),
                element=atom.element,
                preferred_atom_id=atom.atom_id,
                select_created=False,
            )

        for bond in sorted(fragment.bonds.values(), key=lambda item: item.bond_id):
            self.add_bond(
                atom_a_id=bond.atom_a_id,
                atom_b_id=bond.atom_b_id,
                preferred_bond_id=bond.bond_id,
                select_created=False,
            )

        self._emit_document_changed()

    def selected_ids(self) -> tuple[list[int], list[int]]:
        """Return the currently selected atom and bond identifiers."""
        atom_ids: list[int] = []
        bond_ids: list[int] = []

        for item in self.selectedItems():
            if isinstance(item, AtomItem):
                atom_ids.append(item.atom_id)
            elif isinstance(item, BondItem):
                bond_ids.append(item.bond_id)

        return atom_ids, bond_ids

    def snap_to_grid(self, point: QPointF) -> QPointF:
        """Snap a point to the editor grid."""
        return QPointF(
            round(point.x() / GRID_SIZE) * GRID_SIZE,
            round(point.y() / GRID_SIZE) * GRID_SIZE,
        )

    def _handle_bond_click(self, scene_pos: QPointF) -> None:
        atom_item = self._atom_item_at(scene_pos)
        if self._pending_bond_atom_id is None:
            if atom_item is None:
                self.post_status("Click an existing atom to start a bond.")
                return

            self._pending_bond_atom_id = atom_item.atom_id
            self.clearSelection()
            atom_item.setSelected(True)
            self.post_status(f"Bond start set to atom {atom_item.atom_id}.")
            return

        start_atom_id = self._pending_bond_atom_id
        if atom_item is not None:
            if atom_item.atom_id == start_atom_id:
                self.post_status("Choose a different atom for the bond target.")
                return
            if self._document.has_bond_between(start_atom_id, atom_item.atom_id):
                self.post_status("A bond between these atoms already exists.")
                return

            self._command_stack.push(AddBondCommand(self, atom_a_id=start_atom_id, atom_b_id=atom_item.atom_id))
            self._pending_bond_atom_id = None
            return

        target_position = self._resolve_bond_target_position(start_atom_id, scene_pos)
        self._command_stack.push(
            AddBondCommand(
                self,
                atom_a_id=start_atom_id,
                atom_b_id=None,
                atom_b_position=target_position,
            )
        )
        self._pending_bond_atom_id = None

    def _resolve_bond_target_position(self, atom_id: int, scene_pos: QPointF) -> QPointF:
        """Resolve the location for a newly created atom during bond placement."""
        snapped = self.snap_to_grid(scene_pos)
        anchor = self._document.get_atom(atom_id)
        if anchor is None:
            return snapped

        if hypot(anchor.x - snapped.x(), anchor.y - snapped.y()) < GRID_SIZE / 2:
            return QPointF(anchor.x + DEFAULT_BOND_LENGTH, anchor.y)
        return snapped

    def _atom_item_at(self, scene_pos: QPointF) -> AtomItem | None:
        for item in self.items(scene_pos):
            if isinstance(item, AtomItem):
                return item
        return None

    def _pick_deletable_item(self, scene_pos: QPointF) -> AtomItem | BondItem | None:
        for item in self.items(scene_pos):
            if isinstance(item, (AtomItem, BondItem)):
                return item
        return None

    def _emit_document_changed(self) -> None:
        self._refresh_item_styles()
        self.document_changed.emit(self._document.clone())
        atom_ids, bond_ids = self.selected_ids()
        self.selection_summary_changed.emit(len(atom_ids), len(bond_ids))

    def _on_selection_changed(self) -> None:
        self._refresh_item_styles()
        atom_ids, bond_ids = self.selected_ids()
        self.selection_summary_changed.emit(len(atom_ids), len(bond_ids))

    def _refresh_item_styles(self) -> None:
        for atom_item in self._atom_items.values():
            atom_item.update_style()
        for bond_item in self._bond_items.values():
            bond_item.update_style()
