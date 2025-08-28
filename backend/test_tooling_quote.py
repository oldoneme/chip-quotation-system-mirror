#!/usr/bin/env python3
"""
测试工装夹具报价的数据库集成
"""
import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_tooling_quote_creation():
    """测试工装夹具报价创建"""
    
    # 工装夹具报价测试数据
    tooling_quote_data = {
        "title": "芯片测试工装项目 - 测试科技有限公司",
        "quote_type": "tooling",
        "customer_name": "测试科技有限公司",
        "customer_contact": "张三",
        "customer_phone": "13800138000",
        "customer_email": "test@example.com",
        "currency": "CNY",
        "subtotal": 2500.0,
        "total_amount": 2500.0,
        "payment_terms": "30_days",
        "description": "项目：芯片测试工装项目，芯片封装：BGA256，测试类型：FT测试",
        "notes": "交期：2-3周，备注：需要定制测试夹具",
        "items": [
            {
                "item_name": "测试夹具-标准夹具",
                "item_description": "BGA256专用夹具",
                "quantity": 2,
                "unit_price": 800.0,
                "total_price": 1600.0,
                "unit": "件"
            },
            {
                "item_name": "工装板-测试板",
                "item_description": "多通道测试板",
                "quantity": 1,
                "unit_price": 500.0,
                "total_price": 500.0,
                "unit": "件"
            },
            {
                "item_name": "测试程序开发",
                "item_description": "工程服务费",
                "quantity": 1,
                "unit_price": 300.0,
                "total_price": 300.0,
                "unit": "项"
            },
            {
                "item_name": "设备调试费",
                "item_description": "产线设置费",
                "quantity": 1,
                "unit_price": 100.0,
                "total_price": 100.0,
                "unit": "项"
            }
        ]
    }
    
    try:
        # 创建报价单
        print("创建工装夹具报价单...")
        response = requests.post(f"{BASE_URL}/api/v1/quotes/", json=tooling_quote_data)
        
        if response.status_code == 201:
            created_quote = response.json()
            print(f"✅ 工装夹具报价单创建成功！")
            print(f"   报价单号: {created_quote['quote_number']}")
            print(f"   报价类型: {created_quote['quote_type']}")
            print(f"   总价: ¥{created_quote['total_amount']:.2f}")
            print(f"   项目数量: {len(created_quote['items'])}")
            
            # 显示项目详情
            print("   报价项目:")
            for item in created_quote['items']:
                print(f"   - {item['item_name']}: ¥{item['total_price']:.2f}")
            
            return created_quote
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def check_tooling_quotes_in_db():
    """检查数据库中的工装夹具报价"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/quotes/?quote_type=tooling")
        
        if response.status_code == 200:
            quotes = response.json()
            print(f"\n📊 数据库中共有 {len(quotes)} 个工装夹具报价:")
            
            for quote in quotes:
                print(f"   ID: {quote['id']} | 编号: {quote['quote_number']} | 状态: {quote['status']} | 总价: ¥{quote['total_amount']:.2f}")
                
        else:
            print(f"❌ 获取报价列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 查询异常: {str(e)}")

if __name__ == "__main__":
    print("🧪 开始测试工装夹具报价数据库集成")
    print("=" * 50)
    
    # 先检查现有报价
    check_tooling_quotes_in_db()
    
    # 创建新报价
    created_quote = test_tooling_quote_creation()
    
    if created_quote:
        # 再次检查数据库
        print("\n" + "=" * 50)
        check_tooling_quotes_in_db()
        print("\n✅ 工装夹具报价测试完成！")
    else:
        print("\n❌ 工装夹具报价测试失败！")