"""RDKit-backed chemistry service implementation."""

from __future__ import annotations

from typing import Final

from chem_editor.core.models import MoleculeDocument

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from .conversion import document_to_rdkit_mol, imported_rdkit_mol_to_document, rdkit_mol_to_document
except ImportError:  # pragma: no cover - depends on local environment
    Chem = None
    AllChem = None

from .base import ChemistryServiceError


class RDKitChemistryService:
    """RDKit-backed chemistry adapter for import/export and cleanup tasks."""

    DEFAULT_MOLECULE_NAME: Final[str] = "ChemDrawingSmiles"

    name = "RDKit"

    def __init__(self) -> None:
        self.available = Chem is not None and AllChem is not None

    def describe(self) -> str:
        if self.available:
            return "RDKit detected. SMILES import/export and structure export are available."
        return "RDKit is not installed. The UI will run, but chemistry features remain placeholders."

    def import_smiles(self, smiles: str) -> MoleculeDocument:
        self._ensure_available()
        normalized_smiles = smiles.strip()
        if not normalized_smiles:
            raise ChemistryServiceError("SMILES input is empty.")

        mol = Chem.MolFromSmiles(normalized_smiles, sanitize=False)
        if mol is None:
            raise ChemistryServiceError("RDKit could not parse the SMILES string.")

        self._sanitize_mol(mol, context="SMILES import")
        AllChem.Compute2DCoords(mol)
        return imported_rdkit_mol_to_document(mol)

    def export_smiles(self, document: MoleculeDocument) -> str:
        mol = self._document_to_sanitized_mol(document)
        return Chem.MolToSmiles(mol, canonical=True)

    def sanitize(self, document: MoleculeDocument) -> MoleculeDocument:
        mol = self._document_to_sanitized_mol(document)
        return rdkit_mol_to_document(
            mol,
            generate_2d_if_missing=False,
            scale=1.0,
            center=False,
            invert_y=False,
        )

    def generate_2d_coordinates(self, document: MoleculeDocument) -> MoleculeDocument:
        mol = self._document_to_sanitized_mol(document)
        mol.RemoveAllConformers()
        AllChem.Compute2DCoords(mol)
        return imported_rdkit_mol_to_document(mol)

    def export_mol(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        mol = self._document_to_sanitized_mol(document, molecule_name=molecule_name)
        if mol.GetNumConformers() == 0:
            AllChem.Compute2DCoords(mol)
        return Chem.MolToMolBlock(mol)

    def export_sdf(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        mol_block = self.export_mol(document, molecule_name=molecule_name).rstrip()
        return f"{mol_block}\n$$$$\n"

    def export_pdb(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        mol = self._document_to_sanitized_mol(document, molecule_name=molecule_name)
        pdb_mol = Chem.AddHs(Chem.Mol(mol), addCoords=True)
        pdb_mol.SetProp("_Name", molecule_name or self.DEFAULT_MOLECULE_NAME)

        if pdb_mol.GetNumAtoms() > 0:
            params = AllChem.ETKDGv3()
            params.randomSeed = 0xF00D
            status = AllChem.EmbedMolecule(pdb_mol, params)
            if status != 0:
                params.useRandomCoords = True
                status = AllChem.EmbedMolecule(pdb_mol, params)

            if status == 0:
                try:
                    AllChem.UFFOptimizeMolecule(pdb_mol, maxIters=200)
                except Exception:
                    pass
            else:
                AllChem.Compute2DCoords(pdb_mol)

        return Chem.MolToPDBBlock(pdb_mol)

    def _document_to_sanitized_mol(
        self,
        document: MoleculeDocument,
        *,
        molecule_name: str | None = None,
    ):
        self._ensure_available()
        try:
            mol = document_to_rdkit_mol(document, sanitize=True, include_conformer=True)
        except ValueError as exc:
            raise ChemistryServiceError(str(exc)) from exc
        except Exception as exc:
            raise ChemistryServiceError(f"RDKit could not convert the current drawing: {exc}") from exc

        mol.SetProp("_Name", molecule_name or self.DEFAULT_MOLECULE_NAME)
        return mol

    def _sanitize_mol(self, mol, *, context: str) -> None:
        try:
            Chem.SanitizeMol(mol)
        except Exception as exc:
            raise ChemistryServiceError(f"RDKit could not sanitize the molecule during {context}: {exc}") from exc

    def _ensure_available(self) -> None:
        if not self.available:
            raise ChemistryServiceError("RDKit is required for this chemistry operation.")
