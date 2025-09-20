#!/usr/bin/env python3
"""
测试统一审批引擎的路径一致性
验证无论从哪个入口进行审批，结果都应该是一致的
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from datetime import datetime

def create_test_quote():
    """创建测试报价单"""
    print("📋 创建测试报价单...")

    base_url = "http://localhost:8000"

    # 创建基础报价单数据 (使用formal类型确保需要审批)
    quote_data = {
        "title": f"统一审批测试_{datetime.now().strftime('%H%M%S')}",
        "quote_type": "formal",  # 使用formal类型，需要审批
        "customer_name": f"测试客户_{datetime.now().strftime('%H%M%S')}",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "description": "统一审批路径一致性测试",
        "items": [
            {
                "item_name": "测试项目1",
                "item_description": "测试项目描述",
                "machine_type": "测试机",
                "quantity": 1.0,
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
            return quote_id, quote_number
        else:
            print(f"   ❌ 报价单创建失败: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"   ❌ 创建报价单异常: {e}")
        return None, None

def get_quote_status(quote_id):
    """获取报价单当前状态"""
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

def submit_for_approval(quote_id, method="wecom"):
    """提交审批"""
    print(f"📤 提交审批 (方法: {method})...")
    base_url = "http://localhost:8000"

    submit_data = {
        "comments": f"统一审批测试 - {method}方式提交",
        "method": method
    }

    try:
        response = requests.post(f"{base_url}/api/v1/approval/submit/{quote_id}", json=submit_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 提交成功: {result.get('message')}")
            return True
        else:
            print(f"   ❌ 提交失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 提交异常: {e}")
        return False

def approve_via_app(quote_id):
    """通过应用界面批准"""
    print("🟢 通过应用界面批准...")
    base_url = "http://localhost:8000"

    approve_data = {
        "action": "approve",
        "comments": "应用界面批准 - 统一审批一致性测试"
    }

    try:
        response = requests.post(f"{base_url}/api/v2/approval/{quote_id}/operate", json=approve_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 批准成功: {result.get('message')}")
            return True
        else:
            print(f"   ❌ 批准失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 批准异常: {e}")
        return False

def reject_via_wecom(quote_id):
    """通过企业微信端点拒绝"""
    print("🔴 通过企业微信端点拒绝...")
    base_url = "http://localhost:8000"

    reject_data = {
        "comments": "企业微信拒绝 - 统一审批一致性测试",
        "reason": "测试拒绝流程"
    }

    try:
        response = requests.post(f"{base_url}/api/v1/wecom-approval/reject/{quote_id}", json=reject_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 拒绝成功: {result.get('message')}")
            return True
        else:
            print(f"   ❌ 拒绝失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 拒绝异常: {e}")
        return False

def print_status_comparison(quote_id, label):
    """打印状态对比"""
    print(f"\n📊 {label} - 状态检查:")
    status = get_quote_status(quote_id)
    if status:
        print(f"   💾 数据库状态: {status.get('quote_status')}")
        print(f"   🔄 审批状态: {status.get('approval_status')}")
        print(f"   📝 当前步骤: {status.get('current_step')}")
        print(f"   👤 当前审批人: {status.get('current_approvers')}")
        return status
    return None

def test_approval_consistency():
    """测试审批路径一致性"""
    print("🧪 统一审批引擎 - 路径一致性测试")
    print("=" * 60)

    # 创建测试报价单
    quote_id, quote_number = create_test_quote()
    if not quote_id:
        return

    print(f"\n🎯 测试报价单: ID={quote_id}, Number={quote_number}")

    # 初始状态检查
    initial_status = print_status_comparison(quote_id, "初始状态")

    # 测试流程1: 提交 -> 应用批准
    print(f"\n" + "="*60)
    print("🔄 测试流程1: 提交 -> 应用界面批准")
    print("="*60)

    # 提交审批
    if submit_for_approval(quote_id):
        time.sleep(2)  # 等待状态同步
        submit_status = print_status_comparison(quote_id, "提交后状态")

        # 通过应用批准
        if approve_via_app(quote_id):
            time.sleep(2)
            final_status1 = print_status_comparison(quote_id, "应用批准后状态")

    # 重置状态进行第二个测试
    print(f"\n" + "="*60)
    print("🔄 重置状态进行测试流程2...")
    print("="*60)

    # 重置报价单状态为pending
    import subprocess
    result = subprocess.run(['python3', 'reset_quote_status.py'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ 状态重置成功")
    else:
        print(f"   ❌ 状态重置失败: {result.stderr}")

    time.sleep(1)
    reset_status = print_status_comparison(quote_id, "重置后状态")

    # 测试流程2: 提交 -> 企业微信拒绝
    print(f"\n" + "="*60)
    print("🔄 测试流程2: 提交 -> 企业微信拒绝")
    print("="*60)

    # 重新提交审批
    if submit_for_approval(quote_id):
        time.sleep(2)
        submit_status2 = print_status_comparison(quote_id, "重新提交后状态")

        # 通过企业微信拒绝
        if reject_via_wecom(quote_id):
            time.sleep(2)
            final_status2 = print_status_comparison(quote_id, "企业微信拒绝后状态")

    print(f"\n" + "="*60)
    print("✨ 测试完成 - 一致性验证")
    print("="*60)
    print("🎯 关键验证点:")
    print("   1. 两种提交方式的中间状态应该相同")
    print("   2. 不同审批路径的状态同步应该一致")
    print("   3. 审批记录应该正确记录操作来源")
    print("   4. 通知机制应该在两种路径下都触发")

if __name__ == "__main__":
    test_approval_consistency()