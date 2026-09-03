import { expect, test } from "@playwright/test";

test("the management page displays the project and passed run created by the platform smoke", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/admin");

  await expect(page.getByRole("heading", { name: "项目列表" })).toBeVisible();
  await expect(page.getByText("delivery-smoke", { exact: true })).toBeVisible();
  await expect(page.getByText("e2e_generated_test.py", { exact: false })).toBeVisible();
  await expect(page.getByText("1 通过", { exact: true })).toBeVisible();
  await expect(page.getByText("API 测试报告", { exact: false })).toBeVisible();
});
