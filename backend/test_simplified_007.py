#!/usr/bin/env python3
"""
测试简化CIS-KS20250918007的内容
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote
from app.services.wecom_approval_service import WeComApprovalService

def test_simplified_content():
    """测试简化后的审批内容"""
    print("🧪 测试简化的报价单007审批内容")
    print("=" * 60)

    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == 21).first()
        if not quote:
            print("❌ 找不到报价单ID=21")
            return

        service = WeComApprovalService(db)

        # 临时修改服务的构建方法来测试不同长度的内容
        original_method = service._build_approval_data

        def simplified_build_approval_data(quote, user_id):
            # 调用原始方法
            data = original_method(quote, user_id)

            # 简化Text-1756706160253控件的内容
            for content in data["apply_data"]["contents"]:
                if content.get("id") == "Text-1756706160253":
                    # 测试不同的简化版本
                    simplified_versions = [
                        "简化测试1",  # 最简版本
                        f"总金额: {quote.total_amount}元",  # 只有金额
                        f"报价说明: {quote.description or '无'}",  # 只有描述
                        "总金额: 23000元 项目: CCA101",  # 中等长度
                    ]

                    for i, simplified_text in enumerate(simplified_versions):
                        print(f"\n🔍 测试版本 {i+1}: {simplified_text}")
                        print(f"   长度: {len(simplified_text)} 字符")

                        # 更新内容
                        content["value"]["text"] = simplified_text

                        # 显示这个版本的完整数据
                        import json
                        print(f"   数据: {json.dumps(content, ensure_ascii=False)}")

                        # 这里可以添加实际的API调用测试
                        # 但为了安全起见，我们先只是显示数据

            return data

        # 使用修改后的方法
        service._build_approval_data = simplified_build_approval_data

        print("\n📋 开始测试简化版本...")
        approval_data = service._build_approval_data(quote, 1)

        print(f"\n✅ 测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_simplified_content()