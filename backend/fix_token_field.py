#!/usr/bin/env python3
"""修复approval_link_token字段"""

import sqlite3
import os

def fix_token_field():
    db_path = os.path.join(os.path.dirname(__file__), "app/test.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(quotes)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        if "approval_link_token" not in existing_columns:
            cursor.execute("ALTER TABLE quotes ADD COLUMN approval_link_token TEXT")
            print("✅ 成功添加approval_link_token字段")
        else:
            print("⏭️ approval_link_token字段已存在")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    fix_token_field()