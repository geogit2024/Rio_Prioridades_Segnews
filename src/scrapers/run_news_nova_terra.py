import json
from datetime import datetime, timezone
from pathlib import Path

from src.scrapers.news import fetch_all

PROJECT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CONSOLIDATED_PATH = PROCESSED_DIR / "news_nova_terra_aoi.json"


def _load_consolidated():
    if CONSOLIDATED_PATH.exists():
        return {a["url"]: a for a in json.loads(CONSOLIDATED_PATH.read_text(encoding="utf-8"))}
    return {}


def _save_consolidated(consolidated):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    articles = sorted(consolidated.values(), key=lambda a: a["published"], reverse=True)
    CONSOLIDATED_PATH.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    consolidated = _load_consolidated()
    before = len(consolidated)

    articles = fetch_all()

    new_count = 0
    for article in articles:
        url = article["url"]
        if url and url not in consolidated:
            consolidated[url] = article
            new_count += 1

    _save_consolidated(consolidated)

    print(f"Novos artigos: {new_count}")
    print(f"Total na base consolidada: {before} -> {len(consolidated)}")
    print(f"Salvo em: {CONSOLIDATED_PATH}")


if __name__ == "__main__":
    main()
