"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

const STORAGE_KEY = "kipiai_welcome_dismissed";

export function WelcomeModal() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (!dismissed) {
      setShow(true);
    }
  }, []);

  function handleDismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setShow(false);
  }

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop escuro */}
      <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" />

      {/* Modal */}
      <div className="relative bg-white dark:bg-kipiai-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-y-auto z-10 border border-gray-100 dark:border-gray-700/50">
        {/* Header */}
        <div className="bg-kipiai-gradient rounded-t-2xl px-8 py-6">
          <h2 className="text-2xl font-bold text-white">
            Bem-vindo a Auditoria de Fidelidade RAG/GEO
          </h2>
          <p className="text-white/70 mt-1 text-sm">
            Avalie se as respostas de IA preservam fielmente as informacoes do seu site
          </p>
        </div>

        {/* Content */}
        <div className="px-8 py-6 space-y-6">
          <div>
            <h3 className="text-base font-semibold text-kipiai-dark dark:text-white mb-3">
              Como funciona
            </h3>
            <div className="space-y-3">
              {[
                { step: 1, title: "Selecao do site", desc: "Informe a URL. Analise uma pagina ou o site completo." },
                { step: 2, title: "Selecao de paginas", desc: "No modo Site Completo, as paginas sao descobertas automaticamente via sitemap. Selecione quais incluir." },
                { step: 3, title: "Interpretacao das paginas", desc: "O conteudo visivel e extraido e processado para leitura pela IA." },
                { step: 4, title: "Preparo da base (chunking)", desc: "O conteudo e dividido em trechos e indexado semanticamente (RAG)." },
                { step: 5, title: "Respostas do especialista", desc: "Preencha as respostas oficiais da marca para 5 perguntas estrategicas." },
                { step: 6, title: "Relatorio final", desc: "A IA avalia cada resposta com um Score de Fidelidade (0-100)." },
              ].map((item) => (
                <div key={item.step} className="flex gap-3">
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-kipiai-gradient text-white flex items-center justify-center text-xs font-bold shadow-kipiai-sm">
                    {item.step}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-kipiai-dark dark:text-white">{item.title}</p>
                    <p className="text-xs text-kipiai-gray dark:text-gray-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Escala */}
          <div>
            <h3 className="text-base font-semibold text-kipiai-dark dark:text-white mb-3">
              Escala de avaliacao
            </h3>
            <div className="grid grid-cols-1 gap-1.5 text-sm">
              {[
                { range: "95-100", desc: "Todos os claims preservados literalmente", color: "bg-kipiai-green" },
                { range: "85-94", desc: "Claims principais corretos, reformulacoes minimas", color: "bg-kipiai-green" },
                { range: "70-84", desc: "Essencial presente, detalhes secundarios omitidos", color: "bg-kipiai-yellow" },
                { range: "50-69", desc: "Omissoes significativas ou generalizacoes", color: "bg-kipiai-yellow" },
                { range: "30-49", desc: "Erros factuais ou claims inventados", color: "bg-kipiai-red" },
                { range: "0-29", desc: "Resposta incorreta ou alucinada", color: "bg-kipiai-red" },
              ].map((item) => (
                <div key={item.range} className="flex items-center gap-3 py-1">
                  <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.color}`} />
                  <span className="font-mono text-kipiai-dark dark:text-white font-medium w-14">{item.range}</span>
                  <span className="text-kipiai-gray dark:text-gray-400">{item.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 py-5 border-t border-gray-100 dark:border-gray-700/50">
          <Button variant="gradient" onClick={handleDismiss} size="lg" className="w-full">
            Entendido! Vamos comecar
          </Button>
        </div>
      </div>
    </div>
  );
}
