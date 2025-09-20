#!/usr/bin/env python3
"""
标准化现有审批记录脚本
将现有的审批记录迁移到统一审批系统格式
"""

import sys
import os
import uuid
from datetime import datetime, timezone
import json

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_approval_records():
    """获取当前所有审批记录"""
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT ar.*, q.quote_number, q.approval_method
            FROM approval_records ar
            JOIN quotes q ON ar.quote_id = q.id
            ORDER BY ar.created_at
        """))
        return result.fetchall()

def get_quotes_with_approval_status():
    """获取所有有审批状态的报价单"""
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT id, quote_number, approval_status, approval_method,
                   wecom_approval_id, submitted_at, approved_at, approved_by,
                   rejection_reason, created_at, updated_at
            FROM quotes
            WHERE approval_status != 'not_submitted'
            ORDER BY created_at
        """))
        return result.fetchall()

def create_missing_approval_records():
    """为现有的报价单创建缺失的审批记录"""
    logger.info("检查并创建缺失的审批记录...")

    with SessionLocal() as db:
        try:
            # 获取有审批状态但没有审批记录的报价单
            result = db.execute(text("""
                SELECT q.id, q.quote_number, q.approval_status, q.approval_method,
                       q.wecom_approval_id, q.submitted_at, q.approved_at,
                       q.approved_by, q.rejection_reason, q.created_at
                FROM quotes q
                LEFT JOIN approval_records ar ON q.id = ar.quote_id
                WHERE q.approval_status != 'not_submitted' AND ar.id IS NULL
            """))

            missing_records = result.fetchall()

            if not missing_records:
                logger.info("✅ 所有报价单都已有审批记录")
                return

            logger.info(f"发现 {len(missing_records)} 个报价单缺少审批记录")

            for quote in missing_records:
                quote_id = quote[0]
                quote_number = quote[1]
                approval_status = quote[2]
                approval_method = quote[3]
                wecom_approval_id = quote[4]
                submitted_at = quote[5]
                approved_at = quote[6]
                approved_by = quote[7]
                rejection_reason = quote[8]
                created_at = quote[9]

                logger.info(f"为报价单 {quote_number} 创建审批记录...")

                # 创建提交记录
                if submitted_at:
                    operation_id = str(uuid.uuid4())
                    db.execute(text("""
                        INSERT INTO approval_records (
                            quote_id, action, status, approver_id, comments,
                            wecom_approval_id, created_at, processed_at,
                            step_order, is_final_step, processed,
                            operation_channel, operation_id, sync_status
                        ) VALUES (
                            :quote_id, 'submit', 'completed', NULL, '系统迁移：审批提交',
                            :wecom_approval_id, :submitted_at, :submitted_at,
                            1, FALSE, TRUE,
                            :operation_channel, :operation_id, 'COMPLETED'
                        )
                    """), {
                        'quote_id': quote_id,
                        'wecom_approval_id': wecom_approval_id,
                        'submitted_at': submitted_at,
                        'operation_channel': 'WECOM' if approval_method == 'wecom' else 'INTERNAL',
                        'operation_id': operation_id
                    })

                # 创建最终决策记录
                if approval_status in ['approved', 'rejected'] and approved_at:
                    action = 'approve' if approval_status == 'approved' else 'reject'
                    comments = f'系统迁移：审批{approval_status}'
                    if rejection_reason:
                        comments += f' - {rejection_reason}'

                    operation_id = str(uuid.uuid4())
                    db.execute(text("""
                        INSERT INTO approval_records (
                            quote_id, action, status, approver_id, comments,
                            wecom_approval_id, created_at, processed_at,
                            step_order, is_final_step, processed,
                            operation_channel, operation_id, sync_status
                        ) VALUES (
                            :quote_id, :action, 'completed', :approved_by, :comments,
                            :wecom_approval_id, :approved_at, :approved_at,
                            2, TRUE, TRUE,
                            :operation_channel, :operation_id, 'COMPLETED'
                        )
                    """), {
                        'quote_id': quote_id,
                        'action': action,
                        'approved_by': approved_by,
                        'comments': comments,
                        'wecom_approval_id': wecom_approval_id,
                        'approved_at': approved_at,
                        'operation_channel': 'WECOM' if approval_method == 'wecom' else 'INTERNAL',
                        'operation_id': operation_id
                    })

                logger.info(f"✅ 为报价单 {quote_number} 创建了审批记录")

            db.commit()
            logger.info(f"✅ 成功创建 {len(missing_records)} 个报价单的审批记录")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 创建审批记录失败: {e}")
            raise

def standardize_existing_records():
    """标准化现有的审批记录"""
    logger.info("标准化现有审批记录...")

    with SessionLocal() as db:
        try:
            # 检查现有记录
            result = db.execute(text("SELECT COUNT(*) FROM approval_records"))
            total_records = result.scalar()

            if total_records == 0:
                logger.info("没有现有审批记录需要标准化")
                return

            logger.info(f"发现 {total_records} 条现有审批记录")

            # 标准化operation_channel字段
            result = db.execute(text("""
                SELECT ar.id, ar.quote_id, q.approval_method, ar.operation_channel
                FROM approval_records ar
                JOIN quotes q ON ar.quote_id = q.id
                WHERE ar.operation_channel IS NULL OR ar.operation_channel = ''
            """))

            records_to_update = result.fetchall()

            for record in records_to_update:
                record_id = record[0]
                approval_method = record[2]

                # 根据报价单的审批方式设置操作渠道
                operation_channel = 'WECOM' if approval_method == 'wecom' else 'INTERNAL'

                db.execute(text("""
                    UPDATE approval_records
                    SET operation_channel = :operation_channel
                    WHERE id = :record_id
                """), {
                    'operation_channel': operation_channel,
                    'record_id': record_id
                })

            # 为缺少operation_id的记录生成ID
            result = db.execute(text("""
                SELECT id FROM approval_records
                WHERE operation_id IS NULL OR operation_id = ''
            """))

            records_without_id = result.fetchall()

            for record in records_without_id:
                record_id = record[0]
                operation_id = str(uuid.uuid4())

                db.execute(text("""
                    UPDATE approval_records
                    SET operation_id = :operation_id
                    WHERE id = :record_id
                """), {
                    'operation_id': operation_id,
                    'record_id': record_id
                })

            # 标准化sync_status字段
            db.execute(text("""
                UPDATE approval_records
                SET sync_status = 'COMPLETED'
                WHERE sync_status IS NULL OR sync_status = ''
            """))

            db.commit()
            logger.info(f"✅ 标准化了 {len(records_to_update)} 条记录的操作渠道")
            logger.info(f"✅ 为 {len(records_without_id)} 条记录生成了操作ID")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 标准化记录失败: {e}")
            raise

def update_quotes_for_unified_approval():
    """更新报价单以支持统一审批系统"""
    logger.info("更新报价单以支持统一审批系统...")

    with SessionLocal() as db:
        try:
            # 为所有报价单设置默认的操作渠道
            result = db.execute(text("""
                SELECT id, approval_method FROM quotes
                WHERE last_operation_channel IS NULL OR last_operation_channel = ''
            """))

            quotes_to_update = result.fetchall()

            for quote in quotes_to_update:
                quote_id = quote[0]
                approval_method = quote[1]

                operation_channel = 'WECOM' if approval_method == 'wecom' else 'INTERNAL'

                db.execute(text("""
                    UPDATE quotes
                    SET last_operation_channel = :operation_channel,
                        sync_required = FALSE,
                        last_sync_at = :now
                    WHERE id = :quote_id
                """), {
                    'operation_channel': operation_channel,
                    'quote_id': quote_id,
                    'now': datetime.now(timezone.utc)
                })

            db.commit()
            logger.info(f"✅ 更新了 {len(quotes_to_update)} 个报价单的统一审批字段")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 更新报价单失败: {e}")
            raise

def verify_standardization():
    """验证标准化结果"""
    logger.info("验证标准化结果...")

    with SessionLocal() as db:
        try:
            # 检查审批记录完整性
            result = db.execute(text("""
                SELECT COUNT(*) FROM approval_records
                WHERE operation_channel IS NULL OR operation_channel = ''
                   OR operation_id IS NULL OR operation_id = ''
                   OR sync_status IS NULL OR sync_status = ''
            """))
            incomplete_records = result.scalar()

            if incomplete_records > 0:
                logger.warning(f"⚠️ 发现 {incomplete_records} 条不完整的审批记录")
            else:
                logger.info("✅ 所有审批记录字段完整")

            # 检查报价单统一审批字段
            result = db.execute(text("""
                SELECT COUNT(*) FROM quotes
                WHERE approval_status != 'not_submitted'
                  AND (last_operation_channel IS NULL OR last_operation_channel = '')
            """))
            incomplete_quotes = result.scalar()

            if incomplete_quotes > 0:
                logger.warning(f"⚠️ 发现 {incomplete_quotes} 个报价单缺少统一审批字段")
            else:
                logger.info("✅ 所有报价单统一审批字段完整")

            # 统计各类审批记录
            result = db.execute(text("""
                SELECT operation_channel, COUNT(*)
                FROM approval_records
                GROUP BY operation_channel
            """))

            logger.info("审批记录按渠道统计:")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} 条")

            # 统计各状态的报价单
            result = db.execute(text("""
                SELECT approval_status, COUNT(*)
                FROM quotes
                GROUP BY approval_status
            """))

            logger.info("报价单按审批状态统计:")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} 个")

            logger.info("✅ 标准化验证完成")

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            raise

def main():
    """主函数"""
    try:
        print("🚀 开始标准化现有审批记录")
        print("=" * 50)

        # 步骤1: 创建缺失的审批记录
        create_missing_approval_records()

        # 步骤2: 标准化现有记录
        standardize_existing_records()

        # 步骤3: 更新报价单字段
        update_quotes_for_unified_approval()

        # 步骤4: 验证标准化结果
        verify_standardization()

        print("=" * 50)
        print("🎉 审批记录标准化成功完成!")

        return True

    except Exception as e:
        print(f"❌ 审批记录标准化失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)