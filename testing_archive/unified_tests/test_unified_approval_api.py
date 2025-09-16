#!/usr/bin/env python3
"""
Step 3.3: 测试统一审批API功能
测试新的统一审批端点是否正常工作
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# 测试用户认证令牌 (使用现有的JWT)
JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJxaXhpbi5jaGVuIiwiZXhwIjoxNzU3NDE3MzgxfQ.ttjIlVYpkxbPdxkaJBGNmznEeqPICJdKzI6ff0nr-L8"

def test_approval_status(quote_id: int):
    """测试审批状态查询"""
    print(f"\n🔍 测试审批状态查询 - 报价单ID: {quote_id}")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/approval/status/{quote_id}",
            params={"jwt": JWT_TOKEN}
        )

        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 状态查询成功:")
            print(f"      报价单号: {data.get('quote_number')}")
            print(f"      状态: {data.get('status')}")
            print(f"      审批状态: {data.get('approval_status')}")
            print(f"      是否有企业微信审批: {data.get('has_wecom_approval')}")
            return data
        else:
            print(f"   ❌ 状态查询失败: {response.text}")
            return None

    except Exception as e:
        print(f"   💥 请求异常: {e}")
        return None

def test_approval_history(quote_id: int):
    """测试审批历史查询"""
    print(f"\n📚 测试审批历史查询 - 报价单ID: {quote_id}")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/approval/history/{quote_id}",
            params={"jwt": JWT_TOKEN}
        )

        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 历史查询成功:")
            print(f"      历史记录数: {data.get('total')}")
            for i, record in enumerate(data.get('history', [])[:3]):  # 显示前3条
                print(f"      [{i+1}] 动作: {record.get('action')}, 状态: {record.get('status')}")
            return data
        else:
            print(f"   ❌ 历史查询失败: {response.text}")
            return None

    except Exception as e:
        print(f"   💥 请求异常: {e}")
        return None

def test_submit_approval(quote_id: int):
    """测试提交审批"""
    print(f"\n📤 测试提交审批 - 报价单ID: {quote_id}")

    try:
        # 先检查当前状态
        status_data = test_approval_status(quote_id)
        if not status_data:
            print("   ⚠️ 无法获取当前状态，跳过提交测试")
            return None

        current_status = status_data.get('approval_status')
        if current_status == 'pending':
            print("   ℹ️ 报价单已在审批中，跳过提交测试")
            return None

        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/approval/submit/{quote_id}",
            json={"comments": "统一API测试提交", "method": None},
            params={"jwt": JWT_TOKEN}
        )

        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 提交成功:")
            print(f"      消息: {data.get('message')}")
            print(f"      审批方式: {data.get('approval_method')}")
            print(f"      新状态: {data.get('new_status')}")
            print(f"      审批ID: {data.get('approval_id')}")
            return data
        else:
            print(f"   ❌ 提交失败: {response.text}")
            return None

    except Exception as e:
        print(f"   💥 请求异常: {e}")
        return None

def main():
    """主测试流程"""
    print("🧪 开始测试统一审批API功能")
    print("=" * 50)

    # 使用现有的报价单ID进行测试
    quote_id = 1

    # 1. 测试状态查询
    status_result = test_approval_status(quote_id)

    # 2. 测试历史查询
    history_result = test_approval_history(quote_id)

    # 3. 测试提交审批 (如果当前状态允许)
    submit_result = test_submit_approval(quote_id)

    # 4. 再次查询状态确认变化
    print(f"\n🔄 再次查询状态确认变化")
    final_status = test_approval_status(quote_id)

    # 总结测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   ✅ 状态查询: {'通过' if status_result else '失败'}")
    print(f"   ✅ 历史查询: {'通过' if history_result else '失败'}")
    print(f"   ✅ 提交审批: {'通过' if submit_result else '跳过/失败'}")
    print(f"   ✅ 最终状态: {'通过' if final_status else '失败'}")

    if all([status_result, history_result, final_status]):
        print("\n🎉 统一审批API基本功能测试通过!")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)