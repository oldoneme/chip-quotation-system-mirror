#!/usr/bin/env python3
"""
修复quotes表主键结构 - 从TEXT改为INTEGER AUTOINCREMENT
"""

import sqlite3
import uuid
from datetime import datetime

def fix_quotes_primary_key():
    """修复quotes表主键结构"""
    print("🔧 修复quotes表主键结构")
    print(f"⏰ 修复时间: {datetime.now()}")
    print("=" * 60)

    db_path = 'app/test.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("1️⃣ 备份现有数据...")

        # 查询现有数据
        cursor.execute('SELECT * FROM quotes')
        existing_quotes = cursor.fetchall()

        cursor.execute('SELECT * FROM quote_items')
        existing_items = cursor.fetchall()

        print(f"   备份 {len(existing_quotes)} 个报价单")
        print(f"   备份 {len(existing_items)} 个明细项")

        print("2️⃣ 删除现有表...")
        cursor.execute('DROP TABLE IF EXISTS quote_items')
        cursor.execute('DROP TABLE IF EXISTS quotes')

        print("3️⃣ 重建quotes表(INTEGER AUTOINCREMENT主键)...")
        cursor.execute('''
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence_id INTEGER,
                quote_number TEXT UNIQUE,
                title TEXT,
                quote_type TEXT,
                customer_name TEXT,
                customer_contact TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                customer_address TEXT,
                quote_unit TEXT DEFAULT '昆山芯信安',
                currency TEXT DEFAULT 'CNY',
                subtotal REAL DEFAULT 0.0,
                discount REAL DEFAULT 0.0,
                tax_rate REAL DEFAULT 0.13,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                valid_until DATETIME,
                payment_terms TEXT,
                description TEXT,
                notes TEXT,
                status TEXT DEFAULT 'draft',
                version_field INTEGER DEFAULT 1,
                approval_status TEXT DEFAULT 'not_submitted',
                approval_method VARCHAR(20) DEFAULT 'internal',
                current_approver_id INTEGER,
                submitted_at DATETIME,
                approved_at DATETIME,
                approved_by INTEGER,
                rejection_reason TEXT,
                wecom_approval_id TEXT,
                wecom_approval_template_id TEXT,
                approval_link_token TEXT,
                is_deleted BOOLEAN DEFAULT 0,
                deleted_at DATETIME,
                deleted_by INTEGER,
                version INTEGER DEFAULT 1,
                data_checksum TEXT,
                created_by INTEGER,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')

        print("4️⃣ 重建quote_items表...")
        cursor.execute('''
            CREATE TABLE quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                item_name TEXT,
                item_description TEXT,
                machine_type TEXT,
                supplier TEXT,
                machine_model TEXT,
                configuration TEXT,
                quantity REAL,
                unit TEXT,
                unit_price REAL,
                total_price REAL,
                machine_id INTEGER,
                configuration_id INTEGER,
                FOREIGN KEY (quote_id) REFERENCES quotes (id)
            )
        ''')

        print("5️⃣ 恢复数据...")

        # 获取列名
        cursor.execute('PRAGMA table_info(quotes)')
        columns = [col[1] for col in cursor.fetchall()]

        # 为每个现有报价单分配新的INTEGER ID
        new_id_mapping = {}  # 老ID -> 新ID的映射

        for old_quote in existing_quotes:
            old_id = old_quote[0]  # 原来的TEXT ID

            if old_id is None:
                continue  # 跳过NULL ID记录

            # 插入报价单 (不指定id，让AUTOINCREMENT自动生成)
            quote_values = old_quote[1:]  # 排除第一个id字段
            placeholders = ','.join(['?' for _ in quote_values])
            insert_columns = ','.join(columns[1:])  # 排除id列

            cursor.execute(f'INSERT INTO quotes ({insert_columns}) VALUES ({placeholders})', quote_values)
            new_id = cursor.lastrowid
            new_id_mapping[old_id] = new_id

            print(f"   恢复报价单: {old_id} -> {new_id}")

        # 恢复明细项
        for old_item in existing_items:
            old_quote_id = old_item[1]  # quote_id字段

            if old_quote_id in new_id_mapping:
                new_quote_id = new_id_mapping[old_quote_id]
                # 构建新的明细项数据 (不指定id，让AUTOINCREMENT自动生成，更新quote_id)
                item_values = list(old_item[1:])  # 排除第一个id字段
                item_values[0] = new_quote_id     # 更新quote_id为新ID

                cursor.execute('''
                    INSERT INTO quote_items (
                        quote_id, item_name, item_description, machine_type, supplier,
                        machine_model, configuration, quantity, unit, unit_price,
                        total_price, machine_id, configuration_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', item_values)

        print("6️⃣ 验证修复结果...")
        cursor.execute('SELECT COUNT(*) FROM quotes')
        quote_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM quote_items')
        item_count = cursor.fetchone()[0]

        cursor.execute('SELECT id, quote_number, customer_name FROM quotes ORDER BY id')
        restored_quotes = cursor.fetchall()

        print(f"   恢复了 {quote_count} 个报价单")
        print(f"   恢复了 {item_count} 个明细项")
        print("   恢复的报价单:")
        for quote in restored_quotes:
            print(f"      ID: {quote[0]} | 编号: {quote[1]} | 客户: {quote[2]}")

        conn.commit()
        print("✅ 主键结构修复完成!")
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_quotes_primary_key()

    print("\n" + "="*60)
    if success:
        print("🎉 主键结构完全修复！现在与模型定义匹配！")
        print("   quotes表现在使用INTEGER AUTOINCREMENT主键")
        print("   所有外键关系已正确更新")
    else:
        print("💥 修复失败，需要进一步检查")