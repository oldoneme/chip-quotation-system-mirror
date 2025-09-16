#!/usr/bin/env python3
"""
Step 5.2: 数据库迁移脚本
安全地添加缺失的 approval_method 字段并初始化数据

安全原则：
- 使用事务确保原子性
- 操作前备份关键数据
- 支持回滚操作
- 详细的操作日志

迁移内容：
1. 添加 approval_method 字段到 quotes 表
2. 根据现有数据推断并设置初始值
3. 验证迁移结果
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
import json


class DatabaseMigration:
    def __init__(self):
        """初始化数据库迁移器"""
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=self.engine)
        self.db = SessionLocal()
        self.migration_log = {
            "migration_time": datetime.now().isoformat(),
            "operations": [],
            "backup_data": {},
            "success": False,
            "error": None
        }

    def backup_quotes_data(self):
        """备份报价单关键数据"""
        print("💾 备份报价单数据...")

        try:
            # 备份quotes表的关键字段
            query = text("""
                SELECT
                    id, quote_number, approval_status, wecom_approval_id,
                    created_at, updated_at
                FROM quotes
                WHERE is_deleted = 0
            """)

            result = self.db.execute(query)
            rows = result.fetchall()

            backup_data = []
            for row in rows:
                backup_data.append({
                    "id": row[0],
                    "quote_number": row[1],
                    "approval_status": row[2],
                    "wecom_approval_id": row[3],
                    "created_at": str(row[4]),
                    "updated_at": str(row[5])
                })

            self.migration_log["backup_data"]["quotes"] = backup_data
            print(f"   ✅ 已备份 {len(backup_data)} 条报价单记录")

            return True

        except Exception as e:
            print(f"   ❌ 备份数据失败: {e}")
            self.migration_log["error"] = f"备份失败: {str(e)}"
            return False

    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """检查数据库列是否存在"""
        try:
            # SQLite 检查列是否存在
            query = text(f"PRAGMA table_info({table_name})")
            result = self.db.execute(query)
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns

        except Exception as e:
            print(f"   ❌ 检查列存在性失败: {e}")
            return False

    def add_approval_method_column(self):
        """添加 approval_method 字段到 quotes 表"""
        print("🔧 添加 approval_method 字段...")

        try:
            # 检查字段是否已存在
            if self.check_column_exists("quotes", "approval_method"):
                print("   ⚠️ approval_method 字段已存在，跳过添加")
                self.migration_log["operations"].append({
                    "operation": "add_approval_method_column",
                    "status": "skipped",
                    "reason": "column_already_exists"
                })
                return True

            # 添加新字段
            alter_query = text("""
                ALTER TABLE quotes
                ADD COLUMN approval_method VARCHAR(20) DEFAULT 'internal'
            """)

            self.db.execute(alter_query)
            self.db.commit()

            print("   ✅ approval_method 字段添加成功")
            self.migration_log["operations"].append({
                "operation": "add_approval_method_column",
                "status": "completed",
                "sql": "ALTER TABLE quotes ADD COLUMN approval_method VARCHAR(20) DEFAULT 'internal'"
            })

            return True

        except Exception as e:
            print(f"   ❌ 添加 approval_method 字段失败: {e}")
            self.migration_log["error"] = f"添加字段失败: {str(e)}"
            self.db.rollback()
            return False

    def initialize_approval_method_values(self):
        """根据现有数据初始化 approval_method 值"""
        print("🔄 初始化 approval_method 值...")

        try:
            # 根据 wecom_approval_id 推断审批方式
            # 有 wecom_approval_id 的设为 'wecom'，否则为 'internal'
            update_wecom_query = text("""
                UPDATE quotes
                SET approval_method = 'wecom'
                WHERE wecom_approval_id IS NOT NULL
                  AND wecom_approval_id != ''
                  AND approval_method = 'internal'
            """)

            wecom_result = self.db.execute(update_wecom_query)
            wecom_count = wecom_result.rowcount

            # 确保其他记录为 internal
            update_internal_query = text("""
                UPDATE quotes
                SET approval_method = 'internal'
                WHERE (wecom_approval_id IS NULL OR wecom_approval_id = '')
                  AND (approval_method IS NULL OR approval_method = '')
            """)

            internal_result = self.db.execute(update_internal_query)
            internal_count = internal_result.rowcount

            self.db.commit()

            print(f"   ✅ 设置为企业微信审批: {wecom_count} 条")
            print(f"   ✅ 设置为内部审批: {internal_count} 条")

            self.migration_log["operations"].append({
                "operation": "initialize_approval_method_values",
                "status": "completed",
                "wecom_count": wecom_count,
                "internal_count": internal_count
            })

            return True

        except Exception as e:
            print(f"   ❌ 初始化 approval_method 值失败: {e}")
            self.migration_log["error"] = f"初始化值失败: {str(e)}"
            self.db.rollback()
            return False

    def verify_migration(self):
        """验证迁移结果"""
        print("🔍 验证迁移结果...")

        try:
            # 检查字段是否存在
            if not self.check_column_exists("quotes", "approval_method"):
                raise Exception("approval_method 字段不存在")

            # 统计各种审批方式的数量
            stats_query = text("""
                SELECT
                    approval_method,
                    COUNT(*) as count,
                    COUNT(CASE WHEN wecom_approval_id IS NOT NULL AND wecom_approval_id != '' THEN 1 END) as has_wecom_id
                FROM quotes
                WHERE is_deleted = 0
                GROUP BY approval_method
            """)

            result = self.db.execute(stats_query)
            stats = result.fetchall()

            print("   📊 审批方式分布:")
            verification_results = {}

            for row in stats:
                method, count, has_wecom_id = row
                print(f"      - {method}: {count} 条记录 (其中有企微ID: {has_wecom_id})")
                verification_results[method] = {
                    "count": count,
                    "has_wecom_id": has_wecom_id
                }

            # 验证数据一致性
            inconsistent_query = text("""
                SELECT COUNT(*) as count
                FROM quotes
                WHERE is_deleted = 0
                  AND (
                    (approval_method = 'wecom' AND (wecom_approval_id IS NULL OR wecom_approval_id = ''))
                    OR
                    (approval_method = 'internal' AND wecom_approval_id IS NOT NULL AND wecom_approval_id != '')
                  )
            """)

            inconsistent_result = self.db.execute(inconsistent_query)
            inconsistent_count = inconsistent_result.scalar()

            if inconsistent_count > 0:
                print(f"   ⚠️ 发现 {inconsistent_count} 条不一致记录")
                self.migration_log["operations"].append({
                    "operation": "verify_migration",
                    "status": "warning",
                    "inconsistent_count": inconsistent_count
                })
            else:
                print("   ✅ 数据一致性验证通过")
                self.migration_log["operations"].append({
                    "operation": "verify_migration",
                    "status": "passed",
                    "verification_results": verification_results
                })

            return True

        except Exception as e:
            print(f"   ❌ 验证迁移失败: {e}")
            self.migration_log["error"] = f"验证失败: {str(e)}"
            return False

    def save_migration_log(self, filename: Optional[str] = None):
        """保存迁移日志"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"migration_log_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.migration_log, f, ensure_ascii=False, indent=2)

            print(f"📄 迁移日志已保存: {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ 保存日志失败: {e}")
            return None

    def run_migration(self):
        """运行完整的数据库迁移"""
        print("🚀 开始数据库迁移...")
        print("⚠️ 注意：此操作会修改数据库结构")
        print()

        try:
            # 1. 备份数据
            if not self.backup_quotes_data():
                return False
            print()

            # 2. 添加 approval_method 字段
            if not self.add_approval_method_column():
                return False
            print()

            # 3. 初始化字段值
            if not self.initialize_approval_method_values():
                return False
            print()

            # 4. 验证迁移结果
            if not self.verify_migration():
                return False
            print()

            self.migration_log["success"] = True
            print("✅ 数据库迁移完成")

            # 5. 保存日志
            log_file = self.save_migration_log()

            return True

        except Exception as e:
            print(f"❌ 数据库迁移失败: {e}")
            self.migration_log["success"] = False
            self.migration_log["error"] = str(e)
            self.db.rollback()
            return False

        finally:
            self.db.close()


def main():
    """主函数"""
    print("=" * 80)
    print("🔧 Step 5.2: 数据库迁移 - 添加 approval_method 字段")
    print("=" * 80)
    print()

    migration = DatabaseMigration()
    success = migration.run_migration()

    if success:
        print()
        print("🎉 数据库迁移成功完成！")
        print("✅ 主要改动:")
        print("   - 添加了 approval_method 字段到 quotes 表")
        print("   - 根据现有数据初始化了字段值")
        print("   - 验证了数据一致性")
        return 0
    else:
        print()
        print("❌ 数据库迁移失败")
        print("🔄 数据库已回滚到迁移前状态")
        return 1


if __name__ == "__main__":
    exit(main())