#!/usr/bin/env python3
"""
测试统一审批系统的企业微信集成
验证内部操作是否正确触发企业微信通知
"""

import requests
import json
from datetime import datetime

def test_unified_approval_with_wecom():
    """测试统一审批系统企业微信集成"""
    print("🧪 测试统一审批系统企业微信集成")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # 检查后端服务
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务无法访问")
            return False
        print("✅ 后端服务正常")
    except Exception as e:
        print(f"❌ 后端服务连接失败: {str(e)}")
        return False

    # 测试场景1: V2 API提交审批
    print("\n📋 场景1: 使用V2 API提交审批")
    test_v2_submit_approval(base_url)

    # 测试场景2: V2 API批准审批
    print("\n📋 场景2: 使用V2 API批准审批")
    test_v2_approve_quota(base_url)

    # 测试场景3: V1 API提交审批
    print("\n📋 场景3: 使用V1 API提交审批（向后兼容）")
    test_v1_submit_approval(base_url)

    print("\n" + "=" * 60)
    print("🎯 测试总结:")
    print("   如果所有操作都成功，说明统一审批引擎已正确集成企业微信")
    print("   内部操作应该会触发企业微信审批创建和通知发送")
    print("   检查日志输出中是否有企业微信相关的成功信息")

def test_v2_submit_approval(base_url):
    """测试V2 API提交审批"""
    try:
        # 查找一个可用的报价单
        response = requests.get(f"{base_url}/api/v1/quotes/", timeout=10)
        if response.status_code == 200:
            quotes = response.json()
            if quotes and len(quotes) > 0:
                quote_id = quotes[0]["id"]
                print(f"   使用报价单: {quote_id}")

                # 使用V2 API提交审批
                submit_data = {
                    "action": "submit",
                    "comments": "测试统一审批引擎的企业微信集成",
                    "channel": "internal"  # 明确指定为内部操作
                }

                response = requests.post(
                    f"{base_url}/api/v2/approval/{quote_id}/operate",
                    json=submit_data,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )

                print(f"   状态码: {response.status_code}")
                if response.text:
                    try:
                        result = response.json()
                        if response.status_code == 200:
                            print(f"   ✅ 成功: {result.get('message', '')}")
                            print(f"   新状态: {result.get('new_status', '')}")
                            print(f"   需要同步: {result.get('sync_required', False)}")

                            # 检查是否触发了企业微信集成
                            if result.get('sync_required'):
                                print("   🔔 应该触发企业微信审批创建")
                            else:
                                print("   ⚠️ 未触发企业微信同步")
                        else:
                            print(f"   ❌ 失败: {result.get('message', result)}")
                    except:
                        print(f"   响应文本: {response.text}")
            else:
                print("   ❌ 没有找到可用的报价单")
        else:
            print(f"   ❌ 获取报价单列表失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")

def test_v2_approve_quota(base_url):
    """测试V2 API批准审批"""
    try:
        # 查找一个pending状态的报价单
        response = requests.get(f"{base_url}/api/v1/quotes/?status=pending", timeout=10)
        if response.status_code == 200:
            quotes = response.json()
            pending_quotes = [q for q in quotes if q.get('status') == 'pending']

            if pending_quotes:
                quote_id = pending_quotes[0]["id"]
                print(f"   使用待审批报价单: {quote_id}")

                # 使用V2 API批准审批
                approve_data = {
                    "action": "approve",
                    "comments": "测试统一审批引擎的企业微信通知",
                    "channel": "internal"  # 明确指定为内部操作
                }

                response = requests.post(
                    f"{base_url}/api/v2/approval/{quote_id}/operate",
                    json=approve_data,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )

                print(f"   状态码: {response.status_code}")
                if response.text:
                    try:
                        result = response.json()
                        if response.status_code == 200:
                            print(f"   ✅ 成功: {result.get('message', '')}")
                            print(f"   新状态: {result.get('new_status', '')}")
                            print("   🔔 应该触发企业微信批准通知")
                        else:
                            print(f"   ❌ 失败: {result.get('message', result)}")
                    except:
                        print(f"   响应文本: {response.text}")
            else:
                print("   ❌ 没有找到待审批的报价单")
        else:
            print(f"   ❌ 获取待审批报价单失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")

def test_v1_submit_approval(base_url):
    """测试V1 API提交审批（向后兼容）"""
    try:
        # 查找一个draft状态的报价单
        response = requests.get(f"{base_url}/api/v1/quotes/?status=draft", timeout=10)
        if response.status_code == 200:
            quotes = response.json()
            draft_quotes = [q for q in quotes if q.get('status') == 'draft']

            if draft_quotes:
                quote_id = draft_quotes[0]["id"]
                print(f"   使用草稿报价单: {quote_id}")

                # 使用V1 API提交审批
                submit_data = {
                    "comments": "测试V1 API向后兼容的企业微信集成"
                }

                response = requests.post(
                    f"{base_url}/api/v1/approval/submit/{quote_id}",
                    json=submit_data,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )

                print(f"   状态码: {response.status_code}")
                if response.text:
                    try:
                        result = response.json()
                        if response.status_code == 200:
                            print(f"   ✅ 成功: {result.get('message', '')}")
                            print(f"   审批方法: {result.get('approval_method', '')}")
                            print(f"   新状态: {result.get('new_status', '')}")
                            print("   🔔 V1 API也应该触发企业微信集成")
                        else:
                            print(f"   ❌ 失败: {result.get('message', result)}")
                    except:
                        print(f"   响应文本: {response.text}")
            else:
                print("   ❌ 没有找到草稿状态的报价单")
        else:
            print(f"   ❌ 获取草稿报价单失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_unified_approval_with_wecom()