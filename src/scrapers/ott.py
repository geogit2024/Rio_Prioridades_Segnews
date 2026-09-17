from datetime import datetime, timezone

import requests

# 2026-09: o site trocou de estrutura — a antiga reportview.php (HTML puro)
# não existe mais. O domínio raiz (ondetemtiroteio.com) hoje é um painel de
# login não relacionado; o site público ficou em /website/ott/, que carrega
# os dados via uma API JSON própria (report-data.php). Ela exige um header
# Referer apontando pro próprio site — sem isso retorna {"error":"not_found"}.
OTT_BASE = "https://ondetemtiroteio.com/website/ott"
OTT_DATA_URL = f"{OTT_BASE}/report-data.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; scraper_NovaTerra/1.0)",
    "Referer": f"{OTT_BASE}/index.html",
}

# Bairros e comunidades dentro do polígono de interesse
AOI_NEIGHBORHOODS = {
    "abolição", "aldeia campista", "andaraí", "bairro araújo", "bairro de fátima",
    "baixa do sapateiro", "benfica", "bento ribeiro dantas", "boca do mato",
    "bonsucesso", "brás de pina", "cachambi", "caju", "cascadura",
    "cidade alta", "cidade universitária", "complexo do alemão", "complexo da maré",
    "conjunto esperança", "conjunto pinheiros", "cordovil", "del castilho",
    "encantado", "engenho da rainha", "engenho de dentro", "engenho novo",
    "estácio", "grajaú", "higienópolis", "inhaúma", "irajá",
    "jacarezinho", "jacaré", "jardim américa", "kelson",
    "lins de vasconcelos", "mangueira", "manguinhos", "maria da graça",
    "maré", "méier", "morro do timbau", "nova holanda", "nova maré",
    "olaria", "parada de lucas", "parque maré", "parque rubens vaz",
    "parque união", "penha", "penha circular", "piedade", "pilares",
    "praça da bandeira", "quintino bocaiúva", "ramos", "riachuelo",
    "rio comprido", "rocha", "sampaio", "são cristóvão", "são francisco xavier",
    "tijuca", "todos os santos", "tomás coelho", "triagem", "vasco da gama",
    "vigário geral", "vila isabel", "vila kosmos", "vila da penha",
    "vila do joão", "vila do pinheiro", "vista alegre", "água santa",
    # Duque de Caxias
    "duque de caxias", "parque sarapuí",
}


def _parse_datetime(raw):
    """Parses '06/07/26 00:56' -> ISO 8601."""
    try:
        dt = datetime.strptime(raw.strip(), "%d/%m/%y %H:%M")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return raw.strip()


def fetch_incidents(state="RJ"):
    try:
        resp = requests.get(
            OTT_DATA_URL, headers=HEADERS,
            params={"action": "informes", "state": state}, timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"  [OTT] erro ao buscar: {e}")
        return []

    incidents = []
    for item in payload.get("items", []):
        incidents.append({
            "datetime": _parse_datetime(item.get("date", "")),
            "type": item.get("type", ""),
            "neighborhood": item.get("neighborhood", ""),
            "city": item.get("city", ""),
            "state": item.get("state", ""),
            "lat": item.get("lat"),
            "lng": item.get("lng"),
            "address": item.get("address"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return incidents


def filter_aoi(incidents):
    return [
        inc for inc in incidents
        if inc["neighborhood"].lower() in AOI_NEIGHBORHOODS
    ]
