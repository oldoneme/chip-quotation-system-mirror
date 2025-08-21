from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app import crud, schemas
from app.database import get_db
from app.models import User
from app.auth_routes import get_current_user
from app.middleware.permissions import (
    require_user_permission, 
    require_manager_permission, 
    require_admin_permission
)

router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.post("/calculate", response_model=schemas.QuotationResponse)
def calculate_quotation(
    quotation_request: schemas.QuotationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    require_user_permission()(current_user)
    try:
        total = crud.calculate_quotation(db, quotation_request)
        return schemas.QuotationResponse(
            total=total,
            machine_id=quotation_request.machine_id,
            test_hours=quotation_request.test_hours,
            details=quotation_request.details or {}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@router.get("/", response_model=List[schemas.Quotation])
def read_quotations(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 根据角色返回不同的报价数据
    if current_user.role == "user":
        # 一般用户只能查看自己提交的报价
        quotations = crud.get_user_quotations(db, user_id=current_user.id, skip=skip, limit=limit)
    else:
        # 销售经理及以上可以查看所有报价
        require_manager_permission()(current_user)
        quotations = crud.get_quotations(db, skip=skip, limit=limit)
    return quotations

@router.get("/{quotation_id}", response_model=schemas.Quotation)
def read_quotation(
    quotation_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取报价信息
    db_quotation = crud.get_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # 权限检查：一般用户只能查看自己的报价，经理及以上可以查看所有
    if current_user.role == "user" and db_quotation.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied: Can only view your own quotations")
    
    return db_quotation

@router.post("/", response_model=schemas.Quotation)
def create_quotation(
    quotation: schemas.QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 所有登录用户都可以创建报价申请
    require_user_permission()(current_user)
    
    # 设置创建者信息
    quotation_data = quotation.dict()
    quotation_data['created_by'] = current_user.id
    quotation_data['status'] = 'pending'  # 新建报价默认为待审核状态
    
    return crud.create_quotation(db=db, quotation=quotation_data, user_id=current_user.id)

@router.put("/{quotation_id}", response_model=schemas.Quotation)
def update_quotation(
    quotation_id: int, 
    quotation: schemas.QuotationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取报价信息
    db_quotation = crud.get_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # 权限检查
    if current_user.role == "user":
        # 一般用户只能编辑自己的未审核报价
        if db_quotation.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Permission denied: Can only edit your own quotations")
        if db_quotation.status != "pending":
            raise HTTPException(status_code=403, detail="Permission denied: Can only edit pending quotations")
    else:
        # 销售经理及以上可以修改任何报价
        require_manager_permission()(current_user)
    
    updated_quotation = crud.update_quotation(db, quotation_id=quotation_id, quotation=quotation)
    return updated_quotation

@router.delete("/{quotation_id}", response_model=schemas.Quotation)
def delete_quotation(
    quotation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限：需要管理员级别或以上
    require_admin_permission()(current_user)
    db_quotation = crud.delete_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # 记录删除操作
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="quotation_delete",
        details=f"Deleted quotation {quotation_id}"
    )
    
    return db_quotation


@router.put("/{quotation_id}/status", response_model=schemas.Quotation)
def update_quotation_status(
    quotation_id: int,
    status_update: schemas.QuotationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审核报价 - 销售经理及以上权限"""
    # 检查权限：需要销售经理及以上
    require_manager_permission()(current_user)
    
    db_quotation = crud.get_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    # 更新状态并记录审核人
    updated_quotation = crud.update_quotation_status(
        db, 
        quotation_id=quotation_id, 
        status=status_update.status,
        reviewer_id=current_user.id,
        review_comment=status_update.comment
    )
    return updated_quotation


@router.put("/{quotation_id}/priority", response_model=schemas.Quotation)  
def update_quotation_priority(
    quotation_id: int,
    priority_update: schemas.QuotationPriorityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置报价优先级 - 销售经理及以上权限"""
    # 检查权限：需要销售经理及以上
    require_manager_permission()(current_user)
    
    db_quotation = crud.get_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    updated_quotation = crud.update_quotation_priority(
        db, 
        quotation_id=quotation_id, 
        priority=priority_update.priority
    )
    return updated_quotation


@router.get("/export/data")
def export_quotations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: str = None,
    end_date: str = None
):
    """导出报价数据 - 销售经理及以上权限"""
    # 检查权限：需要销售经理及以上
    require_manager_permission()(current_user)
    
    quotations = crud.get_quotations_for_export(
        db, 
        start_date=start_date, 
        end_date=end_date
    )
    
    # 记录导出操作
    crud.log_operation(
        db,
        user_id=current_user.id,
        operation="data_export",
        details=f"Exported {len(quotations)} quotations"
    )
    
    return {
        "data": quotations,
        "count": len(quotations),
        "exported_by": current_user.name,
        "export_time": datetime.now()
    }
