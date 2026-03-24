# Histórico de Implementação — Kípiai Audit

## Sessão 2026-03-24 #2 — UX/Animações e Polish Visual
**Foco:** 10 melhorias de experiência, animação e dark mode no frontend Next.js
- Motion (framer-motion): transições AnimatePresence entre steps do wizard, staggered reveals nos ResultCards, expand/collapse animado
- Score Gauge radial: SVG animado substituindo números grandes nos ScoreCards, arco preenche com easing + cor dinâmica
- Sonner toasts: notificações por pergunta avaliada, conclusão e erros sem bloquear a UI
- Skeleton loading: placeholders pulsantes nos ScoreCards e ResultCards durante carregamento dinâmico
- Confetti (canvas-confetti): burst celebratório quando Score Final >= 90
- Dark mode: `next-themes` + toggle sol/lua no sidebar, `dark:` em todos os componentes (inputs, cards, tabelas, backgrounds, scrollbars)
- Tooltips (Floating UI): hover nos indicadores de saúde explica cada métrica
- Auto-animate (@formkit): lista de perguntas anima ao adicionar resultados SSE
- Count-up nos gauges: scores animam de 0 ao valor final
- Novos componentes: `ScoreGauge`, `Tooltip`, `Skeleton`, `ThemeToggle`, `Providers`
- **Decisões:** Motion com LazyMotion (~15KB) em vez de react-spring; Sonner em vez de react-hot-toast (menor bundle); SVG custom em vez de lib de charts; dark mode via class strategy (Tailwind)

## Sessão 2026-03-24 #1 — Frontend Next.js: Segurança, Sitemap, RAG e Avaliação
**Foco:** Migração completa do fluxo Streamlit para Next.js + FastAPI, segurança OWASP, e correção de bugs críticos
- Revisão OWASP: CORS restritivo, rate limiting (slowapi), API key via header, XXE protection (defusedxml), DNS rebinding, input validation Pydantic
- Estabilidade: Error Boundary, AbortController no SSE, thread safety (threading.Lock), logging estruturado, exception handling específico
- Performance: React.memo, code splitting (next/dynamic), Zustand selectors otimizados, a11y (aria-label, role, scope)
- Sitemap multi-página: endpoints `/api/sitemap/discover` e `/api/extract/multi/stream` (SSE por página), UI com tabela de seleção + barra de progresso
- RAG indexing: endpoints `/api/rag/index`, `/api/rag/stats`, `/api/rag/clear`, integrado na avaliação SSE
- Fix crítico SSE: payload mismatch (`content`→`context`, `expert_answers`→`questions`), React StrictMode abortava conexão (removido cleanup de abort)
- Modal de boas-vindas: overlay fixo com 6 passos + escala de scores, localStorage para dismiss
- Selo de saúde: badge Excelente/Boa/Mediana/Fraca no HealthPanel com lógica de classificação
- Health + weighted_score emitidos no evento `done` do SSE
- Timeout SSE aumentado de 2min para 10min
- **Decisões:** SSE callbacks com `useAuditStore.getState()` em vez de closures React (evita StrictMode issues); constantes centralizadas em `constants.ts`; overlay manual em vez de `<dialog>` nativo (compatibilidade)

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
