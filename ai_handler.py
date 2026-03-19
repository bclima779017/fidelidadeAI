import json
import re
import time
import google.generativeai as genai

_SYSTEM_INSTRUCTION = (
    "Você é um auditor especializado em GEO (Generative Engine Optimization) e fidelidade "
    "de RAG. Sua função é avaliar se uma resposta gerada por IA preserva com precisão as "
    "informações da fonte original da marca.\n\n"
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
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_INSTRUCTION,
            generation_config=genai.GenerationConfig(
                temperature=0,
                top_p=1.0,
                top_k=1,
            ),
        )
        _cached_api_key = api_key
    return _cached_model


def build_prompt(context: str, question: str, official_answer: str) -> str:
    """Constrói o prompt de auditoria GEO."""
    if len(context) > _MAX_CONTEXT_CHARS:
        context = context[:_MAX_CONTEXT_CHARS]
        print("  [AVISO] Contexto truncado para 100.000 caracteres.")

    return f"""## TAREFA DE AUDITORIA

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
3. Atribua um score de 0 a 100 seguindo estes critérios:
   - 90-100: Resposta semanticamente idêntica, preserva todos os claims, dados e citações.
   - 70-89: Resposta correta no essencial, mas omite detalhes secundários ou reformula claims.
   - 50-69: Resposta parcialmente correta, com omissões significativas ou imprecisões.
   - 30-49: Resposta com erros factuais ou claims inventados não presentes no contexto.
   - 0-29: Resposta incorreta, contraditória ao contexto ou completamente alucinada.

4. Responda EXCLUSIVAMENTE no formato JSON abaixo, sem texto adicional:

{{
  "resposta_ia": "Sua resposta extraída do contexto",
  "score": <número inteiro de 0 a 100>,
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


def evaluate_question(context: str, question: str, official_answer: str, api_key: str = "") -> dict:
    """Envia o prompt para o Gemini e retorna o resultado parseado.

    Se api_key não for fornecida, tenta usar a do config.
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

    model = _get_model(api_key)
    prompt = build_prompt(context, question, official_answer)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)

            if not response.text:
                return {
                    "resposta_ia": "",
                    "score": -1,
                    "justificativa": "[BLOQUEADO] Resposta filtrada pelo modelo (safety filter).",
                }

            return _parse_response(response.text)

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
                return {
                    "resposta_ia": "",
                    "score": -1,
                    "justificativa": f"[ERRO] Falha após {max_retries} tentativas: {e}",
                }
