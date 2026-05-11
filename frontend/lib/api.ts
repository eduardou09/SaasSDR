"use client";

import { useAuth } from "@clerk/nextjs";
import { useOrganization } from "@clerk/nextjs";
import { useCallback } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";

function getFallbackBase(base: string): string | null {
  if (base.includes("127.0.0.1")) return base.replace("127.0.0.1", "localhost");
  if (base.includes("localhost")) return base.replace("localhost", "127.0.0.1");
  return null;
}

export function useApi() {
  const { getToken } = useAuth();
  const { organization } = useOrganization();

  const request = useCallback(
    async <T>(path: string, options: RequestInit = {}): Promise<T> => {
      const token = await getToken();
      let res: Response;
      try {
        const url = BASE.startsWith("http") ? `${BASE}${path}` : `${BASE}${path.replace("/api/v1", "")}`;
        res = await fetch(url, {
          ...options,
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(organization?.id ? { "X-Clerk-Org-Id": organization.id } : {}),
            ...(options.headers as Record<string, string>),
          },
        });
      } catch {
        const fallbackBase = getFallbackBase(BASE);
        if (fallbackBase) {
          try {
            const fallbackUrl = `${fallbackBase}${path}`;
            res = await fetch(fallbackUrl, {
              ...options,
              headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...(organization?.id ? { "X-Clerk-Org-Id": organization.id } : {}),
                ...(options.headers as Record<string, string>),
              },
            });
          } catch {
            throw new Error(
              `Falha de conexão com a API (${BASE} e ${fallbackBase}). Verifique backend ativo e NEXT_PUBLIC_API_URL.`,
            );
          }
        } else {
          throw new Error(
            `Falha de conexão com a API (${BASE}). Verifique backend ativo e NEXT_PUBLIC_API_URL.`,
          );
        }
      }
      if (res.status === 204) return undefined as T;
      const contentType = res.headers.get("content-type") ?? "";
      const body = contentType.includes("application/json")
        ? await res.json()
        : await res.text();
      if (!res.ok) {
        const detail =
          typeof body === "object" && body && "detail" in body
            ? String(body.detail)
            : typeof body === "string" && body
              ? body
              : `HTTP ${res.status}`;
        throw new Error(detail);
      }
      const json = body as T;
      return json as T;
    },
    [getToken, organization?.id],
  );

  return { request };
}
