"""Conversion helpers between editor documents and RDKit molecules."""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Geometry import Point3D

from chem_editor.core.models import Atom, Bond, MoleculeDocument

IMPORT_LAYOUT_SCALE = 50.0


def document_to_rdkit_mol(
    document: MoleculeDocument,
    *,
    sanitize: bool = True,
    include_conformer: bool = True,
) -> Chem.Mol:
    """Convert an editor document into an RDKit molecule."""
    if document.atom_count == 0:
        raise ValueError("Cannot convert an empty document.")

    rw_mol = Chem.RWMol()
    atom_id_to_rdkit_index: dict[int, int] = {}

    for atom in sorted(document.atoms.values(), key=lambda item: item.atom_id):
        rd_atom = Chem.Atom(atom.element)
        rd_atom.SetFormalCharge(atom.formal_charge)
        atom_id_to_rdkit_index[atom.atom_id] = rw_mol.AddAtom(rd_atom)

    for bond in sorted(document.bonds.values(), key=lambda item: item.bond_id):
        atom_a_index = atom_id_to_rdkit_index.get(bond.atom_a_id)
        atom_b_index = atom_id_to_rdkit_index.get(bond.atom_b_id)
        if atom_a_index is None or atom_b_index is None:
            raise ValueError("Bond references an atom that does not exist in the document.")
        rw_mol.AddBond(atom_a_index, atom_b_index, _bond_type_for_order(bond.order))

    mol = rw_mol.GetMol()

    if include_conformer:
        conformer = Chem.Conformer(mol.GetNumAtoms())
        conformer.Set3D(False)
        for atom in sorted(document.atoms.values(), key=lambda item: item.atom_id):
            rdkit_index = atom_id_to_rdkit_index[atom.atom_id]
            conformer.SetAtomPosition(rdkit_index, Point3D(float(atom.x), float(atom.y), 0.0))
        mol.RemoveAllConformers()
        mol.AddConformer(conformer, assignId=True)

    if sanitize:
        Chem.SanitizeMol(mol)

    return mol


def rdkit_mol_to_document(
    mol: Chem.Mol,
    *,
    generate_2d_if_missing: bool = True,
    scale: float = 1.0,
    center: bool = False,
    invert_y: bool = False,
) -> MoleculeDocument:
    """Convert an RDKit molecule into an editor document."""
    working_mol = Chem.Mol(mol)
    if working_mol.GetNumAtoms() == 0:
        return MoleculeDocument()

    if generate_2d_if_missing and working_mol.GetNumConformers() == 0:
        AllChem.Compute2DCoords(working_mol)

    document_mol = Chem.Mol(working_mol)
    try:
        Chem.Kekulize(document_mol, clearAromaticFlags=True)
    except Exception:
        document_mol = working_mol

    conformer = document_mol.GetConformer() if document_mol.GetNumConformers() else None
    center_x = 0.0
    center_y = 0.0

    if conformer is not None and center:
        atom_count = document_mol.GetNumAtoms()
        center_x = sum(conformer.GetAtomPosition(index).x for index in range(atom_count)) / atom_count
        center_y = sum(conformer.GetAtomPosition(index).y for index in range(atom_count)) / atom_count

    document = MoleculeDocument()

    for atom_index, atom in enumerate(document_mol.GetAtoms(), start=1):
        x_pos = 0.0
        y_pos = 0.0
        if conformer is not None:
            position = conformer.GetAtomPosition(atom_index - 1)
            x_pos = (position.x - center_x) * scale
            y_pos = (position.y - center_y) * scale
            if invert_y:
                y_pos *= -1

        document.add_atom(
            Atom(
                atom_id=atom_index,
                element=atom.GetSymbol(),
                x=x_pos,
                y=y_pos,
                formal_charge=atom.GetFormalCharge(),
            )
        )

    for bond_index, bond in enumerate(document_mol.GetBonds(), start=1):
        document.add_bond(
            Bond(
                bond_id=bond_index,
                atom_a_id=bond.GetBeginAtomIdx() + 1,
                atom_b_id=bond.GetEndAtomIdx() + 1,
                order=_bond_order_for_rdkit_bond(bond),
            )
        )

    return document


def imported_rdkit_mol_to_document(mol: Chem.Mol) -> MoleculeDocument:
    """Convert an imported RDKit molecule into centered editor coordinates."""
    return rdkit_mol_to_document(
        mol,
        generate_2d_if_missing=True,
        scale=IMPORT_LAYOUT_SCALE,
        center=True,
        invert_y=True,
    )


def _bond_type_for_order(order: int) -> Chem.BondType:
    normalized_order = max(1, min(order, 3))
    if normalized_order == 2:
        return Chem.BondType.DOUBLE
    if normalized_order == 3:
        return Chem.BondType.TRIPLE
    return Chem.BondType.SINGLE


def _bond_order_for_rdkit_bond(bond: Chem.Bond) -> int:
    order = int(round(bond.GetBondTypeAsDouble()))
    return max(1, min(order, 3))
