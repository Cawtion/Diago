# Diago Web UI

React + TypeScript + Vite + Tailwind frontend for Diago. **Web is the primary target;** desktop (Tauri) and mobile (Capacitor) builds are available in this repo but are not the current focus.

## Prerequisites

- Node.js 18+
- Diago API running (e.g. `uvicorn api.main:app --reload --host 127.0.0.1 --port 8000` from project root)

## Commands

| Command        | Description                                      |
|----------------|--------------------------------------------------|
| `npm run dev`  | Start Vite dev server (default http://localhost:5173) |
| `npm run build`| Production build → `dist/`                       |
| `npm run preview` | Serve `dist/` locally (test production build) |

In dev, the app proxies API requests to the backend (see `vite.config.ts`). Ensure the API is running on port 8000 or set `VITE_API_URL` in `.env`.

## Optional: desktop and mobile

- **Tauri desktop:** `npm run tauri dev` / `npm run tauri build` (requires Rust and Tauri CLI).
- **Capacitor mobile:** `npm run build` then `npm run cap:sync` and open Android/iOS in the IDE.

These are not required for web development.
