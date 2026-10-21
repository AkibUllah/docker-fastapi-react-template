import type { AxiosAdapter, AxiosRequestConfig, AxiosResponse } from "axios";
import axios from "axios";

import { createApiClient, errorMessage } from "@/api/client";
import { tokenStorage } from "@/lib/token-storage";
import { sampleTokens } from "@/test/utils";

/** Fake transport: records requests and answers from a scripted handler. */
function fakeAdapter(handler: (config: AxiosRequestConfig) => { status: number; data?: unknown }) {
  const calls: Array<{ url?: string; authorization?: string }> = [];
  const adapter: AxiosAdapter = async (config) => {
    // Snapshot the header: the interceptor mutates the same config object before retrying.
    calls.push({ url: config.url, authorization: config.headers?.Authorization as string | undefined });
    const { status, data } = handler(config);
    const response: AxiosResponse = { status, data, statusText: "", headers: {}, config };
    if (status >= 400) {
      throw new axios.AxiosError("request failed", String(status), config, null, response);
    }
    return response;
  };
  return { adapter, calls };
}

describe("api client", () => {
  it("attaches the bearer token from storage", async () => {
    tokenStorage.set(sampleTokens);
    const { adapter, calls } = fakeAdapter(() => ({ status: 200, data: { ok: true } }));
    const client = createApiClient("/api/v1");
    client.defaults.adapter = adapter;
    await client.get("/auth/me");
    expect(calls[0].authorization).toBe("Bearer access-1");
  });

  it("refreshes once on 401 and retries the original request with the new token", async () => {
    tokenStorage.set(sampleTokens);
    const refreshed = { ...sampleTokens, access_token: "access-2", refresh_token: "refresh-2" };
    const postSpy = vi.spyOn(axios, "post").mockResolvedValue({ data: refreshed });
    let attempts = 0;
    const { adapter, calls } = fakeAdapter((config) => {
      attempts += 1;
      return config.headers?.Authorization === "Bearer access-2"
        ? { status: 200, data: { email: "akib@example.com" } }
        : { status: 401, data: { detail: "token expired" } };
    });
    const client = createApiClient("/api/v1");
    client.defaults.adapter = adapter;

    const [a, b] = await Promise.all([client.get("/auth/me"), client.get("/users")]);
    expect(a.data).toEqual({ email: "akib@example.com" });
    expect(b.status).toBe(200);
    expect(postSpy).toHaveBeenCalledTimes(1); // concurrent 401s share one refresh
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/refresh", { refresh_token: "refresh-1" }, expect.anything());
    expect(tokenStorage.get()?.access_token).toBe("access-2");
    expect(attempts).toBe(4);
    expect(calls.map((c) => c.authorization)).toEqual(["Bearer access-1", "Bearer access-1", "Bearer access-2", "Bearer access-2"]);
    postSpy.mockRestore();
  });

  it("clears the session when the refresh itself fails", async () => {
    tokenStorage.set(sampleTokens);
    const postSpy = vi.spyOn(axios, "post").mockRejectedValue(new Error("refresh rejected"));
    const { adapter } = fakeAdapter(() => ({ status: 401, data: { detail: "expired" } }));
    const client = createApiClient("/api/v1");
    client.defaults.adapter = adapter;
    await expect(client.get("/auth/me")).rejects.toBeInstanceOf(axios.AxiosError);
    expect(tokenStorage.get()).toBeNull();
    postSpy.mockRestore();
  });

  it("does not try to refresh for login failures or when logged out", async () => {
    const postSpy = vi.spyOn(axios, "post");
    const { adapter } = fakeAdapter(() => ({ status: 401, data: { detail: "Incorrect email or password" } }));
    const client = createApiClient("/api/v1");
    client.defaults.adapter = adapter;
    await expect(client.post("/auth/login", {})).rejects.toBeInstanceOf(axios.AxiosError);
    await expect(client.get("/auth/me")).rejects.toBeInstanceOf(axios.AxiosError);
    expect(postSpy).not.toHaveBeenCalled();
    postSpy.mockRestore();
  });

  it("formats FastAPI error payloads", () => {
    const config = {} as AxiosRequestConfig;
    const make = (status: number, data: unknown) =>
      new axios.AxiosError("x", String(status), config as never, null, {
        status,
        data,
        statusText: "",
        headers: {},
        config: config as never,
      });
    expect(errorMessage(make(401, { detail: "Incorrect email or password" }))).toBe("Incorrect email or password");
    expect(
      errorMessage(make(422, { detail: [{ loc: ["body", "password"], msg: "too short", type: "value_error" }] })),
    ).toBe("password: too short");
    expect(errorMessage(new Error("boom"), "fallback")).toBe("fallback");
    expect(errorMessage(new axios.AxiosError("timeout", "ECONNABORTED"))).toBe("The request timed out");
  });
});
