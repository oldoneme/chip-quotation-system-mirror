from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/hierarchical", tags=["hierarchical"])

class HierarchicalCardConfig(schemas.CardConfig):
    class Config:
        from_attributes = True

class HierarchicalMachine(schemas.MachineBase):
    id: int
    card_configs: List[HierarchicalCardConfig] = []
    
    class Config:
        from_attributes = True

class HierarchicalSupplier(schemas.SupplierBase):
    id: int
    machines: List[HierarchicalMachine] = []
    
    class Config:
        from_attributes = True

class HierarchicalMachineType(schemas.MachineTypeBase):
    id: int
    suppliers: List[HierarchicalSupplier] = []
    
    class Config:
        from_attributes = True

@router.get("/machine-types", response_model=List[HierarchicalMachineType])
def get_hierarchical_machine_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    machine_types = crud.get_machine_types(db, skip=skip, limit=limit)
    hierarchical_machine_types = []
    
    for machine_type in machine_types:
        hierarchical_suppliers = []
        for supplier in machine_type.suppliers:
            hierarchical_machines = []
            for machine in supplier.machines:
                hierarchical_card_configs = []
                for card_config in machine.card_configs:
                    hierarchical_card_configs.append(HierarchicalCardConfig(
                        id=card_config.id,
                        part_number=card_config.part_number,
                        board_name=card_config.board_name,
                        unit_price=card_config.unit_price,
                        machine_id=card_config.machine_id
                    ))
                
                hierarchical_machines.append(HierarchicalMachine(
                    id=machine.id,
                    name=machine.name,
                    description=machine.description,
                    active=machine.active,
                    manufacturer=machine.manufacturer,
                    discount_rate=machine.discount_rate,
                    exchange_rate=machine.exchange_rate,
                    currency=machine.currency,
                    supplier_id=machine.supplier_id,
                    card_configs=hierarchical_card_configs
                ))
            
            hierarchical_suppliers.append(HierarchicalSupplier(
                id=supplier.id,
                name=supplier.name,
                machine_type_id=supplier.machine_type_id,
                machines=hierarchical_machines
            ))
        
        hierarchical_machine_types.append(HierarchicalMachineType(
            id=machine_type.id,
            name=machine_type.name,
            description=machine_type.description,
            suppliers=hierarchical_suppliers
        ))
    
    return hierarchical_machine_types

@router.post("/machine-types", response_model=HierarchicalMachineType)
def create_hierarchical_machine_type(machine_type: schemas.MachineTypeCreate, db: Session = Depends(get_db)):
    db_machine_type = crud.get_machine_type_by_name(db, name=machine_type.name)
    if db_machine_type:
        raise HTTPException(status_code=400, detail="Machine type already registered")
    return crud.create_machine_type(db=db, machine_type=machine_type)