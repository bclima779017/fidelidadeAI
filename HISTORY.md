# Histórico de Implementação — Kípiai Audit

## Sessão 2026-03-20 #3 — Sugestões First Claim + Protocolo de Sessão
**Foco:** Módulo de sugestões baseado no Protocolo First Claim e governança de sessões
- Criado `ingest_knowledge.py` — ingestão de PDF → JSON estruturado (15 iniciativas) + embeddings
- Criado `suggestions.py` — motor de matching por critérios de ativação + relevância + impacto
- Integrado seção 5 no `app.py` com sugestões rankeadas e contextualização Gemini sob demanda
- Nova aba "Sugestões" no Excel (`report_handler.py`) com formatação condicional por impacto
- Criado `HISTORY.md` e atualizado `CLAUDE.md` com protocolo de sessão (revisão + histórico)
- **Decisões:** opção B para protótipo (usar scores existentes, sem auditoria de DOM/HTML)

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
