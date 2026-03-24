"use client";

import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "text-sm",
          duration: 4000,
        }}
        richColors
      />
    </ThemeProvider>
  );
}
