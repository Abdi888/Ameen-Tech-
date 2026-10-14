import { forwardRef, type InputHTMLAttributes } from "react"

type TextFieldProps = {
  id: string
  label: string
  error?: string
} & InputHTMLAttributes<HTMLInputElement>

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { id, label, error, ...props },
  ref,
) {
  const errorId = `${id}-error`
  return (
    <div className="text-field">
      <label htmlFor={id}>{label}</label>
      <input
        ref={ref}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error ? (
        <p id={errorId} className="field-error">
          {error}
        </p>
      ) : null}
    </div>
  )
})
