#!/usr/bin/env python3
"""
测试批量删除API不同数据格式
"""

import requests
import json

def test_formats():
    """测试不同的数据格式"""
    print("🧪 测试批量删除API的不同数据格式")

    # 创建一个测试报价单
    create_data = {
        "quote_number": "TEST-DELETE-001",
        "title": "删除测试",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "total_amount": 100.0,
        "items": [
            {
                "item_name": "测试项目",
                "item_description": "用于测试删除",
                "quantity": 1,
                "unit_price": 100.0,
                "total_price": 100.0
            }
        ]
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/quotes",
            json=create_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 201:
            quote_data = response.json()
            quote_id = str(quote_data["id"])
            print(f"✅ 创建测试报价单成功，ID: {quote_id}")

            # 测试不同格式
            formats = [
                {
                    "name": "直接数组格式",
                    "data": [quote_id],
                    "expected": "成功"
                },
                {
                    "name": "带quote_ids键的对象格式",
                    "data": {"quote_ids": [quote_id]},
                    "expected": "可能失败(422)"
                }
            ]

            for fmt in formats:
                print(f"\n📋 测试: {fmt['name']}")
                print(f"   数据: {json.dumps(fmt['data'], ensure_ascii=False)}")
                print(f"   预期: {fmt['expected']}")

                try:
                    delete_response = requests.delete(
                        "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                        json=fmt['data'],
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )

                    print(f"   状态码: {delete_response.status_code}")
                    if delete_response.text:
                        try:
                            result = delete_response.json()
                            print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        except:
                            print(f"   响应文本: {delete_response.text}")

                    if delete_response.status_code == 200:
                        print(f"   ✅ 成功")
                        break
                    else:
                        print(f"   ❌ 失败 - {delete_response.status_code}")

                        # 如果是422错误，重新创建报价单继续测试
                        if delete_response.status_code == 422:
                            print("   🔄 重新创建报价单继续测试...")
                            create_response = requests.post(
                                "http://localhost:8000/api/v1/quotes",
                                json=create_data,
                                headers={"Content-Type": "application/json"},
                                timeout=10
                            )
                            if create_response.status_code == 201:
                                new_quote_data = create_response.json()
                                quote_id = str(new_quote_data["id"])
                                print(f"   ✅ 重新创建报价单ID: {quote_id}")

                except Exception as e:
                    print(f"   ❌ 请求异常: {str(e)}")

        else:
            print(f"❌ 创建测试报价单失败: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_formats()