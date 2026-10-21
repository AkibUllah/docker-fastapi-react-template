import { api } from "@/api/client";
import { tokenStorage } from "@/lib/token-storage";
import type { TokenPair, User } from "@/types";

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput extends LoginInput {
  full_name: string;
}

export const authApi = {
  async login(input: LoginInput): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/login", input);
    tokenStorage.set(data);
    return data;
  },
  async register(input: RegisterInput): Promise<User> {
    const { data } = await api.post<User>("/auth/register", input);
    return data;
  },
  async me(): Promise<User> {
    const { data } = await api.get<User>("/auth/me");
    return data;
  },
  async logout(): Promise<void> {
    const tokens = tokenStorage.get();
    tokenStorage.clear();
    if (tokens) {
      await api.post("/auth/logout", { refresh_token: tokens.refresh_token }).catch(() => undefined);
    }
  },
};
