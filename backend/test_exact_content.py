#!/usr/bin/env python3
"""
测试报价单21的确切内容，查找特殊字符
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote
from app.services.wecom_approval_service import WeComApprovalService
import re

def test_exact_content():
    """测试报价单21的确切内容"""
    print("🔍 测试报价单21的确切内容和特殊字符")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 获取报价单
        quote = db.query(Quote).filter(Quote.id == 21).first()
        if not quote:
            print("❌ 找不到报价单ID=21")
            return

        print(f"📋 报价单: {quote.quote_number}")
        print(f"📝 描述: {repr(quote.description)}")

        # 检查报价单项目
        if quote.items:
            for i, item in enumerate(quote.items):
                print(f"项目{i+1}: {repr(item.item_name)}, 单位: {repr(item.unit)}")

        # 构建审批数据
        service = WeComApprovalService(db)

        # 检查items_text的构建过程
        items_summary = []
        if quote.items:
            for item in quote.items:
                raw_line = f"{item.item_name}: {item.quantity}{item.unit or 'pcs'} x ¥{item.unit_price} = ¥{item.total_price}"
                items_summary.append(raw_line)
                print(f"🔍 原始项目行: {repr(raw_line)}")

                # 检查特殊字符
                special_chars = re.findall(r'[^\w\s\-\.\:：¥元pcs×=\n]', raw_line)
                if special_chars:
                    print(f"⚠️ 发现特殊字符: {set(special_chars)}")

        items_text = "\n".join(items_summary) if items_summary else "无明细"
        print(f"🔍 items_text: {repr(items_text)}")

        # 检查最终合成的内容
        final_text = f"总金额: {(quote.total_amount or 0):.2f}元 明细: {items_text} 备注: {quote.description or '无'}"
        print(f"🔍 最终文本: {repr(final_text)}")

        # 应用清理函数
        cleaned_text = service._clean_text_for_wecom(final_text)
        print(f"🔍 清理后文本: {repr(cleaned_text)}")

        # 详细检查特殊字符
        special_chars = re.findall(r'[^\w\s\-\.\:：¥元pcs×=\n]', cleaned_text)
        if special_chars:
            print(f"⚠️ 清理后仍有特殊字符: {set(special_chars)}")
            for char in set(special_chars):
                print(f"   字符: '{char}' (Unicode: U+{ord(char):04X})")
        else:
            print("✅ 清理后没有特殊字符")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_exact_content()