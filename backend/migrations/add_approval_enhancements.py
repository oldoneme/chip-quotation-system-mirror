#!/usr/bin/env python3
"""
数据库迁移：增强审批功能
Migration: Add approval enhancements for WeChat Work integration

执行日期: 2025-08-30
作者: Claude Code Assistant
"""

import sqlite3
from datetime import datetime
import os
import sys

# 添加父目录到路径以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_quotes_table(cursor):
    """迁移quotes表，添加新的审批相关字段"""
    
    print("正在迁移quotes表...")
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(quotes)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # 需要添加的新字段
    new_columns = [
        ("approval_status", "TEXT DEFAULT 'not_submitted'"),
        ("current_approver_id", "INTEGER"),
        ("wecom_approval_template_id", "TEXT"),
        ("approval_link_token", "TEXT UNIQUE"),
    ]
    
    for column_name, column_definition in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE quotes ADD COLUMN {column_name} {column_definition}")
                print(f"  ✅ 添加字段: {column_name}")
            except sqlite3.Error as e:
                print(f"  ❌ 添加字段 {column_name} 失败: {e}")
        else:
            print(f"  ⏭️ 字段已存在: {column_name}")
    
    # 创建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_quotes_approval_status ON quotes(approval_status)",
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            print(f"  ✅ 创建索引成功")
        except sqlite3.Error as e:
            print(f"  ⚠️ 创建索引失败: {e}")

def migrate_approval_records_table(cursor):
    """迁移approval_records表，添加增强的审批功能字段"""
    
    print("正在迁移approval_records表...")
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(approval_records)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # 需要添加的新字段
    new_columns = [
        ("step_order", "INTEGER DEFAULT 1"),
        ("is_final_step", "BOOLEAN DEFAULT 1"),
        ("modified_data", "TEXT"),
        ("original_data", "TEXT"),
        ("change_summary", "TEXT"),
        ("forwarded_to_id", "INTEGER"),
        ("forward_reason", "TEXT"),
        ("input_deadline", "DATETIME"),
        ("input_received", "BOOLEAN DEFAULT 0"),
        ("wecom_callback_data", "TEXT"),
        ("deadline", "DATETIME"),
    ]
    
    for column_name, column_definition in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE approval_records ADD COLUMN {column_name} {column_definition}")
                print(f"  ✅ 添加字段: {column_name}")
            except sqlite3.Error as e:
                print(f"  ❌ 添加字段 {column_name} 失败: {e}")
        else:
            print(f"  ⏭️ 字段已存在: {column_name}")
    
    # 创建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_approval_records_action ON approval_records(action)",
        "CREATE INDEX IF NOT EXISTS idx_approval_records_status ON approval_records(status)",
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            print(f"  ✅ 创建索引成功")
        except sqlite3.Error as e:
            print(f"  ⚠️ 创建索引失败: {e}")

def update_existing_data(cursor):
    """更新现有数据以匹配新的状态定义"""
    
    print("正在更新现有数据...")
    
    try:
        # 为所有现有的报价单设置默认的approval_status
        cursor.execute("""
            UPDATE quotes 
            SET approval_status = CASE 
                WHEN status = 'draft' THEN 'not_submitted'
                WHEN status = 'pending' THEN 'pending'
                WHEN status = 'approved' THEN 'approved'
                WHEN status = 'rejected' THEN 'rejected'
                ELSE 'not_submitted'
            END
            WHERE approval_status IS NULL OR approval_status = ''
        """)
        
        updated_rows = cursor.rowcount
        print(f"  ✅ 更新了 {updated_rows} 条报价单的审批状态")
        
    except sqlite3.Error as e:
        print(f"  ❌ 更新现有数据失败: {e}")

def main():
    """执行数据库迁移"""
    
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), "../app/test.db")
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    print(f"🔄 开始数据库迁移: {db_path}")
    print(f"📅 迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 备份提示
        print("⚠️  建议在执行迁移前备份数据库文件")
        
        # 执行迁移
        migrate_quotes_table(cursor)
        migrate_approval_records_table(cursor)
        update_existing_data(cursor)
        
        # 提交更改
        conn.commit()
        
        print("-" * 50)
        print("✅ 数据库迁移完成！")
        print("🎯 新功能已启用:")
        print("   • 6种审批动作支持")
        print("   • 企业微信审批集成字段")
        print("   • 增强的审批状态管理")
        print("   • 审批链接Token支持")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)