import json
import os
import subprocess
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_DIR / "data" / "processed" / "news_nova_terra_aoi.json"
REPO_DIR = Path(os.environ.get("PUBLIC_REPO_DIR", PROJECT_DIR / "public_repo"))
PUBLIC_JSON_PATH = REPO_DIR / "noticias.json"
PUBLIC_TXT_PATH = REPO_DIR / "noticias.txt"


def _run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check, text=True, capture_output=True)


def _format_date(value):
    try:
        return parsedate_to_datetime(value).strftime("%d/%m/%Y")
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return ""


def _load_articles():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Arquivo de notícias não encontrado: {SOURCE_PATH}")
    articles = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if not isinstance(articles, list):
        raise ValueError("O arquivo de notícias deve conter uma lista JSON")
    return articles


def _write_public_files(articles):
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    public_articles = [
        {
            "title": str(article.get("title", "")).strip(),
            "date": str(article.get("published", "")).strip(),
            "source": str(article.get("source", "")).strip(),
            "link": str(article.get("url", "")).strip(),
        }
        for article in articles
    ]
    PUBLIC_JSON_PATH.write_text(
        json.dumps(public_articles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = []
    for article in public_articles:
        title = " ".join(article["title"].split())
        link = article["link"]
        date = _format_date(article["date"])
        if title and link:
            prefix = f"[{date}] " if date else ""
            lines.append(f"{prefix}{title} — {link}")
    PUBLIC_TXT_PATH.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _ensure_repository(repository, token):
    if (REPO_DIR / ".git").is_dir():
        return
    entries = [entry for entry in REPO_DIR.iterdir() if entry.name != ".gitkeep"]
    if entries:
        raise RuntimeError(f"Diretório de publicação não é um clone Git vazio: {REPO_DIR}")
    gitkeep = REPO_DIR / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()
    clone_url = f"https://github.com/{repository}.git"
    _run("git", "clone", clone_url, str(REPO_DIR))


def _publish(repository, token, user_name, user_email):
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY não configurado")
    if not token:
        raise RuntimeError("GITHUB_TOKEN não configurado")

    _ensure_repository(repository, token)
    _run("git", "config", "user.name", user_name, cwd=REPO_DIR)
    _run("git", "config", "user.email", user_email, cwd=REPO_DIR)
    _run("git", "add", "noticias.json", "noticias.txt", cwd=REPO_DIR)
    status = _run("git", "status", "--short", cwd=REPO_DIR).stdout.strip()
    if not status:
        print("Publicação: nada mudou")
        return

    message = f"Atualização automática {datetime.now(timezone.utc).isoformat(timespec='seconds')}"
    _run("git", "commit", "-m", message, cwd=REPO_DIR)
    auth_header = f"AUTHORIZATION: bearer {token}"
    _run("git", "-c", f"http.extraheader={auth_header}", "push", "origin", "main", cwd=REPO_DIR)
    print("Publicação: push realizado em main")


def main():
    articles = _load_articles()
    _write_public_files(articles)
    if os.environ.get("PUBLISH_TO_GITHUB", "true").lower() not in {"0", "false", "no"}:
        _publish(
            os.environ.get("GITHUB_REPOSITORY", ""),
            os.environ.get("GITHUB_TOKEN", ""),
            os.environ.get("GIT_USER_NAME", "Nova Terra News Bot"),
            os.environ.get("GIT_USER_EMAIL", "bot@novaterra.local"),
        )
    print(f"Publicação: {len(articles)} notícias exportadas")


if __name__ == "__main__":
    main()
