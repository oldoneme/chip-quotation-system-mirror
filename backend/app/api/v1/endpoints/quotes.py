"""
报价单相关的API端点
"""

from typing import List, Optional
import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from ....auth_routes import get_current_user
from ....database import get_db
from ....models import User, Quote as QuoteModel
from ....schemas import (
    Quote as QuoteSchema,
    QuoteCreate,
    QuoteUpdate,
    QuoteFilter,
    QuoteStatusUpdate,
    QuoteStatistics,
)
from ....services.quote_service import QuoteService
from .quote_route_helpers import ensure_quote_access, get_quote_by_identifier
from .quote_endpoint_helpers import list_item_to_dict, quote_to_schema, schedule_pdf_refresh

router = APIRouter(prefix="/quotes", tags=["报价单管理"])


@router.post("/", response_model=QuoteSchema, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新报价单并生成快照PDF缓存"""
    logger = logging.getLogger("app.api.quotes")
    # DEBUG: Log incoming quote_data payload before processing
    try:
        logger.info(f"DEBUG: Incoming quote_data for create_quote: {quote_data.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Failed to log incoming quote_data: {e}")

    try:
        service = QuoteService(db)
        quote = service.create_quote(quote_data, current_user.id)
        quote_detail = service.load_quote_with_details(quote.id) or quote
        schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            True,
            "snapshot_generation_failed_on_create",
        )
        return quote_to_schema(service, quote_detail)
    except Exception as exc:  # pragma: no cover - 捕获意外错误并转译
        logger.exception("create_quote_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建报价单失败: {str(exc)}"
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
    """获取报价单列表并附带PDF缓存链接"""
    logger = logging.getLogger("app.api.quotes")
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
        items = [list_item_to_dict(service, q) for q in quotes]

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }
    except Exception as exc:  # pragma: no cover - 捕获意外错误
        logger.exception("get_quotes_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价单列表失败: {str(exc)}"
        )



@router.get("/test", response_model=dict)
async def get_quotes_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试端点 - 返回报价单列表（带权限过滤）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy import desc, and_, or_
        from sqlalchemy.orm import selectinload

        # 基于审批流程的权限控制
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            return {"items": [], "total": 0, "page": 1, "size": 0}

        # 构建权限过滤条件
        base_filters = [Quote.is_deleted == False]

        # 超级管理员可以看到所有报价单
        if user.role == 'super_admin':
            pass  # 不添加额外过滤条件
        else:
            # 构建权限过滤条件（使用OR逻辑）
            permission_filters = [
                Quote.created_by == current_user.id,  # 1. 自己创建的所有报价单
            ]

            # manager和admin可以看到指定自己为审批人且已提交审批的报价单
            if user.role in ['manager', 'admin']:
                permission_filters.append(
                    and_(
                        Quote.current_approver_id == current_user.id,
                        Quote.approval_status.in_(['pending', 'approved', 'rejected'])
                    )
                )

            # admin还可以看到所有已完成审批的报价单（用于统计）
            if user.role == 'admin':
                permission_filters.append(
                    Quote.approval_status.in_(['approved', 'rejected'])
                )

            # 使用OR条件组合所有权限过滤
            base_filters.append(or_(*permission_filters))

        # 获取允许查看的报价单
        quotes = db.query(Quote).filter(
            and_(*base_filters)
        ).options(
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
                # 从configuration中解析UPH和计算机时费率
                uph = None
                hourly_rate = None
                if item.configuration:
                    import re
                    uph_match = re.search(r'UPH:(\d+)', item.configuration)
                    if uph_match:
                        uph = int(uph_match.group(1))
                        hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
                
                detail = {
                    "item_name": item.item_name,
                    "item_description": item.item_description,
                    "machine_type": item.machine_type,
                    "machine_model": item.machine_model,
                    "configuration": item.configuration,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "total_price": item.total_price,
                    "adjusted_price": item.adjusted_price,
                    "adjustment_reason": item.adjustment_reason,
                    "uph": uph,
                    "hourly_rate": hourly_rate
                }
                quote_details.append(detail)
            
            result.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title,
                "quote_type": quote.quote_type,
                "customer_name": quote.customer_name,
                "status": quote.status,
                "approval_status": quote.approval_status,  # 添加审批状态字段
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

@router.get("/by-uuid/{quote_uuid}")
async def get_quote_by_uuid(
    quote_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    按审批链接Token查询报价单详情（完整数据）
    用于企业微信审批链接访问
    """
    try:
        service = QuoteService(db)
        quote = ensure_quote_access(service.get_quote_by_approval_token(quote_uuid), current_user)
        return quote_to_schema(service, quote)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(exc)}"
        )


@router.get("/detail/by-id/{quote_id}")
async def get_quote_detail_by_id(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """按ID获取报价单详情（包含创建者姓名）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        
        # 获取报价单详情，关联用户和明细项
        quote = (db.query(Quote)
                .options(selectinload(Quote.items), selectinload(Quote.creator))
                .filter(Quote.id == quote_id, Quote.is_deleted == False)
                .first())

        quote = ensure_quote_access(quote, current_user)
        
        # 获取创建者姓名
        creator_name = "未知"
        if quote.creator:
            creator_name = quote.creator.name
        
        # 格式化报价明细
        quote_items = []
        for item in quote.items:
            # 从configuration中解析UPH和计算机时费率
            uph = None
            hourly_rate = None
            if item.configuration:
                import re
                uph_match = re.search(r'UPH:(\d+)', item.configuration)
                if uph_match:
                    uph = int(uph_match.group(1))
                    hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
            
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
                "total_price": item.total_price,
                "adjusted_price": item.adjusted_price,
                "adjustment_reason": item.adjustment_reason,
                "machine_id": item.machine_id,
                "configuration_id": item.configuration_id,
                "uph": uph,
                "hourly_rate": hourly_rate
            })
        
        return {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "quote_type": quote.quote_type,
            "customer_name": quote.customer_name,
            "customer_contact": quote.customer_contact,
            "customer_phone": quote.customer_phone,
            "customer_email": quote.customer_email,
            "customer_address": quote.customer_address,
            "quote_unit": quote.quote_unit,  # 添加报价单位字段
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
            "approval_status": quote.approval_status,  # 添加审批状态字段
            "version": quote.version,
            "submitted_at": quote.submitted_at.isoformat() if quote.submitted_at else None,
            "approved_at": quote.approved_at.isoformat() if quote.approved_at else None,
            "approved_by": quote.approved_by,
            "rejection_reason": quote.rejection_reason,
            "wecom_approval_id": quote.wecom_approval_id,
            "created_by": quote.created_by,
            "creator_name": creator_name,
            "created_at": quote.created_at.isoformat() if quote.created_at else None,
            "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
            "items": quote_items
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.getLogger("app.api.quotes").exception(
            "get_quote_detail_by_id_failed",
            extra={"quote_id": quote_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报价单详情失败",
        ) from exc

@router.get("/detail/{quote_number}")
async def get_quote_detail_test(
    quote_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试端点 - 获取报价单详情（包含创建者姓名）"""
    try:
        from ....models import Quote, User, QuoteItem
        from sqlalchemy.orm import selectinload
        
        # 获取报价单详情，关联用户和明细项
        quote = (db.query(Quote)
                .options(selectinload(Quote.items), selectinload(Quote.creator))
                .filter(Quote.quote_number == quote_number, Quote.is_deleted == False)
                .first())

        quote = ensure_quote_access(quote, current_user)
        
        # 获取创建者姓名
        creator_name = "未知"
        if quote.creator:
            creator_name = quote.creator.name
        
        # 格式化报价明细
        quote_items = []
        for item in quote.items:
            # 从configuration中解析UPH和计算机时费率
            uph = None
            hourly_rate = None
            if item.configuration:
                import re
                uph_match = re.search(r'UPH:(\d+)', item.configuration)
                if uph_match:
                    uph = int(uph_match.group(1))
                    hourly_rate = f"¥{(item.unit_price * uph):.2f}/小时" if item.unit_price else "¥0.00/小时"
            
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
                "total_price": item.total_price,
                "adjusted_price": item.adjusted_price,
                "adjustment_reason": item.adjustment_reason,
                "machine_id": item.machine_id,
                "configuration_id": item.configuration_id,
                "uph": uph,
                "hourly_rate": hourly_rate
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
            "approval_status": quote.approval_status,  # 添加审批状态字段
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

    except HTTPException:
        raise
    except Exception as exc:
        logging.getLogger("app.api.quotes").exception(
            "get_quote_detail_by_number_failed",
            extra={"quote_number": quote_number},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报价单详情失败",
        ) from exc

@router.get("/statistics", response_model=QuoteStatistics)
async def get_quote_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报价单统计信息（基于当前用户权限）"""
    try:
        service = QuoteService(db)
        return service.get_quote_statistics(user_id=current_user.id if current_user else None)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/{quote_id}", response_model=QuoteSchema)
async def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID或报价单号获取报价单详情"""
    try:
        service = QuoteService(db)
        quote = ensure_quote_access(get_quote_by_identifier(service, quote_id), current_user)

        return quote_to_schema(service, quote)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(exc)}"
        )



@router.get("/number/{quote_number}", response_model=QuoteSchema)
async def get_quote_by_number(
    quote_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据报价单号获取报价单详情"""
    try:
        service = QuoteService(db)
        quote = ensure_quote_access(service.get_quote_by_number(quote_number), current_user)

        return quote_to_schema(service, quote)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取报价单失败: {str(exc)}"
        )



@router.put("/{quote_id}", response_model=QuoteSchema)
async def update_quote(
    quote_id: str,
    quote_data: QuoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新报价单"""
    logger = logging.getLogger("app.api.quotes")
    try:
        service = QuoteService(db)
        quote = service.update_quote(quote_id, quote_data, current_user.id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        quote_detail = service.load_quote_with_details(quote.id) or quote
        schedule_pdf_refresh(
            background_tasks,
            quote_detail.id,
            current_user.id,
            True,
            "snapshot_generation_failed_on_update",
        )
        return quote_to_schema(service, quote_detail)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("update_quote_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单失败: {str(exc)}"
        )



@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报价单"""
    try:
        service = QuoteService(db)

        # 删除前先获取报价单信息（用于清理PDF缓存）
        quote = service.get_quote_by_id(quote_id)

        success = service.delete_quote(quote_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        if quote and quote.pdf_cache:
            try:
                pdf_path = Path(quote.pdf_cache.pdf_path)
                if not pdf_path.is_absolute():
                    pdf_path = Path(pdf_path)
                if pdf_path.exists():
                    pdf_path.unlink()
                parent_dir = pdf_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                logging.getLogger("app.snapshot").info(
                    json.dumps(
                        {
                            "event": "snapshot_cache_removed_on_delete",
                            "quote_id": quote.id,
                            "quote_number": quote.quote_number,
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as cache_error:  # pragma: no cover - 删除缓存失败不阻断删除
                logging.getLogger("app.snapshot").warning(
                    json.dumps(
                        {
                            "event": "snapshot_cache_cleanup_failed",
                            "quote_id": quote.id if quote else quote_id,
                            "error": str(cache_error),
                        },
                        ensure_ascii=False,
                    )
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


@router.post("/{quote_id}/restore")
async def restore_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复已删除的报价单"""
    try:
        service = QuoteService(db)
        success = service.restore_quote(quote_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在或未被删除"
            )

        return {"message": "报价单恢复成功"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"恢复报价单失败: {str(e)}"
        )


@router.patch("/{quote_id}/status", response_model=QuoteSchema)
async def update_quote_status(
    quote_id: str,
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

        return quote_to_schema(service, quote)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新报价单状态失败: {str(exc)}"
        )
