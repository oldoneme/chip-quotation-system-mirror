#!/usr/bin/env python3
"""
测试新报价单的企业微信审批功能
验证特殊字符修复后的效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_new_quote_wecom():
    """测试新报价单的企业微信审批"""
    print("🧪 测试新报价单的企业微信审批功能")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 1. 创建一个新的报价单
    print("📋 第1步: 创建新报价单（包含特殊字符测试）")
    quote_data = {
        "title": f"特殊字符测试_{datetime.now().strftime('%H%M%S')}",
        "quote_type": "formal",  # 使用formal类型，需要审批
        "customer_name": f"测试客户{datetime.now().strftime('%H%M%S')}",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "description": "项目：测试项目，芯片类型：BGA256，要求：高精度测试",  # 包含特殊字符
        "items": [
            {
                "item_name": "测试项目1",
                "item_description": "测试项目描述，包含：特殊字符",
                "machine_type": "测试机",
                "quantity": 1.0,
                "unit": "件",
                "unit_price": 100.0,
                "total_price": 100.0
            }
        ]
    }

    try:
        response = requests.post(f"{base_url}/api/v1/quotes", json=quote_data)
        if response.status_code in [200, 201]:
            result = response.json()
            quote_id = result.get('id')
            quote_number = result.get('quote_number')
            print(f"   ✅ 报价单创建成功: ID={quote_id}, Number={quote_number}")
        else:
            print(f"   ❌ 报价单创建失败: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"   ❌ 创建报价单异常: {e}")
        return None, None

    # 2. 提交审批
    print(f"\n📤 第2步: 提交报价单 {quote_number} 到企业微信审批")
    submit_data = {
        "comments": "测试新报价单的企业微信审批功能",
        "method": "wecom"
    }

    try:
        response = requests.post(f"{base_url}/api/v1/approval/submit/{quote_id}", json=submit_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 提交成功: {result.get('message')}")
            print(f"   🎯 审批方法: {result.get('approval_method')}")
            print(f"   🆔 审批ID: {result.get('approval_id')}")
            print(f"   📊 新状态: {result.get('new_status')}")
            success = result.get('success')
            return quote_id, quote_number, success
        else:
            print(f"   ❌ 提交失败: {response.status_code} - {response.text}")
            return quote_id, quote_number, False
    except Exception as e:
        print(f"   ❌ 提交异常: {e}")
        return quote_id, quote_number, False

def get_quote_status(quote_id):
    """获取报价单状态"""
    base_url = "http://localhost:8000"

    try:
        response = requests.get(f"{base_url}/api/v2/approval/{quote_id}/status")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取状态失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取状态异常: {e}")
        return None

def main():
    print("🔍 测试新报价单的企业微信审批功能")
    print("   这将验证特殊字符修复是否有效")
    print("=" * 60)

    # 测试新报价单
    quote_id, quote_number, success = test_new_quote_wecom()

    if quote_id:
        print(f"\n📊 第3步: 检查报价单 {quote_number} 的最终状态")
        status = get_quote_status(quote_id)
        if status:
            print(f"   📋 报价单号: {status.get('quote_number')}")
            print(f"   💾 数据库状态: {status.get('status')}")
            print(f"   🔄 审批状态: {status.get('approval_status')}")
            print(f"   🆔 企业微信ID: {status.get('wecom_approval_id')}")

            if status.get('wecom_approval_id'):
                print("\n🎉 SUCCESS: 企业微信审批成功创建!")
                print("   ✅ 特殊字符问题已修复")
                print("   ✅ 审批人应该能收到企业微信通知")
            else:
                print("\n⚠️ WARNING: 企业微信审批ID为空")
                print("   可能使用了内部审批回退机制")

        print(f"\n📝 总结:")
        print(f"   报价单: {quote_number} (ID: {quote_id})")
        print(f"   提交结果: {'成功' if success else '失败'}")
        print(f"   企业微信审批: {'正常' if status.get('wecom_approval_id') else '回退到内部审批'}")

if __name__ == "__main__":
    main()