#!/usr/bin/env python3
"""
测试前端HTML服务
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.frontend_html_service import frontend_html_service

async def test_frontend_html_service():
    """测试前端HTML服务"""
    try:
        print("🧪 开始测试前端HTML服务...")

        # 测试报价单ID 77 (最新的报价单CIS-KS20250922003)
        quote_id = 77

        print(f"📄 测试报价单ID: {quote_id}")

        # 生成PDF
        pdf_bytes = await frontend_html_service.generate_pdf_from_frontend(quote_id)

        print(f"✅ PDF生成成功！")
        print(f"📊 PDF大小: {len(pdf_bytes)} bytes")

        # 保存到测试文件
        test_file = f"test_frontend_html_quote_{quote_id}.pdf"
        with open(test_file, 'wb') as f:
            f.write(pdf_bytes)

        print(f"💾 PDF已保存到: {test_file}")

        # 关闭服务
        await frontend_html_service.close()

        print("🎉 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_html_service())