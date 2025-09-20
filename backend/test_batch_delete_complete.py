#!/usr/bin/env python3
"""
完整测试批量删除功能
"""

import requests
import json

def create_test_quotes(count=3):
    """创建测试报价单"""
    print(f"📝 创建 {count} 个测试报价单...")

    create_data = {
        "title": "批量删除测试",
        "quote_type": "tooling",
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

    quote_ids = []
    for i in range(count):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/quotes/",
                json={**create_data, "quote_number": f"BATCH-DEL-{i+1:03d}"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 201:
                quote_data = response.json()
                quote_ids.append(quote_data["id"])
                print(f"   ✅ 创建报价单 ID: {quote_data['id']}")
        except Exception as e:
            print(f"   ❌ 创建失败: {e}")

    return quote_ids

def test_batch_delete():
    """测试批量删除的各种格式"""
    print("🧪 测试批量删除API各种格式")

    test_cases = [
        {
            "name": "字符串ID数组",
            "format": "string_array",
            "expected": "成功"
        },
        {
            "name": "数字ID数组",
            "format": "number_array",
            "expected": "现在应该成功"
        },
        {
            "name": "对象格式 - 字符串ID",
            "format": "object_string",
            "expected": "成功"
        },
        {
            "name": "对象格式 - 数字ID",
            "format": "object_number",
            "expected": "现在应该成功"
        }
    ]

    for test_case in test_cases:
        print(f"\n📋 测试: {test_case['name']}")
        print(f"   预期: {test_case['expected']}")

        # 为每个测试创建新的报价单
        quote_ids = create_test_quotes(2)
        if not quote_ids:
            print("   ❌ 跳过测试 - 无法创建报价单")
            continue

        # 根据测试格式准备数据
        if test_case['format'] == 'string_array':
            test_data = [str(id) for id in quote_ids]
        elif test_case['format'] == 'number_array':
            test_data = quote_ids  # 保持数字类型
        elif test_case['format'] == 'object_string':
            test_data = {"quote_ids": [str(id) for id in quote_ids]}
        elif test_case['format'] == 'object_number':
            test_data = {"quote_ids": quote_ids}  # 保持数字类型

        print(f"   发送数据: {test_data}")
        print(f"   数据类型: {type(test_data)} - 元素类型: {[type(x) for x in (test_data if isinstance(test_data, list) else test_data['quote_ids'])]}")

        try:
            response = requests.delete(
                "http://localhost:8000/api/v1/admin/quotes/batch-soft-delete",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            print(f"   状态码: {response.status_code}")

            if response.text:
                try:
                    result = response.json()
                    if response.status_code == 200:
                        print(f"   ✅ 成功: {result.get('message', '')} (删除了 {result.get('deleted_count', 0)} 个)")
                    else:
                        print(f"   ❌ 失败: {result.get('detail', result)}")
                except:
                    print(f"   响应文本: {response.text}")

        except Exception as e:
            print(f"   ❌ 请求异常: {str(e)}")

def main():
    """主函数"""
    print("🔧 完整批量删除功能测试")
    print("=" * 50)

    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务无法访问")
            return
        print("✅ 后端服务正常")
    except Exception as e:
        print(f"❌ 后端服务连接失败: {str(e)}")
        return

    test_batch_delete()

    print("\n" + "=" * 50)
    print("🎯 测试总结:")
    print("   如果所有格式都返回200状态码，说明批量删除API修复成功")
    print("   前端的'批量删除失败'问题应该已解决")

if __name__ == "__main__":
    main()