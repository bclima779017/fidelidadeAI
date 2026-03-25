"""Funções utilitárias compartilhadas entre módulos."""

import asyncio
import json
import logging
import re
import threading

import numpy as np
from google import genai

import config

logger = logging.getLogger("kipiai.utils")

# ── Cliente Gemini (thread-safe, singleton) ──
_client_lock = threading.Lock()
_client: genai.Client | None = None
_client_api_key: str | None = None


def get_genai_client(api_key: str) -> genai.Client:
    """Retorna cliente Gemini singleton (thread-safe). Recria se a key mudar."""
    global _client, _client_api_key
    with _client_lock:
        if _client is None or api_key != _client_api_key:
            _client = genai.Client(api_key=api_key)
            _client_api_key = api_key
        return _client


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade cosseno entre dois vetores."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def embed_texts_sync(api_key: str, texts: list[str] | str) -> list[list[float]]:
    """Gera embeddings via Gemini (síncrono, com retry).

    Usado por módulos que ainda não são async (ex: rag.py ingest).
    """
    single = isinstance(texts, str)
    if single:
        texts = [texts]

    client = get_genai_client(api_key)

    import time
    for attempt in range(config.MAX_RETRIES):
        try:
            result = client.models.embed_content(
                model=config.GEMINI_EMBEDDING_MODEL,
                contents=texts,
            )
            emb = [e.values for e in result.embeddings]
            return emb
        except Exception as e:
            error_msg = str(e).lower()
            is_retryable = any(k in error_msg for k in ("429", "quota", "resource", "unavailable", "deadline"))
            if attempt < config.MAX_RETRIES - 1 and is_retryable:
                wait = 2 ** (attempt + 1)
                logger.warning("Embedding falhou (%s), aguardando %ds...", e, wait)
                time.sleep(wait)
            else:
                raise
    return []


async def embed_texts_async(api_key: str, texts: list[str] | str) -> list[list[float]]:
    """Gera embeddings via Gemini (async nativo, com retry)."""
    single = isinstance(texts, str)
    if single:
        texts = [texts]

    client = get_genai_client(api_key)

    for attempt in range(config.MAX_RETRIES):
        try:
            result = await client.aio.models.embed_content(
                model=config.GEMINI_EMBEDDING_MODEL,
                contents=texts,
            )
            emb = [e.values for e in result.embeddings]
            return emb
        except Exception as e:
            error_msg = str(e).lower()
            is_retryable = any(k in error_msg for k in ("429", "quota", "resource", "unavailable", "deadline"))
            if attempt < config.MAX_RETRIES - 1 and is_retryable:
                wait = 2 ** (attempt + 1)
                logger.warning("Embedding async falhou (%s), aguardando %ds...", e, wait)
                await asyncio.sleep(wait)
            else:
                raise
    return []


def parse_json_response(text: str) -> tuple[dict | list, bool]:
    """Extrai JSON (object ou array) de texto do Gemini.

    Returns:
        (resultado_parseado, usou_fallback_regex)
    """
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group()), True
        except json.JSONDecodeError:
            pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group()), True
        except json.JSONDecodeError:
            pass

    logger.warning("JSON parse falhou completamente. Texto (100 chars): %s", text[:100])
    return {"raw": text, "error": "parse_failed"}, True


def clean_html_tags(soup) -> None:
    """Remove tags de ruído de um BeautifulSoup (in-place)."""
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "noscript", "iframe", "svg"]):
        tag.decompose()

