"""Pipeline RAG leve: chunking, embedding e retrieval semântico."""

import re
import math
import numpy as np
import google.generativeai as genai

# Keywords por pergunta para retrieval híbrido
_QUESTION_KEYWORDS = {
    "proposta de valor": ["proposta de valor", "missão", "propósito", "visão", "valores"],
    "diferenciais competitivos": ["diferencial", "competitivo", "vantagem", "único", "exclusivo"],
    "público-alvo": ["público-alvo", "cliente", "persona", "consumidor", "audiência", "mercado"],
    "problema": ["problema", "solução", "dor", "necessidade", "desafio", "resolver"],
    "produtos": ["produto", "serviço", "oferta", "solução", "plataforma", "ferramenta"],
}

# Boost por tipo de página (detectado por URL/título)
_PAGE_TYPE_BOOST = {
    "about": {"proposta de valor": 1.3, "público-alvo": 1.2},
    "product": {"produtos": 1.4, "problema": 1.3, "diferenciais competitivos": 1.2},
    "service": {"produtos": 1.4, "problema": 1.3, "diferenciais competitivos": 1.2},
    "home": {"proposta de valor": 1.1, "diferenciais competitivos": 1.1, "público-alvo": 1.1,
             "problema": 1.1, "produtos": 1.1},
}

# Padrões para detectar tipo de página
_PAGE_TYPE_PATTERNS = {
    "about": ["sobre", "about", "quem-somos", "who-we-are", "nossa-historia", "institucional"],
    "product": ["produto", "product", "catalogo", "catalog"],
    "service": ["servico", "service", "solucao", "solution"],
    "home": [],  # Detectado separadamente
}


def _detect_page_type(url: str, title: str) -> str:
    """Detecta o tipo de página baseado na URL e título."""
    url_lower = url.lower()
    title_lower = title.lower() if title else ""

    # Homepage: path é / ou vazio
    from urllib.parse import urlparse
    path = urlparse(url_lower).path.strip("/")
    if not path or path == "index.html" or path == "index.php":
        return "home"

    for page_type, patterns in _PAGE_TYPE_PATTERNS.items():
        if page_type == "home":
            continue
        for pattern in patterns:
            if pattern in url_lower or pattern in title_lower:
                return page_type

    return "other"


def _get_question_key(question: str) -> str:
    """Mapeia uma pergunta para sua chave de keywords."""
    question_lower = question.lower()
    for key in _QUESTION_KEYWORDS:
        if key in question_lower:
            return key
    # Fallback por índice nas perguntas fixas
    if "proposta" in question_lower or "valor" in question_lower:
        return "proposta de valor"
    if "diferencia" in question_lower:
        return "diferenciais competitivos"
    if "público" in question_lower:
        return "público-alvo"
    if "problema" in question_lower:
        return "problema"
    if "produto" in question_lower or "serviço" in question_lower:
        return "produtos"
    return ""


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 400) -> list[str]:
    """Divide texto em chunks respeitando limites de sentença.

    Args:
        text: Texto a ser dividido.
        chunk_size: Tamanho alvo de cada chunk em caracteres (~500 tokens).
        overlap: Sobreposição entre chunks em caracteres (~100 tokens).

    Returns:
        Lista de chunks de texto.
    """
    if not text or not text.strip():
        return []

    if len(text) <= chunk_size:
        return [text.strip()]

    # Divide por sentenças
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text[:chunk_size].strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))

            # Calcula overlap: mantém últimas sentenças que cabem no overlap
            overlap_chunk = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) > overlap:
                    break
                overlap_chunk.insert(0, s)
                overlap_len += len(s) + 1

            current_chunk = overlap_chunk
            current_length = overlap_len

        current_chunk.append(sentence)
        current_length += sentence_len + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula similaridade cosseno entre dois vetores."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class AuditRAG:
    """Pipeline RAG para auditoria de fidelidade."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self._chunks: list[dict] = []  # {text, url, title, page_type, embedding}
        self._ingested = False

    def ingest(self, page_contents: list[dict], progress_callback=None) -> int:
        """Ingere conteúdo de múltiplas páginas: chunka e embeda.

        Args:
            page_contents: Lista de {url, title, content, char_count}.
            progress_callback: Função(progress: float, text: str) para feedback.

        Returns:
            Número total de chunks indexados.
        """
        self._chunks = []
        all_chunks = []

        # Fase 1: Chunking
        if progress_callback:
            progress_callback(0.0, "Dividindo conteúdo em chunks...")

        for page in page_contents:
            page_type = _detect_page_type(page["url"], page.get("title", ""))
            text_chunks = chunk_text(page["content"])
            for chunk_text_item in text_chunks:
                all_chunks.append({
                    "text": chunk_text_item,
                    "url": page["url"],
                    "title": page.get("title", ""),
                    "page_type": page_type,
                    "embedding": None,
                })

        if not all_chunks:
            return 0

        # Fase 2: Embedding em batches
        if progress_callback:
            progress_callback(0.3, f"Gerando embeddings para {len(all_chunks)} chunks...")

        batch_size = 100
        total_batches = math.ceil(len(all_chunks) / batch_size)

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(all_chunks))
            batch_texts = [c["text"] for c in all_chunks[start:end]]

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=batch_texts,
            )

            for i, embedding in enumerate(result["embedding"]):
                all_chunks[start + i]["embedding"] = np.array(embedding, dtype=np.float32)

            if progress_callback:
                progress = 0.3 + 0.7 * ((batch_idx + 1) / total_batches)
                progress_callback(progress, f"Embeddings: batch {batch_idx + 1}/{total_batches}")

        self._chunks = all_chunks
        self._ingested = True
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 10) -> tuple[str, list[str]]:
        """Recupera os chunks mais relevantes para uma query.

        Usa retrieval híbrido: pré-filtra por keywords, depois rankeia por embedding.
        Aplica boost por tipo de página e deduplicação.

        Args:
            query: Pergunta para busca.
            top_k: Número de chunks a retornar.

        Returns:
            Tupla (contexto_formatado, lista_de_fontes_urls).
        """
        if not self._chunks:
            return "", []

        # Embeda a query
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
        )
        query_embedding = np.array(result["embedding"], dtype=np.float32)

        question_key = _get_question_key(query)
        keywords = _QUESTION_KEYWORDS.get(question_key, [])

        # Calcula scores
        scored_chunks = []
        for chunk in self._chunks:
            if chunk["embedding"] is None:
                continue

            # Score semântico
            sim = _cosine_similarity(query_embedding, chunk["embedding"])

            # Boost por keyword match
            keyword_boost = 1.0
            if keywords:
                chunk_lower = chunk["text"].lower()
                matches = sum(1 for kw in keywords if kw in chunk_lower)
                if matches > 0:
                    keyword_boost = 1.0 + (0.1 * matches)

            # Boost por tipo de página
            page_boost = 1.0
            if question_key and chunk["page_type"] in _PAGE_TYPE_BOOST:
                page_boost = _PAGE_TYPE_BOOST[chunk["page_type"]].get(question_key, 1.0)

            final_score = sim * keyword_boost * page_boost
            scored_chunks.append((final_score, chunk))

        # Ordena por score decrescente
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Deduplicação: remove chunks muito similares (cosseno > 0.92)
        selected = []
        for score, chunk in scored_chunks:
            if len(selected) >= top_k * 2:  # Pega mais para ter margem após dedup
                break
            is_duplicate = False
            for _, sel_chunk in selected:
                sim = _cosine_similarity(chunk["embedding"], sel_chunk["embedding"])
                if sim > 0.92:
                    is_duplicate = True
                    break
            if not is_duplicate:
                selected.append((score, chunk))

        selected = selected[:top_k]

        # Formata contexto com atribuição de fonte
        context_parts = []
        sources = []
        seen_sources = set()

        for _, chunk in selected:
            title_label = f" ({chunk['title']})" if chunk["title"] else ""
            header = f"## Fonte: {chunk['url']}{title_label}"
            context_parts.append(f"{header}\n{chunk['text']}")

            if chunk["url"] not in seen_sources:
                seen_sources.add(chunk["url"])
                sources.append(chunk["url"])

        context = "\n\n".join(context_parts)
        return context, sources

    def get_stats(self) -> dict:
        """Retorna estatísticas do índice."""
        if not self._chunks:
            return {"total_chunks": 0, "total_pages": 0, "chunks_per_page": {}}

        pages = {}
        for chunk in self._chunks:
            url = chunk["url"]
            pages[url] = pages.get(url, 0) + 1

        return {
            "total_chunks": len(self._chunks),
            "total_pages": len(pages),
            "chunks_per_page": pages,
        }

    def clear(self):
        """Limpa o índice."""
        self._chunks = []
        self._ingested = False

    @property
    def is_ready(self) -> bool:
        return self._ingested and len(self._chunks) > 0
