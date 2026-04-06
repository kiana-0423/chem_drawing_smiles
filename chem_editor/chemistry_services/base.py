"""Interfaces and fallback implementations for chemistry services."""

from __future__ import annotations

from typing import Protocol

from chem_editor.core.models import MoleculeDocument


class ChemistryService(Protocol):
    """Common interface for chemistry backends."""

    name: str
    available: bool

    def describe(self) -> str:
        """Describe the backend status."""

    def import_smiles(self, smiles: str) -> MoleculeDocument:
        """Create a document from SMILES."""

    def export_smiles(self, document: MoleculeDocument) -> str:
        """Export a document as SMILES."""

    def sanitize(self, document: MoleculeDocument) -> MoleculeDocument:
        """Sanitize a document."""

    def generate_2d_coordinates(self, document: MoleculeDocument) -> MoleculeDocument:
        """Generate a fresh 2D layout for the document."""

    def export_mol(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        """Export a document as MOL."""

    def export_sdf(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        """Export a document as SDF."""

    def export_pdb(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        """Export a document as PDB."""


class ChemistryServiceError(RuntimeError):
    """Raised when chemistry import/export operations fail."""


class PlaceholderChemistryService:
    """Fallback used when RDKit is unavailable or advanced features are deferred."""

    name = "Placeholder chemistry service"
    available = False

    def describe(self) -> str:
        return "RDKit is not available yet. Chemistry actions remain placeholders in this scaffold."

    def import_smiles(self, smiles: str) -> MoleculeDocument:
        raise self._unavailable()

    def export_smiles(self, document: MoleculeDocument) -> str:
        raise self._unavailable()

    def sanitize(self, document: MoleculeDocument) -> MoleculeDocument:
        raise self._unavailable()

    def generate_2d_coordinates(self, document: MoleculeDocument) -> MoleculeDocument:
        raise self._unavailable()

    def export_mol(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        raise self._unavailable()

    def export_sdf(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        raise self._unavailable()

    def export_pdb(self, document: MoleculeDocument, molecule_name: str | None = None) -> str:
        raise self._unavailable()

    @staticmethod
    def _unavailable() -> ChemistryServiceError:
        return ChemistryServiceError("RDKit is required for chemistry import/export features.")
