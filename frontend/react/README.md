# ClearMed React frontend

This is the supported web frontend for ClearMed AI. It uses React and Vite; the FastAPI backend must be running separately for simplification requests.

## Run locally

From the repository root:

```bash
npm --prefix frontend/react install
npm --prefix frontend/react run dev -- --host 0.0.0.0
```

Vite serves the app at `http://localhost:5173`. The API client defaults to `http://localhost:8000`; override this by setting `VITE_API_URL` in `frontend/react/.env.local` before starting Vite.

To create a production build, run `npm --prefix frontend/react run build` from the repository root.

## Structure

- `src/components/` — reusable, presentational UI
- `src/features/` — user workflows, beginning with report simplification
- `src/services/api.js` — FastAPI client; uses `VITE_API_URL` and defaults to `http://localhost:8000`
- `src/styles/` — global design tokens and foundational styles
