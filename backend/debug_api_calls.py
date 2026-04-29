#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json


def get_auth_headers():
    token = os.getenv("CHIP_QUOTE_AUTH_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}

def test_api_calls():
    """测试实际的API调用路径"""
    print("🔍 诊断API调用路径")
    print("=" * 50)

    base_url = "http://localhost:8000"
    auth_headers = get_auth_headers()
    if auth_headers is None:
        print("⚠️  受保护报价接口需要认证 token")
        print("   请先设置环境变量: export CHIP_QUOTE_AUTH_TOKEN=<token>")
        return

    # 1. 检查当前报价单状态
    print("1. 检查报价单状态...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/quotes/detail/CIS-KS20250918001",
            headers=auth_headers,
        )
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
        f"/api/v1/approval/status/{quote_id}",
        f"/api/v1/approval/history/{quote_id}",
        f"/api/v1/quotes/{quote_id}/submit",
        f"/api/v1/quotes/{quote_id}/approve",
        f"/api/v1/quotes/{quote_id}/reject",
        f"/api/v1/quotes/{quote_id}/approval-records",
        f"/api/v1/wecom-approval/generate-approval-link/{quote_id}",
        f"/api/v1/wecom-approval/sync-status/{quote_id}"
    ]

    for endpoint in endpoints_to_check:
        try:
            response = requests.options(f"{base_url}{endpoint}", headers=auth_headers)
            if response.status_code in [200, 405]:  # 405 = Method Not Allowed，说明端点存在
                print(f"✅ {endpoint} - 可用")
            else:
                print(f"❌ {endpoint} - 不可用 ({response.status_code})")
        except:
            print(f"❌ {endpoint} - 连接失败")

    # 3. 如果报价单是pending状态，尝试拒绝操作
    if quote_data.get('status') == 'pending':
        print(f"\n3. 尝试拒绝操作 (报价单ID: {quote_id})...")

        # 尝试当前报价审批 API
        try:
            reject_data = {
                "reason": "诊断测试拒绝",
                "comments": "这是一个API诊断测试"
            }
            response = requests.post(
                f"{base_url}/api/v1/quotes/{quote_id}/reject",
                json=reject_data,
                headers={**auth_headers, "Content-Type": "application/json"}
            )
            print(f"报价审批拒绝 API 响应: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 报价审批拒绝成功: {response.json()}")
            else:
                print(f"❌ 报价审批拒绝失败: {response.text}")
        except Exception as e:
            print(f"❌ 报价审批拒绝异常: {e}")

if __name__ == "__main__":
    test_api_calls()
