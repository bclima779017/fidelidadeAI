/**
 * As 5 perguntas fixas da auditoria GEO.
 * Devem corresponder exatamente às perguntas em scoring.py no backend.
 */
export const QUESTIONS = [
  {
    key: "q1",
    text: "Qual é a proposta de valor da marca?",
    label: "Proposta de valor",
    placeholder:
      "Ex: A marca oferece solucoes de marketing digital com foco em resultados mensuraveis...",
    weight: 0.25,
  },
  {
    key: "q2",
    text: "Quais são os principais diferenciais competitivos?",
    label: "Diferenciais competitivos",
    placeholder:
      "Ex: Metodologia propria, equipe certificada pelo Google, atendimento personalizado...",
    weight: 0.2,
  },
  {
    key: "q3",
    text: "Qual é o público-alvo da marca?",
    label: "Publico-alvo",
    placeholder:
      "Ex: Empresas de medio porte do setor de tecnologia e e-commerce...",
    weight: 0.2,
  },
  {
    key: "q4",
    text: "Qual problema a marca resolve para seus clientes?",
    label: "Problema resolvido",
    placeholder:
      "Ex: Falta de visibilidade online e baixa conversao de leads em vendas...",
    weight: 0.15,
  },
  {
    key: "q5",
    text: "Quais são os principais produtos e/ou serviços?",
    label: "Produtos e servicos",
    placeholder:
      "Ex: SEO, gestao de trafego pago, automacao de marketing, consultoria estrategica...",
    weight: 0.2,
  },
] as const;

export const MIN_ANSWER_LENGTH = 10;
export const MAX_URL_LENGTH = 2048;
export const MIN_CONTENT_LENGTH = 100;
