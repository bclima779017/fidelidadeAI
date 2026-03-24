# Histórico de Implementação — Kípiai Audit

## Sessão 2026-03-24 #2 — UX/Animações e Polish Visual
**Foco:** 10 melhorias de experiência, animação e dark mode no frontend Next.js
- Motion (framer-motion): transições AnimatePresence entre steps do wizard, staggered reveals nos ResultCards, expand/collapse animado
- Score Gauge radial: SVG animado substituindo números grandes nos ScoreCards, arco preenche com easing + cor dinâmica
- Sonner toasts: notificações por pergunta avaliada, conclusão e erros sem bloquear a UI
- Skeleton loading: placeholders pulsantes nos ScoreCards e ResultCards durante carregamento dinâmico
- Confetti (canvas-confetti): burst celebratório quando Score Final >= 90
- Dark mode: `next-themes` + toggle sol/lua no sidebar, `dark:` em todos os componentes
- Tooltips (Floating UI): hover nos indicadores de saúde explica cada métrica
- Auto-animate (@formkit): lista de perguntas anima ao adicionar resultados SSE
- Count-up nos gauges: scores animam de 0 ao valor final
- Async pipeline: google-genai nativo, httpx AsyncClient, avaliação concorrente (Semaphore+Queue)
- Heartbeat de avaliação: timer cronômetro + mensagens rotativas + cancel button
- Revisão ampla: RAG Lock, eval timeout, JSON validation, sitemap depth limit
- **Decisões:** Motion (~15KB) em vez de react-spring; Sonner em vez de react-hot-toast; SVG custom; dark mode via class strategy

## Sessão 2026-03-24 #1 — Frontend Next.js: Segurança, Sitemap, RAG e Avaliação
**Foco:** Migração completa do fluxo Streamlit para Next.js + FastAPI, segurança OWASP, e correção de bugs críticos
- Revisão OWASP: CORS restritivo, rate limiting (slowapi), API key via header, XXE protection (defusedxml), DNS rebinding, input validation
- Estabilidade: Error Boundary, AbortController no SSE, thread safety, logging estruturado
- Sitemap multi-página: endpoints `/api/sitemap/discover` e `/api/extract/multi/stream`, UI com tabela de seleção
- RAG indexing: endpoints `/api/rag/index`, `/api/rag/stats`, `/api/rag/clear`, integrado na avaliação SSE
- Fix crítico SSE: payload mismatch, React StrictMode abortava conexão
- Modal de boas-vindas, selo de saúde (Excelente/Boa/Mediana/Fraca)
- **Decisões:** SSE callbacks com `useAuditStore.getState()`; constantes centralizadas; overlay manual

## Sessão 2026-03-23 #1 — Hardening do Streamlit + Planejamento e Scaffold Next.js

**Foco:** Revisão completa do código Streamlit, correção de bugs críticos, robustez do pipeline de avaliação e início da migração para Next.js + FastAPI

### Parte 1 — Revisão e Hardening do Streamlit (master)

**Revisão de contexto (protocolo de sessão):**
- Leitura de `HISTORY.md` + `git log --oneline -10` + `git diff HEAD~3 --stat`
- Identificados 7 pontos de atenção; aplicados 3 safe fixes aprovados pelo usuário

**Fixes aplicados (6 commits em master):**

1. `4933c17` — **refactor: remover cálculos duplicados e dead code**
   - `main.py`: `calcular_score_ponderado()` era chamado 2x; `get_stats()` era chamado 2x
   - `suggestions.py`: `if` redundante em `contextualize_suggestion` (ambos caminhos retornavam `parsed`)

2. `133ffef` — **fix: reconstruir dicts ao gerar relatório cacheado**
   - `app.py`: `list(_results_tuple)` produzia lista de tuplas de pares `(k,v)`, não dicts
   - Pandas recebia colunas numéricas em vez de nomeadas → KeyError no DataFrame
   - Fix: `[dict(t) for t in _results_tuple]`

3. `a7a9dff` — **fix: garantir conclusão da avaliação mesmo com falhas parciais**
   - `app.py`: try/except em `_evaluate()` e `future.result()` — thread falhando não derruba o loop
   - `ai_handler.py`: try/except em `rag.retrieve()` — fallback ao contexto agregado quando embedding falha
   - `ai_handler.py`: proteger `response.text` que lança ValueError quando resposta é bloqueada pelo safety filter

4. `659b735` — **fix: modal de boas-vindas reaparecia a cada interação**
   - `@st.dialog` permite fechar clicando fora (Escape) sem acionar callback
   - Fix: marcar `welcome_dismissed = True` antes de chamar `show_welcome()`, garantindo exibição única por sessão

5. `5824a23` — **fix: robustez da avaliação — timeout, retry, concorrência e parciais**
   - `app.py`: `future.result(timeout=120s)` + `as_completed(timeout)` — API travada gera score -1
   - `utils.py`: `embed_texts()` com retry + backoff exponencial para rate limits
   - `config.py`: `MAX_THREADS: 3→2` (pico de ~9 chamadas API para ~6)
   - `app.py`: resultados parciais salvos no `session_state` a cada pergunta concluída

6. `cf90a4a` — **fix: TypeError no relatório — Score como string do cache**
   - `report_handler.py`: `pd.to_numeric(df["Score"], errors="coerce").fillna(-1)` antes de operações numéricas
   - Causa: `str(v)` na conversão hashable fazia pandas concatenar strings ao calcular `.mean()`

7. `5530855` — **fix: varredura defensiva — timeout global, relatório e score float**
   - `app.py`: capturar `TimeoutError` do iterador `as_completed()` (antes crashava sem finalizar)
   - `app.py`: try/except na geração e download do relatório Excel
   - `report_handler.py`: `int()` → `float()` na formatação condicional de scores

**Decisões de hardening:**
- 4 pontos de melhoria NÃO aplicados por incompatibilidade com Streamlit (closure no cache, dependência `@st.cache_resource`, extração paralela, dupla camada de cache de API key)
- Avaliação agora conclui em todos os cenários: timeout parcial/global, falha de API, falha de relatório

### Parte 2 — Planejamento da Migração Next.js + FastAPI

**Análise realizada:**
- Exploração completa da identidade visual do site www.kipiai.com (cores, tipografia, layout, padrões)
- Mapeamento exaustivo da arquitetura Streamlit: 6 seções UI, 12 módulos backend, fluxo de dados, estado
- Separação clara: 11 módulos Python são backend puro (95-100% reutilizáveis), apenas `app.py` é UI-coupled

**Decisões técnicas (alinhadas com o usuário):**
- Backend: FastAPI standalone (deploy independente)
- Frontend: Next.js 14+ (App Router) com Tailwind CSS
- Escopo: MVP incremental em 3 fases (Streamlit funciona em paralelo)
- Realtime: Server-Sent Events (SSE) para progresso da avaliação
- State: Zustand (cliente) + session ID (servidor)
- Isolamento: branch `feat/nextjs-frontend` (master = Streamlit intocado no Railway)
- Preview/QA: Vercel Preview (URL automática por push na branch)
- Brand: paleta extraída do site Kípiai (dark #080808, blue #116dff, Inter font)

**Fases planejadas:**
- Fase 1 (MVP): URL → extração → respostas → avaliação SSE → resultados
- Fase 2: RAG multi-página + sugestões First-Claim + relatório Excel
- Fase 3: Auth, dashboard/histórico, temas, animações, testes E2E, i18n

### Parte 3 — Scaffold Next.js + FastAPI (branch feat/nextjs-frontend)

**Commit `10aeae8` na branch `feat/nextjs-frontend` — 45 arquivos, 3758 linhas:**

**Backend FastAPI criado (`backend/`):**
- `app/main.py` — FastAPI app com CORS, health check, routers, sys.path para services
- `app/schemas.py` — Modelos Pydantic (ExtractRequest, EvaluateRequest, EvaluateResult, etc.)
- `app/routers/extract.py` — `POST /api/extract` chamando `scraper.extract_site_content()`
- `app/routers/evaluate.py` — `POST /api/evaluate` com SSE (eventos: progress, result, done, error)
- `app/services/` — 12 módulos Python copiados da raiz (raiz inalterada para Streamlit)
- `suggestions.py` adaptado: `@st.cache_resource` → `functools.lru_cache`, sem import streamlit
- `report_handler.py` adaptado: suporte a `return_bytes=True` retornando `(BytesIO, filename)`
- `backend/knowledge/` — knowledge_base.json + embeddings.npz copiados

**Frontend Next.js criado (`frontend/`):**
- Design system Kípiai: dark sidebar #080808, CTAs #116dff, Inter font, cards rounded-xl
- 6 componentes UI base: Button (3 variants), Card (collapsible), Input, TextArea, ProgressBar, Badge
- Layout responsivo: sidebar fixa 280px com StepIndicator (6 steps), hamburger mobile
- Landing page com hero e CTA "Iniciar Auditoria"
- Página `/audit` com fluxo condicional por step:
  - SiteInputForm (URL + extração)
  - QuestionsForm (5 text areas PT-BR com placeholders)
  - EvaluationProgress (conexão SSE, barra de progresso, status por pergunta)
  - ScoreCards (3 métricas) + ResultsTable (progress bars) + ResultCard (expandível com claims)
- `lib/store.ts` — Zustand store completo (url, content, answers, results, health, actions)
- `lib/api.ts` — fetch wrapper com error handling
- `lib/sse.ts` — SSE client via ReadableStream (progress/result/done/error)
- `lib/types.ts` — interfaces TypeScript para todo o pipeline

**Para testar localmente:**
```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload  # porta 8000
cd frontend && npm install && npm run dev  # porta 3000
```

**Decisões:**
- Módulos Python na raiz intocados (Streamlit Railway funcional)
- Imports dos services via sys.path (sem refatorar imports existentes)
- Avaliação sequencial no backend (ao invés de parallel) para evitar rate limits via SSE
- Sem persistência de estado — ephemeral por sessão (Fase 3 adicionará DB)

## Sessão 2026-03-20 #3 — UX, Scoring, Sugestões e Governança
**Foco:** Propostas de UX, painel de saúde, scoring composto, módulo de sugestões First Claim e protocolo de sessão
- Levantamento de 5 propostas de melhoria de UX/informação; usuário escolheu painel de saúde (4) para implementar
- Criado `health.py` (EvalHealth, 5 indicadores) integrado em todo o pipeline com thread safety
- Novo modelo de scoring composto: match semântico (peso 1) + taxa claims (peso 2) substituindo score subjetivo do Gemini
- Planejamento e implementação do módulo de sugestões: `ingest_knowledge.py`, `suggestions.py`, seção 5 no app, aba Excel
- Ingestão do "Protocolo First Claim.pdf" → 15 iniciativas estruturadas em `knowledge/` com embeddings pré-computados
- Criado `HISTORY.md` e protocolo de sessão no `CLAUDE.md` (auto-revisão ao abrir + registro ao encerrar)
- **Decisões:** opção B para sugestões (scores existentes, sem auditoria DOM); score Gemini mantido como referência; contextualização Gemini sob demanda (não automática)

## Sessão 2026-03-20 #2 — Scoring Composto + Painel de Saúde
**Foco:** Novo modelo de scoring e indicadores de qualidade da avaliação
- Novo scoring: match semântico via embeddings (peso 1) + taxa de claims (peso 2) = média ponderada
- Criado `health.py` — `EvalHealth` dataclass com 5 indicadores (truncamento, fallback JSON, retries, páginas fracas, chunks finos)
- Health integrado em todo o pipeline: `scraper.py` → `rag.py` → `ai_handler.py` → `app.py`
- Painel "Saúde da Avaliação" com `st.expander` + 5 `st.metric`, visível só com alertas
- **Decisões:** score Gemini mantido como referência; EvalHealth por thread com merge para thread safety

## Sessão 2026-03-20 #1 — Fundação e RAG
**Foco:** Construção inicial da aplicação completa
- Commit inicial com estrutura Streamlit (`app.py`, `main.py`, `config.py`, `scraper.py`)
- Pipeline RAG completo: `sitemap.py` (descoberta) → `rag.py` (chunking + embedding + retrieval híbrido)
- `ai_handler.py` com prompt de auditoria GEO, system instruction, retries e parsing JSON
- `scoring.py` com 5 perguntas fixas e pesos ponderados
- `report_handler.py` com Excel formatado + aba metadados RAG
- Módulo `security.py` para validação de URLs e conteúdo
- Avaliação paralela com `ThreadPoolExecutor` (max 3 threads)
- **Decisões:** Gemini 2.5 Flash com temp=0; chunking ~500 tokens com overlap; retrieval top-10

## Sessão 2026-03-19 — Projeto Inicial
**Foco:** Commit inicial do repositório
- Estrutura base do projeto criada
