"""Playwright 截图（需: uv pip install playwright && playwright install chromium）"""
import asyncio
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8000"

SHOTS = [
    ("01-login.png", "/login", None),
    ("02-gov-workbench.png", "/gov/workbench", ("gov_admin", "123456")),
    ("03-ent-workbench.png", "/ent/workbench", ("ent_admin", "123456")),
    ("04-gov-cockpit.png", "/gov/cockpit", ("gov_admin", "123456")),
    ("05-quality-inspection.png", "/gov/quality/inspections", ("gov_admin", "123456")),
    ("06-trace-apply.png", "/gov/trace/applies", ("gov_admin", "123456")),
    ("07-effluent-plan.png", "/gov/effluent/plans", ("gov_admin", "123456")),
    ("08-enterprise-gis.png", "/gov/party/gis-collect", ("gov_admin", "123456")),
    ("09-party-enterprise.png", "/gov/party/enterprises", ("gov_admin", "123456")),
    ("10-user-manage.png", "/gov/party/users", ("gov_admin", "123456")),
]

async def main():
    from playwright.async_api import async_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        for fname, path, creds in SHOTS:
            if creds:
                await page.goto(f"{BASE}/login")
                await page.wait_for_timeout(800)
                await page.fill('input[placeholder*="用户"], input[type="text"]', creds[0])
                await page.fill('input[type="password"]', creds[1])
                await page.click('button:has-text("登录"), button[type="submit"]')
                await page.wait_for_timeout(1500)
            await page.goto(BASE + path)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(OUT / fname), full_page=False)
            print("OK", fname)
        await page.goto(API + "/docs")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "11-api-docs.png"), full_page=False)
        print("OK 11-api-docs.png")
        await browser.close()

asyncio.run(main())
