#!/usr/bin/env python3
"""
统一审批引擎 - 核心业务逻辑引擎
实现真正的单一审批流程，支持多渠道接入

设计原则：
- 单一数据源，多渠道接入
- 事件驱动架构，松耦合设计
- 状态机保证状态转换合法性
- 渠道感知避免循环同步
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session

# 导入现有组件
from .approval_status_synchronizer import ApprovalStatusSynchronizer
from .approval_record_manager import ApprovalRecordManager
from .unified_approval_service import ApprovalMethod
from .wecom_integration import WeComApprovalIntegration
from ..models import Quote, User


class OperationChannel(Enum):
    """操作渠道枚举"""
    INTERNAL = "internal"     # 内部系统操作
    WECOM = "wecom"          # 企业微信操作
    API = "api"              # API调用
    SYSTEM = "system"        # 系统自动操作


class ApprovalAction(Enum):
    """审批动作枚举"""
    SUBMIT = "submit"         # 提交审批
    APPROVE = "approve"       # 批准
    REJECT = "reject"         # 拒绝
    WITHDRAW = "withdraw"     # 撤回
    DELEGATE = "delegate"     # 委托


class ApprovalStatus(Enum):
    """审批状态枚举"""
    NOT_SUBMITTED = "not_submitted"    # 未提交
    DRAFT = "draft"                    # 草稿
    PENDING = "pending"                # 待审批
    APPROVED = "approved"              # 已批准
    REJECTED = "rejected"              # 已拒绝
    WITHDRAWN = "withdrawn"            # 已撤回


@dataclass
class ApprovalOperation:
    """审批操作数据传输对象"""
    action: ApprovalAction
    quote_id: int
    operator_id: int
    channel: OperationChannel
    comments: Optional[str] = None
    reason: Optional[str] = None
    delegate_to: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ApprovalResult:
    """审批操作结果"""
    success: bool
    message: str
    new_status: ApprovalStatus
    approval_method: ApprovalMethod
    operation_id: Optional[str] = None
    need_notification: bool = True
    sync_required: bool = True


@dataclass
class ApprovalEvent:
    """审批事件数据传输对象"""
    quote_id: int
    action: str
    status: str
    channel: OperationChannel
    user_id: int
    timestamp: datetime = None
    comments: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ApprovalStateMachine:
    """
    审批状态机 - 定义所有合法的状态转换
    确保业务规则的一致性
    """

    # 状态转换规则定义
    ALLOWED_TRANSITIONS = {
        ApprovalStatus.NOT_SUBMITTED: [ApprovalAction.SUBMIT],
        ApprovalStatus.DRAFT: [ApprovalAction.SUBMIT],
        ApprovalStatus.PENDING: [ApprovalAction.APPROVE, ApprovalAction.REJECT, ApprovalAction.WITHDRAW],
        ApprovalStatus.REJECTED: [ApprovalAction.SUBMIT],
        ApprovalStatus.WITHDRAWN: [ApprovalAction.SUBMIT],
        ApprovalStatus.APPROVED: []  # 已批准状态不可变更
    }

    @classmethod
    def validate_transition(cls, from_status: ApprovalStatus, to_status: ApprovalStatus) -> bool:
        """验证状态转换是否合法"""
        # 状态转换映射
        allowed_transitions = {
            ApprovalStatus.NOT_SUBMITTED: [ApprovalStatus.PENDING],
            ApprovalStatus.DRAFT: [ApprovalStatus.PENDING],
            ApprovalStatus.PENDING: [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.WITHDRAWN],
            ApprovalStatus.REJECTED: [ApprovalStatus.PENDING],
            ApprovalStatus.WITHDRAWN: [ApprovalStatus.PENDING],
            ApprovalStatus.APPROVED: []  # 已批准状态不可变更
        }

        allowed = allowed_transitions.get(from_status, [])
        return to_status in allowed

    @classmethod
    def validate_action(cls, current_status: ApprovalStatus, action: ApprovalAction) -> bool:
        """验证在当前状态下动作是否合法"""
        allowed_actions = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return action in allowed_actions

    @classmethod
    def get_next_status(cls, current_status: ApprovalStatus, action: ApprovalAction) -> ApprovalStatus:
        """根据当前状态和动作计算下一个状态"""
        if not cls.validate_action(current_status, action):
            raise ValueError(f"不允许的动作: {current_status} -> {action}")

        # 状态转换映射
        transition_map = {
            ApprovalAction.SUBMIT: ApprovalStatus.PENDING,
            ApprovalAction.APPROVE: ApprovalStatus.APPROVED,
            ApprovalAction.REJECT: ApprovalStatus.REJECTED,
            ApprovalAction.WITHDRAW: ApprovalStatus.WITHDRAWN
        }

        return transition_map[action]


class ApprovalEventBus:
    """
    事件总线 - 处理所有审批相关事件
    实现松耦合的事件驱动架构
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._event_handlers = {}

    def register_handler(self, event_type: str, handler):
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """发布事件"""
        self.logger.info(f"发布事件: {event_type}")

        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                self.logger.error(f"事件处理器执行失败: {e}")

    def publish(self, event: ApprovalEvent) -> bool:
        """发布审批事件"""
        try:
            event_data = {
                'quote_id': event.quote_id,
                'action': event.action,
                'status': event.status,
                'channel': event.channel.value,
                'user_id': event.user_id,
                'timestamp': event.timestamp,
                'comments': event.comments,
                'metadata': event.metadata
            }

            self.publish_event('approval_action', event_data)
            return True
        except Exception as e:
            self.logger.error(f"发布事件失败: {e}")
            return False


class UnifiedApprovalEngine:
    """
    统一审批引擎 - 核心业务逻辑引擎

    职责：
    1. 统一管理所有审批操作
    2. 保证状态转换的一致性
    3. 协调多渠道同步
    4. 发布审批事件
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # 初始化组件
        self.state_machine = ApprovalStateMachine()
        self.event_bus = ApprovalEventBus()
        self.status_synchronizer = ApprovalStatusSynchronizer(db)
        self.record_manager = ApprovalRecordManager(db)
        self.wecom_integration = WeComApprovalIntegration(db)

        # 注册事件处理器
        self._register_event_handlers()

    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_bus.register_handler('approval_submitted', self._handle_approval_submitted)
        self.event_bus.register_handler('approval_approved', self._handle_approval_approved)
        self.event_bus.register_handler('approval_rejected', self._handle_approval_rejected)
        self.event_bus.register_handler('wecom_callback_received', self._handle_wecom_callback)

    def execute_operation(self, operation: ApprovalOperation) -> ApprovalResult:
        """
        执行审批操作 - 统一入口
        这是整个引擎的核心方法
        """
        try:
            self.logger.info(
                f"执行审批操作: {operation.action.value} on quote {operation.quote_id} "
                f"via {operation.channel.value} by user {operation.operator_id}"
            )

            # 1. 数据验证
            self._validate_operation(operation)

            # 2. 权限检查
            self._check_permissions(operation)

            # 3. 状态转换验证
            current_status = self._get_current_approval_status(operation.quote_id)
            if not self.state_machine.validate_action(current_status, operation.action):
                raise ValueError(f"不允许的状态转换: {current_status.value} -> {operation.action.value}")

            # 4. 执行业务逻辑
            result = self._execute_business_logic(operation, current_status)

            # 5. 更新数据库状态
            if result.success:
                new_status = self.state_machine.get_next_status(current_status, operation.action)
                self.status_synchronizer.sync_status_fields(operation.quote_id, new_status)

                # 6. 记录审批历史
                self.record_manager.create_standard_record(
                    quote_id=operation.quote_id,
                    action=operation.action.value,
                    approver_id=operation.operator_id,
                    approval_result=result,
                    comments=operation.comments or operation.reason or "",
                    additional_data={
                        'channel': operation.channel.value,
                        'metadata': operation.metadata
                    }
                )

                # 7. 发布事件
                self._publish_operation_event(operation, result)

            return result

        except Exception as e:
            self.logger.error(f"审批操作执行失败: {e}")
            return ApprovalResult(
                success=False,
                message=f"操作失败: {str(e)}",
                new_status=self._get_current_approval_status(operation.quote_id),
                approval_method=ApprovalMethod.INTERNAL,
                sync_required=False,
                need_notification=False
            )

    def _validate_operation(self, operation: ApprovalOperation):
        """验证操作数据"""
        if not operation.quote_id:
            raise ValueError("报价单ID不能为空")
        if not operation.operator_id:
            raise ValueError("操作人ID不能为空")
        if operation.action == ApprovalAction.REJECT and not (operation.reason or operation.comments):
            raise ValueError("拒绝操作必须提供原因")

    def _check_permissions(self, operation: ApprovalOperation):
        """检查操作权限"""
        quote = self._get_quote(operation.quote_id)
        operator = self.db.query(User).filter(User.id == operation.operator_id).first()

        if not operator:
            raise ValueError("操作人不存在")

        # 提交权限：只有创建者可以提交
        if operation.action == ApprovalAction.SUBMIT:
            if quote.created_by != operation.operator_id:
                raise ValueError("只有创建者可以提交审批")

        # 审批权限：只有管理员可以审批
        elif operation.action in [ApprovalAction.APPROVE, ApprovalAction.REJECT]:
            if operator.role not in ['admin', 'super_admin']:
                raise ValueError("没有审批权限")

        # 撤回权限：只有创建者可以撤回
        elif operation.action == ApprovalAction.WITHDRAW:
            if quote.created_by != operation.operator_id:
                raise ValueError("只有创建者可以撤回审批")

    def _execute_business_logic(self, operation: ApprovalOperation, current_status: ApprovalStatus) -> ApprovalResult:
        """执行具体的业务逻辑"""
        quote = self._get_quote(operation.quote_id)

        if operation.action == ApprovalAction.SUBMIT:
            return self._handle_submit(quote, operation)
        elif operation.action == ApprovalAction.APPROVE:
            return self._handle_approve(quote, operation)
        elif operation.action == ApprovalAction.REJECT:
            return self._handle_reject(quote, operation)
        elif operation.action == ApprovalAction.WITHDRAW:
            return self._handle_withdraw(quote, operation)
        else:
            raise ValueError(f"不支持的操作: {operation.action}")

    def _handle_submit(self, quote: Quote, operation: ApprovalOperation) -> ApprovalResult:
        """处理提交审批"""
        quote.submitted_at = datetime.utcnow()
        quote.submitted_by = operation.operator_id

        # 如果是内部操作，需要同时触发企业微信审批
        approval_method = ApprovalMethod.INTERNAL
        sync_required = False

        if operation.channel == OperationChannel.INTERNAL:
            # 内部提交时，自动创建企业微信审批
            try:
                # 获取创建者信息，避免在异步任务中访问lazy-loaded关系
                creator = self.db.query(User).filter(User.id == quote.created_by).first()
                creator_userid = creator.userid if creator and hasattr(creator, 'userid') else None

                # 异步触发企业微信审批提交（后台任务，不阻塞）
                loop = asyncio.get_event_loop()
                task = loop.create_task(self._trigger_wecom_approval_async(quote.id, creator_userid))
                # 不等待任务完成，让它在后台运行
                # 但我们需要标记为企业微信审批
                approval_method = ApprovalMethod.WECOM  # 标记为企业微信审批
                # 立即更新quote的approval_method（异步任务会更新wecom_approval_id）
                quote.approval_method = 'wecom'
                sync_required = True
                self.logger.info(f"企业微信审批任务已启动: 报价单 {quote.id}, 创建者: {creator_userid}")
            except Exception as e:
                self.logger.error(f"启动企业微信审批任务失败: {e}")
                # 失败时仍然允许内部审批继续
                approval_method = ApprovalMethod.INTERNAL
        elif operation.channel == OperationChannel.WECOM:
            approval_method = ApprovalMethod.WECOM

        return ApprovalResult(
            success=True,
            message="审批已提交",
            new_status=ApprovalStatus.PENDING,
            approval_method=approval_method,
            sync_required=sync_required,
            need_notification=True
        )

    def _handle_approve(self, quote: Quote, operation: ApprovalOperation) -> ApprovalResult:
        """处理批准"""
        quote.approved_at = datetime.utcnow()
        quote.approved_by = operation.operator_id

        # 如果是内部操作，需要通知企业微信
        if operation.channel == OperationChannel.INTERNAL:
            try:
                # 获取创建者企业微信ID
                creator = self.db.query(User).filter(User.id == quote.created_by).first()
                creator_userid = creator.userid if creator and hasattr(creator, 'userid') else None

                # 发送常规通知
                self._trigger_wecom_notification_async(quote.id, "approved", creator_userid)

                # 发送详细的状态更新通知
                operator = self.db.query(User).filter(User.id == operation.operator_id).first()
                operator_name = operator.name if operator else "管理员"

                loop = asyncio.get_event_loop()
                task = loop.create_task(
                    self.wecom_integration.send_approval_status_update_notification(
                        quote.id, "approve", operator_name, operation.comments
                    )
                )
                self.logger.info(f"审批状态更新通知任务已启动: 报价单{quote.id}, 操作人{operator_name}")

            except Exception as e:
                self.logger.error(f"发送企业微信通知失败: {e}")

        return ApprovalResult(
            success=True,
            message="审批已批准",
            new_status=ApprovalStatus.APPROVED,
            approval_method=ApprovalMethod.WECOM if operation.channel == OperationChannel.WECOM else ApprovalMethod.INTERNAL,
            sync_required=(operation.channel != OperationChannel.WECOM),
            need_notification=True
        )

    def _handle_reject(self, quote: Quote, operation: ApprovalOperation) -> ApprovalResult:
        """处理拒绝"""
        quote.rejection_reason = operation.reason or operation.comments
        quote.approved_at = datetime.utcnow()  # 拒绝也算是审批完成
        quote.approved_by = operation.operator_id

        # 如果是内部操作，需要通知企业微信
        if operation.channel == OperationChannel.INTERNAL:
            try:
                # 获取创建者企业微信ID
                creator = self.db.query(User).filter(User.id == quote.created_by).first()
                creator_userid = creator.userid if creator and hasattr(creator, 'userid') else None

                # 发送常规通知
                self._trigger_wecom_notification_async(quote.id, "rejected", creator_userid)

                # 发送详细的状态更新通知
                operator = self.db.query(User).filter(User.id == operation.operator_id).first()
                operator_name = operator.name if operator else "管理员"

                # 构建拒绝原因的详细信息
                reject_details = operation.reason
                if operation.comments and operation.comments != operation.reason:
                    reject_details += f" | {operation.comments}"

                loop = asyncio.get_event_loop()
                task = loop.create_task(
                    self.wecom_integration.send_approval_status_update_notification(
                        quote.id, "reject", operator_name, reject_details
                    )
                )
                self.logger.info(f"审批状态更新通知任务已启动: 报价单{quote.id}, 操作人{operator_name}")

            except Exception as e:
                self.logger.error(f"发送企业微信通知失败: {e}")

        return ApprovalResult(
            success=True,
            message="审批已拒绝",
            new_status=ApprovalStatus.REJECTED,
            approval_method=ApprovalMethod.WECOM if operation.channel == OperationChannel.WECOM else ApprovalMethod.INTERNAL,
            sync_required=(operation.channel != OperationChannel.WECOM),
            need_notification=True
        )

    def _handle_withdraw(self, quote: Quote, operation: ApprovalOperation) -> ApprovalResult:
        """处理撤回"""
        return ApprovalResult(
            success=True,
            message="审批已撤回",
            new_status=ApprovalStatus.WITHDRAWN,
            sync_required=(operation.channel != OperationChannel.WECOM),
            need_notification=True
        )

    def _get_quote(self, quote_id: int) -> Quote:
        """获取报价单"""
        quote = self.db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.is_deleted == False
        ).first()

        if not quote:
            raise ValueError(f"报价单不存在: {quote_id}")

        return quote

    def _get_current_approval_status(self, quote_id: int) -> ApprovalStatus:
        """获取当前审批状态"""
        quote = self._get_quote(quote_id)
        return ApprovalStatus(quote.approval_status or "draft")

    def _publish_operation_event(self, operation: ApprovalOperation, result: ApprovalResult):
        """发布操作事件"""
        event_data = {
            'quote_id': operation.quote_id,
            'action': operation.action.value,
            'operator_id': operation.operator_id,
            'channel': operation.channel.value,
            'result': result,
            'timestamp': datetime.utcnow()
        }

        # 根据操作类型发布不同事件
        event_map = {
            ApprovalAction.SUBMIT: 'approval_submitted',
            ApprovalAction.APPROVE: 'approval_approved',
            ApprovalAction.REJECT: 'approval_rejected',
            ApprovalAction.WITHDRAW: 'approval_withdrawn'
        }

        event_type = event_map.get(operation.action, 'approval_operation')
        self.event_bus.publish_event(event_type, event_data)

    # 事件处理器
    def _handle_approval_submitted(self, event_data: Dict[str, Any]):
        """处理审批提交事件"""
        self.logger.info(f"处理审批提交事件: 报价单 {event_data['quote_id']}")
        # 这里可以添加通知逻辑、企微同步等

    def _handle_approval_approved(self, event_data: Dict[str, Any]):
        """处理审批批准事件"""
        self.logger.info(f"处理审批批准事件: 报价单 {event_data['quote_id']}")
        # 这里可以添加通知逻辑、状态同步等

    def _handle_approval_rejected(self, event_data: Dict[str, Any]):
        """处理审批拒绝事件"""
        self.logger.info(f"处理审批拒绝事件: 报价单 {event_data['quote_id']}")
        # 这里可以添加通知逻辑、状态同步等

    def _handle_wecom_callback(self, event_data: Dict[str, Any]):
        """处理企业微信回调事件"""
        self.logger.info(f"处理企业微信回调事件: {event_data}")
        # 这里处理企业微信回调，转换为内部操作

    def handle_wecom_callback(self, sp_no: str, status: int, operator_info: Dict[str, Any]) -> ApprovalResult:
        """
        处理企业微信审批回调
        确保企业微信的操作同步到内部系统
        """
        try:
            # 查找对应的报价单
            quote = self.db.query(Quote).filter(
                Quote.wecom_approval_id == sp_no,
                Quote.is_deleted == False
            ).first()

            if not quote:
                raise ValueError(f"未找到对应的报价单: {sp_no}")

            # 转换企业微信状态
            if status == 2:  # 已同意
                action = ApprovalAction.APPROVE
            elif status == 3:  # 已拒绝
                action = ApprovalAction.REJECT
            else:
                return ApprovalResult(
                    success=True,
                    message=f"忽略中间状态: {status}",
                    new_status=self._get_current_approval_status(quote.id),
                    sync_required=False
                )

            # 创建操作对象
            operation = ApprovalOperation(
                action=action,
                quote_id=quote.id,
                operator_id=self._get_or_create_wecom_user(operator_info),
                channel=OperationChannel.WECOM,
                comments=operator_info.get('comments', ''),
                metadata={'wecom_callback': True, 'sp_no': sp_no, 'original_status': status}
            )

            # 执行操作（不会再次同步到企业微信）
            return self.execute_operation(operation)

        except Exception as e:
            self.logger.error(f"处理企业微信回调失败: {e}")
            raise

    async def sync_from_wecom_status_change(self, sp_no: str, new_status: str, operator_info: Dict = None) -> bool:
        """
        处理企业微信审批状态变化，同步到内部系统

        Args:
            sp_no: 企业微信审批单号
            new_status: 新状态 (approved, rejected, cancelled)
            operator_info: 操作人信息

        Returns:
            同步是否成功
        """
        try:
            self.logger.info(f"开始同步企业微信状态变化: sp_no={sp_no}, new_status={new_status}")

            # 查找对应的报价单
            quote = self.db.query(Quote).filter(
                Quote.wecom_approval_id == sp_no,
                Quote.is_deleted == False
            ).first()

            if not quote:
                self.logger.error(f"未找到对应的报价单: wecom_approval_id={sp_no}")
                return False

            # 检查状态是否需要更新
            if quote.approval_status == new_status:
                self.logger.info(f"报价单 {quote.id} 状态已是 {new_status}，无需更新")
                return True

            # 获取操作人ID（企业微信操作人映射到内部用户）
            operator_id = self._get_or_create_wecom_user(operator_info or {})

            # 构建统一审批操作
            action_mapping = {
                'approved': ApprovalAction.APPROVE,
                'rejected': ApprovalAction.REJECT,
                'cancelled': ApprovalAction.WITHDRAW
            }

            action = action_mapping.get(new_status)
            if not action:
                self.logger.error(f"不支持的状态: {new_status}")
                return False

            operation = ApprovalOperation(
                action=action,
                quote_id=quote.id,
                operator_id=operator_id,
                channel=OperationChannel.WECOM,  # 标记为企业微信渠道
                comments=f"企业微信审批同步: {new_status}",
                metadata={'wecom_sync': True, 'sp_no': sp_no}
            )

            # 执行统一审批操作（这会触发所有必要的状态更新和通知）
            result = self.execute_operation(operation)

            if result.success:
                self.logger.info(f"企业微信状态同步成功: 报价单 {quote.id} -> {new_status}")
                return True
            else:
                self.logger.error(f"企业微信状态同步失败: {result.message}")
                return False

        except Exception as e:
            self.logger.error(f"企业微信状态同步异常: {e}")
            return False

    def _get_or_create_wecom_user(self, operator_info: Dict[str, Any]) -> int:
        """获取或创建企业微信用户对应的内部用户"""
        # 这里应该实现用户映射逻辑
        # 临时返回系统用户ID
        return 1

    def get_approval_status_info(self, quote_id: int) -> Dict[str, Any]:
        """获取报价单的完整审批状态信息"""
        quote = self._get_quote(quote_id)

        return {
            "quote_id": quote.id,
            "quote_number": quote.quote_number,
            "approval_status": quote.approval_status,
            "approval_method": quote.approval_method,
            "submitted_at": quote.submitted_at,
            "approved_at": quote.approved_at,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "has_wecom_integration": bool(quote.wecom_approval_id),
            "current_status_enum": self._get_current_approval_status(quote_id),
            "available_actions": self._get_available_actions(quote, quote_id)
        }

    def _get_available_actions(self, quote: Quote, quote_id: int) -> List[str]:
        """获取当前可执行的操作"""
        current_status = self._get_current_approval_status(quote_id)
        allowed_actions = self.state_machine.ALLOWED_TRANSITIONS.get(current_status, [])
        return [action.value for action in allowed_actions]

    # === 企业微信集成辅助方法 ===

    async def _trigger_wecom_approval_async(self, quote_id: int, creator_userid: str = None):
        """
        异步触发企业微信审批提交
        在内部提交审批时自动创建企业微信审批
        """
        try:
            self.logger.info(f"开始触发企业微信审批: 报价单 {quote_id}, 创建者userid: {creator_userid}")

            # 获取报价单信息（不需要访问lazy-loaded关系）
            quote = self._get_quote(quote_id)
            self.logger.info(f"报价单 {quote_id} 信息: quote_number={quote.quote_number}")

            # 检查企业微信用户ID
            if creator_userid:
                self.logger.info(f"找到创建者企业微信ID: {creator_userid}，开始提交企业微信审批")

                # 直接调用企业微信集成服务的异步方法
                try:
                    self.logger.info("调用企业微信集成服务...")
                    result = await self.wecom_integration.submit_quote_approval(quote_id, creator_userid=creator_userid)
                    self.logger.info(f"企业微信审批提交成功: {result}")

                    # 保存企业微信审批ID到数据库
                    if result.get('success') and result.get('sp_no'):
                        # 重新获取quote以确保session正确
                        fresh_quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
                        if fresh_quote:
                            fresh_quote.wecom_approval_id = result['sp_no']
                            fresh_quote.approval_method = 'wecom'  # 标记为企业微信审批
                            self.db.commit()
                            self.logger.info(f"已保存企业微信审批ID: {result['sp_no']} 到报价单 {quote_id}")
                        else:
                            self.logger.error(f"无法找到报价单 {quote_id} 来保存企业微信审批ID")
                    else:
                        self.logger.warning(f"企业微信审批提交成功但未返回sp_no: {result}")

                    return True
                except Exception as wecom_error:
                    self.logger.error(f"企业微信集成服务调用失败: {wecom_error}")
                    raise wecom_error
            else:
                error_msg = f"报价单 {quote_id} 的创建者缺少企业微信用户ID"
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

        except Exception as e:
            self.logger.error(f"触发企业微信审批失败: {e}")
            raise

    def _trigger_wecom_notification_async(self, quote_id: int, notification_type: str, recipient_userid: str = None):
        """
        异步触发企业微信通知
        在内部审批操作时发送企业微信通知
        """
        try:
            self.logger.info(f"触发企业微信通知: 报价单{quote_id}, 类型{notification_type}, 接收人{recipient_userid}")

            if recipient_userid:
                # 使用后台任务发送企业微信通知
                try:
                    loop = asyncio.get_event_loop()
                    task = loop.create_task(
                        self._send_wecom_notification_task(quote_id, recipient_userid, notification_type)
                    )
                    self.logger.info(f"企业微信通知任务已启动: 报价单{quote_id}, 类型{notification_type}")
                except Exception as e:
                    self.logger.error(f"启动企业微信通知任务失败: {e}")
            else:
                self.logger.warning(f"无法发送企业微信通知: 找不到接收人用户ID, 报价单{quote_id}")

        except Exception as e:
            self.logger.error(f"发送企业微信通知失败: {e}")
            # 通知失败不应该影响主要的审批流程

    async def _send_wecom_notification_task(self, quote_id: int, recipient_userid: str, notification_type: str):
        """异步发送企业微信通知任务"""
        try:
            success = await self.wecom_integration.send_approval_notification(
                quote_id, recipient_userid, notification_type
            )
            if success:
                self.logger.info(f"企业微信通知发送成功: 报价单{quote_id}, 类型{notification_type}")
            else:
                self.logger.warning(f"企业微信通知发送失败: 报价单{quote_id}, 类型{notification_type}")
        except Exception as e:
            self.logger.error(f"企业微信通知发送异常: {e}")