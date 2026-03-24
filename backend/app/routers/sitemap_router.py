"""Router para descoberta de URLs via sitemap e extração multi-página."""

import asyncio
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
        urls = sitemap_service.discover_urls(url, max_pages=body.max_pages)
        return SitemapResponse(
            urls=[UrlInfo(**u) for u in urls],
            total=len(urls),
        )
    except Exception as e:
        logger.error("Erro ao descobrir URLs de %s: %s", body.url[:80], e)
        raise HTTPException(status_code=500, detail=security.safe_error_message(e))


@router.post("/extract/multi", response_model=MultiExtractResponse)
@limiter.limit("5/minute")
async def extract_multi(request: Request, body: MultiExtractRequest) -> MultiExtractResponse:
    """Extrai conteúdo de múltiplas URLs (resposta única)."""
    validated_urls = []
    for url in body.urls:
        try:
            validated_urls.append(security.validate_url(url))
        except ValueError:
            logger.warning("URL inválida ignorada: %s", url[:80])
            continue

    if not validated_urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL válida informada.")

    try:
        pages = scraper.extract_multi_page_content(validated_urls)
        return MultiExtractResponse(
            pages=[
                ExtractResponse(url=p["url"], title=p["title"], content=p["content"], char_count=p["char_count"])
                for p in pages
            ],
            total_extracted=len(pages),
            total_requested=len(validated_urls),
        )
    except Exception as e:
        logger.error("Erro na extração multi-página: %s", e)
        raise HTTPException(status_code=500, detail=security.safe_error_message(e))


async def _extract_stream(urls: list[str]) -> AsyncGenerator[str, None]:
    """Gera eventos SSE para extração página a página."""
    total = len(urls)
    extracted_pages = []

    for i, url in enumerate(urls):
        # Evento: extraindo
        yield f"data: {json.dumps({'type': 'extracting', 'current': i + 1, 'total': total, 'url': url[:120]}, ensure_ascii=False)}\n\n"

        try:
            page = await asyncio.to_thread(scraper._extract_single_page, url)
            if page["content"].strip():
                extracted_pages.append(page)
                yield f"data: {json.dumps({'type': 'extracted', 'current': i + 1, 'total': total, 'url': page['url'][:120], 'title': page.get('title', '')[:80], 'char_count': page['char_count']}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'failed', 'current': i + 1, 'total': total, 'url': url[:120], 'error': 'Conteudo vazio'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            safe_msg = security.safe_error_message(e)
            logger.warning("Falha ao extrair %s: %s", url[:80], e)
            yield f"data: {json.dumps({'type': 'failed', 'current': i + 1, 'total': total, 'url': url[:120], 'error': safe_msg}, ensure_ascii=False)}\n\n"

    # Evento done com todas as páginas extraídas
    pages_data = [
        {"url": p["url"], "title": p["title"], "content": p["content"], "char_count": p["char_count"]}
        for p in extracted_pages
    ]
    done_event = {
        "type": "done",
        "total_extracted": len(extracted_pages),
        "total_requested": total,
        "pages": pages_data,
    }
    yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"


@router.post("/extract/multi/stream")
@limiter.limit("5/minute")
async def extract_multi_stream(request: Request, body: MultiExtractRequest):
    """Extrai conteúdo de múltiplas URLs via SSE com progresso por página."""
    validated_urls = []
    for url in body.urls:
        try:
            validated_urls.append(security.validate_url(url))
        except ValueError:
            logger.warning("URL inválida ignorada: %s", url[:80])
            continue

    if not validated_urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL válida informada.")

    return StreamingResponse(
        _extract_stream(validated_urls),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
