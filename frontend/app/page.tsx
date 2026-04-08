"use client";

import Link from "next/link";
import { motion } from "motion/react";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
      <motion.div
        className="max-w-2xl text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <motion.h1
          className="text-5xl font-bold mb-2"
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <span className="gradient-text">Kipiai</span>
        </motion.h1>
        <p className="text-lg text-kipiai-gray dark:text-gray-400 mb-4 tracking-wide">
          Auditoria de Fidelidade GEO
        </p>

        <motion.div
          className="bg-white dark:bg-kipiai-gray-800 rounded-xl shadow-kipiai-sm border border-gray-100 dark:border-gray-800/50 p-8 mb-8 text-left"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <h2 className="text-2xl font-semibold text-kipiai-dark dark:text-white mb-4">
            O que esta ferramenta faz?
          </h2>
          <p className="text-kipiai-gray dark:text-gray-400 mb-4">
            A Auditoria de Fidelidade GEO verifica se as respostas geradas por IA
            (RAG/GEO) preservam fielmente o conteudo original do seu site.
          </p>
          <ul className="space-y-3 text-kipiai-gray dark:text-gray-400 mb-6">
            {[
              { n: 1, title: "Extracao de contexto", desc: "o conteudo do site e extraido automaticamente" },
              { n: 2, title: "Respostas do especialista", desc: "voce informa as respostas oficiais para 5 perguntas-chave" },
              { n: 3, title: "Avaliacao por IA", desc: "o Gemini compara as respostas e gera um Score de Fidelidade (0-100)" },
              { n: 4, title: "Relatorio detalhado", desc: "resultados com claims analisados, sugestoes e metricas" },
            ].map((item, i) => (
              <motion.li
                key={item.n}
                className="flex items-start gap-3"
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.3 + i * 0.08 }}
              >
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-kipiai-gradient text-white text-xs font-bold flex items-center justify-center mt-0.5">{item.n}</span>
                <span><strong>{item.title}</strong> — {item.desc}</span>
              </motion.li>
            ))}
          </ul>

          <div className="bg-kipiai-gray-50 dark:bg-kipiai-gray-900 rounded-lg p-4 border border-gray-100 dark:border-gray-800/50">
            <h3 className="text-sm font-semibold text-kipiai-dark dark:text-white mb-2">Escala de Score</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                { color: "bg-kipiai-green", text: "90-100: Fidelidade excelente" },
                { color: "bg-kipiai-green opacity-70", text: "70-89: Essencialmente correta" },
                { color: "bg-kipiai-yellow", text: "50-69: Parcialmente correta" },
                { color: "bg-kipiai-red", text: "0-49: Problemas significativos" },
              ].map((item) => (
                <div key={item.text} className="flex items-center gap-2 text-kipiai-gray dark:text-gray-400">
                  <span className={`w-3 h-3 rounded-full ${item.color}`} />
                  <span>{item.text}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        >
          <Link
            href="/audit"
            className="group inline-flex items-center gap-2 bg-kipiai-gradient text-white font-semibold py-3 px-8 rounded-lg transition-all text-lg shadow-kipiai-md hover:shadow-kipiai-lg hover:-translate-y-0.5"
          >
            Iniciar Auditoria
            <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-1">
              <path d="M5 12h14" /><path d="m12 5 7 7-7 7" />
            </svg>
          </Link>
        </motion.div>
      </motion.div>
    </div>
  );
}
