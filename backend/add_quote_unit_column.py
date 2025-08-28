#!/usr/bin/env python3
"""
脚本：为quotes表添加quote_unit列
"""

import sqlite3
import os

def add_quote_unit_column():
    # 数据库路径
    db_path = os.path.join(os.path.dirname(__file__), "app", "test.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'quote_unit' not in columns:
            # 添加quote_unit列
            cursor.execute("ALTER TABLE quotes ADD COLUMN quote_unit TEXT DEFAULT '昆山芯信安'")
            print("✅ 成功添加quote_unit列到quotes表")
        else:
            print("ℹ️ quote_unit列已存在")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ 添加列失败: {e}")

if __name__ == "__main__":
    add_quote_unit_column()