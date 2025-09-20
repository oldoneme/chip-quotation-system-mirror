#!/usr/bin/env python3
"""
修复审批UI集成问题
解决状态不一致和重复按钮问题
"""

import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_status_inconsistency():
    """修复状态不一致问题"""
    logger.info("开始修复状态不一致问题...")

    with SessionLocal() as db:
        try:
            # 获取状态不一致的报价单
            result = db.execute(text("""
                SELECT id, quote_number, status, approval_status
                FROM quotes
                WHERE status != CASE
                    WHEN approval_status = 'not_submitted' THEN 'draft'
                    WHEN approval_status = 'pending' THEN 'pending'
                    WHEN approval_status = 'approved' THEN 'approved'
                    WHEN approval_status = 'rejected' THEN 'rejected'
                    ELSE status
                END
            """))

            inconsistent_quotes = result.fetchall()

            if not inconsistent_quotes:
                logger.info("✅ 没有发现状态不一致的报价单")
                return

            logger.info(f"发现 {len(inconsistent_quotes)} 个状态不一致的报价单")

            for quote in inconsistent_quotes:
                quote_id = quote[0]
                quote_number = quote[1]
                current_status = quote[2]
                approval_status = quote[3]

                # 根据审批状态计算正确的状态
                correct_status = {
                    'not_submitted': 'draft',
                    'pending': 'pending',
                    'approved': 'approved',
                    'rejected': 'rejected'
                }.get(approval_status, current_status)

                if correct_status != current_status:
                    db.execute(text("""
                        UPDATE quotes
                        SET status = :correct_status, updated_at = :now
                        WHERE id = :quote_id
                    """), {
                        'correct_status': correct_status,
                        'quote_id': quote_id,
                        'now': datetime.now()
                    })

                    logger.info(f"✅ 修复报价单 {quote_number}: {current_status} -> {correct_status}")

            db.commit()
            logger.info(f"✅ 成功修复 {len(inconsistent_quotes)} 个报价单的状态")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 状态修复失败: {e}")
            raise

def check_duplicate_submissions():
    """检查重复提交的问题"""
    logger.info("检查重复提交问题...")

    with SessionLocal() as db:
        try:
            # 查找有多个submit记录的报价单
            result = db.execute(text("""
                SELECT quote_id, COUNT(*) as submit_count
                FROM approval_records
                WHERE action = 'submit'
                GROUP BY quote_id
                HAVING COUNT(*) > 1
            """))

            duplicate_submissions = result.fetchall()

            if duplicate_submissions:
                logger.warning(f"发现 {len(duplicate_submissions)} 个报价单有重复提交:")
                for item in duplicate_submissions:
                    logger.warning(f"  报价单ID {item[0]}: {item[1]} 次提交")
            else:
                logger.info("✅ 没有发现重复提交问题")

        except Exception as e:
            logger.error(f"❌ 检查重复提交失败: {e}")

def get_approval_button_config():
    """生成前端按钮配置建议"""
    logger.info("生成前端按钮配置建议...")

    with SessionLocal() as db:
        try:
            # 获取所有报价单的当前状态
            result = db.execute(text("""
                SELECT id, quote_number, approval_status,
                       CASE
                           WHEN approval_status = 'not_submitted' THEN 'show_submit'
                           WHEN approval_status = 'pending' THEN 'show_withdraw'
                           WHEN approval_status = 'approved' THEN 'show_none'
                           WHEN approval_status = 'rejected' THEN 'show_resubmit'
                           ELSE 'show_none'
                       END as button_config
                FROM quotes
                ORDER BY created_at DESC
                LIMIT 10
            """))

            quotes = result.fetchall()

            print("\n=== 前端按钮配置建议 ===")
            for quote in quotes:
                print(f"报价单 {quote[1]} (ID: {quote[0]})")
                print(f"  状态: {quote[2]}")
                print(f"  建议按钮: {quote[3]}")
                print()

        except Exception as e:
            logger.error(f"❌ 生成配置建议失败: {e}")

def main():
    """主函数"""
    try:
        print("🔧 开始修复审批UI集成问题")
        print("=" * 50)

        # 1. 修复状态不一致
        fix_status_inconsistency()

        # 2. 检查重复提交
        check_duplicate_submissions()

        # 3. 生成前端配置建议
        get_approval_button_config()

        print("=" * 50)
        print("🎉 审批UI集成问题修复完成!")

        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)