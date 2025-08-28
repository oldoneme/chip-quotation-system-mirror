#!/usr/bin/env python3
"""
测试报价单API的完整CRUD操作
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_quote_statistics():
    """测试统计API"""
    print("🔍 测试报价单统计...")
    response = requests.get(f"{BASE_URL}/quotes/statistics")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 统计信息: 总数={stats['total']}, 草稿={stats['draft']}, 待审批={stats['pending']}, 已批准={stats['approved']}, 已拒绝={stats['rejected']}")
        return True
    else:
        print(f"❌ 统计API失败: {response.status_code} - {response.text}")
        return False

def test_get_quotes():
    """测试获取报价单列表"""
    print("🔍 测试获取报价单列表...")
    response = requests.get(f"{BASE_URL}/quotes/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取报价单列表成功: 共{len(data.get('items', []))}条记录")
        return data.get('items', [])
    else:
        print(f"❌ 获取列表失败: {response.status_code} - {response.text}")
        return []

def test_get_quote_by_id(quote_id):
    """测试根据ID获取报价单"""
    print(f"🔍 测试获取报价单ID={quote_id}...")
    response = requests.get(f"{BASE_URL}/quotes/{quote_id}")
    if response.status_code == 200:
        quote = response.json()
        print(f"✅ 获取报价单成功: {quote['quote_number']} - {quote['title']}")
        return quote
    else:
        print(f"❌ 获取报价单失败: {response.status_code} - {response.text}")
        return None

def test_get_quote_by_number(quote_number):
    """测试根据报价单号获取报价单"""
    print(f"🔍 测试获取报价单号={quote_number}...")
    response = requests.get(f"{BASE_URL}/quotes/number/{quote_number}")
    if response.status_code == 200:
        quote = response.json()
        print(f"✅ 根据报价单号获取成功: {quote['title']}")
        return quote
    else:
        print(f"❌ 根据报价单号获取失败: {response.status_code} - {response.text}")
        return None

def test_create_quote():
    """测试创建新报价单"""
    print("🔍 测试创建新报价单...")
    
    new_quote = {
        "title": "API测试报价单",
        "quote_type": "inquiry",
        "customer_name": "测试客户公司",
        "customer_contact": "测试联系人",
        "customer_phone": "123-4567-8901",
        "customer_email": "test@example.com",
        "currency": "CNY",
        "subtotal": 50000.0,
        "discount": 2000.0,
        "tax_rate": 0.13,
        "tax_amount": 6240.0,
        "total_amount": 54240.0,
        "payment_terms": "测试付款条件",
        "description": "这是一个通过API创建的测试报价单",
        "items": [
            {
                "item_name": "API测试项目",
                "item_description": "测试项目描述",
                "machine_type": "测试设备",
                "supplier": "测试供应商",
                "machine_model": "测试型号",
                "quantity": 100,
                "unit": "件",
                "unit_price": 500.0,
                "total_price": 50000.0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/quotes/", json=new_quote)
    if response.status_code == 201:
        quote = response.json()
        print(f"✅ 创建报价单成功: {quote['quote_number']} - {quote['title']}")
        return quote
    else:
        print(f"❌ 创建报价单失败: {response.status_code} - {response.text}")
        return None

def test_update_quote_status(quote_id, new_status):
    """测试更新报价单状态"""
    print(f"🔍 测试更新报价单状态: ID={quote_id}, 新状态={new_status}...")
    
    status_update = {
        "status": new_status,
        "comments": f"API测试：状态更改为{new_status}"
    }
    
    response = requests.patch(f"{BASE_URL}/quotes/{quote_id}/status", json=status_update)
    if response.status_code == 200:
        quote = response.json()
        print(f"✅ 状态更新成功: {quote['status']}")
        return quote
    else:
        print(f"❌ 状态更新失败: {response.status_code} - {response.text}")
        return None

def test_submit_approval(quote_id):
    """测试提交审批"""
    print(f"🔍 测试提交审批: ID={quote_id}...")
    
    response = requests.post(f"{BASE_URL}/quotes/{quote_id}/submit")
    if response.status_code == 200:
        quote = response.json()
        print(f"✅ 提交审批成功: 状态={quote['status']}")
        return quote
    else:
        print(f"❌ 提交审批失败: {response.status_code} - {response.text}")
        return None

def test_get_approval_records(quote_id):
    """测试获取审批记录"""
    print(f"🔍 测试获取审批记录: ID={quote_id}...")
    
    response = requests.get(f"{BASE_URL}/quotes/{quote_id}/approval-records")
    if response.status_code == 200:
        records = response.json()
        print(f"✅ 获取审批记录成功: 共{len(records)}条记录")
        return records
    else:
        print(f"❌ 获取审批记录失败: {response.status_code} - {response.text}")
        return []

def main():
    """主测试函数"""
    print("🚀 开始测试报价单API...")
    print("=" * 60)
    
    # 测试1: 统计信息
    if not test_quote_statistics():
        return
    print()
    
    # 测试2: 获取报价单列表
    quotes = test_get_quotes()
    if not quotes:
        return
    print()
    
    # 测试3: 根据ID获取报价单
    first_quote = test_get_quote_by_id(quotes[0]['id']) if quotes else None
    if not first_quote:
        return
    print()
    
    # 测试4: 根据报价单号获取报价单
    quote_by_number = test_get_quote_by_number(first_quote['quote_number'])
    if not quote_by_number:
        return
    print()
    
    # 测试5: 创建新报价单
    new_quote = test_create_quote()
    if not new_quote:
        return
    print()
    
    # 测试6: 提交审批（如果是草稿状态）
    if new_quote['status'] == 'draft':
        approval_quote = test_submit_approval(new_quote['id'])
        if approval_quote:
            print()
            
            # 测试7: 获取审批记录
            test_get_approval_records(new_quote['id'])
            print()
    
    # 测试8: 更新最终统计
    print("📊 最终统计信息:")
    test_quote_statistics()
    
    print("\n" + "=" * 60)
    print("🎉 API测试完成！")
    print("\n可用的API端点:")
    print("1. GET /api/v1/quotes/statistics - 获取统计信息")
    print("2. GET /api/v1/quotes/ - 获取报价单列表")
    print("3. GET /api/v1/quotes/{id} - 根据ID获取报价单")
    print("4. GET /api/v1/quotes/number/{quote_number} - 根据报价单号获取")
    print("5. POST /api/v1/quotes/ - 创建新报价单")
    print("6. PATCH /api/v1/quotes/{id}/status - 更新状态")
    print("7. POST /api/v1/quotes/{id}/submit - 提交审批")
    print("8. GET /api/v1/quotes/{id}/approval-records - 获取审批记录")
    print("\n访问API文档: http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"\n测试出现错误: {e}")