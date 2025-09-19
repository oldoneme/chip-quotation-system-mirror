#!/usr/bin/env python3
"""
审批记录管理器 - 标准化ApprovalRecord格式和管理
遵循渐进式开发：最小可用版本，统一记录格式
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..models import ApprovalRecord, Quote, User
from .unified_approval_service import ApprovalMethod, ApprovalStatus, ApprovalResult


class ApprovalRecordManager:
    """审批记录管理器 - 标准化记录格式和操作"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def create_standard_record(
        self,
        quote_id: int,
        action: str,
        approver_id: int,
        approval_result: ApprovalResult,
        comments: str = "",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> ApprovalRecord:
        """创建标准化的审批记录"""
        try:
            # 基础审批记录
            record = ApprovalRecord(
                quote_id=quote_id,
                action=action,
                status='completed' if approval_result.success else 'cancelled',
                approver_id=approver_id,
                comments=self._standardize_comments(
                    comments,
                    approval_result.approval_method,
                    approval_result.message
                ),
                processed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )

            # 添加审批方法标识
            if additional_data is None:
                additional_data = {}

            additional_data.update({
                'approval_method': approval_result.approval_method.value,
                'approval_id': getattr(approval_result, 'operation_id', None),
                'success': approval_result.success
            })

            # 处理扩展数据
            if additional_data:
                self._add_additional_data(record, additional_data)

            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

            self.logger.info(
                f"创建标准审批记录 - 报价单:{quote_id}, 动作:{action}, "
                f"方法:{approval_result.approval_method.value}, 成功:{approval_result.success}"
            )

            return record

        except Exception as e:
            self.logger.error(f"创建审批记录失败: {e}")
            self.db.rollback()
            raise

    def _standardize_comments(
        self,
        original_comments: str,
        method: ApprovalMethod,
        result_message: str
    ) -> str:
        """标准化审批意见格式"""
        parts = []

        if original_comments:
            parts.append(original_comments)

        # 添加审批方法信息
        method_label = "企业微信审批" if method == ApprovalMethod.WECOM else "内部审批"
        parts.append(f"(通过{method_label})")

        # 添加结果信息
        if result_message and result_message != original_comments:
            parts.append(f"系统信息: {result_message}")

        return " ".join(parts)

    def _add_additional_data(self, record: ApprovalRecord, data: Dict[str, Any]):
        """添加扩展数据到审批记录"""
        # 处理修改数据
        if 'modified_data' in data:
            record.modified_data = json.dumps(data['modified_data'], ensure_ascii=False)

        if 'original_data' in data:
            record.original_data = json.dumps(data['original_data'], ensure_ascii=False)

        if 'change_summary' in data:
            record.change_summary = data['change_summary']

        # 处理转交数据
        if 'forwarded_to_id' in data:
            record.forwarded_to_id = data['forwarded_to_id']

        if 'forward_reason' in data:
            record.forward_reason = data['forward_reason']

        # 处理征求意见数据
        if 'input_deadline' in data:
            record.input_deadline = data['input_deadline']

    def get_quote_approval_history(self, quote_id: int) -> List[ApprovalRecord]:
        """获取报价单的标准化审批历史"""
        try:
            records = (
                self.db.query(ApprovalRecord)
                .filter(ApprovalRecord.quote_id == quote_id)
                .order_by(ApprovalRecord.created_at.desc())
                .all()
            )

            self.logger.info(f"获取报价单 {quote_id} 审批历史: {len(records)} 条记录")
            return records

        except Exception as e:
            self.logger.error(f"获取审批历史失败: {e}")
            return []

    def get_approval_statistics(self) -> Dict[str, Any]:
        """获取审批统计信息"""
        try:
            # 基础统计
            total_records = self.db.query(ApprovalRecord).count()

            # 按动作分组统计
            action_stats = {}
            actions = ['submit', 'approve', 'reject', 'forward', 'return_for_revision', 'approve_with_changes']

            for action in actions:
                count = self.db.query(ApprovalRecord).filter(ApprovalRecord.action == action).count()
                action_stats[action] = count

            # 按状态分组统计
            status_stats = {}
            statuses = ['completed', 'pending', 'cancelled']

            for status in statuses:
                count = self.db.query(ApprovalRecord).filter(ApprovalRecord.status == status).count()
                status_stats[status] = count

            stats = {
                'total_records': total_records,
                'action_statistics': action_stats,
                'status_statistics': status_stats,
                'generated_at': datetime.utcnow().isoformat()
            }

            self.logger.info(f"生成审批统计信息: {total_records} 条记录")
            return stats

        except Exception as e:
            self.logger.error(f"获取审批统计失败: {e}")
            return {'error': str(e)}

    def cleanup_orphaned_records(self) -> int:
        """清理孤儿审批记录（对应的报价单不存在）"""
        try:
            # 查找孤儿记录
            orphaned_query = (
                self.db.query(ApprovalRecord)
                .outerjoin(Quote, ApprovalRecord.quote_id == Quote.id)
                .filter(Quote.id.is_(None))
            )

            orphaned_count = orphaned_query.count()

            if orphaned_count > 0:
                orphaned_query.delete(synchronize_session=False)
                self.db.commit()

                self.logger.info(f"清理孤儿审批记录: {orphaned_count} 条")

            return orphaned_count

        except Exception as e:
            self.logger.error(f"清理孤儿记录失败: {e}")
            self.db.rollback()
            return 0

    def standardize_existing_records(self) -> Dict[str, int]:
        """标准化现有审批记录（数据迁移用）"""
        try:
            records = self.db.query(ApprovalRecord).all()
            updated_count = 0
            error_count = 0

            for record in records:
                try:
                    # 检查并标准化comments字段
                    if record.comments and not self._is_comments_standardized(record.comments):
                        # 这里可以添加标准化逻辑
                        # 例如：添加审批方法标识等
                        pass

                    # 检查并设置默认值
                    if record.status is None:
                        record.status = 'completed'
                        updated_count += 1

                    if record.step_order is None:
                        record.step_order = 1
                        updated_count += 1

                    if record.is_final_step is None:
                        record.is_final_step = True
                        updated_count += 1

                except Exception as e:
                    self.logger.warning(f"标准化记录 {record.id} 失败: {e}")
                    error_count += 1

            if updated_count > 0:
                self.db.commit()

            result = {
                'total_records': len(records),
                'updated_count': updated_count,
                'error_count': error_count
            }

            self.logger.info(f"标准化现有记录完成: 更新 {updated_count} 条，错误 {error_count} 条")
            return result

        except Exception as e:
            self.logger.error(f"标准化现有记录失败: {e}")
            self.db.rollback()
            return {'error': str(e)}

    def _is_comments_standardized(self, comments: str) -> bool:
        """检查审批意见是否已标准化"""
        return '(通过' in comments and ('企业微信审批' in comments or '内部审批' in comments)