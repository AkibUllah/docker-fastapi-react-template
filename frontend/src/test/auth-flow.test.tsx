import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";

import { authApi } from "@/api/auth";
import type * as AuthModule from "@/api/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { tokenStorage } from "@/lib/token-storage";
import { LoginPage } from "@/pages/LoginPage";
import { renderWithProviders, sampleTokens, sampleUser } from "@/test/utils";

vi.mock("@/api/auth", async (importOriginal) => {
  const actual = await importOriginal<typeof AuthModule>();
  return {
    ...actual,
    authApi: { ...actual.authApi, login: vi.fn(), me: vi.fn(), logout: vi.fn() },
  };
});

const mocked = vi.mocked(authApi);

function Shell() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<h1>Dashboard</h1>} />
        <Route element={<ProtectedRoute requireSuperuser />}>
          <Route path="/users" element={<h1>Users admin</h1>} />
        </Route>
      </Route>
    </Routes>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("auth flow", () => {
  it("redirects anonymous visitors to /login and back after signing in", async () => {
    mocked.login.mockImplementation(async () => {
      tokenStorage.set(sampleTokens);
      return sampleTokens;
    });
    mocked.me.mockResolvedValue(sampleUser);

    renderWithProviders(<Shell />, { route: "/" });
    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email/i), "akib@example.com");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(mocked.login).toHaveBeenCalledWith({ email: "akib@example.com", password: "secret123" });
  });

  it("shows validation errors before calling the API", async () => {
    renderWithProviders(<LoginPage />, { route: "/login" });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.type(screen.getByLabelText(/password/i), "short");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    expect(mocked.login).not.toHaveBeenCalled();
  });

  it("shows the server error message when credentials are rejected", async () => {
    mocked.login.mockRejectedValue(new Error("nope"));
    renderWithProviders(<LoginPage />, { route: "/login" });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email/i), "akib@example.com");
    await user.type(screen.getByLabelText(/password/i), "secret123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to sign in");
  });

  it("keeps non-superusers out of superuser routes", async () => {
    tokenStorage.set(sampleTokens);
    mocked.me.mockResolvedValue(sampleUser);
    renderWithProviders(<Shell />, { route: "/users" });
    await waitFor(() => expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument());
    expect(screen.queryByText("Users admin")).not.toBeInTheDocument();
  });

  it("lets superusers into /users", async () => {
    tokenStorage.set(sampleTokens);
    mocked.me.mockResolvedValue({ ...sampleUser, is_superuser: true });
    renderWithProviders(<Shell />, { route: "/users" });
    expect(await screen.findByText("Users admin")).toBeInTheDocument();
  });
});
