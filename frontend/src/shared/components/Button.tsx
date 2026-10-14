import type { ButtonHTMLAttributes } from "react"

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary"
}

export function Button({ variant = "primary", className, type = "button", ...props }: ButtonProps) {
  const classes = ["button", `button-${variant}`, className].filter(Boolean).join(" ")
  return <button type={type} className={classes} {...props} />
}
