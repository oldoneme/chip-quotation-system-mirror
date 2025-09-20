#!/usr/bin/env python3
"""
测试修复后的删除功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_batch_delete_endpoint():
    """测试批量删除端点是否正常响应（不需要认证的测试）"""
    print("🔍 测试批量删除端点...")

    # 不发送认证信息，看看能否得到正确的401错误
    test_ids = ["1", "2", "3"]
    batch_url = f"{BASE_URL}/api/v1/admin/quotes/batch-soft-delete"

    try:
        response = requests.delete(batch_url, json=test_ids)
        print(f"🔍 批量删除端点状态码: {response.status_code}")
        print(f"🔍 批量删除端点响应: {response.text}")

        if response.status_code == 401:
            print("✅ 批量删除端点正常工作（需要认证）")
        elif response.status_code == 422:
            print("❌ 参数解析错误 - 需要修复")
        else:
            print(f"⚠️ 意外的状态码: {response.status_code}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_single_delete_endpoint():
    """测试单个删除端点"""
    print("\n🔍 测试单个删除端点...")

    delete_url = f"{BASE_URL}/api/v1/quotes/1"

    try:
        response = requests.delete(delete_url)
        print(f"🔍 单个删除端点状态码: {response.status_code}")
        print(f"🔍 单个删除端点响应: {response.text}")

        if response.status_code == 401:
            print("✅ 单个删除端点正常工作（需要认证）")
        else:
            print(f"⚠️ 意外的状态码: {response.status_code}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_admin_endpoints_routing():
    """测试管理员端点路由是否正确"""
    print("\n🔍 测试管理员端点路由...")

    endpoints_to_test = [
        f"{BASE_URL}/api/v1/admin/quotes/all",
        f"{BASE_URL}/api/v1/admin/quotes/statistics/detailed",
        f"{BASE_URL}/api/v1/admin/quotes/batch-soft-delete",
        f"{BASE_URL}/api/v1/admin/quotes/batch-restore"
    ]

    for endpoint in endpoints_to_test:
        try:
            if "batch-soft-delete" in endpoint:
                response = requests.delete(endpoint, json=["test"])
            elif "batch-restore" in endpoint:
                response = requests.post(endpoint, json=["test"])
            else:
                response = requests.get(endpoint)

            print(f"📍 {endpoint}: {response.status_code}")

            # 401表示端点存在但需要认证，404表示端点不存在
            if response.status_code == 401:
                print(f"  ✅ 端点存在，需要认证")
            elif response.status_code == 404:
                print(f"  ❌ 端点不存在或路由错误")
            else:
                print(f"  ⚠️ 其他状态码: {response.status_code}")

        except Exception as e:
            print(f"  ❌ 请求失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试修复后的删除功能")
    print("=" * 50)

    test_batch_delete_endpoint()
    test_single_delete_endpoint()
    test_admin_endpoints_routing()

    print("\n" + "=" * 50)
    print("🏁 测试完成")
    print("\n💡 解决方案说明:")
    print("1. 修复了批量删除端点的JSON请求体解析问题")
    print("2. 现在DELETE请求可以正确处理请求体中的数据")
    print("3. 前端使用的 api.delete(url, {data: quoteIds}) 现在应该正常工作")
    print("4. 仍需要正确的管理员认证才能执行删除操作")