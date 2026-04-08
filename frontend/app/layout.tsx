import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kipiai - Auditoria de Fidelidade GEO",
  description:
    "Auditoria automatizada de fidelidade de respostas RAG/GEO para marcas",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  openGraph: {
    title: "Kipiai - Auditoria de Fidelidade GEO",
    description:
      "Auditoria automatizada de fidelidade de respostas RAG/GEO para marcas",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <ErrorBoundary>
            <div className="flex min-h-screen">
              <Sidebar />
              <main className="flex-1 ml-0 md:ml-[280px] min-h-screen bg-kipiai-gray-50 dark:bg-kipiai-gray-900 transition-colors">
                {children}
              </main>
            </div>
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  );
}
