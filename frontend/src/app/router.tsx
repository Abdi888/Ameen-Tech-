import type { RouteObject } from "react-router"

import { LoginPage } from "../features/auth/LoginPage"
import { AppShell } from "./layout/AppShell"
import { PlatformBoundary } from "./layout/PlatformBoundary"
import { Permitted, RequireSession, TenantGate, UnavailablePage } from "./guards"
import { RootRedirect } from "./RootRedirect"
import { destinations } from "../shared/navigation/items"

export const appRoutes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireSession />,
    children: [
      { path: "/", element: <RootRedirect /> },
      { path: "/platform", element: <PlatformBoundary /> },
      { path: "/platform/*", element: <PlatformBoundary /> },
      {
        path: "/app",
        element: <TenantGate />,
        children: [
          {
            element: <AppShell />,
            children: [
              { index: true, element: <RootRedirect /> },
              ...destinations.map((destination) => ({
                path: destination.path,
                element: <Permitted path={destination.path} />,
              })),
              { path: "*", element: <UnavailablePage /> },
            ],
          },
        ],
      },
      { path: "*", element: <RootRedirect /> },
    ],
  },
]
