from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime, timedelta

from app import crud, schemas
from app.database import get_db
from app.models import User, Quotation, OperationLog
from app.auth_routes import get_current_user
from app.middleware.permissions import (
    require_user_permission, 
    require_manager_permission, 
    require_admin_permission
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/quotations", response_model=schemas.QuotationStats)
def get_quotation_statistics(
    period: str = Query("month", description="统计周期: week, month, quarter, year"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报价统计信息 - 根据角色返回不同范围的统计"""
    
    # 构建基础查询
    if current_user.role == "user":
        # 一般用户只能查看自己的统计
        query = db.query(Quotation).filter(Quotation.created_by == current_user.id)
    elif current_user.role == "manager":
        # 销售经理查看所有报价统计
        require_manager_permission()(current_user)
        query = db.query(Quotation)
    else:
        # 管理员及以上查看所有报价统计
        require_admin_permission()(current_user)
        query = db.query(Quotation)
    
    # 添加时间范围过滤
    if start_date and end_date:
        query = query.filter(Quotation.created_at >= start_date, Quotation.created_at <= end_date)
    else:
        # 根据周期设置默认时间范围
        end = datetime.now()
        if period == "week":
            start = end - timedelta(weeks=1)
        elif period == "month":
            start = end - timedelta(days=30)
        elif period == "quarter":
            start = end - timedelta(days=90)
        elif period == "year":
            start = end - timedelta(days=365)
        else:
            start = end - timedelta(days=30)  # 默认为月
            
        query = query.filter(Quotation.created_at >= start)
    
    # 获取统计数据
    quotations = query.all()
    
    total_count = len(quotations)
    pending_count = sum(1 for q in quotations if getattr(q, 'status', 'pending') == 'pending')
    approved_count = sum(1 for q in quotations if getattr(q, 'status', 'pending') == 'approved')
    rejected_count = sum(1 for q in quotations if getattr(q, 'status', 'pending') == 'rejected')
    
    total_amount = sum(q.total for q in quotations if q.total)
    avg_amount = total_amount / total_count if total_count > 0 else 0
    
    return schemas.QuotationStats(
        total_count=total_count,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_amount=total_amount,
        avg_amount=avg_amount,
        period=period
    )


@router.get("/users", response_model=List[schemas.UserStats])
def get_user_statistics(
    period: str = Query("month", description="统计周期: week, month, quarter, year"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息 - 管理员及以上"""
    require_admin_permission()(current_user)
    
    # 设置时间范围
    if start_date and end_date:
        date_filter = text(f"created_at >= '{start_date}' AND created_at <= '{end_date}'")
    else:
        end = datetime.now()
        if period == "week":
            start = end - timedelta(weeks=1)
        elif period == "month":
            start = end - timedelta(days=30)
        elif period == "quarter":
            start = end - timedelta(days=90)
        elif period == "year":
            start = end - timedelta(days=365)
        else:
            start = end - timedelta(days=30)
        
        date_filter = text(f"created_at >= '{start.strftime('%Y-%m-%d')}'")
    
    # 查询用户统计
    user_stats_query = db.query(
        User.id,
        User.name,
        func.count(Quotation.id).label('quotation_count'),
        func.sum(func.case([(text("status = 'approved'"), 1)], else_=0)).label('approved_count'),
        func.sum(Quotation.total).label('total_amount')
    ).outerjoin(
        Quotation, User.id == Quotation.created_by
    ).filter(
        date_filter if start_date and end_date else text(f"quotations.created_at >= '{start.strftime('%Y-%m-%d')}'")
    ).group_by(User.id, User.name)
    
    user_stats = []
    for user_id, user_name, quotation_count, approved_count, total_amount in user_stats_query.all():
        success_rate = (approved_count / quotation_count * 100) if quotation_count > 0 else 0
        user_stats.append(schemas.UserStats(
            user_id=user_id,
            user_name=user_name or "未知用户",
            quotation_count=quotation_count or 0,
            approved_count=approved_count or 0,
            total_amount=total_amount or 0,
            success_rate=success_rate
        ))
    
    return user_stats


@router.get("/dashboard")
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘数据 - 根据角色返回不同的数据"""
    
    # 基础权限检查
    require_user_permission()(current_user)
    
    # 根据角色返回不同的仪表盘数据
    if current_user.role == "user":
        # 一般用户：个人数据概览
        my_quotations = db.query(Quotation).filter(Quotation.created_by == current_user.id).all()
        total_quotations = len(my_quotations)
        pending_quotations = sum(1 for q in my_quotations if getattr(q, 'status', 'pending') == 'pending')
        approved_quotations = sum(1 for q in my_quotations if getattr(q, 'status', 'pending') == 'approved')
        
        return {
            "role": current_user.role,
            "user_name": current_user.name,
            "personal_stats": {
                "total_quotations": total_quotations,
                "pending_quotations": pending_quotations,
                "approved_quotations": approved_quotations,
                "total_amount": sum(q.total for q in my_quotations if q.total)
            }
        }
    
    elif current_user.role == "manager":
        # 销售经理：团队数据概览
        require_manager_permission()(current_user)
        
        all_quotations = db.query(Quotation).all()
        all_users = db.query(User).filter(User.is_active == True).all()
        
        return {
            "role": current_user.role,
            "user_name": current_user.name,
            "team_stats": {
                "total_users": len(all_users),
                "total_quotations": len(all_quotations),
                "pending_quotations": sum(1 for q in all_quotations if getattr(q, 'status', 'pending') == 'pending'),
                "approved_quotations": sum(1 for q in all_quotations if getattr(q, 'status', 'pending') == 'approved'),
                "total_amount": sum(q.total for q in all_quotations if q.total)
            }
        }
    
    else:
        # 管理员及以上：系统全局数据概览
        require_admin_permission()(current_user)
        
        all_quotations = db.query(Quotation).all()
        all_users = db.query(User).all()
        recent_logs = db.query(OperationLog).order_by(
            OperationLog.created_at.desc()
        ).limit(10).all()
        
        return {
            "role": current_user.role,
            "user_name": current_user.name,
            "system_stats": {
                "total_users": len(all_users),
                "active_users": len([u for u in all_users if u.is_active]),
                "total_quotations": len(all_quotations),
                "pending_quotations": sum(1 for q in all_quotations if getattr(q, 'status', 'pending') == 'pending'),
                "approved_quotations": sum(1 for q in all_quotations if getattr(q, 'status', 'pending') == 'approved'),
                "total_amount": sum(q.total for q in all_quotations if q.total),
                "recent_operations": len(recent_logs)
            },
            "recent_logs": [
                {
                    "id": log.id,
                    "operation": log.operation,
                    "details": log.details,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "user_name": getattr(log, 'user_name', 'Unknown')
                }
                for log in recent_logs
            ]
        }


@router.get("/export")
def export_statistics(
    format: str = Query("json", description="导出格式: json, csv"),
    period: str = Query("month", description="统计周期: week, month, quarter, year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出统计数据 - 销售经理及以上"""
    require_manager_permission()(current_user)
    
    # 获取统计数据
    quotation_stats = get_quotation_statistics(period=period, current_user=current_user, db=db)
    
    # 记录导出操作
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="statistics_export",
        details=f"Exported {period} statistics in {format} format"
    )
    
    if format == "csv":
        # 返回CSV格式的统计数据
        csv_content = f"""Period,Total Count,Pending,Approved,Rejected,Total Amount,Average Amount
{period},{quotation_stats.total_count},{quotation_stats.pending_count},{quotation_stats.approved_count},{quotation_stats.rejected_count},{quotation_stats.total_amount},{quotation_stats.avg_amount}"""
        
        return {
            "format": "csv",
            "content": csv_content,
            "filename": f"quotation_statistics_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    else:
        # 返回JSON格式
        return {
            "format": "json",
            "data": quotation_stats,
            "exported_by": current_user.name,
            "export_time": datetime.now().isoformat()
        }