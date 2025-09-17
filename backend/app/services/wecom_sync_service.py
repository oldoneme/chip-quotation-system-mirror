#!/usr/bin/env python3
"""
企业微信双向同步服务 V2
基于统一审批引擎，实现真正的双向同步机制

设计原则：
- 智能渠道感知，避免循环同步
- 事件驱动架构，松耦合设计
- 幂等性保证，支持重试机制
- 状态追踪和日志记录
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session

# 导入统一审批引擎
from .approval_engine import (
    UnifiedApprovalEngine,
    ApprovalEvent,
    ApprovalOperation,
    ApprovalAction,
    ApprovalStatus,
    OperationChannel
)
from .wecom_integration import WeComApprovalIntegration
from ..models import Quote, ApprovalRecord
from ..database import SessionLocal


class SyncDirection(Enum):
    """同步方向枚举"""
    TO_WECOM = "to_wecom"       # 内部 → 企微
    FROM_WECOM = "from_wecom"   # 企微 → 内部
    BIDIRECTIONAL = "bidirectional"  # 双向


class SyncStatus(Enum):
    """同步状态枚举"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SyncOperation:
    """同步操作数据传输对象"""
    quote_id: int
    direction: SyncDirection
    operation_type: str  # submit, approve, reject, etc.
    source_channel: OperationChannel
    target_channel: OperationChannel
    data: Dict
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    status: SyncStatus
    message: str
    sync_id: Optional[str] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None


class WeComBidirectionalSyncService:
    """
    企业微信双向同步服务

    核心功能：
    1. 监听统一审批引擎的事件
    2. 智能判断同步方向和策略
    3. 处理企业微信回调事件
    4. 防止循环同步
    """

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.logger = logging.getLogger(__name__)

        # 初始化统一审批引擎
        self.approval_engine = UnifiedApprovalEngine(self.db)

        # 初始化企微集成服务
        self.wecom_service = WeComApprovalIntegration(self.db)

        # 同步状态追踪
        self._sync_operations: Dict[str, SyncOperation] = {}
        self._processing_quotes: Set[int] = set()

        # 注册事件处理器
        self._register_event_handlers()

    def _register_event_handlers(self):
        """注册统一审批引擎的事件处理器"""
        event_bus = self.approval_engine.event_bus

        # 注册审批动作事件处理器
        event_bus.register_handler('approval_action', self._handle_approval_event)

        self.logger.info("企微双向同步服务事件处理器已注册")

    async def _handle_approval_event(self, event_data: Dict):
        """
        处理审批事件，决定是否需要同步到企业微信

        Args:
            event_data: 审批事件数据
        """
        try:
            quote_id = event_data.get('quote_id')
            action = event_data.get('action')
            channel = event_data.get('channel')

            # 渠道感知：如果事件来自企微，不再同步回企微
            if channel == OperationChannel.WECOM.value:
                self.logger.info(f"事件来自企微渠道，跳过同步: quote_id={quote_id}")
                return

            # 避免重复处理
            if quote_id in self._processing_quotes:
                self.logger.warning(f"报价单 {quote_id} 正在处理中，跳过重复同步")
                return

            self._processing_quotes.add(quote_id)

            try:
                # 创建同步操作
                sync_op = SyncOperation(
                    quote_id=quote_id,
                    direction=SyncDirection.TO_WECOM,
                    operation_type=action,
                    source_channel=OperationChannel.INTERNAL,
                    target_channel=OperationChannel.WECOM,
                    data=event_data
                )

                # 执行同步
                result = await self._execute_sync_operation(sync_op)

                if result.success:
                    self.logger.info(f"同步成功: quote_id={quote_id}, action={action}")
                else:
                    self.logger.error(f"同步失败: quote_id={quote_id}, error={result.message}")

                    # 失败重试机制
                    if sync_op.retry_count < sync_op.max_retries:
                        await self._schedule_retry(sync_op)

            finally:
                self._processing_quotes.discard(quote_id)

        except Exception as e:
            self.logger.error(f"处理审批事件失败: {e}")

    async def _execute_sync_operation(self, sync_op: SyncOperation) -> SyncResult:
        """
        执行同步操作

        Args:
            sync_op: 同步操作对象

        Returns:
            同步结果
        """
        try:
            quote_id = sync_op.quote_id
            operation_type = sync_op.operation_type

            # 获取报价单
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message=f"报价单不存在: {quote_id}",
                    error_code="QUOTE_NOT_FOUND"
                )

            # 根据操作类型执行不同的同步逻辑
            if operation_type == 'submit':
                return await self._sync_submit_to_wecom(quote, sync_op)
            elif operation_type == 'approve':
                return await self._sync_approve_to_wecom(quote, sync_op)
            elif operation_type == 'reject':
                return await self._sync_reject_to_wecom(quote, sync_op)
            elif operation_type == 'withdraw':
                return await self._sync_withdraw_to_wecom(quote, sync_op)
            else:
                return SyncResult(
                    success=False,
                    status=SyncStatus.SKIPPED,
                    message=f"不支持的操作类型: {operation_type}"
                )

        except Exception as e:
            self.logger.error(f"执行同步操作失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"同步执行异常: {str(e)}",
                error_code="SYNC_EXECUTION_ERROR"
            )

    async def _sync_submit_to_wecom(self, quote: Quote, sync_op: SyncOperation) -> SyncResult:
        """同步提交操作到企业微信"""
        try:
            # 如果已有企微审批ID，跳过
            if quote.wecom_approval_id:
                return SyncResult(
                    success=True,
                    status=SyncStatus.SKIPPED,
                    message="已存在企微审批ID，跳过提交"
                )

            # 提交到企业微信
            user_id = sync_op.data.get('user_id', 1)  # 默认用户ID
            sp_no = self.wecom_service.submit_quote_approval(quote.id, user_id)

            # 更新报价单的企微审批ID
            quote.wecom_approval_id = sp_no
            self.db.commit()

            return SyncResult(
                success=True,
                status=SyncStatus.SUCCESS,
                message=f"成功提交到企微，审批ID: {sp_no}",
                sync_id=sp_no
            )

        except Exception as e:
            self.logger.error(f"同步提交到企微失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"提交同步失败: {str(e)}"
            )

    async def _sync_approve_to_wecom(self, quote: Quote, sync_op: SyncOperation) -> SyncResult:
        """同步批准操作到企业微信"""
        try:
            if not quote.wecom_approval_id:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message="无企微审批ID，无法同步批准操作"
                )

            # 调用企微API批准
            user_id = sync_op.data.get('user_id', 1)
            comments = sync_op.data.get('comments', '系统同步批准')

            result = self.wecom_service.approve_quote(quote.id, user_id, comments)

            return SyncResult(
                success=True,
                status=SyncStatus.SUCCESS,
                message="成功同步批准到企微",
                sync_id=quote.wecom_approval_id
            )

        except Exception as e:
            self.logger.error(f"同步批准到企微失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"批准同步失败: {str(e)}"
            )

    async def _sync_reject_to_wecom(self, quote: Quote, sync_op: SyncOperation) -> SyncResult:
        """同步拒绝操作到企业微信"""
        try:
            if not quote.wecom_approval_id:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message="无企微审批ID，无法同步拒绝操作"
                )

            # 调用企微API拒绝
            user_id = sync_op.data.get('user_id', 1)
            reason = sync_op.data.get('reason', '系统同步拒绝')

            result = self.wecom_service.reject_quote(quote.id, user_id, reason)

            return SyncResult(
                success=True,
                status=SyncStatus.SUCCESS,
                message="成功同步拒绝到企微",
                sync_id=quote.wecom_approval_id
            )

        except Exception as e:
            self.logger.error(f"同步拒绝到企微失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"拒绝同步失败: {str(e)}"
            )

    async def _sync_withdraw_to_wecom(self, quote: Quote, sync_op: SyncOperation) -> SyncResult:
        """同步撤回操作到企业微信"""
        try:
            if not quote.wecom_approval_id:
                return SyncResult(
                    success=True,
                    status=SyncStatus.SKIPPED,
                    message="无企微审批ID，跳过撤回同步"
                )

            # 企微撤回逻辑（如果API支持）
            # 注：企微API可能不支持撤回，这里做兼容处理

            return SyncResult(
                success=True,
                status=SyncStatus.SUCCESS,
                message="撤回操作已处理"
            )

        except Exception as e:
            self.logger.error(f"同步撤回到企微失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"撤回同步失败: {str(e)}"
            )

    async def handle_wecom_callback(self, callback_data: Dict) -> SyncResult:
        """
        处理企业微信回调事件

        Args:
            callback_data: 企微回调数据

        Returns:
            处理结果
        """
        try:
            sp_no = callback_data.get('sp_no')
            sp_status = callback_data.get('sp_status')

            if not sp_no:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message="回调数据缺少审批单号"
                )

            # 查找对应的报价单
            quote = self.db.query(Quote).filter(Quote.wecom_approval_id == sp_no).first()
            if not quote:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message=f"未找到对应的报价单: {sp_no}"
                )

            # 避免重复处理
            if quote.id in self._processing_quotes:
                self.logger.warning(f"报价单 {quote.id} 正在处理中，跳过回调")
                return SyncResult(
                    success=True,
                    status=SyncStatus.SKIPPED,
                    message="报价单正在处理中"
                )

            self._processing_quotes.add(quote.id)

            try:
                # 根据企微状态更新内部状态
                result = await self._update_internal_status_from_wecom(quote, sp_status, callback_data)
                return result

            finally:
                self._processing_quotes.discard(quote.id)

        except Exception as e:
            self.logger.error(f"处理企微回调失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"回调处理异常: {str(e)}"
            )

    async def _update_internal_status_from_wecom(self, quote: Quote, sp_status: int, callback_data: Dict) -> SyncResult:
        """
        根据企微状态更新内部状态

        Args:
            quote: 报价单对象
            sp_status: 企微审批状态 (1=审批中, 2=已同意, 3=已拒绝, 4=已撤销)
            callback_data: 回调数据
        """
        try:
            # 状态映射
            status_map = {
                1: (ApprovalStatus.PENDING, ApprovalAction.SUBMIT),
                2: (ApprovalStatus.APPROVED, ApprovalAction.APPROVE),
                3: (ApprovalStatus.REJECTED, ApprovalAction.REJECT),
                4: (ApprovalStatus.WITHDRAWN, ApprovalAction.WITHDRAW)
            }

            if sp_status not in status_map:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message=f"未知的企微状态: {sp_status}"
                )

            target_status, action = status_map[sp_status]

            # 如果状态没变化，跳过
            current_status = getattr(ApprovalStatus, quote.status.upper(), None)
            if current_status == target_status:
                return SyncResult(
                    success=True,
                    status=SyncStatus.SKIPPED,
                    message="状态无变化，跳过更新"
                )

            # 创建审批操作（标记来源为企微）
            operation = ApprovalOperation(
                action=action,
                quote_id=quote.id,
                operator_id=callback_data.get('operator_id', 1),
                channel=OperationChannel.WECOM,  # 重要：标记来源为企微
                comments=f"企微回调同步: {callback_data.get('comment', '')}"
            )

            # 通过统一审批引擎执行操作
            result = self.approval_engine.execute_operation(operation)

            if result.success:
                return SyncResult(
                    success=True,
                    status=SyncStatus.SUCCESS,
                    message=f"成功从企微同步状态: {target_status.value}"
                )
            else:
                return SyncResult(
                    success=False,
                    status=SyncStatus.FAILED,
                    message=f"状态同步失败: {result.message}"
                )

        except Exception as e:
            self.logger.error(f"更新内部状态失败: {e}")
            return SyncResult(
                success=False,
                status=SyncStatus.FAILED,
                message=f"状态更新异常: {str(e)}"
            )

    async def _schedule_retry(self, sync_op: SyncOperation):
        """安排重试同步操作"""
        sync_op.retry_count += 1
        retry_delay = min(2 ** sync_op.retry_count, 60)  # 指数退避，最大60秒

        self.logger.info(f"安排重试同步: quote_id={sync_op.quote_id}, "
                        f"retry={sync_op.retry_count}, delay={retry_delay}s")

        # 简单的延迟重试（生产环境可以使用任务队列）
        await asyncio.sleep(retry_delay)
        await self._execute_sync_operation(sync_op)

    async def sync_pending_quotes(self) -> Dict[str, int]:
        """
        同步所有待处理的报价单

        Returns:
            同步结果统计
        """
        try:
            # 查询待同步的报价单
            pending_quotes = self.db.query(Quote).filter(
                Quote.status == 'pending',
                Quote.wecom_approval_id.isnot(None)
            ).all()

            stats = {
                'total': len(pending_quotes),
                'success': 0,
                'failed': 0,
                'skipped': 0
            }

            for quote in pending_quotes:
                try:
                    # 查询企微状态
                    approval_detail = await self.wecom_service.get_approval_detail(quote.wecom_approval_id)

                    if approval_detail and approval_detail.get('errcode') == 0:
                        sp_status = approval_detail.get('info', {}).get('sp_status')

                        if sp_status and sp_status != 1:  # 状态有变化
                            result = await self._update_internal_status_from_wecom(
                                quote, sp_status, approval_detail.get('info', {})
                            )

                            if result.success:
                                stats['success'] += 1
                            else:
                                stats['failed'] += 1
                        else:
                            stats['skipped'] += 1
                    else:
                        stats['failed'] += 1

                except Exception as e:
                    self.logger.error(f"同步报价单 {quote.id} 失败: {e}")
                    stats['failed'] += 1

                # 避免请求过快
                await asyncio.sleep(0.5)

            return stats

        except Exception as e:
            self.logger.error(f"批量同步失败: {e}")
            return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

    def close(self):
        """关闭服务，清理资源"""
        self.db.close()
        self.logger.info("企微双向同步服务已关闭")


# 全局同步服务实例
_sync_service_instance = None

def get_sync_service() -> WeComBidirectionalSyncService:
    """获取同步服务单例"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = WeComBidirectionalSyncService()
    return _sync_service_instance


async def run_sync_daemon():
    """运行同步守护进程"""
    sync_service = get_sync_service()

    try:
        while True:
            print(f"\n{'='*60}")
            print(f"开始双向同步 - {datetime.now()}")

            stats = await sync_service.sync_pending_quotes()

            print(f"同步完成: 总计 {stats['total']} 个, "
                  f"成功 {stats['success']} 个, "
                  f"失败 {stats['failed']} 个, "
                  f"跳过 {stats['skipped']} 个")
            print(f"{'='*60}\n")

            # 每30秒同步一次
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n双向同步服务已停止")
    finally:
        sync_service.close()


if __name__ == "__main__":
    # 可以直接运行此文件来启动同步守护进程
    asyncio.run(run_sync_daemon())