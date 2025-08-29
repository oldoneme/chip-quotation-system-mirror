#!/usr/bin/env python3
"""
检查数据库表结构
"""
import sqlite3

def check_table_structure():
    """检查数据库表结构"""
    conn = sqlite3.connect('/home/qixin/projects/chip-quotation-system/backend/app/test.db')
    cursor = conn.cursor()
    
    print("=== 数据库表结构检查 ===\n")
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📋 现有数据库表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查machines表结构
    if any('machines' in table for table in tables):
        print(f"\n🔧 machines表结构:")
        cursor.execute("PRAGMA table_info(machines)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 检查machines表数据
        cursor.execute("SELECT COUNT(*) FROM machines")
        count = cursor.fetchone()[0]
        print(f"\n📊 machines表记录数: {count}")
        
        if count > 0:
            cursor.execute("SELECT name, supplier_id FROM machines LIMIT 5")
            machines = cursor.fetchall()
            print("前5条记录:")
            for machine in machines:
                print(f"  - {machine[0]} (supplier_id: {machine[1]})")
    
    # 检查suppliers表
    if any('suppliers' in table for table in tables):
        print(f"\n🏢 suppliers表数据:")
        cursor.execute("SELECT s.name, mt.name FROM suppliers s JOIN machine_types mt ON s.machine_type_id = mt.id")
        suppliers = cursor.fetchall()
        for supplier in suppliers:
            print(f"  - {supplier[0]} ({supplier[1]})")
    
    # 检查quotes表
    if any('quotes' in table for table in tables):
        print(f"\n📑 quotes表结构:")
        cursor.execute("PRAGMA table_info(quotes)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        count = cursor.fetchone()[0]
        print(f"\n📊 quotes表记录数: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_table_structure()