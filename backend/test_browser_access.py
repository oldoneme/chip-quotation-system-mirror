#!/usr/bin/env python3
"""
最小化测试脚本 - 确认浏览器能否访问前端页面
"""
from playwright.async_api import async_playwright
import asyncio

async def main():
    print("🧪 开始测试浏览器访问前端页面...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page()

        # 测试前端页面URL
        frontend_url = "http://localhost:3000/quote-detail/CIS-KS20250922003"
        print(f"📍 访问地址: {frontend_url}")

        try:
            # 访问页面
            await page.goto(frontend_url, wait_until="networkidle", timeout=30000)
            print("✅ 页面访问成功")

            # 截图调试
            await page.screenshot(path='debug_screenshot.png', full_page=True)
            print("📸 已保存截图到: debug_screenshot.png")

            # 检查页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")

            # 检查页面内容
            content = await page.content()
            print(f"📝 页面内容长度: {len(content)} 字符")

            # 检查是否有报价单内容
            if "报价单" in content:
                print("✅ 页面包含报价单内容")
            else:
                print("⚠️ 页面不包含报价单内容")

            # 检查是否是登录页面
            if "登录" in content or "login" in content.lower():
                print("⚠️ 页面显示为登录页面")
            else:
                print("✅ 页面不是登录页面")

        except Exception as e:
            print(f"❌ 页面访问失败: {str(e)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())