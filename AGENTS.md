# AGENTS.md

## Project Goal

Build a native Python chemical structure editor inspired by Ketcher.
Keep it desktop-first, cleanly structured, and ready to grow into a broader chemistry platform.

## Required Stack

- Python 3.11+
- PySide6
- RDKit

Do not introduce web frontend frameworks, browser shells, or Qt WebEngine unless explicitly requested.

## Architecture Rules

- Keep UI, editor, domain models, commands, and chemistry services separate.
- Prefer modular, layered code over monolithic files.
- Preserve extension points for future plugins and larger chemistry workflows.

## Coding Style

- Keep files small and focused.
- Use type hints on public and non-trivial APIs.
- Add docstrings where they improve clarity.
- Avoid giant classes and oversized utility modules.

## Guardrails

- Keep the app runnable after edits.
- Do not remove working behavior unless replacing it safely.
- Do not add database, ML, or web frontend dependencies in this phase.
- Keep the codebase ready for future plugin expansion.

## Delivery Pattern

1. Scaffold structure first.
2. Build a runnable MVP next.
3. Expand features incrementally without breaking startup.

