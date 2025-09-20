#!/usr/bin/env python3
"""
测试报价单删除功能问题
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"

def test_single_delete():
    """测试单个删除"""
    print("🔍 测试单个删除功能...")

    # 获取一个可删除的报价单
    response = requests.get(f"{BASE_URL}/api/v1/quotes/test")
    if response.status_code != 200:
        print(f"❌ 获取报价单列表失败: {response.status_code} - {response.text}")
        return

    data = response.json()
    quotes = data.get("items", [])

    if not quotes:
        print("⚠️ 没有找到可测试的报价单")
        return

    # 找一个草稿状态的报价单测试
    test_quote = None
    for quote in quotes:
        if quote.get("status") == "draft":
            test_quote = quote
            break

    if not test_quote:
        print("⚠️ 没有找到草稿状态的报价单用于删除测试")
        return

    print(f"📋 测试删除报价单: {test_quote['quote_number']} (ID: {test_quote['id']})")

    # 尝试删除
    delete_url = f"{BASE_URL}/api/v1/quotes/{test_quote['id']}"
    response = requests.delete(delete_url)

    print(f"🔍 删除请求状态: {response.status_code}")
    print(f"🔍 删除响应内容: {response.text}")

    if response.status_code == 200:
        print("✅ 单个删除测试成功")
    else:
        print(f"❌ 单个删除测试失败: {response.status_code} - {response.text}")


def test_batch_delete():
    """测试批量删除"""
    print("\n🔍 测试批量删除功能...")

    # 获取可删除的报价单列表
    response = requests.get(f"{BASE_URL}/api/v1/quotes/test")
    if response.status_code != 200:
        print(f"❌ 获取报价单列表失败: {response.status_code} - {response.text}")
        return

    data = response.json()
    quotes = data.get("items", [])

    # 找草稿状态的报价单
    draft_quotes = [q for q in quotes if q.get("status") == "draft"]

    if len(draft_quotes) < 2:
        print("⚠️ 需要至少2个草稿状态的报价单来测试批量删除")
        return

    # 取前2个进行测试
    test_ids = [str(q["id"]) for q in draft_quotes[:2]]
    print(f"📋 测试批量删除报价单IDs: {test_ids}")

    # 尝试批量删除
    batch_url = f"{BASE_URL}/api/v1/admin/quotes/batch-soft-delete"

    response = requests.delete(batch_url, json=test_ids)

    print(f"🔍 批量删除请求状态: {response.status_code}")
    print(f"🔍 批量删除响应内容: {response.text}")

    if response.status_code == 200:
        print("✅ 批量删除测试成功")
    else:
        print(f"❌ 批量删除测试失败: {response.status_code} - {response.text}")


def check_user_role():
    """检查当前用户角色"""
    print("\n🔍 检查当前用户角色...")

    # 检查用户认证状态
    response = requests.get(f"{BASE_URL}/api/me")

    print(f"🔍 用户认证状态: {response.status_code}")
    print(f"🔍 用户信息: {response.text}")


if __name__ == "__main__":
    print("🚀 开始测试删除功能问题")
    print("=" * 50)

    # 检查用户角色
    check_user_role()

    # 测试单个删除
    test_single_delete()

    # 测试批量删除
    test_batch_delete()

    print("\n" + "=" * 50)
    print("🏁 测试完成")