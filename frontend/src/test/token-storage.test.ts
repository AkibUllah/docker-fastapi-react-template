import { tokenStorage } from "@/lib/token-storage";
import { sampleTokens } from "@/test/utils";

describe("tokenStorage", () => {
  it("persists tokens to localStorage and notifies subscribers", () => {
    const seen: Array<unknown> = [];
    const unsubscribe = tokenStorage.subscribe((t) => seen.push(t));
    tokenStorage.set(sampleTokens);
    expect(tokenStorage.get()).toEqual(sampleTokens);
    expect(JSON.parse(window.localStorage.getItem("starter.tokens") ?? "null")).toEqual(sampleTokens);
    tokenStorage.clear();
    expect(tokenStorage.get()).toBeNull();
    expect(window.localStorage.getItem("starter.tokens")).toBeNull();
    expect(seen).toEqual([sampleTokens, null]);
    unsubscribe();
    tokenStorage.set(sampleTokens);
    expect(seen).toHaveLength(2);
  });

  it("survives malformed storage content", () => {
    window.localStorage.setItem("starter.tokens", "{not json");
    tokenStorage.set(null); // reset cache
    window.localStorage.setItem("starter.tokens", "{not json");
    // force a re-read by constructing fresh state through clear + read path
    expect(() => tokenStorage.get()).not.toThrow();
  });
});
