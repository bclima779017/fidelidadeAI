"""FastAPI application — backend para auditoria de fidelidade RAG/GEO."""

import logging
import sys
import os

# Adiciona o diretório services ao sys.path para que os imports existentes
# (import config, from utils import ..., etc.) funcionem sem modificação.
services_dir = os.path.join(os.path.dirname(__file__), "services")
sys.path.insert(0, services_dir)

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import config
from app.routers import extract, evaluate
from app.routers import sitemap_router, rag_router
from app.routers.evaluate import get_rag_instance
from app.schemas import HealthResponse

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("kipiai")

# ── Diagnóstico de configuração no startup ──
logger.info("=" * 60)
logger.info("CORS_ORIGINS configurado: %s", config.CORS_ORIGINS)
logger.info("GEMINI_API_KEY presente: %s", bool(config.GEMINI_API_KEY))
logger.info("PORT: %s", os.getenv("PORT", "(não definido, default 8000)"))
logger.info("=" * 60)

# ── Rate Limiter ──
limiter = Limiter(key_func=get_remote_address)

# ── Estado global da aplicação ──
_knowledge_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    global _knowledge_loaded
    try:
        import suggestions
        if suggestions.is_available():
            suggestions.load_knowledge()
            _knowledge_loaded = True
            logger.info("Base de conhecimento carregada com sucesso.")
        else:
            logger.warning("Base de conhecimento não encontrada — sugestões desabilitadas.")
    except Exception as e:
        logger.error("Erro ao carregar base de conhecimento: %s", e)

    yield

    logger.info("Encerrando backend.")


app = FastAPI(
    title="Kípiai GEO Audit API",
    description="Backend para auditoria automatizada de fidelidade RAG/GEO",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Rate Limiter ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)


# ── Global exception handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor."},
    )


# ── Routers ──
app.include_router(extract.router)
app.include_router(evaluate.router)
app.include_router(sitemap_router.router)
app.include_router(rag_router.router)


# ── Health Check ──
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    rag = get_rag_instance()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        knowledge_base_loaded=_knowledge_loaded,
        rag_indexed=rag is not None and rag.is_ready,
    )
