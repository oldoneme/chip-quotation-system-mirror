"""
报价单审批触发器
自动创建企业微信审批并发送通知
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime

from ....database import get_db
from ....services.wecom_integration import WeComApprovalIntegration
from ....auth import get_current_user
from ....models import User, Quote

router = APIRouter(prefix="/quote-approval", tags=["报价审批触发"])


@router.post("/submit/{quote_id}")
async def submit_quote_for_approval(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交报价单到企业微信审批
    使用模板预设的审批人，简化流程
    """
    # 获取报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")
    
    # 检查是否可以提交审批
    # 可以提交的状态：draft(草稿), rejected(被驳回)
    # 不能提交的状态：approved(已批准), pending(审批中)
    if quote.status not in ['draft', 'rejected']:
        if quote.status == 'approved':
            raise HTTPException(
                status_code=400, 
                detail="报价单已批准，无需重复提交审批"
            )
        elif quote.status == 'pending':
            raise HTTPException(
                status_code=400, 
                detail="报价单正在审批中，请等待审批结果"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"当前状态不允许提交审批：{quote.status}"
            )
    
    # 检查审批状态是否允许重新提交
    allowed_approval_statuses = [None, "draft", "not_submitted", "rejected", "pending"]
    if hasattr(quote, 'approval_status') and quote.approval_status not in allowed_approval_statuses:
        # 只有approved状态才真正不能重新提交
        if quote.approval_status == "approved":
            raise HTTPException(
                status_code=400, 
                detail="报价单已通过审批，无需重复提交"
            )
    
    # 如果是被驳回的报价单重新提交，清理之前的驳回信息但保持rejected状态
    if quote.status == 'rejected':
        quote.rejection_reason = None
        quote.rejected_at = None
        # 保持rejected状态，只更新审批状态为pending
        # quote.status 保持为 'rejected'，不改变
        quote.approval_status = 'pending'  # 更新为待审批状态
    
    # 初始化企业微信服务
    wecom_service = WeComApprovalIntegration(db)
    
    try:
        # 提交企业微信审批
        result = await wecom_service.submit_quote_approval(quote_id)
        
        # 更新报价单状态 - 只更新审批状态，不改变quote.status
        if hasattr(quote, 'approval_status'):
            quote.approval_status = "pending"
        # 更新状态为pending，不管之前是什么状态
        quote.status = 'pending'
        if hasattr(quote, 'submitted_at'):
            quote.submitted_at = datetime.now()
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交审批失败: {str(e)}")


@router.post("/batch-submit")
async def batch_submit_for_approval(
    quote_ids: List[int],
    approver_userid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量提交报价单审批
    """
    results = []
    wecom_service = WeComApprovalIntegration(db)
    
    for quote_id in quote_ids:
        try:
            # 创建审批
            approval_result = await wecom_service.create_approval(
                quote_id=quote_id,
                approver_userid=approver_userid
            )
            
            # 更新状态
            quote = db.query(Quote).filter(Quote.id == quote_id).first()
            if quote:
                quote.status = "pending"
                quote.approval_status = "pending"
                
            results.append({
                "quote_id": quote_id,
                "success": True,
                "approval_id": approval_result.get("sp_no")
            })
            
        except Exception as e:
            results.append({
                "quote_id": quote_id,
                "success": False,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total": len(quote_ids),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }