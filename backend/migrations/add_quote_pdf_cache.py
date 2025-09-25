#!/usr/bin/env python3
"""
数据库迁移：新增报价单PDF缓存表 quote_pdf_cache

该脚本面向SQLite数据库，负责创建缓存表并确保必要索引存在。
执行前建议备份数据库文件。
"""

import os
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app", "test.db")


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def create_quote_pdf_cache_table(cursor) -> None:
    """创建 quote_pdf_cache 表并添加约束/索引"""
    if table_exists(cursor, "quote_pdf_cache"):
        print("⏭️  表 quote_pdf_cache 已存在，跳过创建")
        return

    print("🛠️  创建表 quote_pdf_cache ...")
    cursor.execute(
        """
        CREATE TABLE quote_pdf_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER UNIQUE NOT NULL,
            pdf_path TEXT NOT NULL,
            source TEXT DEFAULT 'playwright',
            file_size INTEGER DEFAULT 0,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quote_id)
                REFERENCES quotes(id)
                ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_quote_pdf_cache_quote_id ON quote_pdf_cache(quote_id)"
    )
    print("✅  表 quote_pdf_cache 创建成功")


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return 1

    print("🔄 开始执行 quote_pdf_cache 数据库迁移")
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📂 目标数据库:", DB_PATH)

    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        create_quote_pdf_cache_table(cursor)

        connection.commit()
        print("🎉  数据库迁移完成")
        return 0
    except sqlite3.Error as exc:
        print(f"❌ 迁移失败: {exc}")
        return 1
    finally:
        if 'connection' in locals():
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
