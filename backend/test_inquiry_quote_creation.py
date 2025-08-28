#!/usr/bin/env python3
"""
测试询价报价创建功能
"""

import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_create_inquiry_quote():
    """测试创建询价报价"""
    
    # 模拟前端发送的询价报价数据
    quote_data = {
        "title": "测试公司 - 询价项目",
        "quote_type": "inquiry",
        "customer_name": "测试公司",
        "customer_contact": "张三",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "currency": "CNY",
        "subtotal": 1500.0,
        "discount": 0.0,
        "tax_rate": 0.0,
        "tax_amount": 0.0,
        "total_amount": 1500.0,
        "description": "芯片封装: QFN48, 测试类型: FT",
        "notes": "这是一个测试询价单",
        "items": [
            {
                "item_name": "J750 (测试机)",
                "item_description": "机时费率: ￥1500/小时, 询价系数: 1.5",
                "machine_type": "测试机",
                "machine_model": "J750",
                "configuration": "Digital Board, Analog Board",
                "quantity": 1,
                "unit": "台·小时",
                "unit_price": 1500.0,
                "total_price": 1500.0,
                "machine_id": 1
            }
        ]
    }
    
    try:
        print("🧪 测试创建询价报价...")
        print(f"📤 发送数据: {json.dumps(quote_data, indent=2, ensure_ascii=False)}")
        
        # 发送POST请求创建报价单
        response = requests.post(
            f"{BASE_URL}/quotes/",
            json=quote_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        
        if response.status_code == 201:
            created_quote = response.json()
            print("✅ 报价单创建成功!")
            print(f"📋 创建的报价单: {json.dumps(created_quote, indent=2, ensure_ascii=False)}")
            
            # 验证创建的报价单字段
            assert created_quote["quote_type"] == "inquiry"
            assert created_quote["customer_name"] == "测试公司"
            assert created_quote["total_amount"] == 1500.0
            assert created_quote["status"] == "approved"  # 询价报价直接批准
            assert created_quote["approved_by"] is not None  # 应该有批准人
            assert created_quote["approved_at"] is not None  # 应该有批准时间
            assert "quote_number" in created_quote
            print("✅ 所有字段验证通过! 询价报价已自动批准!")
            
            return created_quote
            
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return None

def test_get_quotes_list():
    """测试获取报价单列表"""
    try:
        print("🧪 测试获取报价单列表...")
        response = requests.get(f"{BASE_URL}/quotes/test")
        
        if response.status_code == 200:
            quotes_data = response.json()
            print("✅ 获取报价单列表成功!")
            print(f"📋 报价单数量: {quotes_data.get('total', 0)}")
            
            # 查找我们创建的询价报价
            inquiry_quotes = []
            for quote in quotes_data.get('items', []):
                if quote.get('quote_type') == 'inquiry':
                    inquiry_quotes.append(quote)
            
            print(f"📋 询价报价数量: {len(inquiry_quotes)}")
            for quote in inquiry_quotes:
                print(f"   - {quote.get('quote_number')}: {quote.get('title')} ({quote.get('status')})")
            
            return True
            
        else:
            print(f"❌ 获取失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 开始测试询价报价创建功能")
    print("=" * 60)
    
    # 测试1: 创建询价报价
    created_quote = test_create_inquiry_quote()
    
    print("\n" + "-" * 40)
    
    # 测试2: 获取报价单列表
    test_get_quotes_list()
    
    print("\n" + "=" * 60)
    if created_quote:
        print("🎉 所有测试通过! 询价报价创建功能正常工作")
    else:
        print("❌ 测试失败，需要检查问题")
    print("=" * 60)

if __name__ == "__main__":
    main()