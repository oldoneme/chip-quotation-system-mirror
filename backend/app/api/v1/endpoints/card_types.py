from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/card-types", tags=["card-types"])

@router.get("/", response_model=List[schemas.CardConfig])
def read_card_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    card_types = crud.get_card_configs(db, skip=skip, limit=limit)
    return card_types

@router.get("/{card_type_id}", response_model=schemas.CardConfig)
def read_card_type(card_type_id: int, db: Session = Depends(get_db)):
    db_card_type = crud.get_card_config(db, card_config_id=card_type_id)
    if db_card_type is None:
        raise HTTPException(status_code=404, detail="Card type not found")
    return db_card_type

@router.post("/", response_model=schemas.CardConfig)
def create_card_type(card_type: schemas.CardConfigCreate, db: Session = Depends(get_db)):
    return crud.create_card_config(db=db, card_config=card_type)

@router.put("/{card_type_id}", response_model=schemas.CardConfig)
def update_card_type(card_type_id: int, card_type: schemas.CardConfigUpdate, db: Session = Depends(get_db)):
    db_card_type = crud.update_card_config(db, card_config_id=card_type_id, card_config=card_type)
    if db_card_type is None:
        raise HTTPException(status_code=404, detail="Card type not found")
    return db_card_type

@router.delete("/{card_type_id}", response_model=schemas.CardConfig)
def delete_card_type(card_type_id: int, db: Session = Depends(get_db)):
    db_card_type = crud.delete_card_config(db, card_config_id=card_type_id)
    if db_card_type is None:
        raise HTTPException(status_code=404, detail="Card type not found")
    return db_card_type