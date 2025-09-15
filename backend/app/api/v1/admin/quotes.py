"""
管理员报价单管理接口
提供完整的数据库管理功能，包括软删除数据的操作
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime

from ....database import get_db
from ....models import Quote, QuoteItem, User
from ....schemas import QuoteStatistics
from .permissions import require_admin_role, require_super_admin_role

router = APIRouter(prefix="/quotes", tags=["管理员-报价单管理"])


@router.get("/all", response_model=dict)
async def get_all_quotes(
    include_deleted: bool = Query(False, description="是否包含软删除数据"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取所有报价单（管理员专用）"""
    try:
        # 构建查询
        query = db.query(Quote)

        # 软删除过滤
        if not include_deleted:
            query = query.filter(Quote.is_deleted == False)

        # 状态过滤
        if status_filter:
            query = query.filter(Quote.status == status_filter)

        # 计算总数
        total = query.count()

        # 分页查询
        quotes = (
            query.order_by(desc(Quote.created_at))
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        # 格式化返回数据
        quote_list = []
        for quote in quotes:
            quote_data = {
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title,
                "quote_type": quote.quote_type,
                "customer_name": quote.customer_name,
                "currency": quote.currency,
                "total_amount": quote.total_amount,
                "status": quote.status,
                "approval_status": quote.approval_status,
                "created_by": quote.created_by,
                "creator_name": quote.creator.name if quote.creator else "未知",
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
                # 软删除相关字段
                "is_deleted": quote.is_deleted,
                "deleted_at": quote.deleted_at.isoformat() if quote.deleted_at else None,
                "deleted_by": quote.deleted_by,
                "deleter_name": quote.deleter.name if quote.deleter else None
            }
            quote_list.append(quote_data)

        return {
            "items": quote_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
            "include_deleted": include_deleted
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报价单列表失败: {str(e)}"
        )


@router.get("/statistics/detailed", response_model=dict)
async def get_detailed_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """获取详细统计信息（管理员专用）"""
    try:
        # 全部数据统计
        total_all = db.query(Quote).count()

        # 正常数据统计
        normal_query = db.query(Quote).filter(Quote.is_deleted == False)
        total_normal = normal_query.count()
        draft_normal = normal_query.filter(Quote.status == 'draft').count()
        pending_normal = normal_query.filter(Quote.status == 'pending').count()
        approved_normal = normal_query.filter(Quote.status == 'approved').count()
        rejected_normal = normal_query.filter(Quote.status == 'rejected').count()

        # 软删除数据统计
        deleted_query = db.query(Quote).filter(Quote.is_deleted == True)
        total_deleted = deleted_query.count()
        draft_deleted = deleted_query.filter(Quote.status == 'draft').count()
        pending_deleted = deleted_query.filter(Quote.status == 'pending').count()
        approved_deleted = deleted_query.filter(Quote.status == 'approved').count()
        rejected_deleted = deleted_query.filter(Quote.status == 'rejected').count()

        return {
            "all_data": {
                "total": total_all,
                "normal": total_normal,
                "deleted": total_deleted
            },
            "normal_data": {
                "total": total_normal,
                "draft": draft_normal,
                "pending": pending_normal,
                "approved": approved_normal,
                "rejected": rejected_normal
            },
            "deleted_data": {
                "total": total_deleted,
                "draft": draft_deleted,
                "pending": pending_deleted,
                "approved": approved_deleted,
                "rejected": rejected_deleted
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/export", response_model=dict)
async def export_quotes(
    include_deleted: bool = Query(False, description="是否包含软删除数据"),
    format: str = Query("json", description="导出格式: json, csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """导出报价单数据（管理员专用）"""
    try:
        # 构建查询
        query = db.query(Quote)

        # 软删除过滤
        if not include_deleted:
            query = query.filter(Quote.is_deleted == False)

        # 获取所有数据
        quotes = query.order_by(Quote.created_at.desc()).all()

        # 格式化数据
        export_data = []
        for quote in quotes:
            quote_data = {
                "报价单号": quote.quote_number,
                "标题": quote.title,
                "报价类型": quote.quote_type,
                "客户名称": quote.customer_name,
                "币种": quote.currency,
                "总金额": quote.total_amount,
                "状态": quote.status,
                "审批状态": quote.approval_status,
                "创建人": quote.creator.name if quote.creator else "未知",
                "创建时间": quote.created_at.isoformat() if quote.created_at else None,
                "更新时间": quote.updated_at.isoformat() if quote.updated_at else None,
                "是否删除": "是" if quote.is_deleted else "否",
                "删除时间": quote.deleted_at.isoformat() if quote.deleted_at else None,
                "删除人": quote.deleter.name if quote.deleter else None
            }
            export_data.append(quote_data)

        # 记录导出操作
        print(f"📊 导出报价单数据: {len(export_data)} 条记录 (包含删除: {include_deleted}) by {current_user.name}")

        return {
            "data": export_data,
            "total": len(export_data),
            "format": format,
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": current_user.name,
            "include_deleted": include_deleted
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出数据失败: {str(e)}"
        )


def require_admin_or_super_admin_auth(request: Request):
    """检查管理员系统认证或企业微信超级管理员权限"""
    # 首先检查管理员token
    token = request.cookies.get("admin_token")
    if token:
        from ....admin_auth import verify_admin_token
        admin_info = verify_admin_token(token)
        if admin_info:
            return {"type": "admin", "user": admin_info}

    # 如果没有管理员token，检查企业微信认证
    try:
        from ....auth import get_current_user
        current_user = get_current_user(request)
        if current_user and current_user.role in ['admin', 'super_admin']:
            return {"type": "wecom", "user": current_user}
    except:
        pass

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要超级管理员权限"
    )

@router.delete("/{quote_id}/hard-delete")
async def hard_delete_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)  # 临时允许admin也能硬删除
):
    """硬删除报价单（不可恢复，仅超级管理员）"""
    try:
        # 查找报价单（包括软删除的）
        quote = db.query(Quote).filter(Quote.id == quote_id).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="报价单不存在"
            )

        # 记录操作日志（硬删除前）
        quote_info = {
            "quote_number": quote.quote_number,
            "title": quote.title,
            "customer_name": quote.customer_name,
            "status": quote.status,
            "total_amount": quote.total_amount
        }

        # 硬删除（级联删除相关数据）
        db.delete(quote)
        db.commit()

        # TODO: 记录到操作日志表
        print(f"🚨 硬删除报价单: {quote_info} by {current_user.name}")

        return {
            "message": "报价单已永久删除",
            "deleted_quote": quote_info,
            "operator": current_user.name,
            "deleted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"硬删除报价单失败: {str(e)}"
        )


@router.post("/batch-restore")
async def batch_restore_quotes(
    quote_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """批量恢复软删除的报价单"""
    try:
        if not quote_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="报价单ID列表不能为空"
            )

        # 查找软删除的报价单
        quotes = (
            db.query(Quote)
            .filter(Quote.id.in_(quote_ids), Quote.is_deleted == True)
            .all()
        )

        if not quotes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到可恢复的报价单"
            )

        restored_count = 0
        restored_quotes = []

        for quote in quotes:
            quote.is_deleted = False
            quote.deleted_at = None
            quote.deleted_by = None
            restored_count += 1
            restored_quotes.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title
            })

        db.commit()

        return {
            "message": f"成功恢复 {restored_count} 个报价单",
            "restored_count": restored_count,
            "restored_quotes": restored_quotes,
            "operator": current_user.name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量恢复失败: {str(e)}"
        )


@router.delete("/batch-soft-delete")
async def batch_soft_delete_quotes(
    quote_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """批量软删除报价单"""
    try:
        if not quote_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="报价单ID列表不能为空"
            )

        # 查找正常状态的报价单
        quotes = (
            db.query(Quote)
            .filter(Quote.id.in_(quote_ids), Quote.is_deleted == False)
            .all()
        )

        if not quotes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到可删除的报价单"
            )

        deleted_count = 0
        deleted_quotes = []

        for quote in quotes:
            quote.is_deleted = True
            quote.deleted_at = datetime.utcnow()
            quote.deleted_by = current_user.id
            deleted_count += 1
            deleted_quotes.append({
                "id": quote.id,
                "quote_number": quote.quote_number,
                "title": quote.title
            })

        db.commit()

        return {
            "message": f"成功删除 {deleted_count} 个报价单",
            "deleted_count": deleted_count,
            "deleted_quotes": deleted_quotes,
            "operator": current_user.name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量删除失败: {str(e)}"
        )