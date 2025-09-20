#!/usr/bin/env python3
"""
测试批量删除API问题
"""

import requests
import json

def test_batch_soft_delete():
    """测试批量软删除API"""
    print("🧪 测试批量软删除API")

    # 创建一个测试报价单
    print("📝 先创建一个测试报价单...")
    create_data = {
        "quote_number": "TEST-BATCH-001",
        "title": "批量删除测试",
        "customer_name": "测试客户",
        "customer_contact": "测试联系人",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "total_amount": 100.0,
        "items": [
            {
                "item_name": "测试项目",
                "item_description": "用于测试批量删除",
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
            print(f"✅ 创建成功，报价单ID: {quote_id}")

            # 测试批量软删除API
            print(f"\n🗑️ 测试批量软删除API...")

            # 测试不同的数据格式
            test_cases = [
                {
                    "name": "字符串列表格式",
                    "data": [quote_id]
                },
                {
                    "name": "带quote_ids键的格式",
                    "data": {"quote_ids": [quote_id]}
                },
                {
                    "name": "数字列表格式",
                    "data": [int(quote_id)]
                }
            ]

            for test_case in test_cases:
                print(f"\n📋 测试: {test_case['name']}")
                print(f"   数据: {json.dumps(test_case['data'])}")

                try:
                    delete_response = requests.delete(
                        "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                        json=test_case['data'],
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )

                    print(f"   状态码: {delete_response.status_code}")
                    if delete_response.text:
                        try:
                            result = delete_response.json()
                            print(f"   响应: {json.dumps(result, ensure_ascii=False)}")
                        except:
                            print(f"   响应文本: {delete_response.text}")

                    if delete_response.status_code == 200:
                        print(f"   ✅ 成功")
                        break
                    else:
                        print(f"   ❌ 失败")

                except Exception as e:
                    print(f"   ❌ 请求异常: {str(e)}")

        else:
            print(f"❌ 创建报价单失败: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

def test_single_delete():
    """测试单个删除API"""
    print(f"\n🧪 测试单个删除API")

    # 先检查有没有现有的报价单
    try:
        # 这个需要认证，先跳过
        print("   跳过单个删除测试（需要认证）")

    except Exception as e:
        print(f"❌ 单个删除测试异常: {str(e)}")

if __name__ == "__main__":
    print("🔧 批量删除API问题诊断")
    print("=" * 50)

    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务无法访问")
            exit(1)
        print("✅ 后端服务正常")
    except Exception as e:
        print(f"❌ 后端服务连接失败: {str(e)}")
        exit(1)

    test_batch_soft_delete()
    test_single_delete()

    print(f"\n💡 诊断建议:")
    print(f"   1. 检查前端发送的数据格式是否正确")
    print(f"   2. 确认API期待的参数格式")
    print(f"   3. 可能需要修改FastAPI的参数接收方式")