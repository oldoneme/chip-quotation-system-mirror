#!/usr/bin/env python3
"""
修复 quote_items 表结构问题
主键类型错误导致的 NULL identity key 错误
"""

import sqlite3
import os
from datetime import datetime

def fix_quote_items_schema():
    """修复 quote_items 表结构"""
    db_path = os.path.join(os.path.dirname(__file__), "app/test.db")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 开始修复 quote_items 表结构...")

        # 1. 备份现有数据
        print("1️⃣ 备份现有数据...")
        cursor.execute("""
            CREATE TABLE quote_items_backup AS
            SELECT * FROM quote_items
        """)

        backup_count = cursor.execute("SELECT COUNT(*) FROM quote_items_backup").fetchone()[0]
        print(f"   备份了 {backup_count} 条记录")

        # 2. 删除旧表
        print("2️⃣ 删除旧表...")
        cursor.execute("DROP TABLE quote_items")

        # 3. 创建新表结构（正确的整数主键）
        print("3️⃣ 创建新表结构...")
        cursor.execute("""
            CREATE TABLE quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id TEXT NOT NULL,
                item_name TEXT,
                item_description TEXT,
                machine_type TEXT,
                supplier TEXT,
                machine_model TEXT,
                configuration TEXT,
                quantity REAL DEFAULT 1.0,
                unit TEXT DEFAULT '小时',
                unit_price REAL DEFAULT 0.0,
                total_price REAL DEFAULT 0.0,
                machine_id INTEGER,
                configuration_id INTEGER,
                FOREIGN KEY (quote_id) REFERENCES quotes (id),
                FOREIGN KEY (machine_id) REFERENCES machines (id),
                FOREIGN KEY (configuration_id) REFERENCES configurations (id)
            )
        """)

        # 4. 恢复数据（如果有的话）
        if backup_count > 0:
            print("4️⃣ 恢复数据...")
            cursor.execute("""
                INSERT INTO quote_items (
                    quote_id, item_name, item_description, machine_type,
                    supplier, machine_model, configuration, quantity,
                    unit, unit_price, total_price, machine_id, configuration_id
                )
                SELECT
                    quote_id, item_name, item_description, machine_type,
                    supplier, machine_model, configuration, quantity,
                    unit, unit_price, total_price, machine_id, configuration_id
                FROM quote_items_backup
            """)

            restored_count = cursor.execute("SELECT COUNT(*) FROM quote_items").fetchone()[0]
            print(f"   恢复了 {restored_count} 条记录")

        # 5. 删除备份表
        print("5️⃣ 清理备份表...")
        cursor.execute("DROP TABLE quote_items_backup")

        # 6. 验证新表结构
        print("6️⃣ 验证新表结构...")
        cursor.execute("PRAGMA table_info(quote_items)")
        columns = cursor.fetchall()

        print("   新表结构:")
        for col in columns:
            cid, name, type_, notnull, default, pk = col
            if pk:
                print(f"   ✅ {name}: {type_} (主键)")
            else:
                print(f"      {name}: {type_}")

        conn.commit()
        conn.close()

        print("✅ quote_items 表结构修复完成！")
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚨 quote_items 表结构修复工具")
    print(f"⏰ 执行时间: {datetime.now()}")
    print()

    success = fix_quote_items_schema()

    if success:
        print("\n🎉 修复成功！现在可以正常创建报价单了。")
    else:
        print("\n💥 修复失败！请检查错误信息。")