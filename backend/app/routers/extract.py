"""Router para extração de conteúdo de sites."""

import logging

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import ExtractRequest, ExtractResponse
import scraper
import security

logger = logging.getLogger("kipiai.extract")

router = APIRouter(prefix="/api", tags=["extract"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/extract", response_model=ExtractResponse)
@limiter.limit("10/minute")
async def extract_content(request: Request, body: ExtractRequest) -> ExtractResponse:
    """Extrai texto visível de uma URL."""
    try:
        url = security.validate_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=security.safe_error_message(e))

    try:
        page = scraper._extract_single_page(url)
        return ExtractResponse(
            url=page["url"],
            title=page["title"],
            content=page["content"],
            char_count=page["char_count"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=security.safe_error_message(e))
    except Exception as e:
        safe_msg = security.safe_error_message(e)
        logger.error("Erro ao extrair conteúdo de %s: %s", body.url[:80], e)
        raise HTTPException(status_code=500, detail=f"Erro ao extrair conteúdo: {safe_msg}")
