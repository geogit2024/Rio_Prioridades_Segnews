import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; scraper_NovaTerra/1.0)"}

# Direct RSS feeds — filtered by AOI keywords after fetching
#
# 2026-09: oglobo.globo.com/rio/rss.xml não é mais atualizado (feed genérico
# parado desde 2023) — trocado pelo G1 Rio de Janeiro, que é o feed regional
# real da Globo hoje. rss.uol.com.br/feed/noticias.xml foi removido: o
# próprio backend da UOL retorna um erro de timeout embutido no XML
# ("Erro ao processar conteudo JSON ... 408: timeout"), sem nenhuma
# alternativa funcional encontrada (outras rotas testadas deram 403/404).
RSS_FEEDS = [
    ("G1 Rio de Janeiro", "https://g1.globo.com/rss/g1/rj/rio-de-janeiro/"),
    ("Extra", "https://extra.globo.com/rss.xml"),
    ("CNN Brasil", "https://www.cnnbrasil.com.br/feed/"),
    ("Metrópoles", "https://www.metropoles.com/feed"),
]

# Google News RSS searches — each query already scoped to AOI + violence terms
GOOGLE_NEWS_QUERIES = [
    '("Quintino Bocaiúva" OR "Irajá" OR "Vicente de Carvalho" OR "Maria da Graça" OR "Bonsucesso" OR "Olaria" OR "Ramos") (tiroteio OR confronto OR violência OR operação OR "bala perdida")',
    '("Duque de Caxias" OR "Vigário Geral" OR "Parada de Lucas" OR "Cordovil" OR "Vila da Penha") (tiroteio OR confronto OR violência OR operação OR "bala perdida")',
    '("Complexo do Alemão" OR "Manguinhos" OR "Jacarezinho" OR "Cidade Alta" OR "Mangueira") (tiroteio OR confronto OR violência OR operação OR tráfico OR milícia)',
    '("Complexo da Maré" OR "Nova Holanda" OR "Nova Maré" OR "Parque Maré" OR "Morro do Timbau") (tiroteio OR confronto OR violência OR operação OR tráfico)',
    '("Zona Norte" Rio de Janeiro) (tiroteio OR confronto OR operação policial OR milícia OR tráfico)',
]

GOOGLE_NEWS_BASE = "https://news.google.com/rss/search?hl=pt-BR&gl=BR&ceid=BR:pt-419&q={query}"

# Keywords unambiguously tied to the AOI — match alone is enough
AOI_SPECIFIC_KEYWORDS = [
    # Bairros formais
    "quintino bocaiúva", "quintino bocaíuva",
    "irajá",
    "vicente de carvalho",
    "maria da graça",
    "duque de caxias",
    "parque sarapuí",
    "bonsucesso",
    "ramos",
    "penha circular",
    "brás de pina",
    "vigário geral",
    "olaria",
    "inhaúma",
    "engenho da rainha",
    "tomás coelho",
    "cordovil",
    "parada de lucas",
    "vista alegre",
    "vila kosmos",
    "vila da penha",
    # Morros e comunidades/favelas
    "complexo do alemão",
    "complexo da maré",
    "manguinhos",
    "jacarezinho",
    "cidade alta",
    "mangueira",
    "kelson",
    "nova holanda",
    "nova maré",
    "parque maré",
    "parque rubens vaz",
    "parque união",
    "morro do timbau",
    "baixa do sapateiro",
    "conjunto esperança",
]

# Generic terms that exist in other cities — only valid when paired with an RJ anchor
AOI_GENERIC_KEYWORDS = [
    "cidade universitária",
    "zona norte",
    "quintino",
    "duque",
    "alemão",
    "maré",
    "penha",
]

# Geographic anchors that confirm the article is about Rio de Janeiro
RJ_ANCHORS = [
    "rio de janeiro",
    " rj ",
    "(rj)",
    "/rj",
    "estado do rio",
    "cidade do rio",
]

VIOLENCE_KEYWORDS = [
    "tiroteio", "confronto", "violência", "operação policial",
    "bala perdida", "morto", "mortos", "ferido", "feridos",
    "homicídio", "assassin", "tráfico", "milícia",
]


def _parse_date(entry):
    for field in ("published", "updated"):
        value = entry.get(field)
        if value:
            try:
                return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _entry_to_article(entry, source_name):
    title = entry.get("title", "").strip()
    summary = entry.get("summary", "").strip()
    url = entry.get("link", "").strip()
    return {
        "url": url,
        "title": title,
        "summary": summary,
        "source": source_name,
        "published": _parse_date(entry),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _matches_aoi(article):
    text = (article["title"] + " " + article["summary"]).lower()
    has_specific = any(kw in text for kw in AOI_SPECIFIC_KEYWORDS)
    has_generic_with_rj = (
        any(kw in text for kw in AOI_GENERIC_KEYWORDS)
        and any(anchor in text for anchor in RJ_ANCHORS)
    )
    has_location = has_specific or has_generic_with_rj
    has_violence = any(kw in text for kw in VIOLENCE_KEYWORDS)
    return has_location and has_violence


def fetch_rss_feed(source_name, url, filter_by_aoi=True):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  [{source_name}] erro: {e}")
        return []

    articles = [_entry_to_article(e, source_name) for e in feed.entries if e.get("link")]
    if filter_by_aoi:
        articles = [a for a in articles if _matches_aoi(a)]
    return articles


def _has_violence(article):
    text = (article["title"] + " " + article["summary"]).lower()
    return any(kw in text for kw in VIOLENCE_KEYWORDS)


def fetch_google_news_rss(query):
    url = GOOGLE_NEWS_BASE.format(query=quote_plus(query))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  [Google News] erro na query '{query[:50]}': {e}")
        return []

    articles = []
    for entry in feed.entries:
        if not entry.get("link"):
            continue
        source_name = entry.get("source", {}).get("title", "Google News")
        article = _entry_to_article(entry, source_name)
        # Location is guaranteed by the query — apply only violence filter
        if _has_violence(article):
            articles.append(article)
    return articles


def fetch_all(delay=1.5):
    articles = []

    print("Buscando feeds RSS diretos...")
    for name, url in RSS_FEEDS:
        results = fetch_rss_feed(name, url, filter_by_aoi=True)
        print(f"  {name}: {len(results)} artigos relevantes")
        articles.extend(results)
        time.sleep(delay)

    print("Buscando Google News RSS...")
    for query in GOOGLE_NEWS_QUERIES:
        results = fetch_google_news_rss(query)
        print(f"  query '{query[:60]}...': {len(results)} artigos")
        articles.extend(results)
        time.sleep(delay)

    return articles
