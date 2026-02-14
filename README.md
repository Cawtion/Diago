# Diago — Automotive Audio Spectrogram Analyzer

A **web-first** application for automotive diagnostics that uses audio spectrogram analysis and digital fingerprinting to identify engine and vehicle faults, paired with OBD-II trouble codes. Desktop and mobile builds are planned for later.

## Features

- **Audio Recording & Import**: Record from microphone or import WAV/MP3/FLAC files
- **Spectrogram Visualization**: Real-time STFT and Mel spectrogram display
- **Digital Fingerprinting**: Constellation-map based audio fingerprinting tuned for automotive sounds
- **Fault Matching**: Compare audio against a database of known fault signatures
- **Trouble Code Integration**: Enter OBD-II codes (P/B/C/U) with lookup and NHTSA/Car API fallback
- **Vehicle Context**: VIN decode, recalls, and TSB search (NHTSA + local TSBs)
- **Session Management**: Save and review past analysis sessions
- **Report Export**: Export diagnostic reports as text files

## Requirements

- Python 3.10+
- Node.js 18+ (for the web frontend)
- FFmpeg (optional, for MP3 support via pydub)

## Quick start (web UI)

1. **Backend** — From the project root:
   ```bash
   pip install -r requirements.txt
   uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Frontend** — In another terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **http://localhost:5173** in your browser. The app talks to the API at `http://127.0.0.1:8000` (Vite proxies in dev).

See [frontend/README.md](frontend/README.md) for more frontend options (build, preview). Copy `.env.example` to `.env` and set any optional keys (e.g. `CAR_API_KEY`) if you use external APIs.

**OBD2 / OBD code library:** The app ships with a merged dataset in `database/obd2_codes.json` (1,400+ codes from [OBDIICodes](https://github.com/fabiovila/OBDIICodes) plus the original SAE J2012–style entries with symptoms and mechanical classes). To refresh or re-download: `python -m database.scripts.download_and_merge_obd2_codes`. To use a different file, set `DIAGO_DB_OBD2_CODES_PATH` in `.env`. The database is seeded on first run (or when the table is empty).

## Other ways to run

- **Legacy desktop (PyQt6):** `python main.py` — classic local UI, no API.
- **Tauri desktop / mobile:** The React app can be packaged with Tauri or Capacitor when you’re ready to target desktop or mobile; for now we focus on the web UI.

## Workflow

1. **Record or Import** audio from the vehicle (engine running, driving, etc.)
2. **Enter Trouble Codes** from your OBD-II scanner (e.g., P0301, P0420)
3. Optionally **decode VIN** and review recalls and TSBs for context
4. Click **Analyze & Match** to fingerprint the audio and compare against known fault signatures
5. Review **Match Results** ranked by confidence percentage
6. **Save Session** or **Export Report** for your records

## Project structure

```
api/                    - FastAPI service (primary backend for web)
  main.py               - App entry, CORS, routers
  routes/               - vehicle, codes, tsb, diagnosis, sessions, etc.
  services/             - NHTSA, Car API clients
core/                   - Shared engine (no GUI)
  config.py             - Settings (env, paths, API keys)
  audio_io.py, spectrogram.py, fingerprint.py, matcher.py
database/               - SQLite (signatures, sessions, TSBs)
frontend/               - React + TypeScript + Vite (web UI)
main.py                 - Legacy PyQt6 desktop entry
gui/                    - Legacy PyQt6 UI
```

## Seed fault signatures

| Code Range   | Fault Type                        |
|-------------|-----------------------------------|
| P0300-P0312 | Engine misfire patterns           |
| P0171/P0174 | Vacuum/intake leak hiss           |
| P0420       | Catalytic converter / exhaust     |
| P0500-series| Wheel bearing hum                 |
| —           | Belt squeal / alternator whine    |

## License

MIT License
