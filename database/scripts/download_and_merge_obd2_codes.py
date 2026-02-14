"""
Download OBD-II codes from fabiovila/OBDIICodes (GitHub) and merge with
existing database/obd2_codes.json. Outputs Diago schema (code, description,
system, subsystem, mechanical_classes, symptoms, severity).

Run from project root: python -m database.scripts.download_and_merge_obd2_codes
"""

import json
import re
import sys
from pathlib import Path

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

# Project root = parent of database/
DATABASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = DATABASE_DIR.parent
OBD2_JSON = DATABASE_DIR / "obd2_codes.json"
OBD2_EXTENDED_JSON = DATABASE_DIR / "obd2_codes_extended.json"
SOURCE_URL = "https://raw.githubusercontent.com/fabiovila/OBDIICodes/master/codes.json"

SYSTEM_MAP = {
    "P": "powertrain",
    "B": "body",
    "C": "chassis",
    "U": "network",
}


def normalize_code(raw: str) -> str:
    """Extract canonical code (e.g. P0301) from 'P0301' or 'P0000/SAE'."""
    code = (raw or "").strip().upper()
    # Take only the part before slash (e.g. P0000/SAE -> P0000)
    if "/" in code:
        code = code.split("/")[0].strip()
    # Ensure format P/B/C/U + digits (allow 4 or 5 hex digits)
    if not re.match(r"^[PBCU]\d{4,5}$", code):
        return code  # return as-is and let caller skip if needed
    return code


def infer_system(code: str) -> str:
    """Infer system from first character of code."""
    if not code:
        return "powertrain"
    return SYSTEM_MAP.get(code[0].upper(), "powertrain")


def load_existing() -> dict[str, dict]:
    """Load existing obd2_codes.json into a dict by code."""
    by_code: dict[str, dict] = {}
    if not OBD2_JSON.exists():
        return by_code
    try:
        with open(OBD2_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return by_code
    for entry in data if isinstance(data, list) else []:
        c = entry.get("code") or entry.get("Code")
        if c:
            by_code[normalize_code(str(c))] = {
                "code": entry.get("code", c).upper() if isinstance(c, str) else c,
                "description": entry.get("description") or entry.get("Description", ""),
                "system": entry.get("system", infer_system(str(c))),
                "subsystem": entry.get("subsystem", ""),
                "mechanical_classes": entry.get("mechanical_classes", []),
                "symptoms": entry.get("symptoms", []),
                "severity": entry.get("severity", "medium"),
            }
    return by_code


def download_remote() -> list[dict]:
    """Fetch codes.json from GitHub."""
    print(f"Downloading {SOURCE_URL} ...")
    with urlopen(SOURCE_URL, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data if isinstance(data, list) else []


def merge(existing: dict[str, dict], remote: list[dict]) -> list[dict]:
    """Merge remote list into existing by code. Existing entries are kept (richer)."""
    for item in remote:
        raw_code = item.get("Code") or item.get("code")
        if not raw_code:
            continue
        code = normalize_code(str(raw_code))
        if not re.match(r"^[PBCU]\d{4,5}$", code):
            continue
        if code in existing:
            continue
        existing[code] = {
            "code": code,
            "description": (item.get("Description") or item.get("description") or "").strip(),
            "system": infer_system(code),
            "subsystem": "",
            "mechanical_classes": [],
            "symptoms": [],
            "severity": "medium",
        }
    # Sort by code for stable output
    return [existing[c] for c in sorted(existing.keys())]


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))
    existing = load_existing()
    print(f"Existing codes: {len(existing)}")
    remote = download_remote()
    print(f"Remote codes: {len(remote)}")
    merged = merge(existing, remote)
    print(f"Merged total: {len(merged)}")
    # Write extended copy (optional use via DIAGO_DB_OBD2_CODES_PATH) and replace default
    with open(OBD2_EXTENDED_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    print(f"Wrote {OBD2_EXTENDED_JSON}")
    with open(OBD2_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    print(f"Wrote {OBD2_JSON} (default dataset updated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
