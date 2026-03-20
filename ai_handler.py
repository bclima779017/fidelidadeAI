import json
import re
import time
import google.generativeai as genai

_SYSTEM_INSTRUCTION = (
    "Você é um auditor RIGOROSO especializado em GEO (Generative Engine Optimization) e "
    "fidelidade de RAG. Sua função é avaliar com alto nível de exigência se uma resposta "
    "gerada por IA preserva com precisão as informações da fonte original da marca.\n\n"
    "REGRAS DE RIGOR:\n"
    "- Na dúvida entre dois scores, SEMPRE escolha o menor.\n"
    "- Claims generalizados ou reformulados com perda de especificidade DEVEM ser penalizados.\n"
    "- Dados quantitativos (números, percentuais, valores) omitidos ou alterados: penalidade mínima de 15 pontos.\n"
    "- Informações inventadas (hallucination) não presentes no contexto: score máximo de 40.\n"
    "- Omissão de claims centrais da marca: score máximo de 60.\n"
    "- Score acima de 90 é EXCEPCIONAL e exige preservação literal de todos os claims.\n\n"
    "Princípios do Manifesto GEO da Kípiai que você deve aplicar:\n"
    "1. COMPREENSIBILIDADE: A resposta deve ser clara e acessível, sem distorcer o conteúdo original.\n"
    "2. CITAÇÃO DE AUTORIDADE: Claims técnicos, certificações, prêmios e dados quantitativos "
    "devem ser preservados fielmente.\n"
    "3. PRESERVAÇÃO DE CLAIMS: Nenhuma afirmação da marca deve ser omitida, inventada ou alterada."
)

_MAX_CONTEXT_CHARS = 100_000

# Cache do modelo para evitar recriar a cada chamada
_cached_model = None
_cached_api_key = None


def _get_model(api_key: str) -> genai.GenerativeModel:
    """Retorna o modelo Gemini, configurando a API key se necessário."""
    global _cached_model, _cached_api_key
    if _cached_model is None or api_key != _cached_api_key:
        genai.configure(api_key=api_key)
        _cached_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=_SYSTEM_INSTRUCTION,
            generation_config=genai.GenerationConfig(
                temperature=0,
                top_p=1.0,
                top_k=1,
            ),
        )
        _cached_api_key = api_key
    return _cached_model


def build_prompt(context: str, question: str, official_answer: str, rag_mode: bool = False) -> str:
    """Constrói o prompt de auditoria GEO."""
    if len(context) > _MAX_CONTEXT_CHARS:
        context = context[:_MAX_CONTEXT_CHARS]
        print("  [AVISO] Contexto truncado para 100.000 caracteres.")

    rag_note = ""
    if rag_mode:
        rag_note = (
            "\nNOTA: O contexto abaixo foi recuperado de múltiplas páginas do site, "
            "selecionado por relevância semântica para esta pergunta. "
            "Cada trecho está rotulado com sua URL de origem. "
            "Considere TODOS os trechos ao formular sua resposta.\n"
        )

    return f"""## TAREFA DE AUDITORIA
{rag_note}
### Conteúdo original do site da marca (CONTEXTO):
{context}

### Pergunta estratégica:
{question}

### Resposta oficial esperada (ground truth):
{official_answer}

---

INSTRUÇÕES:
1. Com base EXCLUSIVAMENTE no contexto acima, responda à pergunta.
2. Compare sua resposta com a resposta oficial esperada.
3. ANTES de atribuir o score, analise EXPLICITAMENTE:
   a) Claims da resposta oficial que FORAM preservados na sua resposta
   b) Claims da resposta oficial que foram OMITIDOS ou generalizados
   c) Informações na sua resposta que NÃO constam no contexto original (hallucinations)
4. Atribua um score de 0 a 100 seguindo estes critérios RIGOROSOS:
   - 95-100: TODOS os claims preservados LITERALMENTE, incluindo dados quantitativos, nomes próprios, certificações. NENHUMA omissão, nenhuma generalização. Score excepcional e raro.
   - 85-94: Todos os claims principais preservados com dados quantitativos corretos, mas com reformulações menores que NÃO perdem informação factual.
   - 70-84: Claims principais presentes mas com omissões de detalhes secundários (ex: lista incompleta de serviços, dados numéricos parciais).
   - 50-69: Claims principais presentes mas com omissões significativas, generalizações que perdem especificidade, ou dados quantitativos ausentes.
   - 30-49: Erros factuais, claims inventados não presentes no contexto, ou omissões de claims centrais da marca.
   - 0-29: Resposta incorreta, contraditória ao contexto ou predominantemente alucinada.

5. Responda EXCLUSIVAMENTE no formato JSON abaixo, sem texto adicional:

{{
  "resposta_ia": "Sua resposta extraída do contexto",
  "score": <número inteiro de 0 a 100>,
  "claims_preservados": ["claim 1", "claim 2"],
  "claims_omitidos": ["claim omitido 1"],
  "hallucinations": ["informação inventada 1 (se houver)"],
  "justificativa": "Explicação concisa do score, citando claims preservados ou perdidos"
}}"""


def _parse_response(text: str) -> dict:
    """Tenta extrair JSON da resposta do modelo."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "resposta_ia": text,
        "score": -1,
        "justificativa": "[ERRO] Não foi possível interpretar a resposta do modelo.",
    }


def evaluate_question(context: str, question: str, official_answer: str, api_key: str = "", rag=None) -> dict:
    """Envia o prompt para o Gemini e retorna o resultado parseado.

    Se api_key não for fornecida, tenta usar a do config.
    Se rag (AuditRAG) for fornecido, usa retrieval semântico como contexto.

    Returns:
        Dict com resposta_ia, score, justificativa e opcionalmente fontes.
    """
    if not api_key:
        import config
        api_key = config.GEMINI_API_KEY

    if not api_key:
        return {
            "resposta_ia": "",
            "score": -1,
            "justificativa": "[ERRO] Chave da API Gemini não configurada.",
        }

    # Se RAG disponível, usa retrieval semântico
    sources = []
    rag_mode = False
    if rag is not None and rag.is_ready:
        context, sources = rag.retrieve(question)
        rag_mode = True

    model = _get_model(api_key)
    prompt = build_prompt(context, question, official_answer, rag_mode=rag_mode)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)

            if not response.text:
                result = {
                    "resposta_ia": "",
                    "score": -1,
                    "justificativa": "[BLOQUEADO] Resposta filtrada pelo modelo (safety filter).",
                }
                if sources:
                    result["fontes"] = sources
                return result

            result = _parse_response(response.text)
            if sources:
                result["fontes"] = sources
            return result

        except Exception as e:
            error_msg = str(e).lower()
            if attempt < max_retries - 1 and ("quota" in error_msg or "429" in error_msg or "resource" in error_msg):
                wait = 2 ** (attempt + 1)
                print(f"  [RETRY] Rate limit Gemini, aguardando {wait}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  [RETRY] Erro Gemini ({e}), tentando novamente em {wait}s...")
                time.sleep(wait)
            else:
                result = {
                    "resposta_ia": "",
                    "score": -1,
                    "justificativa": f"[ERRO] Falha após {max_retries} tentativas: {e}",
                }
                if sources:
                    result["fontes"] = sources
                return result
