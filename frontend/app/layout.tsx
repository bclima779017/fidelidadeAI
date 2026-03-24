import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kipiai - Auditoria de Fidelidade GEO",
  description:
    "Auditoria automatizada de fidelidade de respostas RAG/GEO para marcas",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <ErrorBoundary>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-0 md:ml-[280px] min-h-screen bg-gray-50">
              {children}
            </main>
          </div>
        </ErrorBoundary>
      </body>
    </html>
  );
}
