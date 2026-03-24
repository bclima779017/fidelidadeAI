"""Configuração centralizada — variáveis de ambiente + constantes do pipeline."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"

# ── Limites de contexto ──
MAX_CONTEXT_CHARS = 100_000

# ── RAG Pipeline ──
CHUNK_SIZE = 2000          # ~500 tokens
CHUNK_OVERLAP = 400        # ~100 tokens
EMBEDDING_BATCH_SIZE = 100
RAG_TOP_K = 10
DEDUP_THRESHOLD = 0.92

# ── Scoring ──
PESO_SEMANTICO = 1
PESO_CLAIMS = 2
SUGGESTION_THRESHOLD_SCORE = 80

# ── Execução ──
MAX_RETRIES = 3
MAX_THREADS = 2            # Limitado para reduzir rate limits (cada thread faz ~3 chamadas API)
EVAL_TIMEOUT = 120         # Timeout por pergunta em segundos

# ── Health thresholds ──
POOR_EXTRACTION_THRESHOLD = 500   # chars
THIN_CHUNK_THRESHOLD = 200        # chars

# ── HTTP ──
SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── CORS (FastAPI) ──
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]

# ── Rate Limiting ──
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = os.getenv("RATE_LIMIT_WINDOW", "minute")
