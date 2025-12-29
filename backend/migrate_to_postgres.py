#!/usr/bin/env python3
import sqlite3
import re

# 连接SQLite
conn = sqlite3.connect('app/test.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("生成PostgreSQL兼容的SQL...")

with open('postgres_clean.sql', 'w', encoding='utf-8') as f:
    # 先导入基础表（无外键依赖）
    base_tables = ['users', 'suppliers', 'machine_types', 'machines', 'card_configs']
    
    for table in base_tables:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        
        if rows:
            print(f"处理 {table}: {len(rows)} 行")
            cols = list(rows[0].keys())
            
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, bool) or val in [0, 1] and table in ['machines', 'suppliers']:
                        # 处理布尔值
                        values.append('true' if val else 'false')
                    elif isinstance(val, str):
                        # 转义单引号
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        values.append(str(val))
                
                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(values)}) ON CONFLICT (id) DO NOTHING;\n"
                f.write(sql)

conn.close()
print("✓ 文件创建完成: postgres_clean.sql")
