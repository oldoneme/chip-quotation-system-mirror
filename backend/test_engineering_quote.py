#!/usr/bin/env python3
"""
测试工程机时报价的数据库集成
"""
import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_engineering_quote_creation():
    """测试工程机时报价创建"""
    
    # 工程机时报价测试数据
    engineering_quote_data = {
        "title": "芯片工程测试项目 - 科技测试公司",
        "quote_type": "engineering",
        "customer_name": "科技测试公司",
        "customer_contact": "李工",
        "customer_phone": "13900139000",
        "customer_email": "engineer@example.com",
        "currency": "CNY",
        "subtotal": 15000.0,
        "total_amount": 15000.0,
        "payment_terms": "30_days",
        "description": "工程机时报价，工程系数：1.2，币种：CNY",
        "notes": "汇率：7.2，选配设备：2台",
        "items": [
            {
                "item_name": "V93000 - 标准配置",
                "item_description": "工程机时 - Advantest",
                "machine_type": "测试机",
                "supplier": "Advantest",
                "machine_model": "V93000",
                "configuration": "标准配置",
                "quantity": 8.0,
                "unit": "台·小时",
                "unit_price": 1500.0,
                "total_price": 12000.0
            },
            {
                "item_name": "PA200 - 高级配置",
                "item_description": "工程机时 - AETRIUM",
                "machine_type": "分选机",
                "supplier": "AETRIUM",
                "machine_model": "PA200",
                "configuration": "高级配置",
                "quantity": 3.0,
                "unit": "台·小时",
                "unit_price": 1000.0,
                "total_price": 3000.0
            }
        ]
    }
    
    try:
        # 创建报价单
        print("创建工程机时报价单...")
        response = requests.post(f"{BASE_URL}/api/v1/quotes/", json=engineering_quote_data)
        
        if response.status_code == 201:
            created_quote = response.json()
            print(f"✅ 工程机时报价单创建成功！")
            print(f"   报价单号: {created_quote['quote_number']}")
            print(f"   报价类型: {created_quote['quote_type']}")
            print(f"   总价: ¥{created_quote['total_amount']:.2f}")
            print(f"   项目数量: {len(created_quote['items'])}项")
            
            # 显示项目详情
            print("   报价项目:")
            for item in created_quote['items']:
                print(f"   - {item['item_name']}: {item['quantity']}{item['unit']} × ¥{item['unit_price']:.2f} = ¥{item['total_price']:.2f}")
            
            return created_quote
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def check_engineering_quotes_in_db():
    """检查数据库中的工程机时报价"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/quotes/?quote_type=engineering")
        
        if response.status_code == 200:
            quotes = response.json()
            print(f"\n📊 数据库中共有 {len(quotes)} 个工程机时报价:")
            
            for quote in quotes:
                print(f"   ID: {quote['id']} | 编号: {quote['quote_number']} | 状态: {quote['status']} | 总价: ¥{quote['total_amount']:.2f}")
                
        else:
            print(f"❌ 获取报价列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 查询异常: {str(e)}")

if __name__ == "__main__":
    print("🧪 开始测试工程机时报价数据库集成")
    print("=" * 50)
    
    # 先检查现有报价
    check_engineering_quotes_in_db()
    
    # 创建新报价
    created_quote = test_engineering_quote_creation()
    
    if created_quote:
        # 再次检查数据库
        print("\n" + "=" * 50)
        check_engineering_quotes_in_db()
        print("\n✅ 工程机时报价测试完成！")
    else:
        print("\n❌ 工程机时报价测试失败！")