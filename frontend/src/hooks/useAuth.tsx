import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { authApi, type LoginInput } from "@/api/auth";
import { tokenStorage } from "@/lib/token-storage";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (input: LoginInput) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasTokens, setHasTokens] = useState<boolean>(() => tokenStorage.get() !== null);

  useEffect(() => tokenStorage.subscribe((tokens) => setHasTokens(tokens !== null)), []);

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: hasTokens,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const login = useCallback(
    async (input: LoginInput) => {
      await authApi.login(input);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    [queryClient],
  );

  const logout = useCallback(async () => {
    await authApi.logout();
    queryClient.removeQueries({ queryKey: ["me"] });
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: hasTokens ? (meQuery.data ?? null) : null,
      isAuthenticated: hasTokens && !meQuery.isError,
      isLoading: hasTokens && meQuery.isPending,
      login,
      logout,
    }),
    [hasTokens, meQuery.data, meQuery.isError, meQuery.isPending, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
