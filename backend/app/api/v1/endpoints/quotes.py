"""
报价单相关的API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....services.quote_service import QuoteService
from ....schemas import (
    Quote, QuoteCreate, QuoteUpdate, QuoteList, 
    QuoteFilter, QuoteStatusUpdate, QuoteStatistics,
    ApprovalRecord
)
from ....auth import get_current_user
from ....models import User

router = APIRouter(prefix="/quotes", tags=["报价单管理"])


@router.post("/", response_model=Quote, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新报价单"""
    try:
        service = QuoteService(db)
        quote = service.create_quote(quote_data, current_user.id)
        return quote
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建报价单失败: {str(e)}"
        )


@router.get("/", response_model=dict)
async def get_quotes(
    status: Optional[str] = Query(None, description="状态筛选"),
    quote_type: Optional[str] = Query(None, description="报价类型筛选"),
    customer_name: Optional[str] = Query(None, description="客户名称筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报价单列表"""
    try:
        service = QuoteService(db)
        filter_params = QuoteFilter(
            status=status,
            quote_type=quote_type,
            customer_name=customer_name,
            page=page,
            size=size
        )
        
        quotes, total = service.get_quotes(filter_params, current_user.id if current_user else None)
        
        return {
            "items": quotes,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    except Exception as e:
        print(f"API错误详情: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价单列表失败: {str(e)}"
        )


@router.get("/test", response_model=dict)
async def get_quotes_test(
    db: Session = Depends(get_db)
):
    """测试端点 - 直接返回报价单列表"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy import desc
        from sqlalchemy.orm import selectinload
        
        # 获取所有报价单，按创建时间倒序排列，并关联用户信息和报价项目
        quotes = db.query(Quote).options(
            selectinload(Quote.items)
        ).join(User, Quote.created_by == User.id, isouter=True).order_by(desc(Quote.created_at)).all()
        
        result = []
        for quote in quotes:
            # 获取创建者姓名
            creator_name = "未知"
            if quote.creator:
                creator_name = quote.creator.name
            
            # 格式化报价明细
            quote_details = []
            for item in quote.items:
                detail = {
                    "item_name": item.item_name,
                    "machine_type": item.machine_type,
                    "machine_model": item.machine_model,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "total_price": item.total_price
                }
                quote_details.append(detail)
            
            result.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title,
                "quote_type": quote.quote_type,
                "customer_name": quote.customer_name,
                "status": quote.status,
                "created_at": quote.created_at.isoformat(),
                "total_amount": quote.total_amount,
                "creator_name": creator_name,
                "quote_details": quote_details
            })
        return {
            "items": result,
            "total": len(result),
            "page": 1,
            "size": len(result)
        }
    except Exception as e:
        print(f"测试端点错误: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/detail/{quote_number}")
async def get_quote_detail_test(
    quote_number: str,
    db: Session = Depends(get_db)
):
    """测试端点 - 获取报价单详情（包含创建者姓名）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        
        # 获取报价单详情，关联用户和明细项
        quote = (db.query(Quote)
                .options(selectinload(Quote.items), selectinload(Quote.creator))
                .filter(Quote.quote_number == quote_number)
                .first())
        
        if not quote:
            return {"error": "报价单不存在"}
        
        # 获取创建者姓名
        creator_name = "未知"
        if quote.creator:
            creator_name = quote.creator.name
        
        # 格式化报价明细
        quote_items = []
        for item in quote.items:
            quote_items.append({
                "id": item.id,
                "item_name": item.item_name,
                "item_description": item.item_description,
                "machine_type": item.machine_type,
                "supplier": item.supplier,
                "machine_model": item.machine_model,
                "configuration": item.configuration,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            })
        
        result = {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "quote_type": quote.quote_type,
            "customer_name": quote.customer_name,
            "customer_contact": quote.customer_contact,
            "customer_phone": quote.customer_phone,
            "customer_email": quote.customer_email,
            "customer_address": quote.customer_address,
            "currency": quote.currency,
            "subtotal": quote.subtotal,
            "discount": quote.discount,
            "tax_rate": quote.tax_rate,
            "tax_amount": quote.tax_amount,
            "total_amount": quote.total_amount,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
            "payment_terms": quote.payment_terms,
            "description": quote.description,
            "notes": quote.notes,
            "status": quote.status,
            "version": quote.version,
            "submitted_at": quote.submitted_at.isoformat() if quote.submitted_at else None,
            "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "created_by": quote.created_by,
            "creator_name": creator_name,
            "created_at": quote.created_at.isoformat(),
            "updated_at": quote.updated_at.isoformat(),
            "items": quote_items
        }
        
        return result
        
    except Exception as e:
        print(f"获取报价单详情错误: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/statistics", response_model=QuoteStatistics)
async def get_quote_statistics(
    db: Session = Depends(get_db)
):
    """获取报价单统计信息"""
    try:
        service = QuoteService(db)
        # 暂时不使用用户过滤，返回全部统计
        return service.get_quote_statistics(user_id=None)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/{quote_id}", response_model=Quote)
async def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取报价单详情"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_id(quote_id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单"
            )
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(e)}"
        )


@router.get("/number/{quote_number}", response_model=Quote)
async def get_quote_by_number(
    quote_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据报价单号获取报价单详情"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_number(quote_number)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单"
            )
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(e)}"
        )


@router.put("/{quote_id}", response_model=Quote)
async def update_quote(
    quote_id: int,
    quote_data: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单"""
    try:
        service = QuoteService(db)
        quote = service.update_quote(quote_id, quote_data, current_user.id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        return quote
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单失败: {str(e)}"
        )


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报价单"""
    try:
        service = QuoteService(db)
        success = service.delete_quote(quote_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        return {"message": "报价单删除成功"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除报价单失败: {str(e)}"
        )


@router.patch("/{quote_id}/status", response_model=Quote)
async def update_quote_status(
    quote_id: int,
    status_update: QuoteStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单状态"""
    try:
        service = QuoteService(db)
        quote = service.update_quote_status(quote_id, status_update, current_user.id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单状态失败: {str(e)}"
        )


@router.post("/{quote_id}/submit", response_model=Quote)
async def submit_quote_for_approval(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交报价单审批"""
    try:
        service = QuoteService(db)
        quote = service.submit_for_approval(quote_id, current_user.id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # TODO: 这里将来集成企业微信审批API
        # wecom_service = WeComApprovalService()
        # approval_id = wecom_service.submit_approval(quote)
        # quote.wecom_approval_id = approval_id
        
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"提交审批失败: {str(e)}"
        )


@router.get("/{quote_id}/approval-records", response_model=List[ApprovalRecord])
async def get_quote_approval_records(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报价单审批记录"""
    try:
        service = QuoteService(db)
        quote = service.get_quote_by_id(quote_id)
        
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )
        
        # 检查访问权限
        if (quote.created_by != current_user.id and 
            current_user.role not in ['admin', 'super_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此报价单的审批记录"
            )
        
        records = service.get_approval_records(quote_id)
        return records
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取审批记录失败: {str(e)}"
        )


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: int,
    approval_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批准报价单"""
    try:
        service = QuoteService(db)
        
        # 检查权限 - 只有管理员可以审批
        if current_user.role not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行审批操作"
            )
        
        quote = service.approve_quote(quote_id, current_user.id, approval_data.get('comments', '审批通过'))
        return {"message": "报价单已批准", "quote": quote}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批准操作失败: {str(e)}"
        )


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: int,
    rejection_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝报价单"""
    try:
        service = QuoteService(db)
        
        # 检查权限 - 只有管理员可以审批
        if current_user.role not in ['admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行审批操作"
            )
        
        comments = rejection_data.get('comments', '')
        if not comments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="拒绝时必须提供拒绝原因"
            )
        
        quote = service.reject_quote(quote_id, current_user.id, comments)
        return {"message": "报价单已拒绝", "quote": quote}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"拒绝操作失败: {str(e)}"
        )