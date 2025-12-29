#!/usr/bin/env python3
import sqlite3
import json

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
    if col_name in ['is_active', 'active', 'is_deleted', 'is_approved']:
        return 'true' if val in [1, True, 'true', 't'] else 'false'
    if isinstance(val, str):
        return escape_string(val)
    return str(val)

# PostgreSQL quotes表的实际列
pg_quote_cols = [
    'id', 'quote_number', 'title', 'quote_type', 'customer_name', 
    'customer_contact', 'customer_phone', 'customer_email', 'customer_address',
    'quote_unit', 'currency', 'subtotal', 'discount', 'tax_rate', 'tax_amount',
    'total_amount', 'valid_until', 'payment_terms', 'description', 'notes',
    'status', 'version', 'approval_status', 'created_at', 'updated_at'
]

with open('final_migration.sql', 'w', encoding='utf-8') as f:
    # 导出quotes - 只包含PostgreSQL中存在的列
    cur.execute("SELECT * FROM quotes")
    quotes = cur.fetchall()
    print(f"处理 {len(quotes)} 条报价")
    
    for row in quotes:
        values = []
        cols_to_insert = []
        
        for col in pg_quote_cols:
            if col in row.keys():
                cols_to_insert.append(col)
                values.append(format_value(row[col], col))
        
        if cols_to_insert:
            sql = f"INSERT INTO quotes ({','.join(cols_to_insert)}) VALUES ({','.join(values)}) ON CONFLICT (id) DO NOTHING;\n"
            f.write(sql)
    
    # 导出quote_items
    cur.execute("SELECT * FROM quote_items")
    items = cur.fetchall()
    print(f"处理 {len(items)} 条报价项")
    
    for row in items:
        # 检查必要的字段
        cols = []
        vals = []
        for col in row.keys():
            if col not in ['sequence_id']:  # 跳过不存在的列
                cols.append(col)
                vals.append(format_value(row[col], col))
        
        if cols:
            sql = f"INSERT INTO quote_items ({','.join(cols)}) VALUES ({','.join(vals)}) ON CONFLICT (id) DO NOTHING;\n"
            f.write(sql)
    
    # 重置序列
    f.write("\n-- 重置序列\n")
    f.write("SELECT setval('quotes_id_seq', COALESCE(MAX(id), 1)) FROM quotes;\n")
    f.write("SELECT setval('quote_items_id_seq', COALESCE(MAX(id), 1)) FROM quote_items;\n")

conn.close()
print("✅ 生成完成: final_migration.sql")
