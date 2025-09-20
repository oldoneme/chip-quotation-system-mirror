#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_status_sync_with_logging():
    """测试状态同步，查看详细日志"""
    base_url = "http://127.0.0.1:8000"
    quote_id = 12  # 使用已存在的报价单

    print("🔍 测试状态同步 - 详细日志版本")
    print("=" * 50)

    # 1. 检查初始状态
    print("\n📊 1. 检查初始状态")
    response = requests.get(f"{base_url}/api/v2/approval/{quote_id}/status")
    if response.status_code == 200:
        status_data = response.json()
        print(f"初始状态: {status_data}")
    else:
        print(f"❌ 获取状态失败: {response.status_code} - {response.text}")
        return False

    # 2. 提交审批
    print("\n🚀 2. 提交审批 (查看详细日志)")
    operation_data = {
        "action": "SUBMIT",
        "operator_id": 1,
        "channel": "INTERNAL",
        "comments": "测试状态同步日志"
    }

    response = requests.post(f"{base_url}/api/v2/approval/{quote_id}/operate", json=operation_data)
    print(f"API响应状态: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"API响应: {result}")
    else:
        print(f"❌ 操作失败: {response.status_code} - {response.text}")
        return False

    # 3. 再次检查状态
    print("\n📊 3. 检查操作后状态")
    response = requests.get(f"{base_url}/api/v2/approval/{quote_id}/status")
    if response.status_code == 200:
        status_data = response.json()
        print(f"操作后状态: {status_data}")

        # 验证状态一致性
        current_status = status_data.get('current_status')
        approval_status = status_data.get('approval_status')

        if current_status == approval_status:
            print("✅ 状态字段一致")
            return True
        else:
            print(f"❌ 状态字段不一致: current_status={current_status}, approval_status={approval_status}")
            return False
    else:
        print(f"❌ 获取状态失败: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_status_sync_with_logging()
    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")