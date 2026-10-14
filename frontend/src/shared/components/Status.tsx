import type { ReactNode } from "react"

import { Button } from "./Button"
import { PageHeader } from "./PageHeader"

export function LoadingStatus({ label = "Loading" }: { label?: string }) {
  return (
    <p className="status" role="status">
      {label}
    </p>
  )
}

export function EmptyDestination({ title }: { title: string }) {
  return (
    <div className="status-block page">
      <PageHeader title={title} />
      <p>Nothing to show here yet.</p>
    </div>
  )
}

export function ErrorStatus({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="status-block" role="alert">
      <h1>Something went wrong</h1>
      <p>{message}</p>
      {onRetry ? <Button onClick={onRetry}>Try again</Button> : null}
    </div>
  )
}

export function AccessDenied({ message = "You do not have access to this page." }: { message?: string }) {
  return (
    <div className="status-block" role="alert">
      <h1>Access denied</h1>
      <p>{message}</p>
    </div>
  )
}

export function FullScreen({ children }: { children: ReactNode }) {
  return (
    <main className="fullscreen">
      <div className="card">{children}</div>
    </main>
  )
}
