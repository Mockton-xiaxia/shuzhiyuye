"""截取 8 张功能页真实截图，对照 README/SCREENSHOTS 命名。"""
from __future__ import annotations

import asyncio
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
BASE = "http://127.0.0.1:5173"
CREDS = ("gov_admin", "123456")

# (文件名, 路径, 等待毫秒)
SHOTS = [
    ("01-gov-workbench.png", "/gov/workbench", 2500),
    ("02-gov-cockpit.png", "/gov/cockpit", 5000),
    ("03-gis-pond-collect.png", "/gov/party/gis-collect", 4000),
    ("04-quality-policy.png", "/gov/quality/policies", 2500),
    ("05-trace-stats.png", "/gov/trace/label-stats", 2500),
    ("06-ezviz-config.png", "/gov/iot/ezviz", 2500),
    ("07-supply-equipment.png", "/gov/supply/equip", 2500),
    ("08-domestication-stats.png", "/gov/specialty/domestication", 3500),
]


async def login(page) -> None:
    await page.goto(f"{BASE}/login", wait_until="networkidle")
    await page.wait_for_timeout(600)
    await page.fill('input[type="text"]', CREDS[0])
    await page.fill('input[type="password"]', CREDS[1])
    await page.click('button:has-text("登录")')
    await page.wait_for_timeout(2000)


async def main() -> None:
    from playwright.async_api import async_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await login(page)
        for fname, path, wait_ms in SHOTS:
            await page.goto(BASE + path, wait_until="networkidle")
            await page.wait_for_timeout(wait_ms)
            if "cockpit" in path:
                await page.wait_for_timeout(2000)
            target = OUT / fname
            await page.screenshot(path=str(target), full_page=False)
            print("OK", fname, target.stat().st_size)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
