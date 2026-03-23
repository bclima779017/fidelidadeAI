"""Router para extração de conteúdo de sites."""

from fastapi import APIRouter, HTTPException

from app.schemas import ExtractRequest, ExtractResponse
import scraper
import security

router = APIRouter(prefix="/api", tags=["extract"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest):
    """Extrai texto visível de uma URL."""
    try:
        url = security.validate_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        page = scraper._extract_single_page(url)
        return ExtractResponse(
            url=page["url"],
            title=page["title"],
            content=page["content"],
            char_count=page["char_count"],
        )
    except Exception as e:
        safe_msg = security.safe_error_message(e)
        raise HTTPException(status_code=502, detail=f"Erro ao extrair conteúdo: {safe_msg}")
