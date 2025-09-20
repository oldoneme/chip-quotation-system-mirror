#!/usr/bin/env python3
"""
测试数字ID vs 字符串ID的问题
"""

import requests
import json

def test_id_types():
    """测试不同ID类型"""
    print("🧪 测试数字ID vs 字符串ID")

    # 先创建一个测试报价单
    create_data = {
        "quote_number": "TEST-ID-001",
        "title": "ID类型测试",
        "quote_type": "tooling",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "total_amount": 100.0,
        "items": [
            {
                "item_name": "测试项目",
                "item_description": "用于测试ID类型",
                "quantity": 1,
                "unit_price": 100.0,
                "total_price": 100.0
            }
        ]
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/quotes/",
            json=create_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 201:
            quote_data = response.json()
            quote_id = quote_data["id"]
            print(f"✅ 创建报价单 ID: {quote_id} (类型: {type(quote_id)})")

            # 测试不同的ID格式
            test_cases = [
                {
                    "name": "字符串ID数组",
                    "data": [str(quote_id)],
                    "expected": "成功"
                },
                {
                    "name": "数字ID数组",
                    "data": [quote_id],  # 数字类型
                    "expected": "可能失败(422)"
                },
                {
                    "name": "混合ID数组",
                    "data": [quote_id, str(quote_id)],
                    "expected": "可能失败(422)"
                }
            ]

            for test_case in test_cases:
                print(f"\n📋 测试: {test_case['name']}")
                print(f"   数据: {test_case['data']} (类型: {[type(x) for x in test_case['data']]})")
                print(f"   预期: {test_case['expected']}")

                try:
                    response = requests.delete(
                        "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                        json=test_case['data'],
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )

                    print(f"   状态码: {response.status_code}")
                    if response.text:
                        try:
                            result = response.json()
                            if response.status_code == 200:
                                print(f"   ✅ 成功: {result.get('message', '')}")
                                # 重新创建报价单供下次测试
                                create_response = requests.post(
                                    "http://localhost:8000/api/v1/quotes/",
                                    json={**create_data, "quote_number": f"TEST-ID-{len(test_cases)+1:03d}"},
                                    headers={"Content-Type": "application/json"},
                                    timeout=10
                                )
                                if create_response.status_code == 201:
                                    new_data = create_response.json()
                                    quote_id = new_data["id"]
                            else:
                                print(f"   ❌ 失败: {result.get('detail', result)}")
                        except:
                            print(f"   响应文本: {response.text}")

                except Exception as e:
                    print(f"   ❌ 请求异常: {str(e)}")

        else:
            print(f"❌ 创建报价单失败: {response.status_code}")

    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_id_types()