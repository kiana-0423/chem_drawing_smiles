# Chem Drawing Smiles

`chem-drawing-smiles` is the initial scaffold for a native Python desktop chemical structure editor.
It uses PySide6 for the GUI and keeps RDKit isolated behind a chemistry service layer.

This first phase is intentionally small:

- native desktop shell only
- no web frontend
- no database
- no machine learning
- no advanced chemistry editing yet

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

The first runnable editor MVP includes:

- selection tool
- atom placement tool
- bond placement tool
- delete selected items
- clear canvas
- zoom in and zoom out
- undo and redo through a command layer
- SMILES import into the editor through an RDKit service layer
- SMILES generation from the current drawing
- MOL, SDF, and PDB export through the chemistry service layer

This is still a simple editor. It does not aim for full chemical correctness yet, but it is structured for future extension.

## Chemistry Integration

RDKit is isolated behind a chemistry service / adapter layer. The current implementation supports:

- import from SMILES
- export to canonical SMILES
- document sanitization through RDKit where possible
- 2D coordinate generation when importing or rebuilding layouts
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

## Notes

- Use the right-side inspector panel or the Chemistry/File menu actions to load SMILES and export structures.
- RDKit is required for SMILES import/export and MOL/SDF/PDB export.
- PySide6 must be installed to launch the GUI. If it is missing, the app exits with a clear setup message.
