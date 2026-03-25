"""Extração de texto visível de páginas web — async com httpx."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

import httpx
from bs4 import BeautifulSoup

import config
import security
from utils import clean_html_tags

logger = logging.getLogger("kipiai.scraper")

# ── Cliente httpx reutilizável ──
_http_limits = httpx.Limits(
    max_connections=config.MAX_CONCURRENT_EXTRACTIONS + 2,
    max_keepalive_connections=config.MAX_CONCURRENT_EXTRACTIONS,
    keepalive_expiry=config.HTTP_KEEPALIVE_EXPIRY,
)


def _get_async_client() -> httpx.AsyncClient:
    """Cria um AsyncClient httpx com pooling."""
    return httpx.AsyncClient(
        limits=_http_limits,
        timeout=httpx.Timeout(config.HTTP_TIMEOUT, connect=config.HTTP_CONNECT_TIMEOUT),
        follow_redirects=True,
        headers=config.SCRAPER_HEADERS,
    )


def _parse_html(raw: bytes, url: str) -> dict:
    """Parseia HTML raw e retorna dict com conteúdo (CPU-bound, roda em thread)."""
    soup = BeautifulSoup(raw, "html.parser")

    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()

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


async def extract_single_page_async(url: str, client: httpx.AsyncClient | None = None) -> dict:
    """Extrai conteúdo de uma única página (async).

    Se client não for fornecido, cria um temporário.
    """
    url = security.validate_url(url)
    own_client = client is None

    if own_client:
        client = _get_async_client()

    try:
        response = await client.get(url)
        response.raise_for_status()
        security.check_redirect_count(response)
        security.check_content_length(dict(response.headers))
        security.check_content_type_html(dict(response.headers))

        raw = response.content[:security.MAX_RESPONSE_BYTES]

        # BeautifulSoup parsing é CPU-bound → thread
        page = await asyncio.to_thread(_parse_html, raw, str(response.url))
        return page
    finally:
        if own_client:
            await client.aclose()


async def extract_multi_page_async(
    urls: list[str],
    on_progress: Callable[..., Awaitable[None]] | None = None,
    health: "EvalHealth | None" = None,
) -> list[dict]:
    """Extrai conteúdo de múltiplas URLs em paralelo com semáforo.

    Args:
        urls: Lista de URLs para extrair.
        on_progress: Callback async (current, total, url, status, page) para progresso.
        health: EvalHealth opcional.

    Returns:
        Lista de dicts {url, title, content, char_count}.
    """
    results: list[dict] = []
    sem = asyncio.Semaphore(config.MAX_CONCURRENT_EXTRACTIONS)
    total = len(urls)

    async with _get_async_client() as client:
        async def _extract_one(i: int, url: str) -> dict | None:
            async with sem:
                try:
                    page = await extract_single_page_async(url, client)
                    if page["content"].strip():
                        if health is not None and page["char_count"] < health.poor_extraction_threshold:
                            health.poor_extraction_pages.append({
                                "url": page["url"],
                                "char_count": page["char_count"],
                            })
                        if on_progress:
                            await on_progress(i + 1, total, url, "extracted", page)
                        return page
                    else:
                        if on_progress:
                            await on_progress(i + 1, total, url, "empty", None)
                        return None
                except Exception as e:
                    logger.warning("Falha ao extrair %s: %s", url[:80], e)
                    if on_progress:
                        await on_progress(i + 1, total, url, "failed", None)
                    return None

        tasks = [_extract_one(i, url) for i, url in enumerate(urls)]
        pages = await asyncio.gather(*tasks)
        results = [p for p in pages if p is not None]

    return results
