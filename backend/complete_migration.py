#!/usr/bin/env python3
"""
完整的 SQLite 到 PostgreSQL 数据迁移脚本
处理所有24个表，按照依赖关系顺序迁移
"""
import sqlite3
import json
from datetime import datetime

# 连接SQLite
conn = sqlite3.connect('app/test.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def escape_string(val):
    """转义字符串中的单引号"""
    if val is None:
        return 'NULL'
    return "'" + str(val).replace("'", "''").replace('\n', '\\n').replace('\r', '\\r') + "'"

def format_value(val, col_name):
    """格式化值为PostgreSQL兼容格式"""
    if val is None:
        return 'NULL'

    # 布尔值字段
    bool_cols = ['is_active', 'active', 'is_deleted', 'is_approved', 'is_draft',
                 'is_public', 'is_default', 'enabled', 'approved']
    if col_name in bool_cols or col_name.startswith('is_'):
        return 'true' if val in [1, True, 'true', 't', 'True'] else 'false'

    # JSON字段
    if col_name in ['config_data', 'metadata', 'settings', 'parameters', 'data']:
        if isinstance(val, str):
            return escape_string(val)
        else:
            return escape_string(json.dumps(val))

    # 字符串
    if isinstance(val, str):
        return escape_string(val)

    # 数字
    return str(val)

def export_table(f, table_name, order_by='id'):
    """导出单个表的数据"""
    try:
        cur.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}")
        rows = cur.fetchall()

        if not rows:
            print(f"  {table_name}: 无数据")
            return 0

        print(f"  {table_name}: {len(rows)} 行")

        for row in rows:
            cols = []
            vals = []

            for col in row.keys():
                cols.append(col)
                vals.append(format_value(row[col], col))

            if cols:
                sql = f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({','.join(vals)}) ON CONFLICT (id) DO NOTHING;\n"
                f.write(sql)

        return len(rows)
    except Exception as e:
        print(f"  {table_name}: 错误 - {e}")
        return 0

# 按依赖关系顺序定义表
table_groups = {
    "基础表（无外键依赖）": [
        'users',
        'departments',
        'machine_types',
        'suppliers',
        'configurations',
        'global_configs',
    ],
    "设备相关表": [
        'machines',
        'card_configs',
        'auxiliary_equipment',
    ],
    "报价主表": [
        'quotes',
        'quotations',
        'quote_templates',
    ],
    "报价关联表": [
        'quote_items',
        'quote_snapshots',
        'quote_pdf_cache',
        'effective_quotes',
    ],
    "审批相关表": [
        'approval_instance',
        'approval_records',
        'approval_timeline',
        'approval_timeline_errors',
    ],
    "日志和会话表": [
        'operation_logs',
        'user_sessions',
    ],
}

print("=" * 60)
print("开始生成 PostgreSQL 迁移 SQL...")
print("=" * 60)

with open('complete_migration.sql', 'w', encoding='utf-8') as f:
    f.write("-- =============================================\n")
    f.write("-- 芯片报价系统 SQLite 到 PostgreSQL 完整迁移\n")
    f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("-- =============================================\n\n")

    f.write("-- 禁用触发器以提高性能\n")
    f.write("SET session_replication_role = 'replica';\n\n")

    total_rows = 0

    # 按组导出表
    for group_name, tables in table_groups.items():
        print(f"\n{group_name}:")
        f.write(f"\n-- {group_name}\n")

        for table in tables:
            rows = export_table(f, table)
            total_rows += rows

    # 恢复触发器
    f.write("\n-- 恢复触发器\n")
    f.write("SET session_replication_role = 'origin';\n\n")

    # 重置所有序列
    f.write("\n-- 重置所有序列\n")
    all_tables = [table for tables in table_groups.values() for table in tables]
    for table in all_tables:
        f.write(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), true);\n")

conn.close()

print("\n" + "=" * 60)
print(f"✅ 迁移 SQL 生成完成: complete_migration.sql")
print(f"   总共导出 {total_rows} 行数据")
print("=" * 60)
print("\n使用方法:")
print("  1. 将 complete_migration.sql 传输到服务器")
print("  2. 在服务器上执行: psql -U postgres -d 数据库名 -f complete_migration.sql")
print("  3. 验证数据: psql -U postgres -d 数据库名 -c 'SELECT COUNT(*) FROM quotes;'")
