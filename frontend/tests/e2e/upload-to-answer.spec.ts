import { test, expect } from "@playwright/test";
import path from "path";

function uniqueEmail() {
  return `e2e-${Date.now()}@example.com`;
}

const PASSWORD = "e2e-password-123";

const SAMPLE_PDF = path.join(__dirname, "fixtures", "generate-sample-pdf.pdf");

test.describe("Upload to answer", () => {
  test("uploads a PDF and receives a streamed mock answer", async ({ page }) => {
    test.setTimeout(120_000);

    const email = uniqueEmail();

    // 1. Register a new user
    await page.goto("/register");
    await page.fill("#email", email);
    await page.fill("#password", PASSWORD);
    await page.fill("#confirmPassword", PASSWORD);
    await page.click('button:has-text("Create account")');
    await page.waitForURL("/chat");

    // 2. Upload the sample PDF
    await page.goto("/upload");
    await page.locator('input[type="file"]').setInputFiles(SAMPLE_PDF);

    await expect(page.getByText("generate-sample-pdf.pdf")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.locator('span:has-text("indexed")').first()).toBeVisible({
      timeout: 30_000,
    });

    // 3. Ask a question about the uploaded document
    await page.goto("/chat");
    await page.fill(
      'textarea[placeholder="Type a message..."]',
      "What is the capital of France?"
    );
    await page.click('button:has-text("Send")');

    // 4. Verify the streamed mock answer appears
    const answer = page.getByText(/Mock LLM/).first();
    await expect(answer).toBeVisible({ timeout: 60_000 });
  });
});
