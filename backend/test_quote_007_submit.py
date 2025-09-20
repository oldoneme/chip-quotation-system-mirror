#!/usr/bin/env python3
"""
测试报价单CIS-KS20250918007的企业微信提交
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_quote_007_submit():
    """测试报价单007的企业微信提交"""
    print("🧪 测试报价单CIS-KS20250918007的企业微信提交")
    print("=" * 60)

    base_url = "http://localhost:8000"
    quote_id = 21  # CIS-KS20250918007的ID

    print(f"📋 报价单ID: {quote_id}")

    # 1. 检查报价单当前状态
    print("\n🔍 Step 1: 检查报价单当前状态")
    try:
        response = requests.get(f"{base_url}/api/v2/approval/{quote_id}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ 当前状态: {status.get('current_status')}")
            print(f"   📊 审批状态: {status.get('approval_status')}")
            print(f"   🆔 企业微信ID: {status.get('wecom_approval_id')}")
        else:
            print(f"   ❌ 获取状态失败: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 获取状态异常: {e}")
        return

    # 2. 尝试提交审批
    print("\n📤 Step 2: 提交审批到企业微信")
    submit_data = {
        "comments": "测试CIS-KS20250918007企业微信审批提交"
    }

    try:
        response = requests.post(f"{base_url}/api/v1/approval/submit/{quote_id}",
                               json=submit_data)
        print(f"   📊 HTTP状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 提交成功: {result.get('message')}")
            print(f"   🎯 审批方法: {result.get('approval_method')}")
            print(f"   🆔 审批ID: {result.get('approval_id')}")
        else:
            print(f"   ❌ 提交失败: {response.text}")

            # 详细错误分析
            try:
                error_detail = response.json()
                print(f"   🔍 详细错误: {error_detail}")
            except:
                pass
    except Exception as e:
        print(f"   ❌ 提交异常: {e}")

    # 3. 再次检查状态
    print("\n🔍 Step 3: 检查提交后状态")
    try:
        response = requests.get(f"{base_url}/api/v2/approval/{quote_id}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ 当前状态: {status.get('current_status')}")
            print(f"   📊 审批状态: {status.get('approval_status')}")
            print(f"   🆔 企业微信ID: {status.get('wecom_approval_id')}")
        else:
            print(f"   ❌ 获取状态失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取状态异常: {e}")

if __name__ == "__main__":
    test_quote_007_submit()