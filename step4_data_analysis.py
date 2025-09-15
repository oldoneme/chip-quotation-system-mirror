#!/usr/bin/env python3
"""
Step 4: 数据库状态分析和数据质量检查
安全地分析当前数据库中报价单的状态，不修改任何数据
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def analyze_database():
    """分析数据库中报价单的状态和数据质量"""

    # 数据库路径
    db_path = Path(__file__).parent / "backend" / "app" / "test.db"

    if not db_path.exists():
        print("❌ 数据库文件不存在:", db_path)
        return

    print("🔍 Step 4: 数据库状态分析")
    print("=" * 50)

    try:
        # 连接数据库（只读模式）
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("\n📊 1. 基础统计分析:")
        print("-" * 30)

        # 总报价单数量
        cursor.execute("SELECT COUNT(*) as total FROM quotes")
        total_quotes = cursor.fetchone()['total']
        print(f"📈 总报价单数量: {total_quotes}")

        # 按删除状态分组
        cursor.execute("""
            SELECT
                is_deleted,
                COUNT(*) as count,
                CASE
                    WHEN is_deleted = 1 THEN '已删除'
                    ELSE '正常'
                END as status_text
            FROM quotes
            GROUP BY is_deleted
        """)

        status_stats = cursor.fetchall()
        for row in status_stats:
            print(f"  {row['status_text']}: {row['count']} 条")

        # 按审批状态分组
        print(f"\n📊 2. 审批状态分析:")
        print("-" * 30)

        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count
            FROM quotes
            WHERE is_deleted = 0 OR is_deleted IS NULL
            GROUP BY status
        """)

        approval_stats = cursor.fetchall()
        for row in approval_stats:
            print(f"  {row['status']}: {row['count']} 条")

        print(f"\n📊 3. 详细报价单列表:")
        print("-" * 30)

        # 获取所有报价单的详细信息
        cursor.execute("""
            SELECT
                id, quote_number, customer_name, status,
                is_deleted, deleted_at, deleted_by,
                created_at, updated_at
            FROM quotes
            ORDER BY created_at DESC
        """)

        quotes = cursor.fetchall()

        if quotes:
            print(f"{'ID':<4} {'报价号':<15} {'客户':<15} {'状态':<10} {'删除':<6} {'创建时间':<19}")
            print("-" * 80)

            for quote in quotes:
                deleted_status = "是" if quote['is_deleted'] else "否"
                created_time = quote['created_at'][:19] if quote['created_at'] else "N/A"

                print(f"{quote['id']:<4} {quote['quote_number']:<15} "
                      f"{quote['customer_name'][:12]:<15} {quote['status']:<10} "
                      f"{deleted_status:<6} {created_time:<19}")

        print(f"\n📊 4. 数据质量检查:")
        print("-" * 30)

        # 检查空值或异常数据
        cursor.execute("""
            SELECT
                SUM(CASE WHEN quote_number IS NULL OR quote_number = '' THEN 1 ELSE 0 END) as empty_quote_number,
                SUM(CASE WHEN customer_name IS NULL OR customer_name = '' THEN 1 ELSE 0 END) as empty_customer,
                SUM(CASE WHEN status IS NULL OR status = '' THEN 1 ELSE 0 END) as empty_status
            FROM quotes
        """)

        quality_check = cursor.fetchone()
        print(f"  🔍 缺少报价号: {quality_check['empty_quote_number']} 条")
        print(f"  🔍 缺少客户名: {quality_check['empty_customer']} 条")
        print(f"  🔍 缺少状态: {quality_check['empty_status']} 条")

        # 检查软删除字段一致性
        cursor.execute("""
            SELECT COUNT(*) as inconsistent_deletes
            FROM quotes
            WHERE (is_deleted = 1 AND deleted_at IS NULL)
               OR (is_deleted = 0 AND deleted_at IS NOT NULL)
        """)

        inconsistent = cursor.fetchone()['inconsistent_deletes']
        print(f"  🔍 软删除字段不一致: {inconsistent} 条")

        print(f"\n📊 5. 清理建议:")
        print("-" * 30)

        if inconsistent > 0:
            print(f"  ⚠️  发现 {inconsistent} 条软删除字段不一致的记录，建议修复")

        # 查找测试数据（根据常见的测试命名模式）
        cursor.execute("""
            SELECT COUNT(*) as test_data_count
            FROM quotes
            WHERE customer_name LIKE '%测试%'
               OR customer_name LIKE '%test%'
               OR customer_name LIKE '%Test%'
               OR customer_name LIKE '%演示%'
               OR customer_name LIKE '%demo%'
               OR quote_number LIKE '%test%'
               OR quote_number LIKE '%Test%'
        """)

        test_count = cursor.fetchone()['test_data_count']
        if test_count > 0:
            print(f"  🧪 发现 {test_count} 条疑似测试数据，建议清理")

        print(f"\n✅ 数据库分析完成!")
        print(f"📈 总结: {total_quotes} 条报价单，其中正常数据和删除数据分布如上所示")

    except Exception as e:
        print(f"❌ 分析过程中出错: {str(e)}")

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    analyze_database()