# Chem Drawing Smiles

`chem-drawing-smiles` is a native Python desktop chemical structure editor MVP.
It uses PySide6 for the GUI and keeps RDKit isolated behind a chemistry service layer.

This phase is intentionally focused:

- native desktop shell only
- no web frontend
- no database
- no machine learning

## Current Structure

```text
chem_editor/
  app.py
  __main__.py
  ui/
  editor/
  core/
  commands/
  chemistry_services/
```

## Included Starter UI

The starter window already provides:

- menu bar
- toolbar
- left tool panel
- central editor canvas
- right inspector panel
- bottom status/log panel

The code is organized so editor logic, domain models, command handling, and chemistry integrations can evolve independently.

## Current MVP Features

The current runnable editor includes:

- selection tool
- atom placement and atom retagging
- bond placement and bond retagging
- delete selected items
- clear canvas
- zoom in and zoom out
- undo and redo through a command layer
- common element quick buttons plus a full periodic table dialog
- single, double, triple, and aromatic bond types
- RDKit-backed validation refresh after each structural edit
- implicit hydrogen counts derived from RDKit sanitization
- invalid atom / valence warning highlighting in the canvas
- SMILES import into the editor through an RDKit service layer
- SMILES generation from the current drawing
- 2D coordinate regeneration
- optional explicit hydrogen expansion through RDKit `AddHs`
- MOL, SDF, and PDB export through the chemistry service layer

This is still a first-phase editor. It does not aim for full production chemistry editing yet, but it is structured for future extension.

## Chemistry Integration

RDKit is isolated behind a chemistry service / adapter layer. The current implementation supports:

- import from SMILES
- export to canonical SMILES
- document sanitization through RDKit where possible
- 2D coordinate generation when importing or rebuilding layouts
- atom-level implicit hydrogen refresh from temporary RDKit molecules
- atom-level validation warnings when RDKit detects chemistry problems
- MOL export
- SDF export
- PDB export with RDKit 3D conformer generation when possible

The editor widgets operate on project domain objects. RDKit conversion logic lives in the chemistry layer rather than in the scene or widget code.

## Setup

Create and activate a Python 3.11+ virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

You can run the app either way:

```bash
python -m chem_editor
```

or:

```bash
pip install -e .
chem-editor
```

## Editor Usage

- Use the left tool panel or top toolbar to switch between `Select`, `Atom`, `Bond`, and `Delete`.
- Choose common elements from the quick buttons, or open `More Elements...` for the full periodic table.
- Choose the current bond type from the bond controls before drawing or retagging a bond.
- Click an existing atom with the atom tool to change its element.
- Click an existing bond with the bond tool to change its bond type.
- Implicit hydrogens are not drawn as atoms by default. They are recomputed from RDKit after each structural edit and used for validation, tooltips, and exports where valid.
- Use the inspector or the `Chemistry` menu to load SMILES, generate canonical SMILES, regenerate 2D coordinates, expand explicit hydrogens, and export MOL/SDF/PDB.

## Notes

- Use the right-side inspector panel or the menu actions to load SMILES and export structures.
- RDKit is required for SMILES import/export and MOL/SDF/PDB export.
- RDKit is also used to refresh implicit hydrogen counts and validation warnings after structure edits.
- PySide6 must be installed to launch the GUI. If it is missing, the app exits with a clear setup message.
