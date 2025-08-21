from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
    # 检查权限
    require_user_permission()(current_user)
    quotations = crud.get_quotations(db, skip=skip, limit=limit)
    return quotations

@router.get("/{quotation_id}", response_model=schemas.Quotation)
def read_quotation(
    quotation_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限
    require_user_permission()(current_user)
    db_quotation = crud.get_quotation(db, quotation_id=quotation_id)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return db_quotation

@router.post("/", response_model=schemas.Quotation)
def create_quotation(
    quotation: schemas.QuotationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限：需要经理级别或以上
    require_manager_permission()(current_user)
    return crud.create_quotation(db=db, quotation=quotation)

@router.put("/{quotation_id}", response_model=schemas.Quotation)
def update_quotation(
    quotation_id: int, 
    quotation: schemas.QuotationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查权限：需要经理级别或以上
    require_manager_permission()(current_user)
    db_quotation = crud.update_quotation(db, quotation_id=quotation_id, quotation=quotation)
    if db_quotation is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return db_quotation

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
    return db_quotation
