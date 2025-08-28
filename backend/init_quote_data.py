#!/usr/bin/env python3
"""
初始化报价单示例数据
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Quote, QuoteItem, ApprovalRecord, User

def init_quote_data():
    """初始化报价单示例数据"""
    print("📝 正在初始化报价单示例数据...")
    
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_quotes = db.query(Quote).count()
        if existing_quotes > 3:  # 除了测试数据外还有其他数据
            print(f"ℹ️ 已存在 {existing_quotes} 条报价单记录，跳过初始化")
            return True
        
        # 确保有用户数据
        user_count = db.query(User).count()
        if user_count == 0:
            # 创建测试用户
            test_user = User(
                userid="test_user_001",
                name="张三",
                role="admin",
                department="测试部门"
            )
            db.add(test_user)
            db.commit()
            print("✅ 创建测试用户")
        
        # 清除旧的测试数据，保留真实数据
        db.query(Quote).filter(Quote.quote_number.like("QT202408%")).delete()
        db.commit()
        
        # 创建示例报价单
        quotes_data = [
            {
                "quote_number": "QT202408001",
                "title": "华为技术有限公司芯片测试报价",
                "quote_type": "mass_production",
                "customer_name": "华为技术有限公司",
                "customer_contact": "张经理",
                "customer_phone": "138-1234-5678",
                "customer_email": "zhang@huawei.com",
                "customer_address": "深圳市龙岗区坂田华为基地",
                "currency": "CNY",
                "subtotal": 220000.0,
                "discount": 10000.0,
                "tax_rate": 0.13,
                "tax_amount": 28600.0,
                "total_amount": 238600.0,
                "valid_until": datetime.now() + timedelta(days=30),
                "payment_terms": "30天账期",
                "description": "华为技术有限公司Kirin系列芯片综合测试服务报价，包含功能测试、性能测试、老化测试等项目。",
                "status": "approved",
                "version": "V1.2",
                "created_by": 1,
                "approved_at": datetime.now() - timedelta(days=1),
                "approved_by": 1
            },
            {
                "quote_number": "QT202408002",
                "title": "中兴通讯工程测试报价",
                "quote_type": "engineering",
                "customer_name": "中兴通讯股份有限公司",
                "customer_contact": "李工程师",
                "customer_phone": "139-5678-9012",
                "customer_email": "li@zte.com.cn",
                "customer_address": "深圳市南山区中兴通讯大厦",
                "currency": "CNY",
                "subtotal": 158600.0,
                "discount": 0.0,
                "tax_rate": 0.13,
                "tax_amount": 20618.0,
                "total_amount": 179218.0,
                "valid_until": datetime.now() + timedelta(days=25),
                "payment_terms": "现金结算",
                "description": "中兴通讯5G芯片工程测试阶段报价，主要针对新产品开发验证。",
                "status": "pending",
                "version": "V1.0",
                "created_by": 1,
                "submitted_at": datetime.now() - timedelta(days=2)
            },
            {
                "quote_number": "QT202408003",
                "title": "小米科技询价报价单",
                "quote_type": "inquiry",
                "customer_name": "小米科技有限责任公司",
                "customer_contact": "王总监",
                "customer_phone": "150-9876-5432",
                "customer_email": "wang@xiaomi.com",
                "customer_address": "北京市海淀区小米科技园",
                "currency": "CNY",
                "subtotal": 95000.0,
                "discount": 5000.0,
                "tax_rate": 0.13,
                "tax_amount": 11700.0,
                "total_amount": 101700.0,
                "valid_until": datetime.now() + timedelta(days=20),
                "payment_terms": "月结30天",
                "description": "小米科技新品芯片测试方案初步询价。",
                "status": "draft",
                "version": "V1.0",
                "created_by": 1
            },
            {
                "quote_number": "QT202408004",
                "title": "OPPO综合测试服务报价",
                "quote_type": "comprehensive",
                "customer_name": "OPPO广东移动通信有限公司",
                "customer_contact": "陈主管",
                "customer_phone": "136-8888-9999",
                "customer_email": "chen@oppo.com",
                "customer_address": "广东省东莞市长安镇OPPO工业园",
                "currency": "CNY",
                "subtotal": 180000.0,
                "discount": 8000.0,
                "tax_rate": 0.13,
                "tax_amount": 22360.0,
                "total_amount": 194360.0,
                "valid_until": datetime.now() + timedelta(days=18),
                "payment_terms": "45天账期",
                "description": "OPPO手机芯片综合测试服务，包含RF、基带、电源管理等多项测试。",
                "status": "approved",
                "version": "V1.1",
                "created_by": 1,
                "approved_at": datetime.now() - timedelta(hours=5),
                "approved_by": 1
            },
            {
                "quote_number": "QT202408005",
                "title": "比亚迪汽车芯片测试报价",
                "quote_type": "mass_production",
                "customer_name": "比亚迪股份有限公司",
                "customer_contact": "刘工",
                "customer_phone": "186-6666-7777",
                "customer_email": "liu@byd.com",
                "customer_address": "广东省深圳市坪山区比亚迪路3009号",
                "currency": "USD",
                "subtotal": 25000.0,
                "discount": 2000.0,
                "tax_rate": 0.0,  # 美元报价不含税
                "tax_amount": 0.0,
                "total_amount": 23000.0,
                "valid_until": datetime.now() + timedelta(days=15),
                "payment_terms": "T/T 30天",
                "description": "比亚迪汽车电子控制芯片量产测试服务。",
                "status": "rejected",
                "version": "V1.0",
                "created_by": 1,
                "rejection_reason": "价格超出预算范围，需要重新调整方案。"
            }
        ]
        
        created_quotes = []
        
        # 创建报价单
        for quote_data in quotes_data:
            quote = Quote(**quote_data)
            db.add(quote)
            db.flush()  # 获取ID
            created_quotes.append(quote)
            
            # 为每个报价单添加明细项目
            items_data = []
            
            if quote.quote_number == "QT202408001":
                items_data = [
                    {
                        "item_name": "Kirin 9000 芯片测试",
                        "item_description": "功能测试、性能测试、老化测试",
                        "machine_type": "测试机",
                        "supplier": "Advantest",
                        "machine_model": "V93000 SOC Series",
                        "configuration": "Pin Scale 1024, 6.4Gbps",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 120.50,
                        "total_price": 120500.00
                    },
                    {
                        "item_name": "封装测试",
                        "item_description": "封装完整性测试",
                        "machine_type": "分选机",
                        "supplier": "Cohu",
                        "machine_model": "PA200 Series",
                        "configuration": "标准配置",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 85.30,
                        "total_price": 85300.00
                    },
                    {
                        "item_name": "编带包装",
                        "item_description": "成品编带包装服务",
                        "machine_type": "编带机",
                        "supplier": "ASM",
                        "machine_model": "AMICRA NOVA",
                        "configuration": "7寸料盘",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 40.00,
                        "total_price": 40000.00
                    }
                ]
            elif quote.quote_number == "QT202408002":
                items_data = [
                    {
                        "item_name": "5G基带芯片工程测试",
                        "item_description": "新产品开发测试验证",
                        "machine_type": "测试机",
                        "supplier": "Teradyne",
                        "machine_model": "UltraFLEX Plus",
                        "configuration": "512通道配置",
                        "quantity": 500,
                        "unit": "颗",
                        "unit_price": 317.20,
                        "total_price": 158600.00
                    }
                ]
            elif quote.quote_number == "QT202408003":
                items_data = [
                    {
                        "item_name": "小米芯片初步测试",
                        "item_description": "产品可行性测试",
                        "machine_type": "测试机",
                        "supplier": "Advantest",
                        "machine_model": "T2000",
                        "configuration": "基础配置",
                        "quantity": 200,
                        "unit": "颗",
                        "unit_price": 475.00,
                        "total_price": 95000.00
                    }
                ]
            elif quote.quote_number == "QT202408004":
                items_data = [
                    {
                        "item_name": "RF芯片测试",
                        "item_description": "射频性能测试",
                        "machine_type": "测试机",
                        "supplier": "Keysight",
                        "machine_model": "EXA N9010A",
                        "configuration": "全频段配置",
                        "quantity": 800,
                        "unit": "颗",
                        "unit_price": 150.00,
                        "total_price": 120000.00
                    },
                    {
                        "item_name": "基带芯片测试",
                        "item_description": "数字基带性能测试",
                        "machine_type": "测试机",
                        "supplier": "Advantest",
                        "machine_model": "V93000",
                        "configuration": "数字测试配置",
                        "quantity": 800,
                        "unit": "颗",
                        "unit_price": 75.00,
                        "total_price": 60000.00
                    }
                ]
            elif quote.quote_number == "QT202408005":
                items_data = [
                    {
                        "item_name": "汽车级芯片测试",
                        "item_description": "AEC-Q100标准测试",
                        "machine_type": "测试机",
                        "supplier": "Teradyne",
                        "machine_model": "J750EX",
                        "configuration": "汽车级测试配置",
                        "quantity": 100,
                        "unit": "颗",
                        "unit_price": 250.00,
                        "total_price": 25000.00
                    }
                ]
            
            # 添加明细项目
            for item_data in items_data:
                item_data["quote_id"] = quote.id
                item = QuoteItem(**item_data)
                db.add(item)
        
        # 提交所有数据
        db.commit()
        
        print(f"✅ 成功创建 {len(quotes_data)} 个报价单:")
        for quote in created_quotes:
            items_count = db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).count()
            print(f"   - {quote.quote_number}: {quote.title} ({quote.status}, {items_count}项)")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化数据失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = init_quote_data()
    print("\n" + "="*50)
    if success:
        print("🎉 报价单示例数据初始化成功！")
        print("\n可以开始:")
        print("1. 实现报价单CRUD接口")
        print("2. 测试前端数据对接")
        print("3. 开发企业微信审批集成")
    else:
        print("❌ 报价单示例数据初始化失败！")
    
    sys.exit(0 if success else 1)