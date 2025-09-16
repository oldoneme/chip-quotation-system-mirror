#!/usr/bin/env python3
"""
测试所有报价类型的创建功能
验证修复后的schema是否对所有报价类型都有效
"""

import sys
import os
import requests
import json

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import User, Quote, QuoteItem

API_BASE = "http://127.0.0.1:8000"

def test_quote_type(quote_type, description):
    """测试指定类型的报价单创建"""
    print(f"\n🧪 测试 {quote_type} 报价类型...")
    print(f"   描述: {description}")

    # 测试数据
    quote_data = {
        "title": f"测试{description} - TestQuote",
        "quote_type": quote_type,
        "customer_name": f"Test Customer {quote_type.upper()}",
        "customer_contact": "张先生",
        "customer_phone": "13812345678",
        "customer_email": "test@example.com",
        "quote_unit": "昆山芯信安",
        "currency": "CNY",
        "description": f"测试{description}的创建功能",
        "notes": f"自动化测试 - {quote_type}",
        "items": [
            {
                "item_name": "ETS-88",
                "item_description": "FT测试机 - Teradyne",
                "machine_type": "测试机",
                "supplier": "Teradyne",
                "machine_model": "ETS-88",
                "configuration": "标准配置",
                "quantity": 1.0,
                "unit": "小时",
                "unit_price": 100.0,
                "total_price": 100.0,
                "machine_id": 1,
                "configuration_id": 1
            },
            {
                "item_name": "JHT6080",
                "item_description": "FT分选机 - 金海通",
                "machine_type": "分选机",
                "supplier": "金海通",
                "machine_model": "JHT6080",
                "configuration": "标准配置",
                "quantity": 1.0,
                "unit": "小时",
                "unit_price": 50.0,
                "total_price": 50.0,
                "machine_id": 2,
                "configuration_id": 2
            }
        ],
        "subtotal": 150.0,
        "total_amount": 150.0
    }

    try:
        # 模拟登录用户（使用测试用户ID=1）
        headers = {
            "Content-Type": "application/json",
            "X-Test-User-ID": "1"  # 测试用的用户ID
        }

        # 发送创建请求
        response = requests.post(
            f"{API_BASE}/api/v1/quotes/",
            json=quote_data,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ {quote_type} 创建成功")
            print(f"   📋 报价单号: {result.get('quote_number', 'N/A')}")
            print(f"   🆔 ID: {result.get('id', 'N/A')}")
            print(f"   📊 状态: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"   ❌ {quote_type} 创建失败")
            print(f"   📝 状态码: {response.status_code}")
            print(f"   💬 响应: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ {quote_type} 测试异常: {e}")
        return False

def main():
    print("🔧 测试所有报价类型的创建功能")
    print("=" * 50)

    # 定义所有报价类型
    quote_types = {
        "inquiry": "询价报价",
        "tooling": "工装报价",
        "engineering": "工程报价",
        "mass_production": "量产报价",
        "process": "工艺报价",
        "comprehensive": "综合报价"
    }

    success_count = 0
    total_count = len(quote_types)

    # 测试每种报价类型
    for quote_type, description in quote_types.items():
        if test_quote_type(quote_type, description):
            success_count += 1

    # 汇总结果
    print(f"\n📊 测试结果汇总:")
    print(f"   ✅ 成功: {success_count}/{total_count}")
    print(f"   ❌ 失败: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 所有报价类型测试通过！")
    else:
        print(f"\n⚠️ 有 {total_count - success_count} 个报价类型测试失败")

    # 检查数据库中的结果
    print(f"\n🗄️ 数据库验证:")
    db = SessionLocal()
    try:
        quotes = db.query(Quote).all()
        items = db.query(QuoteItem).all()
        print(f"   报价单总数: {len(quotes)}")
        print(f"   报价项目总数: {len(items)}")

        for quote in quotes[-6:]:  # 显示最后6个（测试创建的）
            print(f"   - ID:{quote.id}, 类型:{quote.quote_type}, 编号:{quote.quote_number}")
    finally:
        db.close()

if __name__ == "__main__":
    main()