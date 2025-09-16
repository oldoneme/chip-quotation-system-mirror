#!/usr/bin/env python3
"""
使用原始SQL测试报价单创建
绕过SQLAlchemy来确定问题所在
"""

import sqlite3
import uuid
from datetime import datetime

def test_raw_sql_creation():
    """使用原始SQL测试报价单创建"""
    print("🔍 使用原始SQL测试报价单创建")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 60)

    db_path = 'app/test.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("1️⃣ 检查当前数据库状态...")
        cursor.execute('SELECT COUNT(*) FROM quotes')
        initial_count = cursor.fetchone()[0]
        print(f"   当前报价单数量: {initial_count}")

        print("2️⃣ 直接插入报价单...")

        # 生成测试数据
        quote_id = str(uuid.uuid4())
        quote_number = "CIS-KS20250916001"
        now = datetime.now()

        # 直接SQL插入
        cursor.execute('''
            INSERT INTO quotes (
                id, quote_number, title, quote_type, customer_name, customer_contact,
                customer_phone, customer_email, quote_unit, currency, subtotal,
                discount, tax_rate, tax_amount, total_amount, description, notes,
                status, version, approval_status, approval_method, is_deleted,
                created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quote_id, quote_number, "原始SQL测试", "tooling", "SQL测试客户", "测试联系人",
            "123456789", "sql@test.com", "昆山芯信安", "CNY", 500.0,
            0.0, 0.13, 0.0, 500.0, "原始SQL测试描述", "测试备注",
            "draft", "V1.0", "not_submitted", "internal", 0,
            1, now.isoformat(), now.isoformat()
        ))

        print(f"   插入报价单: {quote_number}")

        print("3️⃣ 插入明细项...")

        item_id = 1
        cursor.execute('''
            INSERT INTO quote_items (
                id, quote_id, item_name, item_description, machine_type, supplier,
                machine_model, configuration, quantity, unit, unit_price, total_price,
                machine_id, configuration_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, quote_id, "原始SQL测试项", "测试明细项", "测试机", "测试供应商",
            "SQL-001", "基础配置", 1.0, "个", 500.0, 500.0, 1, 1
        ))

        print("   插入明细项完成")

        print("4️⃣ 提交事务...")
        conn.commit()
        print("   事务提交成功")

        print("5️⃣ 验证插入结果...")

        # 查询报价单
        cursor.execute('SELECT quote_number, customer_name, total_amount FROM quotes WHERE quote_number = ?', (quote_number,))
        quote_result = cursor.fetchone()

        if quote_result:
            print(f"   ✅ 报价单查询成功:")
            print(f"      编号: {quote_result[0]}")
            print(f"      客户: {quote_result[1]}")
            print(f"      金额: ¥{quote_result[2]}")
        else:
            print("   ❌ 报价单查询失败")
            return False

        # 查询明细项
        cursor.execute('SELECT item_name, total_price FROM quote_items WHERE quote_id = ?', (quote_id,))
        item_result = cursor.fetchone()

        if item_result:
            print(f"   ✅ 明细项查询成功:")
            print(f"      名称: {item_result[0]}")
            print(f"      金额: ¥{item_result[1]}")
        else:
            print("   ❌ 明细项查询失败")
            return False

        # 最终验证
        cursor.execute('SELECT COUNT(*) FROM quotes')
        final_count = cursor.fetchone()[0]
        print(f"   📊 最终报价单数量: {final_count}")

        return True

    except Exception as e:
        print(f"❌ 原始SQL测试失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = test_raw_sql_creation()
    print("\n" + "="*60)
    if success:
        print("🎉 原始SQL创建成功！问题出在SQLAlchemy层面。")
        print("   现在需要修复SQLAlchemy的使用方式。")
    else:
        print("💥 原始SQL也失败了！问题更深层。")