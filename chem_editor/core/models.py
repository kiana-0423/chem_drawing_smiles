"""Domain models for the editor document."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field


@dataclass(slots=True)
class Atom:
    """A minimal atom record for future editor and chemistry integration."""

    atom_id: int
    element: str
    x: float
    y: float
    formal_charge: int = 0


@dataclass(slots=True)
class Bond:
    """A minimal bond record for future editor and chemistry integration."""

    bond_id: int
    atom_a_id: int
    atom_b_id: int
    order: int = 1


@dataclass(slots=True)
class MoleculeDocument:
    """In-memory document model for the current editor session."""

    atoms: dict[int, Atom] = field(default_factory=dict)
    bonds: dict[int, Bond] = field(default_factory=dict)
    next_atom_id: int = 1
    next_bond_id: int = 1

    @property
    def atom_count(self) -> int:
        """Return the number of atoms in the document."""
        return len(self.atoms)

    @property
    def bond_count(self) -> int:
        """Return the number of bonds in the document."""
        return len(self.bonds)

    def clone(self) -> "MoleculeDocument":
        """Return a detached copy of the document."""
        return deepcopy(self)

    def allocate_atom_id(self, preferred_id: int | None = None) -> int:
        """Allocate a stable atom identifier."""
        atom_id = preferred_id if preferred_id is not None else self.next_atom_id
        self.next_atom_id = max(self.next_atom_id, atom_id + 1)
        return atom_id

    def allocate_bond_id(self, preferred_id: int | None = None) -> int:
        """Allocate a stable bond identifier."""
        bond_id = preferred_id if preferred_id is not None else self.next_bond_id
        self.next_bond_id = max(self.next_bond_id, bond_id + 1)
        return bond_id

    def add_atom(self, atom: Atom) -> None:
        """Insert or replace an atom in the document."""
        self.atoms[atom.atom_id] = atom
        self.next_atom_id = max(self.next_atom_id, atom.atom_id + 1)

    def add_bond(self, bond: Bond) -> None:
        """Insert or replace a bond in the document."""
        self.bonds[bond.bond_id] = bond
        self.next_bond_id = max(self.next_bond_id, bond.bond_id + 1)

    def get_atom(self, atom_id: int) -> Atom | None:
        """Fetch an atom by identifier."""
        return self.atoms.get(atom_id)

    def get_bond(self, bond_id: int) -> Bond | None:
        """Fetch a bond by identifier."""
        return self.bonds.get(bond_id)

    def remove_atom(self, atom_id: int) -> Atom | None:
        """Remove an atom from the document."""
        return self.atoms.pop(atom_id, None)

    def remove_bond(self, bond_id: int) -> Bond | None:
        """Remove a bond from the document."""
        return self.bonds.pop(bond_id, None)

    def bond_ids_for_atom(self, atom_id: int) -> list[int]:
        """Return all bond ids connected to the atom."""
        return [
            bond_id
            for bond_id, bond in self.bonds.items()
            if bond.atom_a_id == atom_id or bond.atom_b_id == atom_id
        ]

    def has_bond_between(self, atom_a_id: int, atom_b_id: int) -> bool:
        """Return whether a bond already exists between two atoms."""
        atom_pair = {atom_a_id, atom_b_id}
        return any({bond.atom_a_id, bond.atom_b_id} == atom_pair for bond in self.bonds.values())
