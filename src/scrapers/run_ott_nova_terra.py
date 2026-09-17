import json
from pathlib import Path

from src.scrapers.ott import fetch_incidents, filter_aoi

PROJECT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CONSOLIDATED_PATH = PROCESSED_DIR / "ott_nova_terra_aoi.json"


def _incident_key(inc):
    return f"{inc['datetime']}|{inc['type']}|{inc['neighborhood']}"


def _load_consolidated():
    if CONSOLIDATED_PATH.exists():
        return {_incident_key(i): i for i in json.loads(CONSOLIDATED_PATH.read_text(encoding="utf-8"))}
    return {}


def _save_consolidated(consolidated):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    incidents = sorted(consolidated.values(), key=lambda i: i["datetime"], reverse=True)
    CONSOLIDATED_PATH.write_text(
        json.dumps(incidents, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    consolidated = _load_consolidated()
    before = len(consolidated)

    incidents = fetch_incidents()
    aoi_incidents = filter_aoi(incidents)

    new_count = 0
    for inc in aoi_incidents:
        key = _incident_key(inc)
        if key not in consolidated:
            consolidated[key] = inc
            new_count += 1

    _save_consolidated(consolidated)

    print(f"OTT: {len(incidents)} incidentes buscados | {len(aoi_incidents)} na região")
    print(f"Novos: {new_count} | Total consolidado: {before} -> {len(consolidated)}")
    print(f"Salvo em: {CONSOLIDATED_PATH}")


if __name__ == "__main__":
    main()
