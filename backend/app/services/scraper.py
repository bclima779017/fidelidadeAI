"""Extração de texto visível de páginas web (página única e multi-página)."""

import requests
from bs4 import BeautifulSoup

import config
import security
from utils import clean_html_tags


def extract_site_content(url: str) -> str:
    """Extrai texto visível de uma URL, removendo scripts, styles e navegação."""
    page = _extract_single_page(url)
    return page["content"]


def _extract_single_page(url: str) -> dict:
    """Extrai conteúdo e título de uma única página.

    Returns:
        Dict com {url, title, content, char_count}.
    """
    url = security.validate_url(url)
    response = requests.get(
        url, headers=config.SCRAPER_HEADERS, timeout=30,
        allow_redirects=True, stream=True,
    )
    response.raise_for_status()
    security.check_content_length(response.headers)
    security.check_content_type_html(response.headers)
    raw = response.content[:security.MAX_RESPONSE_BYTES]
    response.close()

    soup = BeautifulSoup(raw, "html.parser")

    # Extrai título
    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()

    # Remover elementos de ruído
    clean_html_tags(soup)

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    return {
        "url": url,
        "title": title,
        "content": content,
        "char_count": len(content),
    }


def extract_multi_page_content(urls: list[str], progress_callback=None, health=None) -> list[dict]:
    """Extrai conteúdo de múltiplas URLs.

    Args:
        urls: Lista de URLs para extrair.
        progress_callback: Função(progress: float, text: str) para feedback.
        health: EvalHealth opcional para registrar páginas com extração fraca.

    Returns:
        Lista de dicts {url, title, content, char_count}.
    """
    results = []
    total = len(urls)

    for i, url in enumerate(urls):
        if progress_callback:
            progress_callback(i / total, f"Extraindo {i + 1}/{total}: {url[:60]}...")

        try:
            page = _extract_single_page(url)
            if page["content"].strip():
                results.append(page)
                if health is not None and page["char_count"] < health.poor_extraction_threshold:
                    health.poor_extraction_pages.append({
                        "url": page["url"],
                        "char_count": page["char_count"],
                    })
        except Exception as e:
            print(f"  [AVISO] Falha ao extrair {url}: {e}")
            continue

    if progress_callback:
        progress_callback(1.0, f"Extração concluída: {len(results)}/{total} páginas")

    return results
