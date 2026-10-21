import { useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";

interface Readiness {
  status: string;
  database: string;
  redis: string;
}

export function DashboardPage() {
  const { user } = useAuth();
  const readiness = useQuery({
    queryKey: ["health", "ready"],
    queryFn: async () => (await api.get<Readiness>("/health/ready")).data,
    refetchInterval: 30_000,
  });

  const items = [
    { label: "Signed in as", value: user?.email ?? "-" },
    { label: "Role", value: user?.is_superuser ? "Superuser" : "Member" },
    { label: "API", value: readiness.data?.status ?? (readiness.isError ? "unreachable" : "checking...") },
    { label: "Database", value: readiness.data?.database ?? "-" },
    { label: "Redis", value: readiness.data?.redis ?? "-" },
  ];

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Welcome{user?.full_name ? `, ${user.full_name}` : ""}</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div key={item.label} className="card">
            <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
            <p className="mt-1 text-lg font-medium">{item.value}</p>
          </div>
        ))}
      </div>
      <p className="mt-8 text-sm text-slate-500">
        This page is the starting point for a client project: replace the cards with the first real feature and keep the
        auth flow, API client and layout.
      </p>
    </div>
  );
}
