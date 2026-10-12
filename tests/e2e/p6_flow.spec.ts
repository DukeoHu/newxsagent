import { expect, test } from "@playwright/test";

test("onboarding -> write -> supervision flow", async ({ page }) => {
  // Force simulator mode in E2E to avoid external LLM dependency.
  const current = await page.request.get("/api/settings/llm");
  const config = await current.json();
  await page.request.put("/api/settings/llm", {
    data: { ...config, mode: "simulator" },
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "项目" })).toBeVisible();

  await page.getByRole("button", { name: "新建项目" }).click();
  await page.getByLabel("项目名称 *").fill(`E2E项目-${Date.now()}`);
  await page.getByLabel("类型 *").fill("玄幻");
  await page.getByRole("button", { name: "创建" }).click();

  await expect(page.getByText("项目概览")).toBeVisible();

  await page.getByRole("link", { name: "引导" }).click();
  await expect(page.getByText("创作引导")).toBeVisible();
  await page.getByRole("button", { name: "开始引导问答" }).click();
  await page.getByPlaceholder("输入你的回答…").fill("一个少年在废弃邮局收到神秘来信。");
  await page.getByRole("button", { name: "发送" }).click();
  await page.getByPlaceholder("输入你的回答…").fill("主角林夕，冷静敏锐，想查明身世。");
  await page.getByRole("button", { name: "发送" }).click();
  await page.getByPlaceholder("输入你的回答…").fill("现代都市下有古物共鸣的隐秘规则。");
  await page.getByRole("button", { name: "发送" }).click();
  await page.getByRole("button", { name: "生成设定草案" }).click();
  await page.getByRole("button", { name: "应用引导草案到设定集" }).click();
  await expect(page.getByText("引导已完成")).toBeVisible();

  await page.getByRole("link", { name: "写作" }).click();
  await expect(page.getByText("触发 AI 写作任务")).toBeVisible();
  await page.getByRole("button", { name: "开始写作" }).click();
  await expect(page.getByText("任务进度")).toBeVisible();
  await expect(page.getByText("100%")).toBeVisible({ timeout: 25_000 });

  await page.getByRole("link", { name: "监督" }).click();
  await expect(page.getByText("查看风险项并执行确认、忽略或回滚")).toBeVisible();
  await expect(page.getByText("待处理")).toBeVisible();
});
