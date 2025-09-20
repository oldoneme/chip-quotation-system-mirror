#!/usr/bin/env python3
"""
直接测试批量删除API
"""

import requests
import json

def test_batch_delete():
    """测试批量删除API两种格式"""
    print("🧪 测试批量删除API两种格式")

    # 使用现有的报价单ID进行测试
    quote_ids = ["12", "11"]  # 使用现有未删除的报价单

    # 测试格式1: 直接数组
    print("\n📋 测试格式1: 直接数组")
    try:
        response = requests.delete(
            "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
            json=quote_ids,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"   状态码: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except:
                print(f"   响应文本: {response.text}")

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")

    # 测试格式2: 对象格式
    print("\n📋 测试格式2: 对象格式")
    try:
        response = requests.delete(
            "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
            json={"quote_ids": quote_ids},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"   状态码: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except:
                print(f"   响应文本: {response.text}")

    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_batch_delete()