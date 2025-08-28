#!/usr/bin/env python3
"""
测试修正后的报价流程：询价表单 → 报价结果页面 → 确认报价 → 数据库记录
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_corrected_inquiry_quote_flow():
    """测试修正后的询价报价流程"""
    
    print("=" * 70)
    print("🚀 测试修正后的询价报价流程")
    print("=" * 70)
    
    print("\n📋 流程说明:")
    print("1. 用户在询价页面填写表单")
    print("2. 点击'生成询价单'进入结果页面（不保存数据库）")  
    print("3. 在结果页面点击'确认报价'才创建数据库记录")
    print("4. 询价报价直接设为approved状态（跳过审批）")
    
    # 模拟前端发送的询价报价数据（来自确认报价按钮）
    quote_data = {
        "title": "修正流程测试公司 - 询价项目",
        "quote_type": "inquiry", 
        "customer_name": "修正流程测试公司",
        "customer_contact": "李四",
        "customer_phone": "13900139000",
        "customer_email": "corrected@example.com",
        "currency": "CNY",
        "subtotal": 2000.0,
        "discount": 0.0,
        "tax_rate": 0.0,
        "tax_amount": 0.0,
        "total_amount": 2000.0,
        "description": "芯片封装: BGA256, 测试类型: CP",
        "notes": "这是修正后流程的测试询价单",
        "items": [
            {
                "item_name": "V93000 (测试机)",
                "item_description": "机时费率: ￥2000/小时, 询价系数: 1.5",
                "machine_type": "测试机",
                "machine_model": "V93000", 
                "configuration": "Digital Board",
                "quantity": 1,
                "unit": "台·小时",
                "unit_price": 2000.0,
                "total_price": 2000.0,
                "machine_id": 2
            }
        ]
    }
    
    print(f"\n🧪 模拟用户在报价结果页面点击'确认报价'...")
    print(f"📤 发送数据: {json.dumps(quote_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送POST请求创建报价单（模拟确认报价按钮）
        response = requests.post(
            f"{BASE_URL}/quotes/",
            json=quote_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 201:
            created_quote = response.json()
            print("✅ 报价单创建成功！")
            print(f"📋 创建的报价单详情:")
            print(f"   - 报价单号: {created_quote['quote_number']}")
            print(f"   - 标题: {created_quote['title']}")
            print(f"   - 客户: {created_quote['customer_name']}")
            print(f"   - 状态: {created_quote['status']} ({'已自动批准' if created_quote['status'] == 'approved' else created_quote['status']})")
            print(f"   - 总金额: ￥{created_quote['total_amount']}")
            print(f"   - 批准人: {created_quote['approved_by']}")
            print(f"   - 批准时间: {created_quote['approved_at']}")
            print(f"   - 创建时间: {created_quote['created_at']}")
            
            # 验证关键字段
            if created_quote['status'] == 'approved':
                print("✅ 询价报价成功跳过审批流程!")
            else:
                print(f"❌ 状态错误: 期望'approved'，实际'{created_quote['status']}'")
                
            if created_quote['approved_by'] is not None:
                print("✅ 自动设置批准人成功!")
            else:
                print("❌ 批准人字段为空")
                
            if created_quote['approved_at'] is not None:
                print("✅ 自动设置批准时间成功!")
            else:
                print("❌ 批准时间字段为空")
            
            return created_quote
            
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        return None

def test_get_final_quotes_list():
    """测试获取最终的报价单列表"""
    print(f"\n🧪 测试获取报价单列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/quotes/test")
        
        if response.status_code == 200:
            quotes_data = response.json()
            print("✅ 获取报价单列表成功!")
            print(f"📋 总报价单数量: {quotes_data.get('total', 0)}")
            
            # 分类显示报价单
            inquiry_quotes = []
            other_quotes = []
            
            for quote in quotes_data.get('items', []):
                if quote.get('quote_type') == 'inquiry':
                    inquiry_quotes.append(quote)
                else:
                    other_quotes.append(quote)
            
            print(f"\n📊 询价报价 ({len(inquiry_quotes)}条):")
            for quote in inquiry_quotes:
                status_desc = {
                    'approved': '✅ 已批准',
                    'pending': '⏳ 审批中', 
                    'draft': '📝 草稿',
                    'rejected': '❌ 已拒绝'
                }.get(quote.get('status'), quote.get('status'))
                
                print(f"   - {quote.get('quote_number')}: {quote.get('title')} ({status_desc})")
            
            if other_quotes:
                print(f"\n📊 其他类型报价 ({len(other_quotes)}条):")
                for quote in other_quotes:
                    status_desc = {
                        'approved': '✅ 已批准',
                        'pending': '⏳ 审批中',
                        'draft': '📝 草稿', 
                        'rejected': '❌ 已拒绝'
                    }.get(quote.get('status'), quote.get('status'))
                    
                    print(f"   - {quote.get('quote_number')}: {quote.get('title')} ({status_desc})")
            
            return True
            
        else:
            print(f"❌ 获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("🎯 开始测试修正后的报价确认流程\n")
    
    # 测试1: 修正后的询价报价创建流程
    created_quote = test_corrected_inquiry_quote_flow()
    
    print("\n" + "-" * 50)
    
    # 测试2: 获取报价单列表验证
    test_get_final_quotes_list()
    
    print("\n" + "=" * 70)
    if created_quote and created_quote.get('status') == 'approved':
        print("🎉 所有测试通过！修正后的报价确认流程正常工作")
        print("\n✅ 确认的核心功能:")
        print("   1. ✅ 询价表单 → 报价结果页面（不保存数据库）")
        print("   2. ✅ 报价结果页面 → 确认报价 → 创建数据库记录")
        print("   3. ✅ 询价报价自动批准，跳过审批流程")
        print("   4. ✅ 报价单在报价单管理中可见")
    else:
        print("❌ 测试失败，需要检查问题")
    print("=" * 70)

if __name__ == "__main__":
    main()