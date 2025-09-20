#!/usr/bin/env python3
"""
模拟前端批量删除请求格式
"""

import requests
import json

def test_frontend_format():
    """模拟前端发送的请求格式"""
    print("🧪 模拟前端批量删除请求")

    # 先创建一些测试报价单
    create_data = {
        "quote_number": "TEST-DEL-001",
        "title": "删除测试",
        "quote_type": "tooling",
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

    quote_ids = []
    for i in range(2):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/quotes/",
                json={**create_data, "quote_number": f"TEST-DEL-{i+1:03d}"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 201:
                quote_data = response.json()
                quote_ids.append(str(quote_data["id"]))
                print(f"✅ 创建报价单 {quote_data['id']}")
        except Exception as e:
            print(f"❌ 创建失败: {e}")

    if not quote_ids:
        print("❌ 没有创建成功的报价单，跳过测试")
        return

    print(f"\n🗑️ 测试删除报价单: {quote_ids}")

    # 测试不同的数据发送方式
    test_cases = [
        {
            "name": "方式1: requests.delete(..., json=data)",
            "method": "json"
        },
        {
            "name": "方式2: requests.delete(..., data=json.dumps(data))",
            "method": "data_json_str"
        },
        {
            "name": "方式3: requests.request('DELETE', ..., data=data)",
            "method": "request_data"
        }
    ]

    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")

        try:
            if test_case['method'] == 'json':
                # 模拟我们之前测试成功的方式
                response = requests.delete(
                    "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                    json=quote_ids,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            elif test_case['method'] == 'data_json_str':
                # 可能更接近前端axios的方式
                response = requests.delete(
                    "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                    data=json.dumps(quote_ids),
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            elif test_case['method'] == 'request_data':
                # 更直接模拟axios的data参数
                response = requests.request(
                    'DELETE',
                    "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                    json=quote_ids,  # 这应该相当于axios的data参数
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

            print(f"   状态码: {response.status_code}")
            if response.text:
                try:
                    result = response.json()
                    if response.status_code == 200:
                        print(f"   ✅ 成功删除 {result.get('deleted_count', 0)} 个报价单")
                    else:
                        print(f"   ❌ 失败: {result.get('detail', result)}")
                except:
                    print(f"   响应文本: {response.text}")

        except Exception as e:
            print(f"   ❌ 请求异常: {str(e)}")

        # 每次测试后重新创建报价单
        if test_case != test_cases[-1]:  # 不是最后一个测试
            quote_ids.clear()
            for i in range(2):
                try:
                    response = requests.post(
                        "http://localhost:8000/api/v1/quotes/",
                        json={**create_data, "quote_number": f"TEST-DEL-{len(test_cases)+i+1:03d}"},
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    if response.status_code == 201:
                        quote_data = response.json()
                        quote_ids.append(str(quote_data["id"]))
                except:
                    pass

if __name__ == "__main__":
    test_frontend_format()