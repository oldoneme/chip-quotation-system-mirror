#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_api_calls():
    """测试实际的API调用路径"""
    print("🔍 诊断API调用路径")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # 1. 检查当前报价单状态
    print("1. 检查报价单状态...")
    try:
        response = requests.get(f"{base_url}/api/v1/quotes/detail/CIS-KS20250918001")
        if response.status_code == 200:
            quote_data = response.json()
            print(f"📋 报价单: {quote_data.get('quote_number')}")
            print(f"📊 状态: {quote_data.get('status')}")
            print(f"📊 审批状态: {quote_data.get('approval_status')}")
            quote_id = quote_data.get('id')
        else:
            print(f"❌ 获取报价单失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return

    # 2. 检查可用的API端点
    print("\n2. 检查可用的审批API端点...")
    endpoints_to_check = [
        "/api/v1/wecom-approval/submit",
        "/api/v1/wecom-approval/approve",
        "/api/v1/wecom-approval/reject",
        "/api/v1/quote-approval/submit",
        "/api/v1/quote-approval/approve",
        "/api/v1/quote-approval/reject",
        "/api/v2/approval/submit",
        "/api/v2/approval/approve",
        "/api/v2/approval/reject"
    ]

    for endpoint in endpoints_to_check:
        try:
            response = requests.options(f"{base_url}{endpoint}")
            if response.status_code in [200, 405]:  # 405 = Method Not Allowed，说明端点存在
                print(f"✅ {endpoint} - 可用")
            else:
                print(f"❌ {endpoint} - 不可用 ({response.status_code})")
        except:
            print(f"❌ {endpoint} - 连接失败")

    # 3. 如果报价单是pending状态，尝试拒绝操作
    if quote_data.get('status') == 'pending':
        print(f"\n3. 尝试拒绝操作 (报价单ID: {quote_id})...")

        # 尝试V1 API
        try:
            reject_data = {
                "reason": "诊断测试拒绝",
                "comments": "这是一个API诊断测试"
            }
            response = requests.post(
                f"{base_url}/api/v1/wecom-approval/reject/{quote_id}",
                json=reject_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"V1 拒绝API响应: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ V1 拒绝成功: {response.json()}")
            else:
                print(f"❌ V1 拒绝失败: {response.text}")
        except Exception as e:
            print(f"❌ V1 拒绝异常: {e}")

        # 尝试V2 API
        try:
            reject_data = {
                "action": "reject",
                "reason": "诊断测试拒绝",
                "comments": "这是一个API诊断测试"
            }
            response = requests.post(
                f"{base_url}/api/v2/approval/{quote_id}/operation",
                json=reject_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"V2 拒绝API响应: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ V2 拒绝成功: {response.json()}")
            else:
                print(f"❌ V2 拒绝失败: {response.text}")
        except Exception as e:
            print(f"❌ V2 拒绝异常: {e}")

if __name__ == "__main__":
    test_api_calls()