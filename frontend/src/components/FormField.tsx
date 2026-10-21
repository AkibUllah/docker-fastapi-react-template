import type { InputHTMLAttributes } from "react";
import { forwardRef } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(function FormField(
  { label, error, id, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  return (
    <div>
      <label htmlFor={inputId} className="label">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        className="input"
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? `${inputId}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});
