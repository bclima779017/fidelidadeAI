"""Script de ingestão do PDF de conhecimento → knowledge_base.json + embeddings.npz.

Roda uma única vez (ou quando o PDF for atualizado).
Uso: python ingest_knowledge.py [--api-key SUA_KEY]
"""

import argparse
import json
import os
import sys

import numpy as np
import google.generativeai as genai

import config
from utils import ensure_genai_configured, embed_texts, parse_json_response

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
RAW_DIR = os.path.join(KNOWLEDGE_DIR, "raw")
OUTPUT_JSON = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
OUTPUT_EMB = os.path.join(KNOWLEDGE_DIR, "embeddings.npz")

_STRUCTURING_PROMPT = """Você receberá o texto completo de um protocolo de otimização da métrica First-Claim (GEO).

Extraia TODAS as iniciativas/parâmetros de auditoria do documento e retorne um JSON ARRAY.

Para cada iniciativa, retorne:
{
  "id": "FC-XX" (número sequencial),
  "titulo": "título curto e descritivo",
  "eixo": "nome do eixo (ex: Arquitetura Semântica e Textual)",
  "eixo_numero": 1,
  "descricao_profunda": "descrição completa da iniciativa",
  "implementacao_humana": "o que a equipe de conteúdo/dev precisa fazer",
  "parametro_auditoria": "o que o agente deve verificar",
  "gatilho_erro": "condição que indica falha",
  "impacto": "alto" | "medio" | "baixo",
  "perguntas_relacionadas": ["proposta de valor", "diferenciais competitivos", "público-alvo", "problema", "produtos"],
  "criterios_ativacao": {
    "score_max": número (sugestão ativa quando score < este valor),
    "match_semantico_max": número (sugestão ativa quando match < este valor),
    "taxa_claims_max": número (sugestão ativa quando taxa < este valor),
    "requer_hallucinations": boolean,
    "requer_claims_quantitativos": boolean
  }
}

REGRAS:
- "perguntas_relacionadas" deve conter APENAS valores desta lista: "proposta de valor", "diferenciais competitivos", "público-alvo", "problema", "produtos"
- "impacto" deve ser inferido pela severidade descrita (falha crítica = alto, proposta de melhoria = medio/baixo)
- "criterios_ativacao" devem ser calibrados pela criticidade (iniciativas fundamentais = score_max alto ~80, iniciativas avançadas = score_max baixo ~40)
- Retorne APENAS o JSON array, sem texto adicional.

TEXTO DO PROTOCOLO:
"""


def _extract_pdf_text(pdf_path: str) -> str:
    """Extrai texto completo do PDF."""
    try:
        import pdfplumber
    except ImportError:
        print("[ERRO] pdfplumber não instalado. Execute: pip install pdfplumber")
        sys.exit(1)

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

    return "\n\n".join(text_parts)


def _find_pdf() -> str:
    """Encontra o PDF na pasta raw/."""
    if not os.path.exists(RAW_DIR):
        print(f"[ERRO] Pasta {RAW_DIR} não existe.")
        sys.exit(1)

    pdfs = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        print(f"[ERRO] Nenhum PDF encontrado em {RAW_DIR}")
        sys.exit(1)

    if len(pdfs) > 1:
        print(f"[AVISO] Múltiplos PDFs encontrados, usando: {pdfs[0]}")

    return os.path.join(RAW_DIR, pdfs[0])


def _structure_with_gemini(text: str, api_key: str) -> list[dict]:
    """Envia o texto ao Gemini para estruturação em JSON."""
    ensure_genai_configured(api_key)
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL_NAME,
        generation_config=genai.GenerationConfig(temperature=0, top_p=1.0, top_k=1),
    )

    response = model.generate_content(_STRUCTURING_PROMPT + text)

    parsed, _ = parse_json_response(response.text)
    if isinstance(parsed, list):
        return parsed
    raise ValueError(f"Esperava JSON array, recebeu: {type(parsed)}")


def _generate_embeddings(initiatives: list[dict], api_key: str) -> np.ndarray:
    """Gera embeddings para cada iniciativa (título + descrição)."""
    ensure_genai_configured(api_key)

    texts = [
        f"{init['titulo']}. {init['descricao_profunda']}. {init['implementacao_humana']}"
        for init in initiatives
    ]

    embeddings = embed_texts(texts)
    return np.array(embeddings, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser(description="Ingestão do PDF de conhecimento First-Claim")
    parser.add_argument("--api-key", help="Gemini API Key (ou usar .env)")
    args = parser.parse_args()

    api_key = args.api_key
    if not api_key:
        api_key = config.GEMINI_API_KEY

    if not api_key:
        print("[ERRO] API key não fornecida. Use --api-key ou configure no .env")
        sys.exit(1)

    # 1. Encontrar e extrair PDF
    pdf_path = _find_pdf()
    print(f"[1/3] Extraindo texto de: {os.path.basename(pdf_path)}")
    pdf_text = _extract_pdf_text(pdf_path)
    print(f"       {len(pdf_text):,} caracteres extraídos")

    # 2. Estruturar via Gemini
    print("[2/3] Estruturando iniciativas via Gemini...")
    initiatives = _structure_with_gemini(pdf_text, api_key)
    print(f"       {len(initiatives)} iniciativas extraídas")

    # Salvar JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(initiatives, f, ensure_ascii=False, indent=2)
    print(f"       Salvo: {OUTPUT_JSON}")

    # 3. Gerar embeddings
    print("[3/3] Gerando embeddings...")
    embeddings = _generate_embeddings(initiatives, api_key)
    np.savez_compressed(OUTPUT_EMB, embeddings=embeddings)
    print(f"       Salvo: {OUTPUT_EMB} ({embeddings.shape})")

    print("\n[OK] Ingestão concluída com sucesso!")


if __name__ == "__main__":
    main()
