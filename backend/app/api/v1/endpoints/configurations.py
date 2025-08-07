from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/configurations", tags=["configurations"])


@router.get("/", response_model=List[schemas.Configuration])
def read_configurations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configurations = crud.get_configurations(db, skip=skip, limit=limit)
    return configurations


@router.get("/{configuration_id}", response_model=schemas.Configuration)
def read_configuration(configuration_id: int, db: Session = Depends(get_db)):
    db_configuration = crud.get_configuration(db, configuration_id=configuration_id)
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_configuration


@router.post("/", response_model=schemas.Configuration)
def create_configuration(configuration: schemas.ConfigurationCreate, db: Session = Depends(get_db)):
    return crud.create_configuration(db=db, configuration=configuration)


@router.put("/{configuration_id}", response_model=schemas.Configuration)
def update_configuration(configuration_id: int, configuration: schemas.ConfigurationUpdate, db: Session = Depends(get_db)):
    db_configuration = crud.update_configuration(db, configuration_id=configuration_id, configuration=configuration)
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_configuration


@router.delete("/{configuration_id}", response_model=schemas.Configuration)
def delete_configuration(configuration_id: int, db: Session = Depends(get_db)):
    db_configuration = crud.delete_configuration(db, configuration_id=configuration_id)
    if db_configuration is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_configuration