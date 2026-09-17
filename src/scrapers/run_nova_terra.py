import glob
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.scrapers.fogo_cruzado import (
    FogoCruzadoClient,
    RIO_DE_JANEIRO_CITY_ID,
    RIO_DE_JANEIRO_STATE_ID,
)
from src.utils.geo import is_inside, load_polygons_from_kmz

PROJECT_DIR = Path(__file__).resolve().parents[2]
KMZ_PATH = PROJECT_DIR / "Regiao_interesse_NT.KMZ"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CONSOLIDATED_PATH = PROCESSED_DIR / "occurrences_nova_terra_aoi.json"

# Late-validated occurrences can appear days after the event date, so each run
# re-fetches a buffer window before the last known date to catch updates.
OVERLAP_DAYS = 7
FIRST_RUN_INITIAL_DATE = "2003-01-01"


def _occurrence_date(occurrence):
    return datetime.fromisoformat(occurrence["date"].replace("Z", "+00:00"))


def _load_consolidated():
    if CONSOLIDATED_PATH.exists():
        return {o["id"]: o for o in json.loads(CONSOLIDATED_PATH.read_text(encoding="utf-8"))}

    # Bootstrap from a prior full extraction if one exists, instead of refetching
    # the entire history on the first incremental run.
    seed_candidates = sorted(glob.glob(str(PROJECT_DIR / "data" / "raw" / "occurrences_nova_terra_aoi_*.json")))
    if seed_candidates:
        seed = json.loads(Path(seed_candidates[-1]).read_text(encoding="utf-8"))
        return {o["id"]: o for o in seed}
    return {}


def _save_consolidated(consolidated):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CONSOLIDATED_PATH.write_text(
        json.dumps(list(consolidated.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    polygons = load_polygons_from_kmz(KMZ_PATH)
    consolidated = _load_consolidated()

    if consolidated:
        last_date = max(_occurrence_date(o) for o in consolidated.values())
        since_date = (last_date - timedelta(days=OVERLAP_DAYS)).strftime("%Y-%m-%d")
    else:
        since_date = FIRST_RUN_INITIAL_DATE

    client = FogoCruzadoClient()
    fetched = client.fetch_occurrences_since(
        since_date, idState=RIO_DE_JANEIRO_STATE_ID, idCities=RIO_DE_JANEIRO_CITY_ID
    )
    new_in_aoi = [
        o
        for o in fetched
        if o.get("latitude")
        and o.get("longitude")
        and is_inside(o["latitude"], o["longitude"], polygons)
    ]

    before = len(consolidated)
    for occurrence in new_in_aoi:
        consolidated[occurrence["id"]] = occurrence
    _save_consolidated(consolidated)

    print(f"Buscado desde: {since_date}")
    print(f"Ocorrências buscadas na cidade RJ: {len(fetched)} | Dentro da região: {len(new_in_aoi)}")
    print(f"Total na base consolidada: {before} -> {len(consolidated)}")
    print(f"Salvo em: {CONSOLIDATED_PATH}")


if __name__ == "__main__":
    main()
