#!/usr/bin/env python3
"""
创建企业微信审批相关的数据库表
"""

import sqlite3
import os

# 数据库路径
DB_PATH = "app/test.db"

def create_tables():
    """创建审批相关表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建审批实例映射表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approval_instance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quotation_id INTEGER NOT NULL,
        sp_no TEXT UNIQUE,
        third_no TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 创建回调时间线表（用于幂等处理）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approval_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sp_no TEXT,
        event_id TEXT UNIQUE,
        open_sp_status INTEGER,
        raw_payload TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_instance_sp_no ON approval_instance(sp_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_instance_third_no ON approval_instance(third_no)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_timeline_event_id ON approval_timeline(event_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ 审批相关表创建成功")
    print("   - approval_instance: 审批实例映射")
    print("   - approval_timeline: 回调时间线（幂等）")

if __name__ == "__main__":
    create_tables()