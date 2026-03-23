"use client";

import React, { useState } from "react";
import { useAuditStore } from "@/lib/store";
import { Card } from "@/components/ui/Card";
import { TextArea } from "@/components/ui/TextArea";
import { Button } from "@/components/ui/Button";

const QUESTIONS = [
  {
    key: "q1",
    label: "1. Qual e a proposta de valor da marca?",
    placeholder:
      "Ex: A marca oferece solucoes de marketing digital com foco em resultados mensuraveis...",
  },
  {
    key: "q2",
    label: "2. Quais sao os principais diferenciais competitivos?",
    placeholder:
      "Ex: Metodologia propria, equipe certificada pelo Google, atendimento personalizado...",
  },
  {
    key: "q3",
    label: "3. Qual e o publico-alvo da marca?",
    placeholder:
      "Ex: Empresas de medio porte do setor de tecnologia e e-commerce...",
  },
  {
    key: "q4",
    label: "4. Qual problema a marca resolve para seus clientes?",
    placeholder:
      "Ex: Falta de visibilidade online e baixa conversao de leads em vendas...",
  },
  {
    key: "q5",
    label: "5. Quais sao os principais produtos e/ou servicos?",
    placeholder:
      "Ex: SEO, gestao de trafego pago, automacao de marketing, consultoria estrategica...",
  },
];

export function QuestionsForm() {
  const { expertAnswers, setAnswer, currentStep, setCurrentStep, setEvaluationStatus } =
    useAuditStore();
  const [error, setError] = useState<string | null>(null);

  const isCompleted = currentStep >= 3;

  function handleSubmit() {
    const filledCount = Object.values(expertAnswers).filter(
      (a) => a && a.trim()
    ).length;

    if (filledCount === 0) {
      setError("Preencha pelo menos uma resposta para prosseguir");
      return;
    }

    setError(null);
    setEvaluationStatus("running");
    setCurrentStep(3);
  }

  return (
    <Card title="2. Respostas do Especialista">
      <p className="text-sm text-kipiai-gray mb-4">
        Informe as respostas oficiais da marca para cada pergunta. A IA
        comparara com o conteudo extraido do site.
      </p>

      <div className="space-y-5">
        {QUESTIONS.map((q) => (
          <TextArea
            key={q.key}
            label={q.label}
            placeholder={q.placeholder}
            value={expertAnswers[q.key] || ""}
            onChange={(e) => setAnswer(q.key, e.target.value)}
            disabled={isCompleted}
            rows={3}
          />
        ))}
      </div>

      {error && (
        <p className="mt-3 text-sm text-kipiai-red">{error}</p>
      )}

      {!isCompleted && (
        <div className="mt-6">
          <Button onClick={handleSubmit}>
            Avaliar Fidelidade
          </Button>
        </div>
      )}
    </Card>
  );
}
