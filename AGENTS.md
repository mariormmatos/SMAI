# Repository Guidelines

## Project Structure & Module Organization
- `SMAI/app.py` is the main Streamlit app entry point.
- `SMAI/core/` holds data access, scoring, sentiment, and DCF logic.
- `SMAI/ui/` holds theme, components, charts, and page rendering.
- `assets/legacy/` contains historical snapshots (`SMAI_v1.0.py` to `SMAI_v4.0.py` and legacy `SMAI.py`).
- `assets/docs/` contains the product rationale document (`Stock Market Analysis & Insights.docx`) and prompts.
- `README.md`, `instrucoes.md`, and `contexto.md` capture product goals, UX rules, and development notes.
- `venv/` is a local virtual environment (do not edit manually; avoid committing it).

## Build, Test, and Development Commands
Create and activate a virtual environment (Windows PowerShell):
```
python -m venv venv
.\venv\Scripts\python.exe -m pip install -U pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```
Run the app:
```
.\venv\Scripts\python.exe -m streamlit run SMAI/app.py
```
There is no separate build step; Streamlit runs directly from source.

## Coding Style & Naming Conventions
- Python only; keep functions small and focused.
- Use `snake_case` for functions/variables and `PascalCase` for classes/dataclasses.
- Favor helper modules as the app grows (target split: `core/` for data/logic, `ui/` for styling/components).
- Follow the UI constraints from `Instrucoes.md`: dark theme, high contrast, Plotly charts with hover.
- Handle missing data defensively; never assume a column exists.

## Testing Guidelines
No testing framework is currently configured. If you add tests:
- Prefer `pytest` and place tests under `tests/`.
- Name tests `test_*.py` and keep them deterministic (no live API calls without mocks).

## Commit & Pull Request Guidelines
Git is not available in this environment, so commit conventions could not be inferred.
Recommended default until defined:
- Short, imperative commit messages (e.g., "Add DCF sensitivity table").
- PRs should include: summary, screenshots of key UI changes, and any known API limitations.

## Security & Configuration Tips
- External data sources include Yahoo Finance, Stocktwits, and Reddit; add clear warnings and graceful fallbacks on failures or rate limits.
- Use `st.cache_data` with a TTL for network calls to reduce latency and API load.
