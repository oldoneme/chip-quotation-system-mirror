from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/auxiliary-equipment", tags=["auxiliary-equipment"])


@router.get("/", response_model=List[schemas.AuxiliaryEquipment])
def read_auxiliary_equipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    equipments = crud.get_auxiliary_equipments(db, skip=skip, limit=limit)
    return equipments


@router.get("/{equipment_id}", response_model=schemas.AuxiliaryEquipment)
def read_auxiliary_equipment(equipment_id: int, db: Session = Depends(get_db)):
    db_equipment = crud.get_auxiliary_equipment(db, equipment_id=equipment_id)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Auxiliary equipment not found")
    return db_equipment


@router.post("/", response_model=schemas.AuxiliaryEquipment)
def create_auxiliary_equipment(equipment: schemas.AuxiliaryEquipmentCreate, db: Session = Depends(get_db)):
    return crud.create_auxiliary_equipment(db=db, equipment=equipment)


@router.put("/{equipment_id}", response_model=schemas.AuxiliaryEquipment)
def update_auxiliary_equipment(equipment_id: int, equipment: schemas.AuxiliaryEquipmentUpdate, db: Session = Depends(get_db)):
    db_equipment = crud.update_auxiliary_equipment(db, equipment_id=equipment_id, equipment=equipment)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Auxiliary equipment not found")
    return db_equipment


@router.delete("/{equipment_id}", response_model=schemas.AuxiliaryEquipment)
def delete_auxiliary_equipment(equipment_id: int, db: Session = Depends(get_db)):
    db_equipment = crud.delete_auxiliary_equipment(db, equipment_id=equipment_id)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Auxiliary equipment not found")
    return db_equipment