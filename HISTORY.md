# Histórico de Implementação — Kípiai Audit

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
