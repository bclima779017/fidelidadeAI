# Auditoria de Fidelidade RAG/GEO — Kípiai

## Protocolo de Sessão

### Ao iniciar uma nova sessão:
1. **Ler `HISTORY.md`** para entender o contexto de construção, decisões anteriores e estado atual do projeto
2. **Revisão rápida do código recente**: rodar `git log --oneline -10` e `git diff HEAD~3 --stat` para identificar mudanças recentes
3. **Identificar possíveis otimizações** e reportar ao usuário antes de qualquer tarefa:
   - Código duplicado entre módulos
   - Imports não utilizados ou inconsistentes
   - Padrões quebrados (ex: módulo sem docstring, função sem type hints onde outros têm)
   - Oportunidades de performance (chamadas redundantes à API, cálculos repetidos)
   - Problemas de segurança (chaves expostas, inputs não validados)
4. **Apresentar resumo**: "Revisão concluída. X pontos de atenção encontrados." + lista curta com prioridade
5. Aguardar confirmação do usuário antes de aplicar qualquer otimização sugerida

### Ao encerrar uma sessão (quando o usuário solicitar com "registra histórico" ou similar):
1. **Registrar em `HISTORY.md`** uma entrada concisa no TOPO do arquivo (cronológico reverso)
2. Formato obrigatório:
   ```
   ## Sessão YYYY-MM-DD #N — Título curto do foco
   **Foco:** Descrição de uma linha
   - Bullet points das atividades principais (max 5-6 linhas)
   - **Decisões:** escolhas de design/arquitetura tomadas nesta sessão
   ```
3. Não incluir detalhes de implementação (o código e commits são a fonte de verdade)
4. Focar em **o quê** e **por quê**, não em **como**

## Visão Geral
Aplicação web Next.js + FastAPI para auditoria automatizada de fidelidade de respostas RAG/GEO.
O usuário informa a URL de um site (contexto via scraping), preenche 5 respostas do especialista,
e a IA compara as respostas extraídas do site com as do especialista, gerando um Score de Fidelidade (0-100).

## Arquitetura

```
backend/
  app/
    main.py                → FastAPI app: CORS, rate limiting, routers, lifespan
    schemas.py             → Modelos Pydantic (request/response validation)
    routers/
      extract.py           → POST /api/extract (página única, async)
      evaluate.py          → POST /api/evaluate (SSE: progress, result, done, error)
      sitemap_router.py    → POST /api/sitemap/discover + /api/extract/multi/stream (SSE)
      rag_router.py        → POST /api/rag/index, GET /api/rag/stats, DELETE /api/rag/clear
    services/
      config.py            → Configuração centralizada: .env + constantes + paths knowledge base
      utils.py             → Funções utilitárias (cosine_similarity, embed_texts_sync/async, parse_json_response)
      scraper.py           → Extração async de texto visível (httpx.AsyncClient)
      sitemap.py           → Descoberta async de URLs via sitemap.xml ou crawling (httpx)
      rag.py               → Pipeline RAG: chunking + embedding + retrieval semântico
      scoring.py           → Perguntas, pesos, scoring composto (semântico + claims)
      ai_handler.py        → Prompt de auditoria + chamada Gemini async (google-genai SDK)
      health.py            → EvalHealth: 5 indicadores de qualidade da avaliação
      suggestions.py       → Motor de matching: resultados → sugestões First-Claim rankeadas
      security.py          → Validação de URLs (anti-SSRF, DNS pinning), sanitização
      report_handler.py    → Relatório .xlsx (Resultados + Metadados RAG + Sugestões)
  knowledge/               → Base de conhecimento persistida (JSON + embeddings)

frontend/
  app/                     → Next.js App Router (pages, layout, globals.css)
  components/              → Componentes React (UI, layout, results, evaluation)
  lib/                     → Store (Zustand), API client, SSE client, types, constants

ingest_knowledge.py        → Script offline: PDF → knowledge_base.json + embeddings.npz
HISTORY.md                 → Histórico de sessões de desenvolvimento
```

## Fluxo de Execução (Next.js + FastAPI)

### Modo Página Única
1. Usuário informa URL → POST /api/extract → scraper async extrai texto visível
2. Usuário preenche respostas do especialista para 5 perguntas fixas
3. POST /api/evaluate via SSE: para cada pergunta, Gemini avalia
4. Frontend recebe eventos SSE (progress, result, done) e atualiza UI em tempo real
5. Resultados com score cards, gauges animados e tabela expandível

### Modo Site Completo (RAG)
1. Usuário informa URL → POST /api/sitemap/discover → sitemap async descobre páginas
2. Usuário seleciona páginas em tabela com checkboxes
3. POST /api/extract/multi/stream (SSE) → scraper async extrai em paralelo com progresso
4. POST /api/rag/index → chunking (~500 tokens) + embedding via gemini-embedding-001
5. Avaliação SSE com retrieval híbrido (keyword + semântico) → top-10 chunks por pergunta
6. Resultados com source attribution + relatório Excel

## 5 Perguntas Fixas
1. Qual é a proposta de valor da marca?
2. Quais são os principais diferenciais competitivos?
3. Qual é o público-alvo da marca?
4. Qual problema a marca resolve para seus clientes?
5. Quais são os principais produtos e/ou serviços?

## Premissas GEO (Manifesto Kípiai)
1. **Compreensibilidade**: Resposta clara sem distorcer conteúdo original
2. **Citação de Autoridade**: Claims técnicos, certificações, prêmios e dados preservados
3. **Preservação de Claims**: Nenhuma afirmação omitida, inventada ou alterada

## Escala de Score
- **90-100**: Semanticamente idêntica, todos os claims preservados
- **70-89**: Correta no essencial, detalhes secundários omitidos
- **50-69**: Parcialmente correta, omissões significativas
- **30-49**: Erros factuais ou claims inventados
- **0-29**: Incorreta, contraditória ou alucinada

## Configuração
- Copiar `.env.example` → `.env` e preencher `GEMINI_API_KEY`
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload` (porta 8000)
- Frontend: `cd frontend && npm install && npm run dev` (porta 3000)

## Modelo de IA
- **Gemini 2.5 Flash** com `temperature=0`, `top_p=1.0`, `top_k=1`
- **Gemini gemini-embedding-001** para embeddings no pipeline RAG
- Prompt retorna JSON estruturado, com fallback de parsing via regex

## Pipeline RAG
- **Chunking**: ~500 tokens (~2000 chars) com overlap de ~100 tokens, respeitando sentenças
- **Embedding**: gemini-embedding-001 em batches de até 100 chunks
- **Storage**: numpy arrays em memória (leve, efêmero por sessão)
- **Retrieval**: Híbrido (keywords por pergunta + similaridade cosseno) com boost por tipo de página
- **Deduplicação**: Chunks com cosseno > 0.92 removidos
- **Orçamento**: ~10 chunks x ~500 tokens = ~5k tokens de contexto focado por pergunta

## Convenções
- Linguagem do código: Python 3.10+ (backend), TypeScript (frontend)
- Comentários em português (PT-BR), logging via módulo `logging`
- Backend 100% async (httpx, google-genai async, FastAPI)
- SDK Google: `from google import genai` (novo SDK google-genai, não google-generativeai)
- Módulos independentes com responsabilidade única
- Retries com backoff exponencial para API Gemini
- Contexto truncado a 100k caracteres para respeitar limites do modelo
- Frontend: Next.js 14+ App Router, Tailwind CSS, Zustand, Motion, Sonner toasts
