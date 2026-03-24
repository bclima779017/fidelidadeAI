"use client";

import React, { useState, useCallback } from "react";
import { useAuditStore } from "@/lib/store";
import { QUESTIONS, MIN_ANSWER_LENGTH } from "@/lib/constants";
import { Card } from "@/components/ui/Card";
import { TextArea } from "@/components/ui/TextArea";
import { Button } from "@/components/ui/Button";

export function QuestionsForm() {
  const expertAnswers = useAuditStore((s) => s.expertAnswers);
  const setAnswer = useAuditStore((s) => s.setAnswer);
  const currentStep = useAuditStore((s) => s.currentStep);
  const setCurrentStep = useAuditStore((s) => s.setCurrentStep);
  const setEvaluationStatus = useAuditStore((s) => s.setEvaluationStatus);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isCompleted = currentStep >= 3;

  const validate = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};
    let hasAnyFilled = false;

    for (const q of QUESTIONS) {
      const value = (expertAnswers[q.key] || "").trim();
      if (value) {
        hasAnyFilled = true;
        if (value.length < MIN_ANSWER_LENGTH) {
          newErrors[q.key] = `Resposta muito curta (minimo ${MIN_ANSWER_LENGTH} caracteres)`;
        }
      }
    }

    if (!hasAnyFilled) {
      newErrors._global = "Preencha pelo menos uma resposta para prosseguir";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [expertAnswers]);

  const handleSubmit = useCallback(() => {
    if (!validate()) return;
    setErrors({});
    setEvaluationStatus("running");
    setCurrentStep(3);
  }, [validate, setEvaluationStatus, setCurrentStep]);

  const filledCount = QUESTIONS.filter(
    (q) => (expertAnswers[q.key] || "").trim().length >= MIN_ANSWER_LENGTH
  ).length;

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
            label={q.text}
            placeholder={q.placeholder}
            value={expertAnswers[q.key] || ""}
            onChange={(e) => {
              setAnswer(q.key, e.target.value);
              if (errors[q.key]) {
                setErrors((prev) => {
                  const next = { ...prev };
                  delete next[q.key];
                  return next;
                });
              }
            }}
            disabled={isCompleted}
            rows={3}
            error={errors[q.key]}
            aria-required="true"
            maxLength={10000}
          />
        ))}
      </div>

      {errors._global && (
        <p className="mt-3 text-sm text-kipiai-red" role="alert">
          {errors._global}
        </p>
      )}

      {!isCompleted && (
        <div className="mt-6 flex items-center gap-4">
          <Button onClick={handleSubmit}>
            Avaliar Fidelidade
          </Button>
          <span className="text-sm text-kipiai-gray">
            {filledCount}/5 perguntas preenchidas
          </span>
        </div>
      )}
    </Card>
  );
}
