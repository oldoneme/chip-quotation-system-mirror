import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app import crud, schemas, models

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/machines", tags=["machines"])

@router.get("/", response_model=List[schemas.Machine])
def read_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("Fetching machines list...")
    machines = db.query(models.Machine).options(
        joinedload(models.Machine.supplier).joinedload(models.Supplier.machine_type)
    ).offset(skip).limit(limit).all()
    logger.info(f"Fetched {len(machines)} machines.")
    return machines

@router.get("/{machine_id}", response_model=schemas.Machine)
def read_machine(machine_id: int, db: Session = Depends(get_db)):
    db_machine = db.query(models.Machine).options(
        joinedload(models.Machine.supplier).joinedload(models.Supplier.machine_type)
    ).filter(models.Machine.id == machine_id).first()
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.post("/", response_model=schemas.Machine)
def create_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    return crud.create_machine(db=db, machine=machine)

@router.put("/{machine_id}", response_model=schemas.Machine)
def update_machine(machine_id: int, machine: schemas.MachineUpdate, db: Session = Depends(get_db)):
    db_machine = crud.update_machine(db, machine_id=machine_id, machine=machine)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.delete("/{machine_id}", response_model=schemas.Machine)
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    db_machine = crud.delete_machine(db, machine_id=machine_id)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.post("/{machine_id}/cards/{card_id}")
def add_card_to_machine(machine_id: int, card_id: int, db: Session = Depends(get_db)):
    db_machine = crud.get_machine(db, machine_id=machine_id)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # 这里应该添加将板卡关联到机器的逻辑
    # 暂时返回成功消息
    return {"message": f"Card {card_id} added to machine {machine_id}"}

@router.delete("/{machine_id}/cards/{card_id}")
def remove_card_from_machine(machine_id: int, card_id: int, db: Session = Depends(get_db)):
    db_machine = crud.get_machine(db, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # 删除对应的CardConfig
    db_card_config = db.query(models.CardConfig).filter(
        models.CardConfig.id == card_id,
        models.CardConfig.machine_id == machine_id
    ).first()
    
    if not db_card_config:
        raise HTTPException(status_code=404, detail="Card configuration not found")
    
    db.delete(db_card_config)
    db.commit()
    
    return {"message": "Card removed from machine successfully"}
