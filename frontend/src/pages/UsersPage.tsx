import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { errorMessage } from "@/api/client";
import { usersApi } from "@/api/users";
import { Spinner } from "@/components/Spinner";
import { useAuth } from "@/hooks/useAuth";
import type { User } from "@/types";

const PAGE_SIZE = 10;

export function UsersPage() {
  const { user: me } = useAuth();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["users", offset],
    queryFn: () => usersApi.list(offset, PAGE_SIZE),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["users"] });
  const toggleActive = useMutation({
    mutationFn: (u: User) => usersApi.update(u.id, { is_active: !u.is_active }),
    onSuccess: invalidate,
    onError: (e) => setError(errorMessage(e)),
  });
  const toggleRole = useMutation({
    mutationFn: (u: User) => usersApi.update(u.id, { is_superuser: !u.is_superuser }),
    onSuccess: invalidate,
    onError: (e) => setError(errorMessage(e)),
  });
  const remove = useMutation({
    mutationFn: (u: User) => usersApi.remove(u.id),
    onSuccess: invalidate,
    onError: (e) => setError(errorMessage(e)),
  });

  if (query.isPending) return <Spinner label="Loading users" />;
  if (query.isError) return <p className="text-red-600">{errorMessage(query.error)}</p>;

  const { items, total } = query.data;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Users</h1>
        <span className="text-sm text-slate-500">{total} total</span>
      </div>
      {error && (
        <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => {
              const isMe = u.id === me?.id;
              return (
                <tr key={u.id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-4 py-3 font-medium">{u.email}</td>
                  <td className="px-4 py-3">{u.full_name || "-"}</td>
                  <td className="px-4 py-3">{u.is_superuser ? "Superuser" : "Member"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        u.is_active ? "bg-green-100 text-green-700" : "bg-slate-200 text-slate-600"
                      }`}
                    >
                      {u.is_active ? "active" : "disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button className="btn-secondary px-2 py-1 text-xs" disabled={isMe} onClick={() => toggleRole.mutate(u)}>
                        {u.is_superuser ? "Demote" : "Promote"}
                      </button>
                      <button className="btn-secondary px-2 py-1 text-xs" disabled={isMe} onClick={() => toggleActive.mutate(u)}>
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                      <button
                        className="btn-secondary px-2 py-1 text-xs text-red-600"
                        disabled={isMe}
                        onClick={() => window.confirm(`Delete ${u.email}?`) && remove.mutate(u)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm">
        <button className="btn-secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
          Previous
        </button>
        <span className="text-slate-500">
          Page {page} of {pages}
        </span>
        <button className="btn-secondary" disabled={page >= pages} onClick={() => setOffset(offset + PAGE_SIZE)}>
          Next
        </button>
      </div>
    </div>
  );
}
