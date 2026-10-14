import { readFileSync, readdirSync, statSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")

function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const fullPath = path.join(directory, entry)
    if (statSync(fullPath).isDirectory()) return sourceFiles(fullPath)
    return /\.(ts|tsx|css)$/.test(entry) ? [fullPath] : []
  })
}

describe("token usage", () => {
  it("keeps brand hex, storage, and the session cookie out of the frontend source", () => {
    const files = sourceFiles(sourceRoot).filter((file) => !file.includes(`${path.sep}test${path.sep}`))
    expect(files.length).toBeGreaterThan(0)
    for (const file of files) {
      const text = readFileSync(file, "utf8")
      expect(text.toLowerCase()).not.toContain("#147d78")
      expect(text).not.toContain("localStorage")
      expect(text).not.toContain("sessionStorage")
      expect(text).not.toContain("ameen_session")
    }
  })
})
