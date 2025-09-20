#!/usr/bin/env python3
"""
检查报价单状态
"""

import sqlite3

def check_quotes():
    """检查报价单状态"""
    print("🔍 检查报价单状态")

    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 检查所有报价单
        cursor.execute('''
            SELECT id, quote_number, status, approval_status, is_deleted
            FROM quotes
            ORDER BY id DESC
            LIMIT 10
        ''')
        quotes = cursor.fetchall()

        print(f"\n📋 最近10个报价单:")
        for quote_id, quote_number, status, approval_status, is_deleted in quotes:
            deleted_text = " (已删除)" if is_deleted else ""
            print(f"   ID: {quote_id}, 编号: {quote_number}, 状态: {status}/{approval_status}{deleted_text}")

        return quotes

    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    check_quotes()