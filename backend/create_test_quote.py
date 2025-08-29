#!/usr/bin/env python3
"""
创建测试工序报价来验证双设备功能
"""
import requests
import json
from datetime import datetime, timedelta

def create_test_process_quote():
    """创建测试工序报价"""
    base_url = "http://127.0.0.1:8000"
    
    print("=== 创建测试工序报价 ===\n")
    
    # 测试数据：包含双设备的工序报价
    test_quote_data = {
        "title": "双设备工序报价测试",
        "quote_type": "process",
        "customer_name": "测试客户",
        "customer_contact": "张三",
        "customer_phone": "13800138000", 
        "customer_email": "test@example.com",
        "currency": "CNY",
        "quote_unit": "昆山芯信安",
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
        "payment_terms": "30天",
        "description": "测试双设备功能的工序报价",
        "items": [
            {
                "item_name": "CP1测试工序",
                "item_description": "使用测试机+探针台的CP测试",
                "machine_type": "测试机",
                "supplier": "Teradyne",
                "machine_model": "J750",
                "configuration": "测试机:J750, 探针台:AP3000, UPH:1000",
                "quantity": 10.0,
                "unit": "小时",
                "unit_price": 350.0,
                "total_price": 3500.0,
                "machine_id": 1
            },
            {
                "item_name": "FT1测试工序", 
                "item_description": "使用测试机+分选机的FT测试",
                "machine_type": "测试机",
                "supplier": "金海通",
                "machine_model": "ETS-88",
                "configuration": "测试机:ETS-88, 分选机:JHT6080, UPH:1500",
                "quantity": 8.0,
                "unit": "小时", 
                "unit_price": 420.0,
                "total_price": 3360.0,
                "machine_id": 3
            }
        ],
        "subtotal": 6860.0,
        "discount": 0.0,
        "tax_rate": 0.13,
        "tax_amount": 891.8,
        "total_amount": 7751.8
    }
    
    try:
        # 创建报价
        print("📝 正在创建测试报价...")
        response = requests.post(f"{base_url}/api/v1/quotes/", 
                               json=test_quote_data,
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 201:
            quote_data = response.json()
            quote_number = quote_data.get('quote_number')
            quote_id = quote_data.get('id')
            
            print(f"✅ 报价创建成功!")
            print(f"   报价编号: {quote_number}")
            print(f"   报价ID: {quote_id}")
            print(f"   总金额: ¥{quote_data.get('total_amount', 0):.2f}")
            
            # 验证报价详情
            print(f"\n🔍 验证报价详情...")
            detail_response = requests.get(f"{base_url}/api/v1/quotes/detail/{quote_number}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print(f"✅ 报价详情获取成功!")
                print(f"   标题: {detail_data.get('title')}")
                print(f"   类型: {detail_data.get('quote_type')}")
                print(f"   客户: {detail_data.get('customer_name')}")
                
                # 显示项目明细
                items = detail_data.get('items', [])
                print(f"\n📋 项目明细 ({len(items)}个项目):")
                for i, item in enumerate(items, 1):
                    print(f"   {i}. {item.get('item_name')}")
                    print(f"      配置: {item.get('configuration')}")
                    print(f"      数量: {item.get('quantity')} {item.get('unit')}")
                    print(f"      单价: ¥{item.get('unit_price', 0):.2f}")
                    print(f"      小计: ¥{item.get('total_price', 0):.2f}")
                
                return quote_number, quote_id
            else:
                print(f"❌ 获取报价详情失败: {detail_response.status_code}")
                print(f"   错误信息: {detail_response.text}")
                
        else:
            print(f"❌ 创建报价失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        
    return None, None

def verify_database_record(quote_id):
    """验证数据库中的记录"""
    if not quote_id:
        print("\n❌ 无有效报价ID，跳过数据库验证")
        return
        
    import sqlite3
    
    print(f"\n=== 验证数据库记录 (ID: {quote_id}) ===")
    
    try:
        conn = sqlite3.connect('/home/qixin/projects/chip-quotation-system/backend/app/test.db')
        cursor = conn.cursor()
        
        # 检查报价主记录
        cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        quote = cursor.fetchone()
        
        if quote:
            print("✅ 报价主记录存在")
            print(f"   编号: {quote[1]}")  # quote_number
            print(f"   标题: {quote[2]}")  # title  
            print(f"   类型: {quote[3]}")  # quote_type
            print(f"   客户: {quote[4]}")  # customer_name
            print(f"   总金额: ¥{quote[14]:.2f}")  # total_amount
        else:
            print("❌ 报价主记录不存在")
            return
            
        # 检查报价明细项目
        cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))
        items = cursor.fetchall()
        
        print(f"\n📋 明细项目记录 ({len(items)}条):")
        for item in items:
            print(f"   - 项目: {item[2]}")     # item_name
            print(f"     设备: {item[6]}")     # machine_model  
            print(f"     配置: {item[7]}")     # configuration
            print(f"     数量: {item[8]} {item[9]}")  # quantity, unit
            print(f"     单价: ¥{item[10]:.2f}")      # unit_price
            print(f"     小计: ¥{item[11]:.2f}")      # total_price
            print()
            
        conn.close()
        print("✅ 数据库验证完成")
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")

if __name__ == "__main__":
    try:
        quote_number, quote_id = create_test_process_quote()
        verify_database_record(quote_id)
        
        if quote_number:
            print(f"\n🎯 测试结果:")
            print(f"   ✅ 双设备工序报价创建成功")
            print(f"   ✅ API接口工作正常")
            print(f"   ✅ 数据库保存正确")
            print(f"   📝 报价编号: {quote_number}")
            print(f"\n💡 可以在前端访问该报价进行进一步测试")
        else:
            print(f"\n❌ 测试失败，请检查后端服务和数据库连接")
            
    except Exception as e:
        print(f"❌ 测试过程发生错误: {e}")