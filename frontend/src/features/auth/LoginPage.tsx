import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { Navigate, useSearchParams } from "react-router"
import { z } from "zod"

import { ApiRequestError, unavailableMessage } from "../../shared/api/errors"
import { apiRequest, setProvenTenantId } from "../../shared/api/client"
import { Button } from "../../shared/components/Button"
import { Card } from "../../shared/components/Card"
import { ErrorStatus, FullScreen, LoadingStatus } from "../../shared/components/Status"
import { TextField } from "../../shared/components/TextField"
import { safeReturnTo, workspacePath } from "../../shared/navigation/items"
import type { Profile } from "../../shared/session/profile"
import { sessionQueryKey } from "../../shared/session/queryClient"
import { useSession } from "../../shared/session/useSession"

const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
})

type LoginValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const session = useSession()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const requested = safeReturnTo(params.get("return"))
  const [formError, setFormError] = useState<string | null>(null)
  const form = useForm<LoginValues>({ defaultValues: { email: "", password: "" } })

  if (session.isPending) {
    return (
      <FullScreen>
        <LoadingStatus />
      </FullScreen>
    )
  }
  if (session.isError) {
    return (
      <FullScreen>
        <ErrorStatus
          message={session.error instanceof ApiRequestError ? session.error.message : unavailableMessage()}
          onRetry={() => void session.refetch()}
        />
      </FullScreen>
    )
  }
  if (session.data) {
    return <Navigate to={workspacePath(session.data, requested)} replace />
  }

  async function onSubmit(values: LoginValues) {
    const parsed = loginSchema.safeParse(values)
    if (!parsed.success) {
      for (const issue of parsed.error.issues) {
        const field = issue.path[0]
        if (field === "email" || field === "password") form.setError(field, { message: issue.message })
      }
      return
    }
    setFormError(null)
    setProvenTenantId(null)
    try {
      const profile = await apiRequest<Profile>("/api/v1/auth/login", {
        method: "POST",
        body: parsed.data,
      })
      setProvenTenantId(profile.tenant?.id ?? null)
      queryClient.setQueryData(sessionQueryKey, profile)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 422) {
        for (const item of error.errors) {
          if (item.field === "email" || item.field === "password") {
            form.setError(item.field, { message: item.message })
          }
        }
        return
      }
      setFormError(error instanceof ApiRequestError ? error.message : unavailableMessage())
    }
  }

  return (
    <main className="login-screen">
      <Card>
        <h1>Sign in</h1>
        <form className="login-form" noValidate onSubmit={form.handleSubmit(onSubmit)}>
          <TextField
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            error={form.formState.errors.email?.message}
            {...form.register("email")}
          />
          <TextField
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            error={form.formState.errors.password?.message}
            {...form.register("password")}
          />
          {formError ? (
            <p className="form-error" role="alert">
              {formError}
            </p>
          ) : null}
          <Button type="submit" disabled={form.formState.isSubmitting} aria-busy={form.formState.isSubmitting}>
            Sign in
          </Button>
        </form>
      </Card>
    </main>
  )
}
