# ClearMed React frontend

This folder is the production frontend for ClearMed AI. It uses Vite for development and builds, and Motion is available for purposeful interface animation.

## Run locally

```bash
cd frontend/react
npm install
npm run dev -- --host 0.0.0.0
```

Vite serves the app at `http://localhost:5173`. Start the FastAPI backend separately on port 8000, or set `VITE_API_URL` in a local `.env` file.

## Structure

- `src/components/` — reusable, presentational UI
- `src/features/` — user workflows, beginning with report simplification
- `src/services/api.js` — FastAPI client; uses `VITE_API_URL` and defaults to `http://localhost:8000`
- `src/styles/` — global design tokens and foundational styles
