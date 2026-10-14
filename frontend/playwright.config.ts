import path from "node:path"
import { fileURLToPath } from "node:url"
import { defineConfig } from "@playwright/test"

const frontend = path.dirname(fileURLToPath(import.meta.url))
const backend = path.resolve(frontend, "../backend")
const databaseUrl = process.env.DATABASE_URL ?? "postgres://ameen:ameen@localhost:5432/ameen_retail_e2e"

process.env.DJANGO_SETTINGS_MODULE ??= "config.settings.test"
process.env.SECRET_KEY ??= "test-only-not-for-production"
process.env.DEBUG ??= "false"
process.env.ALLOWED_HOSTS ??= "localhost,127.0.0.1"
process.env.DATABASE_URL = databaseUrl
process.env.CORS_ALLOWED_ORIGINS ??= "http://localhost:5173"

const djangoEnv = {
  DJANGO_SETTINGS_MODULE: process.env.DJANGO_SETTINGS_MODULE,
  SECRET_KEY: process.env.SECRET_KEY,
  DEBUG: process.env.DEBUG,
  ALLOWED_HOSTS: process.env.ALLOWED_HOSTS,
  DATABASE_URL: databaseUrl,
  CORS_ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGINS,
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "python -m uv run python ../frontend/e2e/prepare_database.py && python -m uv run python manage.py runserver localhost:8000 --noreload",
      cwd: backend,
      url: "http://localhost:8000/api/v1/health",
      reuseExistingServer: false,
      timeout: 120_000,
      env: djangoEnv,
    },
    {
      command: "npm run dev -- --host localhost --port 5173 --strictPort",
      cwd: frontend,
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 } } },
  ],
})
