"""FastAPI application — backend para auditoria de fidelidade RAG/GEO."""

import sys
import os

# Adiciona o diretório services ao sys.path para que os imports existentes
# (import config, from utils import ..., etc.) funcionem sem modificação.
services_dir = os.path.join(os.path.dirname(__file__), "services")
sys.path.insert(0, services_dir)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from app.routers import extract, evaluate
from app.schemas import HealthResponse


# ── Estado global da aplicação ──
_knowledge_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    global _knowledge_loaded
    # Carrega a base de conhecimento no startup
    try:
        import suggestions
        if suggestions.is_available():
            suggestions.load_knowledge()
            _knowledge_loaded = True
            print("[STARTUP] Base de conhecimento carregada com sucesso.")
        else:
            print("[STARTUP] Base de conhecimento não encontrada — sugestões desabilitadas.")
    except Exception as e:
        print(f"[STARTUP] Erro ao carregar base de conhecimento: {e}")

    yield  # Aplicação rodando

    # Shutdown
    print("[SHUTDOWN] Encerrando backend.")


app = FastAPI(
    title="Kípiai GEO Audit API",
    description="Backend para auditoria automatizada de fidelidade RAG/GEO",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(extract.router)
app.include_router(evaluate.router)


# ── Health Check ──
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        knowledge_base_loaded=_knowledge_loaded,
    )
