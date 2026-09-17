import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api-service.fogocruzado.org.br/api/v2"
DATA_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class FogoCruzadoClient:
    def __init__(self, email=None, password=None):
        self.email = email or os.environ["FOGOCRUZADO_EMAIL"]
        self.password = password or os.environ["FOGOCRUZADO_PASSWORD"]
        self._token = None

    def login(self):
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": self.email, "password": self.password},
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["data"]["accessToken"]
        return self._token

    @property
    def token(self):
        if self._token is None:
            self.login()
        return self._token

    def fetch_occurrences(self, page=1, take=100, **filters):
        params = {"page": page, "take": take, **filters}
        for attempt in range(6):
            resp = requests.get(
                f"{BASE_URL}/occurrences",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
                timeout=30,
            )
            if resp.status_code == 401:
                self.login()
                continue
            if resp.status_code != 429:
                resp.raise_for_status()
                return resp.json()
            retry_after = resp.headers.get("Retry-After")
            wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else min(60 * 2**attempt, 600)
            print(f"Limite Fogo Cruzado na página {page}; aguardando {wait_seconds}s")
            time.sleep(wait_seconds)
        resp.raise_for_status()

    def fetch_all_occurrences(self, delay=1.0, **filters):
        page = 1
        all_results = []
        while True:
            payload = self.fetch_occurrences(page=page, **filters)
            results = payload.get("data", [])
            if not results:
                break
            all_results.extend(results)
            pagination = payload.get("pageMeta", {})
            if page >= pagination.get("pageCount", page):
                break
            page += 1
            time.sleep(delay)
        return all_results

    def fetch_occurrences_since(self, initial_date, delay=1.0, **filters):
        """Fetches occurrences with date >= initial_date (YYYY-MM-DD), oldest first."""
        return self.fetch_all_occurrences(
            delay=delay, initialdate=initial_date, order="ASC", **filters
        )


def save_raw(data, prefix="occurrences"):
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = DATA_RAW_DIR / f"{prefix}_{timestamp}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


RIO_DE_JANEIRO_STATE_ID = "b112ffbe-17b3-4ad0-8f2a-2038745d1d14"
RIO_DE_JANEIRO_CITY_ID = "d1bf56cc-6d85-4e6a-a5f5-0ab3f4074be3"


def main():
    client = FogoCruzadoClient()
    occurrences = client.fetch_all_occurrences(
        idState=RIO_DE_JANEIRO_STATE_ID, idCities=RIO_DE_JANEIRO_CITY_ID
    )
    out_path = save_raw(occurrences, prefix="occurrences_rio_de_janeiro")
    print(f"Salvas {len(occurrences)} ocorrências em {out_path}")


if __name__ == "__main__":
    main()
