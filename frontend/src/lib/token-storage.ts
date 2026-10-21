import type { TokenPair } from "@/types";

const KEY = "starter.tokens";

type Listener = (tokens: TokenPair | null) => void;

/**
 * Tiny observable store for the token pair. Persisted to localStorage so a
 * reload keeps the session; listeners let React re-render on login/logout.
 * Swap this for an httpOnly-cookie strategy if the threat model requires it.
 */
class TokenStorage {
  private listeners = new Set<Listener>();
  private cache: TokenPair | null | undefined;

  get(): TokenPair | null {
    if (this.cache !== undefined) return this.cache;
    try {
      const raw = window.localStorage.getItem(KEY);
      this.cache = raw ? (JSON.parse(raw) as TokenPair) : null;
    } catch {
      this.cache = null;
    }
    return this.cache;
  }

  set(tokens: TokenPair | null): void {
    this.cache = tokens;
    try {
      if (tokens) window.localStorage.setItem(KEY, JSON.stringify(tokens));
      else window.localStorage.removeItem(KEY);
    } catch {
      // Storage may be unavailable (private mode); keep the in-memory copy.
    }
    this.listeners.forEach((listener) => listener(tokens));
  }

  clear(): void {
    this.set(null);
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export const tokenStorage = new TokenStorage();
