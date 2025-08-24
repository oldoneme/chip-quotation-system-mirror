from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, schemas
from app.database import get_db
from app.auth_routes import get_current_user_optional
from app.models import User

router = APIRouter(prefix="/card-configs", tags=["card-configs"])

@router.post("/", response_model=schemas.CardConfig)
def create_card_config(card_config: schemas.CardConfigCreate, db: Session = Depends(get_db)):
    return crud.create_card_config(db=db, card_config=card_config)

def filter_price_data(card_config_data, user: Optional[User]):
    """根据用户权限过滤价格敏感信息
    注意：即使非管理员用户，也需要返回unit_price用于前端计算机时费
    前端会根据权限决定是否显示Unit Price列
    """
    # 所有用户都返回完整数据，前端控制显示
    return card_config_data

@router.get("/")
def read_card_configs(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    card_configs = crud.get_card_configs(db, skip=skip, limit=limit)
    # 转换为字典格式以便修改
    card_configs_dict = [
        {
            "id": config.id,
            "machine_id": config.machine_id,
            "part_number": config.part_number,
            "board_name": config.board_name,
            "unit_price": config.unit_price,
            "currency": config.currency,
            "exchange_rate": config.exchange_rate
        }
        for config in card_configs
    ]
    
    # 根据用户权限过滤价格信息
    filtered_configs = filter_price_data(card_configs_dict, current_user)
    return filtered_configs

@router.get("/{card_config_id}")
def read_card_config(
    card_config_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    db_card_config = crud.get_card_config(db, card_config_id=card_config_id)
    if db_card_config is None:
        raise HTTPException(status_code=404, detail="Card config not found")
    
    # 转换为字典格式
    card_config_dict = {
        "id": db_card_config.id,
        "machine_id": db_card_config.machine_id,
        "part_number": db_card_config.part_number,
        "board_name": db_card_config.board_name,
        "unit_price": db_card_config.unit_price,
        "currency": db_card_config.currency,
        "exchange_rate": db_card_config.exchange_rate
    }
    
    # 根据用户权限过滤价格信息
    filtered_config = filter_price_data(card_config_dict, current_user)
    return filtered_config

@router.put("/{card_config_id}", response_model=schemas.CardConfig)
def update_card_config(card_config_id: int, card_config: schemas.CardConfigUpdate, db: Session = Depends(get_db)):
    db_card_config = crud.update_card_config(db, card_config_id=card_config_id, card_config=card_config)
    if db_card_config is None:
        raise HTTPException(status_code=404, detail="Card config not found")
    return db_card_config

@router.delete("/{card_config_id}", response_model=schemas.CardConfig)
def delete_card_config(card_config_id: int, db: Session = Depends(get_db)):
    db_card_config = crud.delete_card_config(db, card_config_id=card_config_id)
    if db_card_config is None:
        raise HTTPException(status_code=404, detail="Card config not found")
    return db_card_config