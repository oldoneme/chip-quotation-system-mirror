#!/usr/bin/env python3
"""
测试企业微信通知修复
验证所有审批操作都能正确发送通知
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_notification_workflow():
    """测试完整的通知工作流"""
    print("🚀 测试企业微信通知修复")
    print("=" * 60)

    base_url = "http://localhost:8000"
    quote_number = "CIS-KS20250918001"

    # 1. 重置报价单状态
    print("1. 重置报价单状态到 pending...")
    try:
        response = requests.get(f"{base_url}/api/v1/quotes/detail/{quote_number}")
        if response.status_code == 200:
            quote_data = response.json()
            quote_id = quote_data.get('id')
            print(f"   📋 报价单ID: {quote_id}")
            print(f"   📊 当前状态: {quote_data.get('status')}")
            print(f"   📊 审批状态: {quote_data.get('approval_status')}")
        else:
            print(f"   ❌ 获取报价单失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

    # 2. 如果不是pending状态，先重置
    if quote_data.get('status') != 'pending':
        print("   🔄 重置报价单状态为pending...")
        import subprocess
        result = subprocess.run(['python3', 'reset_quote_status.py'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ 状态重置成功")
        else:
            print(f"   ❌ 状态重置失败: {result.stderr}")
            return False

    # 3. 测试拒绝操作（通过修复后的API端点）
    print("\n2. 测试拒绝操作（修复后的wecom-approval端点）...")
    try:
        reject_data = {
            "reason": "测试企业微信通知修复",
            "comments": "验证统一审批引擎通知功能"
        }
        response = requests.post(
            f"{base_url}/api/v1/wecom-approval/reject/{quote_id}",
            json=reject_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   📤 拒绝API响应: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 拒绝成功: {result.get('message')}")
            print("   📱 检查是否收到企业微信通知...")
        else:
            print(f"   ❌ 拒绝失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 拒绝操作异常: {e}")
        return False

    # 4. 重新提交审批（测试提交通知）
    print("\n3. 重新提交审批（测试修复后的提交通知）...")
    try:
        # 先重置状态为draft
        import subprocess
        result = subprocess.run(['python3', 'reset_quote_status.py'],
                              capture_output=True, text=True)

        # 提交审批 - 使用统一审批端点
        submit_data = {
            "comments": "测试企业微信通知修复 - 提交审批",
            "method": "wecom"
        }
        response = requests.post(
            f"{base_url}/api/v1/approval/submit/{quote_id}",
            json=submit_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   📤 提交API响应: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 提交成功: {result.get('message')}")
            print("   📱 检查是否收到企业微信审批通知...")
        else:
            print(f"   ❌ 提交失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 提交操作异常: {e}")

    # 5. 测试批准操作
    print("\n4. 测试批准操作（修复后的approve端点）...")
    try:
        approve_data = {
            "comments": "测试企业微信通知修复 - 批准"
        }
        response = requests.post(
            f"{base_url}/api/v1/wecom-approval/approve/{quote_id}",
            json=approve_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   📤 批准API响应: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 批准成功: {result.get('message')}")
            print("   📱 检查是否收到企业微信批准通知...")
        else:
            print(f"   ❌ 批准失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 批准操作异常: {e}")

    print("\n" + "=" * 60)
    print("✨ 通知测试完成！")
    print("📱 请检查企业微信是否收到以下通知：")
    print("   1. 拒绝审批通知（发送给创建者）")
    print("   2. 重新提交审批通知（发送给审批人）")
    print("   3. 批准审批通知（发送给创建者）")
    print("=" * 60)

    return True

def test_api_endpoints():
    """测试API端点可用性"""
    print("\n🔍 测试API端点可用性...")
    print("-" * 40)

    base_url = "http://localhost:8000"
    endpoints = [
        "/api/v1/approval/submit/1",
        "/api/v1/wecom-approval/approve/1",
        "/api/v1/wecom-approval/reject/1",
        "/api/v1/submit/1",
        "/api/v1/quotes/1/submit"
    ]

    for endpoint in endpoints:
        try:
            response = requests.options(f"{base_url}{endpoint}")
            if response.status_code in [200, 405]:  # 405 = Method Not Allowed，说明端点存在
                print(f"✅ {endpoint}")
            else:
                print(f"❌ {endpoint} ({response.status_code})")
        except:
            print(f"❌ {endpoint} (连接失败)")

if __name__ == "__main__":
    # 先测试API端点
    test_api_endpoints()

    # 然后测试通知工作流
    test_notification_workflow()