"""Funções utilitárias compartilhadas entre módulos."""

import json
import re

import numpy as np
import google.generativeai as genai

import config

# ── Estado global da configuração Gemini ──
_configured_api_key: str | None = None


def ensure_genai_configured(api_key: str) -> None:
    """Configura a API Gemini apenas se a key mudou."""
    global _configured_api_key
    if api_key != _configured_api_key:
        genai.configure(api_key=api_key)
        _configured_api_key = api_key


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade cosseno entre dois vetores."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def embed_texts(texts: list[str] | str) -> list[list[float]]:
    """Gera embeddings via Gemini. Aceita string única ou lista.

    Returns:
        Lista de embeddings (cada um é list[float]).
    """
    single = isinstance(texts, str)
    if single:
        texts = [texts]

    result = genai.embed_content(
        model=config.GEMINI_EMBEDDING_MODEL,
        content=texts,
    )

    emb = result["embedding"]
    # embed_content retorna list[float] para input único, list[list[float]] para lista
    if single and not isinstance(emb[0], list):
        return [emb]
    return emb


def parse_json_response(text: str) -> tuple[dict | list, bool]:
    """Extrai JSON (object ou array) de texto do Gemini.

    Returns:
        (resultado_parseado, usou_fallback_regex)
    """
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        pass

    # Tenta extrair object {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group()), True
        except json.JSONDecodeError:
            pass

    # Tenta extrair array [...]
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group()), True
        except json.JSONDecodeError:
            pass

    return {"raw": text, "error": "parse_failed"}, True


def clean_html_tags(soup) -> None:
    """Remove tags de ruído de um BeautifulSoup (in-place)."""
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "noscript", "iframe", "svg"]):
        tag.decompose()
