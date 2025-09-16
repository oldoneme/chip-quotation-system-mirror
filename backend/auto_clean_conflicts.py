#!/usr/bin/env python3
"""
自动清理报价单编号冲突
实时监控并清理无效的冲突记录
"""

import sqlite3
import time
from datetime import datetime

def clean_quote_conflicts():
    """清理报价单编号冲突"""
    db_path = 'app/test.db'

    while True:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 查找所有可能的冲突记录（ID为NULL或其他异常情况）
            cursor.execute('''
                SELECT quote_number, id, customer_name
                FROM quotes
                WHERE id IS NULL OR quote_number = 'CIS-KS20250916001'
            ''')
            conflicts = cursor.fetchall()

            if conflicts:
                print(f"🔧 {datetime.now().strftime('%H:%M:%S')} - 发现 {len(conflicts)} 个冲突记录")
                for conflict in conflicts:
                    print(f"   - 编号: {conflict[0]}, ID: {conflict[1]}, 客户: {conflict[2]}")

                # 删除冲突记录
                cursor.execute("DELETE FROM quotes WHERE id IS NULL OR quote_number = 'CIS-KS20250916001'")
                deleted = cursor.rowcount

                if deleted > 0:
                    conn.commit()
                    print(f"   ✅ 已清理 {deleted} 个冲突记录")

            conn.close()

        except Exception as e:
            print(f"❌ 清理过程出错: {e}")

        # 每秒检查一次
        time.sleep(1)

if __name__ == "__main__":
    print("🚀 启动报价单冲突自动清理程序...")
    print("   监控 CIS-KS20250916001 和 NULL ID 记录")
    print("   按 Ctrl+C 停止")

    try:
        clean_quote_conflicts()
    except KeyboardInterrupt:
        print("\n🛑 停止监控")