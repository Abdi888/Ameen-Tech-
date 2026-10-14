export type ApiFieldError = {
  code: string
  message: string
  field: string | null
}

export class ApiRequestError extends Error {
  readonly status: number
  readonly code: string
  readonly field: string | null
  readonly errors: ApiFieldError[]

  constructor(status: number, errors: ApiFieldError[]) {
    const first = errors[0]
    super(first?.message || "The service is unavailable. Try again.")
    this.name = "ApiRequestError"
    this.status = status
    this.code = first?.code ?? "INTERNAL_ERROR"
    this.field = first?.field ?? null
    this.errors = errors
  }
}

export function isAuthFailure(error: unknown): boolean {
  return error instanceof ApiRequestError && error.status === 401
}

export function isUnavailable(error: unknown): boolean {
  if (!(error instanceof ApiRequestError)) return true
  return error.status === 0 || error.status >= 500
}

export function unavailableMessage(): string {
  return "The service is unavailable. Try again."
}
