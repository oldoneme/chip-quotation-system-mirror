#!/usr/bin/env python3
"""
报价单系统数据库迁移脚本
创建新的报价单相关表结构
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models import Base, Quote, QuoteItem, ApprovalRecord, QuoteTemplate


def create_tables():
    """创建新的数据库表"""
    print("🔧 正在创建报价单相关数据库表...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False


def insert_sample_data():
    """插入示例数据"""
    print("📝 正在插入示例数据...")
    
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_quotes = db.query(Quote).count()
        if existing_quotes > 0:
            print(f"ℹ️ 已存在 {existing_quotes} 条报价单记录，跳过示例数据插入")
            return True
        
        # 插入示例报价单
        sample_quotes = [
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
                "tax_amount": 28600.0,
                "total_amount": 238600.0,
                "payment_terms": "30天账期",
                "description": "华为技术有限公司Kirin系列芯片综合测试服务报价，包含功能测试、性能测试、老化测试等项目。",
                "status": "approved",
                "version": "V1.2",
                "created_by": 1,
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
                "tax_amount": 20618.0,
                "total_amount": 179218.0,
                "payment_terms": "现金结算",
                "description": "中兴通讯5G芯片工程测试阶段报价，主要针对新产品开发验证。",
                "status": "pending",
                "version": "V1.0",
                "created_by": 1,
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
                "tax_amount": 11700.0,
                "total_amount": 101700.0,
                "payment_terms": "月结30天",
                "description": "小米科技新品芯片测试方案初步询价。",
                "status": "draft",
                "version": "V1.0",
                "created_by": 1,
            }
        ]
        
        # 创建报价单记录
        for quote_data in sample_quotes:
            quote = Quote(**quote_data)
            db.add(quote)
            db.flush()  # 获取ID但不提交
            
            # 添加报价明细
            if quote.quote_number == "QT202408001":
                items = [
                    {
                        "quote_id": quote.id,
                        "item_name": "Kirin 9000 芯片测试",
                        "item_description": "功能测试、性能测试、老化测试",
                        "machine_type": "测试机",
                        "supplier": "Advantest",
                        "machine_model": "V93000 SOC Series",
                        "configuration": "Pin Scale 1024, 6.4Gbps",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 120.50,
                        "total_price": 120500.00,
                        "machine_id": 1
                    },
                    {
                        "quote_id": quote.id,
                        "item_name": "封装测试",
                        "item_description": "封装完整性测试",
                        "machine_type": "分选机",
                        "supplier": "Cohu",
                        "machine_model": "PA200 Series",
                        "configuration": "标准配置",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 85.30,
                        "total_price": 85300.00,
                        "machine_id": 2
                    },
                    {
                        "quote_id": quote.id,
                        "item_name": "编带包装",
                        "item_description": "成品编带包装服务",
                        "machine_type": "编带机",
                        "supplier": "ASM",
                        "machine_model": "AMICRA NOVA",
                        "configuration": "7寸料盘",
                        "quantity": 1000,
                        "unit": "颗",
                        "unit_price": 40.00,
                        "total_price": 40000.00,
                        "machine_id": 3
                    }
                ]
            elif quote.quote_number == "QT202408002":
                items = [
                    {
                        "quote_id": quote.id,
                        "item_name": "5G基带芯片工程测试",
                        "item_description": "新产品开发测试验证",
                        "machine_type": "测试机",
                        "supplier": "Teradyne",
                        "machine_model": "UltraFLEX Plus",
                        "configuration": "512通道配置",
                        "quantity": 500,
                        "unit": "颗",
                        "unit_price": 317.20,
                        "total_price": 158600.00,
                        "machine_id": 1
                    }
                ]
            else:  # QT202408003
                items = [
                    {
                        "quote_id": quote.id,
                        "item_name": "小米芯片初步测试",
                        "item_description": "产品可行性测试",
                        "machine_type": "测试机",
                        "supplier": "Advantest",
                        "machine_model": "T2000",
                        "configuration": "基础配置",
                        "quantity": 200,
                        "unit": "颗",
                        "unit_price": 475.00,
                        "total_price": 95000.00,
                        "machine_id": 1
                    }
                ]
            
            # 添加明细项目
            for item_data in items:
                item = QuoteItem(**item_data)
                db.add(item)
        
        # 提交所有更改
        db.commit()
        print("✅ 示例数据插入成功！")
        print(f"   - 创建了 {len(sample_quotes)} 个报价单")
        return True
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_tables():
    """验证表结构"""
    print("🔍 正在验证数据库表结构...")
    
    db = SessionLocal()
    try:
        # 检查主要表的记录数
        quotes_count = db.query(Quote).count()
        items_count = db.query(QuoteItem).count()
        
        print(f"✅ 验证完成:")
        print(f"   - 报价单表 (quotes): {quotes_count} 条记录")
        print(f"   - 报价明细表 (quote_items): {items_count} 条记录")
        
        # 显示报价单列表
        if quotes_count > 0:
            print("\n📋 当前报价单列表:")
            quotes = db.query(Quote).all()
            for quote in quotes:
                print(f"   - {quote.quote_number}: {quote.title} ({quote.status})")
        
        return True
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        db.close()


def main():
    """主函数"""
    print("🚀 开始报价单系统数据库迁移...")
    print("=" * 50)
    
    # 步骤1：创建表
    if not create_tables():
        print("❌ 迁移失败：无法创建数据库表")
        return False
    
    print()
    
    # 步骤2：插入示例数据
    if not insert_sample_data():
        print("❌ 迁移失败：无法插入示例数据")
        return False
    
    print()
    
    # 步骤3：验证结果
    if not verify_tables():
        print("❌ 迁移失败：验证失败")
        return False
    
    print()
    print("=" * 50)
    print("🎉 报价单系统数据库迁移完成！")
    print("\n下一步可以:")
    print("1. 启动后端服务：python3 -m uvicorn app.main:app --reload")
    print("2. 访问API文档：http://localhost:8000/docs")
    print("3. 开始开发报价单CRUD接口")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)