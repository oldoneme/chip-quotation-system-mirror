"""
企业微信审批状态自动同步服务
主动查询企业微信审批状态并更新本地数据库
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from ..models import Quote, ApprovalRecord
from ..database import SessionLocal
from .wecom_integration import WeComApprovalIntegration


class WeComApprovalSyncService:
    """企业微信审批状态同步服务"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.wecom_service = WeComApprovalIntegration(self.db)
        
    async def sync_approval_status(self, quote_id: int) -> bool:
        """
        同步单个报价单的审批状态
        
        Args:
            quote_id: 报价单ID
            
        Returns:
            是否同步成功
        """
        try:
            # 获取报价单
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote or not quote.wecom_approval_id:
                print(f"报价单不存在或无企业微信审批ID: {quote_id}")
                return False
            
            # 只同步pending状态的报价单
            if quote.status not in ['pending']:
                print(f"报价单 {quote.quote_number} 状态为 {quote.status}，无需同步")
                return True  # 不需要同步
            
            print(f"尝试同步报价单 {quote.quote_number} (审批ID: {quote.wecom_approval_id})")
            
            try:
                # 查询企业微信审批详情
                approval_detail = await self.wecom_service.get_approval_detail(quote.wecom_approval_id)
                
                if not approval_detail or approval_detail.get('errcode') != 0:
                    print(f"获取审批详情失败: {approval_detail}")
                    return False
                
                # 解析审批状态
                sp_status = approval_detail.get('info', {}).get('sp_status')
                
                # 映射状态: 1=审批中, 2=已同意, 3=已拒绝, 4=已撤销
                status_mapping = {
                    1: ('pending', 'pending'),
                    2: ('approved', 'approved'),
                    3: ('rejected', 'rejected'),
                    4: ('draft', 'cancelled')
                }
                
                new_status, new_approval_status = status_mapping.get(sp_status, (None, None))
                
                if new_status and new_status != quote.status:
                    # 状态有变化，更新数据库
                    print(f"检测到状态变化: {quote.quote_number} 从 {quote.status} 变为 {new_status}")
                    
                    quote.status = new_status
                    quote.approval_status = new_approval_status
                    
                    if new_status == 'approved':
                        quote.approved_at = datetime.now()
                        quote.approved_by = None  # TODO: 从审批详情中获取审批人
                    elif new_status == 'rejected':
                        quote.approved_at = datetime.now()
                        # 获取拒绝原因
                        comments = approval_detail.get('info', {}).get('comment', [])
                        if comments:
                            quote.rejection_reason = comments[0].get('content', '审批被拒绝')
                    
                    # 记录审批记录
                    try:
                        from sqlalchemy import text
                        self.db.execute(text("""
                            INSERT INTO approval_records 
                            (quote_id, action, status, comments, wecom_approval_id, wecom_sp_no, 
                             step_order, is_final_step, created_at) 
                            VALUES 
                            (:quote_id, :action, :status, :comments, :wecom_approval_id, :wecom_sp_no,
                             :step_order, :is_final_step, :created_at)
                        """), {
                            'quote_id': quote.id,
                            'action': new_status,
                            'status': 'completed',
                            'comments': f'自动同步自企业微信 - {new_status}',
                            'wecom_approval_id': quote.wecom_approval_id,
                            'wecom_sp_no': quote.wecom_approval_id,
                            'step_order': 1,
                            'is_final_step': True,
                            'created_at': datetime.now()
                        })
                    except Exception as e:
                        print(f"创建审批记录失败: {e}")
                    
                    self.db.commit()
                    print(f"✅ 成功同步状态: {quote.quote_number} -> {new_status}")
                    return True
                else:
                    print(f"报价单 {quote.quote_number} 状态无变化: {quote.status}")
                    return True
                    
            except Exception as api_error:
                # 处理API权限错误
                error_msg = str(api_error)
                if "no approval auth" in error_msg or "301055" in error_msg:
                    print(f"❌ 企业微信审批API权限不足: {quote.quote_number}")
                    print("建议：配置企业微信应用审批权限或使用手动同步")
                    return False
                else:
                    print(f"❌ 企业微信API调用失败: {error_msg}")
                    return False
            
        except Exception as e:
            print(f"同步审批状态失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return False
    
    async def sync_all_pending_quotes(self) -> Dict[str, int]:
        """
        同步所有待审批的报价单
        
        Returns:
            同步结果统计
        """
        try:
            # 查询所有pending状态的报价单
            pending_quotes = self.db.query(Quote).filter(
                Quote.status == 'pending',
                Quote.wecom_approval_id.isnot(None)
            ).all()
            
            print(f"找到 {len(pending_quotes)} 个待同步的报价单")
            
            success_count = 0
            failed_count = 0
            
            for quote in pending_quotes:
                print(f"同步报价单: {quote.quote_number}")
                if await self.sync_approval_status(quote.id):
                    success_count += 1
                else:
                    failed_count += 1
                
                # 避免请求过快
                await asyncio.sleep(0.5)
            
            return {
                'total': len(pending_quotes),
                'success': success_count,
                'failed': failed_count
            }
            
        except Exception as e:
            print(f"批量同步失败: {str(e)}")
            return {'total': 0, 'success': 0, 'failed': 0}
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


async def run_sync_service():
    """运行同步服务（可以作为定时任务）"""
    sync_service = WeComApprovalSyncService()
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"开始同步企业微信审批状态 - {datetime.now()}")
            
            result = await sync_service.sync_all_pending_quotes()
            
            print(f"同步完成: 总计 {result['total']} 个, 成功 {result['success']} 个, 失败 {result['failed']} 个")
            print(f"{'='*60}\n")
            
            # 每30秒同步一次
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n同步服务已停止")
    finally:
        sync_service.close()


if __name__ == "__main__":
    # 可以直接运行此文件来启动同步服务
    asyncio.run(run_sync_service())