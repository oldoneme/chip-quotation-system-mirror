#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

# 连接SQLite
conn = sqlite3.connect('app/test.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def escape_string(val):
    if val is None:
        return 'NULL'
    return "'" + str(val).replace("'", "''") + "'"

def format_value(val, col_name):
    if val is None:
        return 'NULL'
    # 布尔值处理
    if col_name in ['is_active', 'active', 'is_approved', 'is_draft']:
        return 'true' if val in [1, True, 'true', 't'] else 'false'
    # 字符串
    if isinstance(val, str):
        return escape_string(val)
    # 数字
    return str(val)

with open('full_migration.sql', 'w', encoding='utf-8') as f:
    # 1. 用户表
    cur.execute("SELECT * FROM users")
    for row in cur.fetchall():
        cols = list(row.keys())
        values = [format_value(row[col], col) for col in cols]
        f.write(f"INSERT INTO users ({','.join(cols)}) VALUES ({','.join(values)}) ON CONFLICT (id) DO NOTHING;\n")
    
    # 2. Machine types
    cur.execute("SELECT * FROM machine_types")
    for row in cur.fetchall():
        f.write(f"INSERT INTO machine_types (id, name, description) VALUES ({row['id']}, {escape_string(row['name'])}, {escape_string(row['description'])}) ON CONFLICT (id) DO NOTHING;\n")
    
    # 3. Suppliers 
    cur.execute("SELECT * FROM suppliers")
    for row in cur.fetchall():
        machine_type = row['machine_type_id'] if row['machine_type_id'] else 'NULL'
        f.write(f"INSERT INTO suppliers (id, name) VALUES ({row['id']}, {escape_string(row['name'])}) ON CONFLICT (id) DO NOTHING;\n")
    
    # 4. Machines
    cur.execute("SELECT * FROM machines")
    for row in cur.fetchall():
        f.write(f"INSERT INTO machines (id, name, description, base_hourly_rate, active, manufacturer, discount_rate, exchange_rate, currency) VALUES ({row['id']}, {escape_string(row['name'])}, {escape_string(row['description'])}, {row['base_hourly_rate'] or 'NULL'}, {format_value(row['active'], 'active')}, {escape_string(row['manufacturer'])}, {row['discount_rate'] or 1.0}, {row['exchange_rate'] or 1.0}, {escape_string(row['currency'] or 'RMB')}) ON CONFLICT (id) DO NOTHING;\n")
    
    # 5. Quotes - 最重要的表
    cur.execute("SELECT * FROM quotes")  
    quotes = cur.fetchall()
    print(f"准备迁移 {len(quotes)} 条报价")
    
    for row in quotes:
        # 处理每个字段
        fields = []
        values = []
        for col in row.keys():
            if col in ['created_at', 'updated_at', 'submitted_at', 'approved_at']:
                # 时间字段
                if row[col]:
                    values.append(escape_string(row[col]))
                else:
                    values.append('NULL')
            elif col in ['is_draft', 'is_approved']:
                # 布尔字段
                values.append(format_value(row[col], col))
            else:
                # 其他字段
                values.append(format_value(row[col], col))
            fields.append(col)
        
        f.write(f"INSERT INTO quotes ({','.join(fields)}) VALUES ({','.join(values)}) ON CONFLICT (id) DO NOTHING;\n")
    
    # 6. Quote items
    cur.execute("SELECT * FROM quote_items")
    items = cur.fetchall()
    print(f"准备迁移 {len(items)} 条报价项")
    
    for row in items:
        fields = []
        values = []
        for col in row.keys():
            values.append(format_value(row[col], col))
            fields.append(col)
        f.write(f"INSERT INTO quote_items ({','.join(fields)}) VALUES ({','.join(values)}) ON CONFLICT (id) DO NOTHING;\n")

    # 重置序列
    f.write("\n-- Reset sequences\n")
    for table in ['users', 'machines', 'quotes', 'quote_items', 'suppliers', 'machine_types']:
        f.write(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};\n")

conn.close()
print("\n✅ 迁移脚本生成完成: full_migration.sql")
