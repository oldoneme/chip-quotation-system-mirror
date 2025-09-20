#!/usr/bin/env python3
"""
比较正常工作的报价单和失败的报价单内容
找出差异，特别是Text-1756706160253控件的内容
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote
from app.services.wecom_approval_service import WeComApprovalService

def compare_quotes():
    """比较报价单内容"""
    print("🔍 比较正常和失败的报价单内容")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 获取失败的报价单007 (ID=21)
        quote_007 = db.query(Quote).filter(Quote.id == 21).first()
        # 获取成功的报价单009 (ID=23)
        quote_009 = db.query(Quote).filter(Quote.id == 23).first()

        if not quote_007:
            print("❌ 找不到报价单007 (ID=21)")
            return
        if not quote_009:
            print("❌ 找不到报价单009 (ID=23)")
            return

        print(f"📋 失败报价单: {quote_007.quote_number} (ID: {quote_007.id})")
        print(f"📋 成功报价单: {quote_009.quote_number} (ID: {quote_009.id})")

        service = WeComApprovalService(db)

        # 构建两个报价单的审批数据
        approval_data_007 = service._build_approval_data(quote_007, 1)
        approval_data_009 = service._build_approval_data(quote_009, 1)

        # 找到Text-1756706160253控件内容
        text_007 = None
        text_009 = None

        for content in approval_data_007["apply_data"]["contents"]:
            if content.get("id") == "Text-1756706160253":
                text_007 = content["value"]["text"]
                break

        for content in approval_data_009["apply_data"]["contents"]:
            if content.get("id") == "Text-1756706160253":
                text_009 = content["value"]["text"]
                break

        print("\n" + "=" * 60)
        print("🎯 Text-1756706160253 控件内容对比:")
        print("=" * 60)

        if text_007:
            print(f"\n❌ 失败报价单007内容:")
            print(f"   原始: {repr(text_007)}")
            print(f"   长度: {len(text_007)} 字符")
            print(f"   显示:")
            for i, line in enumerate(text_007.split('\n')):
                print(f"     行{i+1}: {line}")

        if text_009:
            print(f"\n✅ 成功报价单009内容:")
            print(f"   原始: {repr(text_009)}")
            print(f"   长度: {len(text_009)} 字符")
            print(f"   显示:")
            for i, line in enumerate(text_009.split('\n')):
                print(f"     行{i+1}: {line}")

        # 分析差异
        print(f"\n🔍 差异分析:")
        if text_007 and text_009:
            print(f"   长度差异: {len(text_007)} vs {len(text_009)}")
            print(f"   换行符数量: {text_007.count(chr(10))} vs {text_009.count(chr(10))}")
            print(f"   中文冒号数量: {text_007.count('：')} vs {text_009.count('：')}")
            print(f"   英文冒号数量: {text_007.count(':')} vs {text_009.count(':')}")
            print(f"   特殊字符检查:")

            # 检查特殊字符
            special_chars_007 = set()
            special_chars_009 = set()

            for char in text_007:
                if ord(char) > 127 or char in ['\n', '\r', '\t']:
                    special_chars_007.add(f"'{char}'({ord(char)})")

            for char in text_009:
                if ord(char) > 127 or char in ['\n', '\r', '\t']:
                    special_chars_009.add(f"'{char}'({ord(char)})")

            print(f"     007特殊字符: {sorted(special_chars_007)}")
            print(f"     009特殊字符: {sorted(special_chars_009)}")

            # 找出只在007中存在的特殊字符
            only_in_007 = special_chars_007 - special_chars_009
            if only_in_007:
                print(f"   🚨 只在失败报价单中的特殊字符: {sorted(only_in_007)}")

        # 检查其他可能的差异
        print(f"\n📊 基本信息对比:")
        print(f"   客户名称: '{quote_007.customer_name}' vs '{quote_009.customer_name}'")
        print(f"   描述长度: {len(quote_007.description or '')} vs {len(quote_009.description or '')}")
        print(f"   项目数量: {len(quote_007.items)} vs {len(quote_009.items)}")

        if quote_007.items:
            print(f"   007项目:")
            for i, item in enumerate(quote_007.items):
                print(f"     {i+1}: {item.item_name} - 特殊字符: {[c for c in item.item_name if ord(c) > 127]}")

        if quote_009.items:
            print(f"   009项目:")
            for i, item in enumerate(quote_009.items):
                print(f"     {i+1}: {item.item_name} - 特殊字符: {[c for c in item.item_name if ord(c) > 127]}")

    except Exception as e:
        print(f"❌ 比较失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    compare_quotes()