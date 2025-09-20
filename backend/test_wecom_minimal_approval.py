#!/usr/bin/env python3
"""
测试企业微信审批的最小化参数
逐步减少参数来定位问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote
from app.services.wecom_approval_service import WeComApprovalService
import json

def test_minimal_approval():
    """测试最小化的审批参数"""
    print("🧪 测试企业微信审批的最小化参数")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 获取报价单
        quote = db.query(Quote).filter(Quote.id == 21).first()
        if not quote:
            print("❌ 找不到报价单ID=21")
            return

        print(f"📋 报价单: {quote.quote_number}")

        # 构建最小化的审批数据
        service = WeComApprovalService(db)

        # 方案1: 只测试第一个文本控件
        print("\n🔍 方案1: 只测试第一个文本控件")
        minimal_data_1 = {
            "creator_userid": "qixin.chen",
            "template_id": "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh",
            "use_template_approver": 0,
            "process_code": "",
            "apply_data": {
                "contents": [
                    {
                        "control": "Text",
                        "id": "Text-1756706105289",
                        "title": [{"text": "报价单类型", "lang": "zh_CN"}],
                        "value": {"text": "测试报价"}
                    }
                ]
            }
        }
        print("📝 最小数据1:", json.dumps(minimal_data_1, indent=2, ensure_ascii=False))

        # 方案2: 测试问题控件但使用最简单的文本
        print("\n🔍 方案2: 测试问题控件Text-1756706160253但使用最简单的文本")
        minimal_data_2 = {
            "creator_userid": "qixin.chen",
            "template_id": "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh",
            "use_template_approver": 0,
            "process_code": "",
            "apply_data": {
                "contents": [
                    {
                        "control": "Text",
                        "id": "Text-1756706160253",
                        "title": [{"text": "报价说明", "lang": "zh_CN"}],
                        "value": {"text": "test"}
                    }
                ]
            }
        }
        print("📝 最小数据2:", json.dumps(minimal_data_2, indent=2, ensure_ascii=False))

        # 方案3: 测试所有控件但都使用最简单的文本
        print("\n🔍 方案3: 所有控件都使用最简单的文本")
        minimal_data_3 = {
            "creator_userid": "qixin.chen",
            "template_id": "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh",
            "use_template_approver": 0,
            "process_code": "",
            "apply_data": {
                "contents": [
                    {
                        "control": "Text",
                        "id": "Text-1756706105289",
                        "title": [{"text": "报价单类型", "lang": "zh_CN"}],
                        "value": {"text": "test1"}
                    },
                    {
                        "control": "Text",
                        "id": "Text-1756705975378",
                        "title": [{"text": "报价单号", "lang": "zh_CN"}],
                        "value": {"text": "test2"}
                    },
                    {
                        "control": "Text",
                        "id": "Text-1756706001498",
                        "title": [{"text": "客户名称", "lang": "zh_CN"}],
                        "value": {"text": "test3"}
                    },
                    {
                        "control": "Text",
                        "id": "Text-1756706160253",
                        "title": [{"text": "报价说明", "lang": "zh_CN"}],
                        "value": {"text": "test4"}
                    },
                    {
                        "control": "Text",
                        "id": "Text-1756897248857",
                        "title": [{"text": "报价单详情链接", "lang": "zh_CN"}],
                        "value": {"text": "test5"}
                    }
                ]
            }
        }
        print("📝 最小数据3:", json.dumps(minimal_data_3, indent=2, ensure_ascii=False))

        # 测试是否能构建完整的原始数据
        print("\n🔍 方案4: 检查当前构建的完整数据")
        try:
            original_data = service._build_approval_data(quote, 1)
            print("✅ 原始数据构建成功")

            # 检查每个控件的值长度
            for content in original_data["apply_data"]["contents"]:
                if content["id"] == "Text-1756706160253":
                    text_value = content["value"]["text"]
                    print(f"🔍 问题控件长度: {len(text_value)} 字符")
                    print(f"📝 内容预览: {repr(text_value[:100])}")

                    # 检查是否有特殊字符
                    import re
                    special_chars = re.findall(r'[^\w\s\-\.\:：¥元件×=\n]', text_value)
                    if special_chars:
                        print(f"⚠️ 发现特殊字符: {set(special_chars)}")
                    else:
                        print("✅ 没有发现特殊字符")

        except Exception as e:
            print(f"❌ 原始数据构建失败: {e}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_minimal_approval()