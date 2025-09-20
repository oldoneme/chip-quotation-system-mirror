#!/usr/bin/env python3
"""
数据库结构优化脚本
为统一审批系统添加必要的字段和索引，优化性能
"""

import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from sqlalchemy import text, Index
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(db, table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns
    except Exception as e:
        logger.error(f"检查列失败: {e}")
        return False

def check_index_exists(db, index_name):
    """检查索引是否存在"""
    try:
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name=?"), (index_name,))
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"检查索引失败: {e}")
        return False

def add_approval_engine_fields():
    """为统一审批引擎添加必要字段"""
    logger.info("开始数据库结构优化...")

    with SessionLocal() as db:
        try:
            # 1. 为quotes表添加统一审批引擎字段
            logger.info("优化quotes表结构...")

            # 添加操作渠道字段
            if not check_column_exists(db, "quotes", "last_operation_channel"):
                db.execute(text("""
                    ALTER TABLE quotes
                    ADD COLUMN last_operation_channel VARCHAR(20) DEFAULT 'INTERNAL'
                """))
                logger.info("✅ 添加 last_operation_channel 字段")

            # 添加同步状态字段
            if not check_column_exists(db, "quotes", "sync_required"):
                db.execute(text("""
                    ALTER TABLE quotes
                    ADD COLUMN sync_required BOOLEAN DEFAULT FALSE
                """))
                logger.info("✅ 添加 sync_required 字段")

            # 添加最后同步时间
            if not check_column_exists(db, "quotes", "last_sync_at"):
                db.execute(text("""
                    ALTER TABLE quotes
                    ADD COLUMN last_sync_at DATETIME
                """))
                logger.info("✅ 添加 last_sync_at 字段")

            # 添加操作ID字段（用于跟踪操作）
            if not check_column_exists(db, "quotes", "last_operation_id"):
                db.execute(text("""
                    ALTER TABLE quotes
                    ADD COLUMN last_operation_id VARCHAR(50)
                """))
                logger.info("✅ 添加 last_operation_id 字段")

            # 2. 为approval_records表添加统一审批引擎字段
            logger.info("优化approval_records表结构...")

            # 添加操作渠道字段
            if not check_column_exists(db, "approval_records", "operation_channel"):
                db.execute(text("""
                    ALTER TABLE approval_records
                    ADD COLUMN operation_channel VARCHAR(20) DEFAULT 'INTERNAL'
                """))
                logger.info("✅ 添加 operation_channel 字段")

            # 添加操作ID字段
            if not check_column_exists(db, "approval_records", "operation_id"):
                db.execute(text("""
                    ALTER TABLE approval_records
                    ADD COLUMN operation_id VARCHAR(50)
                """))
                logger.info("✅ 添加 operation_id 字段")

            # 添加事件数据字段
            if not check_column_exists(db, "approval_records", "event_data"):
                db.execute(text("""
                    ALTER TABLE approval_records
                    ADD COLUMN event_data TEXT
                """))
                logger.info("✅ 添加 event_data 字段")

            # 添加同步状态字段
            if not check_column_exists(db, "approval_records", "sync_status"):
                db.execute(text("""
                    ALTER TABLE approval_records
                    ADD COLUMN sync_status VARCHAR(20) DEFAULT 'PENDING'
                """))
                logger.info("✅ 添加 sync_status 字段")

            # 3. 创建性能优化索引
            logger.info("创建性能优化索引...")

            # quotes表索引
            indexes_to_create = [
                ("idx_quotes_approval_status_method", "CREATE INDEX IF NOT EXISTS idx_quotes_approval_status_method ON quotes(approval_status, approval_method)"),
                ("idx_quotes_operation_channel", "CREATE INDEX IF NOT EXISTS idx_quotes_operation_channel ON quotes(last_operation_channel)"),
                ("idx_quotes_sync_required", "CREATE INDEX IF NOT EXISTS idx_quotes_sync_required ON quotes(sync_required)"),
                ("idx_quotes_wecom_approval_id", "CREATE INDEX IF NOT EXISTS idx_quotes_wecom_approval_id ON quotes(wecom_approval_id)"),

                # approval_records表索引
                ("idx_approval_records_quote_action", "CREATE INDEX IF NOT EXISTS idx_approval_records_quote_action ON approval_records(quote_id, action)"),
                ("idx_approval_records_operation_channel", "CREATE INDEX IF NOT EXISTS idx_approval_records_operation_channel ON approval_records(operation_channel)"),
                ("idx_approval_records_operation_id", "CREATE INDEX IF NOT EXISTS idx_approval_records_operation_id ON approval_records(operation_id)"),
                ("idx_approval_records_sync_status", "CREATE INDEX IF NOT EXISTS idx_approval_records_sync_status ON approval_records(sync_status)"),
                ("idx_approval_records_created_at", "CREATE INDEX IF NOT EXISTS idx_approval_records_created_at ON approval_records(created_at)"),
            ]

            for index_name, sql in indexes_to_create:
                try:
                    db.execute(text(sql))
                    logger.info(f"✅ 创建索引: {index_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 索引 {index_name} 可能已存在: {e}")

            # 提交所有更改
            db.commit()
            logger.info("✅ 数据库结构优化完成")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 数据库结构优化失败: {e}")
            raise

def verify_optimization():
    """验证优化结果"""
    logger.info("验证数据库优化结果...")

    with SessionLocal() as db:
        try:
            # 检查新增字段
            required_quote_fields = [
                "last_operation_channel", "sync_required",
                "last_sync_at", "last_operation_id"
            ]

            required_approval_fields = [
                "operation_channel", "operation_id",
                "event_data", "sync_status"
            ]

            # 验证quotes表字段
            logger.info("验证quotes表字段...")
            for field in required_quote_fields:
                if check_column_exists(db, "quotes", field):
                    logger.info(f"✅ quotes.{field} 存在")
                else:
                    logger.error(f"❌ quotes.{field} 不存在")

            # 验证approval_records表字段
            logger.info("验证approval_records表字段...")
            for field in required_approval_fields:
                if check_column_exists(db, "approval_records", field):
                    logger.info(f"✅ approval_records.{field} 存在")
                else:
                    logger.error(f"❌ approval_records.{field} 不存在")

            # 检查索引
            logger.info("验证索引...")
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"))
            indexes = [row[0] for row in result]
            logger.info(f"现有索引数量: {len(indexes)}")

            for index in indexes:
                logger.info(f"✅ 索引: {index}")

            logger.info("✅ 数据库优化验证完成")

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            raise

def update_existing_data():
    """更新现有数据的默认值"""
    logger.info("更新现有数据...")

    with SessionLocal() as db:
        try:
            # 更新quotes表的默认值
            db.execute(text("""
                UPDATE quotes
                SET last_operation_channel = 'INTERNAL',
                    sync_required = FALSE
                WHERE last_operation_channel IS NULL
            """))

            # 更新approval_records表的默认值
            db.execute(text("""
                UPDATE approval_records
                SET operation_channel = 'INTERNAL',
                    sync_status = 'COMPLETED'
                WHERE operation_channel IS NULL
            """))

            db.commit()
            logger.info("✅ 现有数据更新完成")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 数据更新失败: {e}")
            raise

def main():
    """主函数"""
    try:
        print("🚀 开始数据库结构优化")
        print("=" * 50)

        # 步骤1: 添加必要字段和索引
        add_approval_engine_fields()

        # 步骤2: 更新现有数据
        update_existing_data()

        # 步骤3: 验证优化结果
        verify_optimization()

        print("=" * 50)
        print("🎉 数据库结构优化成功完成!")

        return True

    except Exception as e:
        print(f"❌ 数据库结构优化失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)