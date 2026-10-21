import "@testing-library/jest-dom/vitest";

import { afterEach } from "vitest";

import { tokenStorage } from "@/lib/token-storage";

afterEach(() => {
  window.localStorage.clear();
  tokenStorage.clear();
});
