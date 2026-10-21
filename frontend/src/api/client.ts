import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { config } from "@/lib/config";
import { tokenStorage } from "@/lib/token-storage";
import type { ApiError, TokenPair } from "@/types";

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

/**
 * Build an axios instance with:
 *  - the bearer token attached from token storage,
 *  - a single in-flight refresh on 401 (concurrent requests share the promise),
 *  - the request retried once with the new token, or the session cleared.
 */
export function createApiClient(baseURL: string = config.apiBaseUrl): AxiosInstance {
  const client = axios.create({ baseURL, timeout: 15_000 });
  let refreshing: Promise<TokenPair | null> | null = null;

  const refreshTokens = async (): Promise<TokenPair | null> => {
    const current = tokenStorage.get();
    if (!current) return null;
    try {
      const { data } = await axios.post<TokenPair>(
        `${baseURL}/auth/refresh`,
        { refresh_token: current.refresh_token },
        { timeout: 15_000 },
      );
      tokenStorage.set(data);
      return data;
    } catch {
      tokenStorage.clear();
      return null;
    }
  };

  client.interceptors.request.use((request) => {
    const tokens = tokenStorage.get();
    if (tokens && !request.headers.Authorization) {
      request.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
    return request;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<ApiError>) => {
      const original = error.config as RetriableConfig | undefined;
      const isAuthRoute = original?.url?.includes("/auth/login") || original?.url?.includes("/auth/refresh");
      if (error.response?.status !== 401 || !original || original._retry || isAuthRoute || !tokenStorage.get()) {
        return Promise.reject(error);
      }
      original._retry = true;
      refreshing ??= refreshTokens().finally(() => {
        refreshing = null;
      });
      const tokens = await refreshing;
      if (!tokens) return Promise.reject(error);
      original.headers.Authorization = `Bearer ${tokens.access_token}`;
      return client(original);
    },
  );

  return client;
}

export const api = createApiClient();

/** Turn a FastAPI error payload into a single human-readable message. */
export function errorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError<ApiError>(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
    if (error.code === "ECONNABORTED") return "The request timed out";
    if (!error.response) return "Cannot reach the server";
  }
  return fallback;
}
