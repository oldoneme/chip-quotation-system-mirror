from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/machine-types", tags=["machine-types"])

@router.post("/", response_model=schemas.MachineType)
def create_machine_type(machine_type: schemas.MachineTypeCreate, db: Session = Depends(get_db)):
    db_machine_type = crud.get_machine_type_by_name(db, name=machine_type.name)
    if db_machine_type:
        raise HTTPException(status_code=400, detail="Machine type already registered")
    return crud.create_machine_type(db=db, machine_type=machine_type)

@router.get("/", response_model=List[schemas.MachineType])
def read_machine_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    machine_types = crud.get_machine_types(db, skip=skip, limit=limit)
    return machine_types

@router.get("/{machine_type_id}", response_model=schemas.MachineType)
def read_machine_type(machine_type_id: int, db: Session = Depends(get_db)):
    db_machine_type = crud.get_machine_type(db, machine_type_id=machine_type_id)
    if db_machine_type is None:
        raise HTTPException(status_code=404, detail="Machine type not found")
    return db_machine_type

@router.put("/{machine_type_id}", response_model=schemas.MachineType)
def update_machine_type(machine_type_id: int, machine_type: schemas.MachineTypeUpdate, db: Session = Depends(get_db)):
    db_machine_type = crud.update_machine_type(db, machine_type_id=machine_type_id, machine_type=machine_type)
    if db_machine_type is None:
        raise HTTPException(status_code=404, detail="Machine type not found")
    return db_machine_type

@router.delete("/{machine_type_id}", response_model=schemas.MachineType)
def delete_machine_type(machine_type_id: int, db: Session = Depends(get_db)):
    db_machine_type = crud.delete_machine_type(db, machine_type_id=machine_type_id)
    if db_machine_type is None:
        raise HTTPException(status_code=404, detail="Machine type not found")
    return db_machine_type