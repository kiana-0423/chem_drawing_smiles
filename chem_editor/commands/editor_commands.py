"""Undoable editor commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand

from chem_editor.core.models import MoleculeDocument

if TYPE_CHECKING:
    from chem_editor.editor.scene import MoleculeScene


class AddAtomCommand(QUndoCommand):
    """Create an atom at a fixed position."""

    def __init__(self, scene: "MoleculeScene", position: QPointF, element: str = "C") -> None:
        super().__init__("Add Atom")
        self._scene = scene
        self._position = QPointF(position)
        self._element = element
        self._atom_id: int | None = None

    def redo(self) -> None:
        atom = self._scene.add_atom(
            position=self._position,
            element=self._element,
            preferred_atom_id=self._atom_id,
            select_created=True,
        )
        self._atom_id = atom.atom_id
        self._scene.post_status(f"Placed atom {atom.element}{atom.atom_id}.")

    def undo(self) -> None:
        if self._atom_id is None:
            return
        self._scene.remove_atom(self._atom_id)
        self._scene.post_status("Undid atom placement.")


class AddBondCommand(QUndoCommand):
    """Create a bond between two atoms, optionally creating the second atom."""

    def __init__(
        self,
        scene: "MoleculeScene",
        atom_a_id: int,
        atom_b_id: int | None = None,
        atom_b_position: QPointF | None = None,
    ) -> None:
        super().__init__("Add Bond")
        self._scene = scene
        self._atom_a_id = atom_a_id
        self._atom_b_id = atom_b_id
        self._atom_b_position = QPointF(atom_b_position) if atom_b_position is not None else None
        self._created_atom_id: int | None = None
        self._bond_id: int | None = None

    def redo(self) -> None:
        atom_b_id = self._atom_b_id
        if atom_b_id is None:
            if self._atom_b_position is None:
                raise RuntimeError("A target position is required when creating a new bonded atom.")
            new_atom = self._scene.add_atom(
                position=self._atom_b_position,
                preferred_atom_id=self._created_atom_id,
                select_created=False,
            )
            self._created_atom_id = new_atom.atom_id
            atom_b_id = new_atom.atom_id

        bond = self._scene.add_bond(
            atom_a_id=self._atom_a_id,
            atom_b_id=atom_b_id,
            preferred_bond_id=self._bond_id,
            select_created=True,
        )
        self._atom_b_id = atom_b_id
        self._bond_id = bond.bond_id
        self._scene.post_status(f"Placed bond {bond.bond_id} between atoms {bond.atom_a_id} and {bond.atom_b_id}.")

    def undo(self) -> None:
        if self._bond_id is not None:
            self._scene.remove_bond(self._bond_id)
        if self._created_atom_id is not None:
            self._scene.remove_atom(self._created_atom_id)
        self._scene.post_status("Undid bond placement.")


class DeleteSelectionCommand(QUndoCommand):
    """Delete a fragment of the current document."""

    def __init__(self, scene: "MoleculeScene", fragment: MoleculeDocument) -> None:
        super().__init__("Delete Selection")
        self._scene = scene
        self._fragment = fragment.clone()

    def redo(self) -> None:
        self._scene.delete_fragment(self._fragment)
        self._scene.post_status(
            f"Deleted {self._fragment.atom_count} atoms and {self._fragment.bond_count} bonds."
        )

    def undo(self) -> None:
        self._scene.restore_fragment(self._fragment)
        self._scene.post_status("Restored deleted selection.")


class ClearCanvasCommand(QUndoCommand):
    """Clear the editor scene while allowing undo."""

    def __init__(self, scene: "MoleculeScene", snapshot: MoleculeDocument) -> None:
        super().__init__("Clear Canvas")
        self._scene = scene
        self._snapshot = snapshot.clone()

    def redo(self) -> None:
        self._scene.load_document(MoleculeDocument())
        self._scene.post_status("Canvas cleared.")

    def undo(self) -> None:
        self._scene.load_document(self._snapshot)
        self._scene.post_status("Restored cleared canvas.")
