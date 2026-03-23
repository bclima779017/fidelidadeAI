import { ExtractResponse } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMessage = `Erro ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // keep default error message
    }
    throw new ApiError(errorMessage, response.status);
  }

  return response.json();
}

export async function extractContent(url: string): Promise<ExtractResponse> {
  return fetchApi<ExtractResponse>("/api/extract", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}
