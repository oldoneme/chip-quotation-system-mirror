#!/usr/bin/env python3
"""
清理所有报价单数据的脚本
用于测试准备，删除所有报价单及相关数据
"""

import sqlite3
import os

def clear_all_quotes():
    """清理所有报价单相关数据"""
    db_path = "app/test.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 清理相关表的数据（按依赖关系顺序）
        tables_to_clear = [
            "approval_timeline",  # 审批时间线
            "approval_instance",  # 审批实例映射  
            "approval_records",   # 审批记录
            "quote_items",        # 报价单项目
            "quotes"              # 报价单主表
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                affected_rows = cursor.rowcount
                print(f"✅ 清理表 {table}: 删除了 {affected_rows} 条记录")
            except sqlite3.Error as e:
                print(f"⚠️  清理表 {table} 时出错 (可能表不存在): {e}")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('quotes', 'quote_items', 'approval_records')")
        print("✅ 重置了自增ID序列")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 所有报价单数据清理完成！")
        print("现在可以重新创建报价单进行测试了。")
        
    except Exception as e:
        print(f"❌ 清理数据时发生错误: {e}")

if __name__ == "__main__":
    print("🧹 开始清理所有报价单数据...")
    clear_all_quotes()