from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/card-configs", tags=["card-configs"])

@router.post("/", response_model=schemas.CardConfig)
def create_card_config(card_config: schemas.CardConfigCreate, db: Session = Depends(get_db)):
    return crud.create_card_config(db=db, card_config=card_config)

@router.get("/", response_model=List[schemas.CardConfig])
def read_card_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    card_configs = crud.get_card_configs(db, skip=skip, limit=limit)
    return card_configs

@router.get("/{card_config_id}", response_model=schemas.CardConfig)
def read_card_config(card_config_id: int, db: Session = Depends(get_db)):
    db_card_config = crud.get_card_config(db, card_config_id=card_config_id)
    if db_card_config is None:
        raise HTTPException(status_code=404, detail="Card config not found")
    return db_card_config

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