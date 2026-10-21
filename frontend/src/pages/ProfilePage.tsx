import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { usersApi } from "@/api/users";
import { FormField } from "@/components/FormField";
import { useAuth } from "@/hooks/useAuth";

const schema = z.object({
  full_name: z.string().min(2, "Enter your name").max(120),
  password: z
    .string()
    .optional()
    .refine((v) => !v || (v.length >= 8 && /[A-Za-z]/.test(v) && /\d/.test(v)), {
      message: "At least 8 characters with letters and digits",
    }),
});
type FormValues = z.infer<typeof schema>;

export function ProfilePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { full_name: user?.full_name ?? "" } });

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      usersApi.update(user!.id, { full_name: values.full_name, ...(values.password ? { password: values.password } : {}) }),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      reset({ full_name: updated.full_name, password: "" });
      setMessage({ kind: "ok", text: "Profile updated" });
    },
    onError: (error) => setMessage({ kind: "error", text: errorMessage(error) }),
  });

  if (!user) return null;

  return (
    <div className="max-w-md">
      <h1 className="mb-6 text-2xl font-semibold">Profile</h1>
      <form className="card space-y-4" onSubmit={handleSubmit((v) => mutation.mutate(v))} noValidate>
        <div>
          <p className="label">Email</p>
          <p className="text-sm">{user.email}</p>
        </div>
        <FormField label="Full name" {...register("full_name")} error={errors.full_name?.message} />
        <FormField
          label="New password (optional)"
          type="password"
          autoComplete="new-password"
          {...register("password")}
          error={errors.password?.message}
        />
        {message && (
          <p
            role="status"
            className={`rounded-md px-3 py-2 text-sm ${
              message.kind === "ok" ? "bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300" : "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300"
            }`}
          >
            {message.text}
          </p>
        )}
        <button type="submit" className="btn-primary" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving..." : "Save changes"}
        </button>
      </form>
    </div>
  );
}
