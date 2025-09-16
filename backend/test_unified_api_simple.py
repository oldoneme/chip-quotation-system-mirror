#!/usr/bin/env python3
"""
Step 3.3: 简化的统一审批API测试
只测试状态和历史查询，不测试需要认证的操作
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

def test_unified_approval_endpoints():
    """测试统一审批API的基本功能"""
    print("🧪 测试统一审批API端点")
    print("=" * 50)

    # 测试用的报价单ID（从现有数据中选择）
    approved_quote = "2a72d639-1486-442d-bce3-02a20672de28"  # 已批准
    pending_quote = "b75a20ec-79c0-4c98-94de-55bdf4928a97"   # 待审批

    test_results = []

    # 1. 测试已批准报价单的状态查询
    print(f"\n🔍 测试1: 查询已批准报价单状态")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/approval/status/{approved_quote}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data['quote_number']}, 状态: {data['approval_status']}")
            test_results.append(True)
        else:
            print(f"   ❌ 失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"   💥 异常: {e}")
        test_results.append(False)

    # 2. 测试待审批报价单的状态查询
    print(f"\n🔍 测试2: 查询待审批报价单状态")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/approval/status/{pending_quote}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data['quote_number']}, 状态: {data['approval_status']}")
            test_results.append(True)
        else:
            print(f"   ❌ 失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"   💥 异常: {e}")
        test_results.append(False)

    # 3. 测试历史查询
    print(f"\n📚 测试3: 查询审批历史")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/approval/history/{approved_quote}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: 历史记录数 = {data['total']}")
            test_results.append(True)
        else:
            print(f"   ❌ 失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"   💥 异常: {e}")
        test_results.append(False)

    # 4. 测试API路径格式兼容性
    print(f"\n🛣️ 测试4: API路径格式兼容性")
    try:
        # 测试 UUID 格式
        response = requests.get(f"{BASE_URL}{API_PREFIX}/approval/status/{approved_quote}")
        uuid_works = response.status_code == 200

        # 测试不存在的ID
        response = requests.get(f"{BASE_URL}{API_PREFIX}/approval/status/nonexistent")
        not_found_works = response.status_code == 404

        if uuid_works and not_found_works:
            print(f"   ✅ 成功: UUID格式支持正常，错误处理正确")
            test_results.append(True)
        else:
            print(f"   ❌ 失败: UUID支持={uuid_works}, 错误处理={not_found_works}")
            test_results.append(False)
    except Exception as e:
        print(f"   💥 异常: {e}")
        test_results.append(False)

    # 总结测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    passed = sum(test_results)
    total = len(test_results)

    for i, result in enumerate(test_results, 1):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   测试{i}: {status}")

    print(f"\n总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 统一审批API基本功能测试全部通过!")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = test_unified_approval_endpoints()
    exit(0 if success else 1)