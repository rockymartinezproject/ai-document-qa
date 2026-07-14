import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright end-to-end test configuration.
 *
 * The config starts the backend and frontend dev servers automatically before
 * running tests. In CI the servers are always started fresh; locally an existing
 * server is reused if its health endpoint is already healthy.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: "cd ../backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: {
        DATABASE_URL: "sqlite+aiosqlite:///./e2e.db",
        SECRET_KEY: "test-secret-key-for-e2e",
        // Keep E2E fast and deterministic: use mock LLM and skip model downloads.
        OPENAI_API_KEY: "",
        ANTHROPIC_API_KEY: "",
        LOCAL_LLM_URL: "",
        DEFAULT_LLM_PROVIDER: "mock",
        RERANK_ENABLED: "false",
        HF_HUB_OFFLINE: "1",
      },
    },
    {
      // Build first, then serve the production app for more stable E2E runs.
      command: "npm run build && npm run start",
      url: "http://127.0.0.1:3000",
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
