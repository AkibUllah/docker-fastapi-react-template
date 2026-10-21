import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { authApi } from "@/api/auth";
import { errorMessage } from "@/api/client";
import { FormField } from "@/components/FormField";
import { useAuth } from "@/hooks/useAuth";

const schema = z
  .object({
    full_name: z.string().min(2, "Enter your name").max(120),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Za-z]/, "Include at least one letter")
      .regex(/\d/, "Include at least one digit"),
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, { path: ["confirm"], message: "Passwords do not match" });
type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async ({ confirm: _confirm, ...values }: FormValues) => {
    setServerError(null);
    try {
      await authApi.register(values);
      await login({ email: values.email, password: values.password });
      navigate("/", { replace: true });
    } catch (error) {
      setServerError(errorMessage(error, "Unable to register"));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="card w-full max-w-sm">
        <h1 className="mb-6 text-xl font-semibold">Create an account</h1>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <FormField label="Full name" autoComplete="name" {...register("full_name")} error={errors.full_name?.message} />
          <FormField label="Email" type="email" autoComplete="email" {...register("email")} error={errors.email?.message} />
          <FormField
            label="Password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
            error={errors.password?.message}
          />
          <FormField
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            {...register("confirm")}
            error={errors.confirm?.message}
          />
          {serverError && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300" role="alert">
              {serverError}
            </p>
          )}
          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create account"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Already registered?{" "}
          <Link to="/login" className="text-brand-600 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
