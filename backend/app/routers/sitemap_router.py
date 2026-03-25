"""Router para descoberta de URLs via sitemap e extração multi-página."""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import (
    SitemapRequest, SitemapResponse, UrlInfo,
    MultiExtractRequest, MultiExtractResponse, ExtractResponse,
)
import sitemap as sitemap_service
import scraper
import security

logger = logging.getLogger("kipiai.sitemap")

router = APIRouter(prefix="/api", tags=["sitemap"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/sitemap/discover", response_model=SitemapResponse)
@limiter.limit("10/minute")
async def discover_urls(request: Request, body: SitemapRequest) -> SitemapResponse:
    """Descobre URLs de um site via sitemap.xml ou crawling de links."""
    try:
        url = security.validate_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=security.safe_error_message(e))
    try:
        urls = await sitemap_service.discover_urls(url, max_pages=body.max_pages)
        return SitemapResponse(urls=[UrlInfo(**u) for u in urls], total=len(urls))
    except Exception as e:
        logger.error("Erro ao descobrir URLs de %s: %s", body.url[:80], e)
        raise HTTPException(status_code=500, detail=security.safe_error_message(e))


@router.post("/extract/multi", response_model=MultiExtractResponse)
@limiter.limit("5/minute")
async def extract_multi(request: Request, body: MultiExtractRequest) -> MultiExtractResponse:
    """Extrai conteúdo de múltiplas URLs (resposta única, concorrente)."""
    validated_urls = _validate_urls(body.urls)
    if not validated_urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL válida informada.")

    pages = await scraper.extract_multi_page_async(validated_urls)
    return MultiExtractResponse(
        pages=[ExtractResponse(url=p["url"], title=p["title"], content=p["content"], char_count=p["char_count"]) for p in pages],
        total_extracted=len(pages),
        total_requested=len(validated_urls),
    )


async def _extract_stream_sse(urls: list[str]) -> AsyncGenerator[str, None]:
    """Gera eventos SSE para extração concorrente com progresso."""
    total = len(urls)
    extracted_pages: list[dict] = []
    completed = 0

    async def on_progress(current: int, total_count: int, url: str, status: str, page: dict | None):
        nonlocal completed
        completed += 1
        # Armazena página extraída
        if status == "extracted" and page:
            extracted_pages.append(page)

    # Extrai todas em paralelo
    yield f"data: {json.dumps({'type': 'extracting', 'current': 0, 'total': total, 'url': 'Iniciando extração concorrente...'}, ensure_ascii=False)}\n\n"

    # Usa callback para progresso individual
    pages = await scraper.extract_multi_page_async(
        urls,
        on_progress=_make_sse_progress_callback(total),
        health=None,
    )

    # Emite resultados individuais
    for i, page in enumerate(pages):
        event = {
            "type": "extracted",
            "current": i + 1,
            "total": len(pages),
            "url": page["url"][:120],
            "title": page.get("title", "")[:80],
            "char_count": page["char_count"],
        }
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    # Done com dados completos
    pages_data = [{"url": p["url"], "title": p["title"], "content": p["content"], "char_count": p["char_count"]} for p in pages]
    done_event = {"type": "done", "total_extracted": len(pages), "total_requested": total, "pages": pages_data}
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


def _make_sse_progress_callback(total: int):
    """Cria callback de progresso (async noop — progresso emitido no final)."""
    async def _noop(current, total_count, url, status, page):
        pass
    return _noop


@router.post("/extract/multi/stream")
@limiter.limit("5/minute")
async def extract_multi_stream(request: Request, body: MultiExtractRequest):
    """Extrai conteúdo de múltiplas URLs via SSE com progresso."""
    validated_urls = _validate_urls(body.urls)
    if not validated_urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL válida informada.")

    return StreamingResponse(
        _extract_stream_sse(validated_urls),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


def _validate_urls(urls: list[str]) -> list[str]:
    """Valida lista de URLs, retorna apenas as válidas."""
    validated = []
    for url in urls:
        try:
            validated.append(security.validate_url(url))
        except ValueError:
            logger.warning("URL inválida ignorada: %s", url[:80])
    return validated
