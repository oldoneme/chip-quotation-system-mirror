#!/usr/bin/env python3
"""
测试前端页面快照功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.frontend_snapshot_pdf_service import frontend_snapshot_pdf_service

async def test_frontend_snapshot():
    """测试前端页面快照"""
    try:
        print("🧪 开始测试前端页面快照功能...")

        # 测试报价单号
        quote_number = "CIS-KS20250922003"

        print(f"📄 测试报价单号: {quote_number}")

        # 生成PDF
        pdf_bytes = await frontend_snapshot_pdf_service.generate_quote_pdf_from_frontend_snapshot(quote_number)

        print(f"✅ 前端快照PDF生成成功！")
        print(f"📊 PDF大小: {len(pdf_bytes)} bytes")

        # 保存到测试文件
        test_file = f"test_frontend_snapshot_{quote_number}.pdf"
        with open(test_file, 'wb') as f:
            f.write(pdf_bytes)

        print(f"💾 PDF已保存到: {test_file}")
        print("🎉 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_frontend_snapshot())