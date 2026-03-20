"""Coletor de sinais de qualidade da avaliação (Saúde da Avaliação)."""

from dataclasses import dataclass, field


@dataclass
class EvalHealth:
    """Agrega indicadores de qualidade ao longo do pipeline de avaliação."""

    # Indicador 1: Truncamento de contexto
    context_truncated: bool = False
    context_original_chars: int = 0
    context_used_chars: int = 0

    # Indicador 2: Fallback de parsing JSON
    json_parse_failures: int = 0
    json_parse_details: list[str] = field(default_factory=list)

    # Indicador 3: Retries por rate-limit ou erro
    total_retries: int = 0
    retry_details: list[dict] = field(default_factory=list)

    # Indicador 4: Páginas com extração fraca (< 500 chars)
    poor_extraction_pages: list[dict] = field(default_factory=list)
    poor_extraction_threshold: int = 500

    # Indicador 5: Chunks finos (< 200 chars)
    thin_chunks: list[dict] = field(default_factory=list)
    thin_chunk_threshold: int = 200

    @property
    def pct_lost(self) -> float:
        if self.context_original_chars == 0:
            return 0.0
        return (1 - self.context_used_chars / self.context_original_chars) * 100

    @property
    def has_warnings(self) -> bool:
        return (
            self.context_truncated
            or self.json_parse_failures > 0
            or self.total_retries > 0
            or len(self.poor_extraction_pages) > 0
            or len(self.thin_chunks) > 0
        )

    def merge(self, other: "EvalHealth") -> None:
        """Mescla outro EvalHealth neste (usado para juntar resultados de threads)."""
        if other.context_truncated:
            self.context_truncated = True
            self.context_original_chars = max(self.context_original_chars, other.context_original_chars)
            self.context_used_chars = other.context_used_chars
        self.json_parse_failures += other.json_parse_failures
        self.json_parse_details.extend(other.json_parse_details)
        self.total_retries += other.total_retries
        self.retry_details.extend(other.retry_details)
        # poor_extraction_pages e thin_chunks não vêm de threads, não precisa mesclar
