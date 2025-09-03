from typing import Dict, Any
from ..models import Quote
import logging

logger = logging.getLogger(__name__)

class OutboxService:
    """外部副作用处理服务 - MVP简化版本"""
    
    def __init__(self):
        self.handlers = {
            "notify_submit": self._handle_notify_submit,
            "notify_approved": self._handle_notify_approved,
            "generate_export": self._handle_generate_export
        }
    
    def add(self, job_type: str, payload: Dict[str, Any]):
        """添加任务到outbox - MVP阶段直接执行"""
        try:
            if job_type in self.handlers:
                self.handlers[job_type](payload)
            else:
                logger.warning(f"未知的任务类型: {job_type}")
        except Exception as e:
            logger.error(f"处理外部任务失败: {job_type}, {e}")
    
    def _handle_notify_submit(self, payload: Dict[str, Any]):
        """处理提交审批通知"""
        quote_id = payload.get("quote_id")
        instance_id = payload.get("instance_id")
        logger.info(f"审批已提交: quote_id={quote_id}, instance_id={instance_id}")
        # TODO: 发送通知给相关人员
    
    def _handle_notify_approved(self, payload: Dict[str, Any]):
        """处理审批通过通知"""
        quote_id = payload.get("quote_id")
        export_url = payload.get("export_url")
        logger.info(f"审批已通过: quote_id={quote_id}, export_url={export_url}")
        # TODO: 通知申请人和相关人员
    
    def _handle_generate_export(self, payload: Dict[str, Any]):
        """处理导出文件生成"""
        quote_id = payload.get("quote_id")
        logger.info(f"生成导出文件: quote_id={quote_id}")
        # TODO: 异步生成导出文件

# 全局实例
outbox = OutboxService()