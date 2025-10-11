#!/usr/bin/env python3
"""
测试前端快照功能的简单脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.frontend_snapshot_pdf_service import frontend_snapshot_pdf_service

def test_frontend_snapshot():
    """测试前端页面快照"""
    try:
        print("🧪 开始测试前端页面快照功能...")

        # 测试已知存在的报价单号
        quote_number = "CIS-KS20250922005"
        output_path = f"test_snapshot_{quote_number}.pdf"

        print(f"📄 测试报价单号: {quote_number}")
        print(f"💾 输出路径: {output_path}")

        # 生成PDF
        pdf_bytes = frontend_snapshot_pdf_service.generate_quote_pdf_from_frontend_snapshot_sync(
            quote_number=quote_number,
            output_path=output_path
        )

        print(f"✅ 前端快照PDF生成成功！")
        print(f"📊 PDF大小: {len(pdf_bytes)} bytes")
        print(f"💾 PDF已保存到: {output_path}")
        print("🎉 测试完成！")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_frontend_snapshot()
    sys.exit(0 if success else 1)