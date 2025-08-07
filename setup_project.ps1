# Chip Testing Quotation System - Automated Setup Script
Write-Host "Setting up Chip Testing Quotation System..." -ForegroundColor Green

# Create project structure
Write-Host "Creating project structure..." -ForegroundColor Yellow

# Backend directories
New-Item -ItemType Directory -Path "backend" -Force | Out-Null
New-Item -ItemType Directory -Path "backend/app" -Force | Out-Null
New-Item -ItemType Directory -Path "backend/app/api" -Force | Out-Null
New-Item -ItemType Directory -Path "backend/app/api/v1" -Force | Out-Null
New-Item -ItemType Directory -Path "backend/app/api/v1/endpoints" -Force | Out-Null

# Frontend directory
New-Item -ItemType Directory -Path "frontend" -Force | Out-Null

# Create backend files
Write-Host "Creating backend files..." -ForegroundColor Yellow

# requirements.txt
Set-Content -Path "backend/requirements.txt" -Value @"
fastapi>=0.100.0
uvicorn>=0.20.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-dotenv>=1.0.0
"@

# __init__.py files
Set-Content -Path "backend/app/__init__.py" -Value ""
Set-Content -Path "backend/app/api/__init__.py" -Value ""
Set-Content -Path "backend/app/api/v1/__init__.py" -Value ""
Set-Content -Path "backend/app/api/v1/endpoints/__init__.py" -Value ""

# database.py
Set-Content -Path "backend/app/database.py" -Value @"
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# For development, we'll use SQLite. In production, you can switch to PostgreSQL
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chip_quotation.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
"@

# models.py
Set-Content -Path "backend/app/models.py" -Value @"
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Association table for machine-configurations relationship
machine_configurations = Table(
    "machine_configurations",
    Base.metadata,
    Column("machine_id", Integer, ForeignKey("machines.id")),
    Column("configuration_id", Integer, ForeignKey("configurations.id"))
)

# Association table for configuration-card_types relationship
configuration_card_types = Table(
    "configuration_card_types",
    Base.metadata,
    Column("configuration_id", Integer, ForeignKey("configurations.id")),
    Column("card_type_id", Integer, ForeignKey("card_types.id"))
)

class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    base_hourly_rate = Column(Float)
    active = Column(Boolean, default=True)
    
    # Relationships
    configurations = relationship("Configuration", secondary=machine_configurations, back_populates="machines")

class Configuration(Base):
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    additional_rate = Column(Float, default=0.0)
    
    # Relationships
    machines = relationship("Machine", secondary=machine_configurations, back_populates="configurations")
    card_types = relationship("CardType", secondary=configuration_card_types, back_populates="card_types")

class CardType(Base):
    __tablename__ = "card_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    hourly_rate = Column(Float)
    
    # Relationships
    configurations = relationship("Configuration", secondary=configuration_card_types, back_populates="card_types")

class AuxiliaryEquipment(Base):
    __tablename__ = "auxiliary_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    hourly_rate = Column(Float)

class Personnel(Base):
    __tablename__ = "personnel"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)
    hourly_rate = Column(Float)
"@

# schemas.py
Set-Content -Path "backend/app/schemas.py" -Value @"
from pydantic import BaseModel
from typing import List, Optional

# Machine schemas
class MachineBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_hourly_rate: float
    active: Optional[bool] = True

class MachineCreate(MachineBase):
    pass

class MachineUpdate(MachineBase):
    name: Optional[str] = None
    base_hourly_rate: Optional[float] = None

class Machine(MachineBase):
    id: int
    
    class Config:
        from_attributes = True

# Configuration schemas
class ConfigurationBase(BaseModel):
    name: str
    description: Optional[str] = None
    additional_rate: Optional[float] = 0.0

class ConfigurationCreate(ConfigurationBase):
    pass

class Configuration(ConfigurationBase):
    id: int
    
    class Config:
        from_attributes = True

# Card Type schemas
class CardTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    hourly_rate: float

class CardTypeCreate(CardTypeBase):
    pass

class CardType(CardTypeBase):
    id: int
    
    class Config:
        from_attributes = True

# Auxiliary Equipment schemas
class AuxiliaryEquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    hourly_rate: float

class AuxiliaryEquipmentCreate(AuxiliaryEquipmentBase):
    pass

class AuxiliaryEquipment(AuxiliaryEquipmentBase):
    id: int
    
    class Config:
        from_attributes = True

# Personnel schemas
class PersonnelBase(BaseModel):
    name: str
    role: str
    hourly_rate: float

class PersonnelCreate(PersonnelBase):
    pass

class Personnel(PersonnelBase):
    id: int
    
    class Config:
        from_attributes = True

# Quotation schemas
class QuotationRequest(BaseModel):
    machine_id: int
    configuration_id: int
    card_types: List[int] = []
    auxiliary_equipment_ids: List[int] = []
    personnel_ids: List[int] = []
    test_hours: float

class QuotationItem(BaseModel):
    name: str
    rate: float
    quantity: float
    subtotal: float

class QuotationResponse(BaseModel):
    items: List[QuotationItem]
    total: float
"@

# crud.py
Set-Content -Path "backend/app/crud.py" -Value @"
from sqlalchemy.orm import Session
from . import models, schemas

# Machine CRUD operations
def get_machine(db: Session, machine_id: int):
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def get_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Machine).offset(skip).limit(limit).all()

def create_machine(db: Session, machine: schemas.MachineCreate):
    db_machine = models.Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

def update_machine(db: Session, machine_id: int, machine: schemas.MachineUpdate):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        update_data = machine.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_machine, key, value)
        db.commit()
        db.refresh(db_machine)
    return db_machine

def delete_machine(db: Session, machine_id: int):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        db.delete(db_machine)
        db.commit()
    return db_machine

# Configuration CRUD operations
def get_configuration(db: Session, configuration_id: int):
    return db.query(models.Configuration).filter(models.Configuration.id == configuration_id).first()

def get_configurations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Configuration).offset(skip).limit(limit).all()

def create_configuration(db: Session, configuration: schemas.ConfigurationCreate):
    db_configuration = models.Configuration(**configuration.dict())
    db.add(db_configuration)
    db.commit()
    db.refresh(db_configuration)
    return db_configuration

# Card Type CRUD operations
def get_card_type(db: Session, card_type_id: int):
    return db.query(models.CardType).filter(models.CardType.id == card_type_id).first()

def get_card_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CardType).offset(skip).limit(limit).all()

def create_card_type(db: Session, card_type: schemas.CardTypeCreate):
    db_card_type = models.CardType(**card_type.dict())
    db.add(db_card_type)
    db.commit()
    db.refresh(db_card_type)
    return db_card_type

# Auxiliary Equipment CRUD operations
def get_auxiliary_equipment(db: Session, equipment_id: int):
    return db.query(models.AuxiliaryEquipment).filter(models.AuxiliaryEquipment.id == equipment_id).first()

def get_auxiliary_equipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AuxiliaryEquipment).offset(skip).limit(limit).all()

def create_auxiliary_equipment(db: Session, equipment: schemas.AuxiliaryEquipmentCreate):
    db_equipment = models.AuxiliaryEquipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

# Personnel CRUD operations
def get_personnel(db: Session, personnel_id: int):
    return db.query(models.Personnel).filter(models.Personnel.id == personnel_id).first()

def get_all_personnel(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Personnel).offset(skip).limit(limit).all()

def create_personnel(db: Session, personnel: schemas.PersonnelCreate):
    db_personnel = models.Personnel(**personnel.dict())
    db.add(db_personnel)
    db.commit()
    db.refresh(db_personnel)
    return db_personnel

# Quotation calculation
def calculate_quotation(db: Session, quotation_request: schemas.QuotationRequest):
    # Get machine
    machine = get_machine(db, quotation_request.machine_id)
    if not machine:
        raise ValueError("Machine not found")
    
    # Get configuration
    configuration = get_configuration(db, quotation_request.configuration_id)
    if not configuration:
        raise ValueError("Configuration not found")
    
    items = []
    
    # Machine base rate
    items.append(schemas.QuotationItem(
        name=f"Machine: {machine.name}",
        rate=machine.base_hourly_rate,
        quantity=quotation_request.test_hours,
        subtotal=machine.base_hourly_rate * quotation_request.test_hours
    ))
    
    # Configuration additional rate
    if configuration.additional_rate > 0:
        items.append(schemas.QuotationItem(
            name=f"Configuration: {configuration.name}",
            rate=configuration.additional_rate,
            quantity=quotation_request.test_hours,
            subtotal=configuration.additional_rate * quotation_request.test_hours
        ))
    
    # Card types
    for card_type_id in quotation_request.card_types:
        card_type = get_card_type(db, card_type_id)
        if card_type:
            items.append(schemas.QuotationItem(
                name=f"Card Type: {card_type.name}",
                rate=card_type.hourly_rate,
                quantity=quotation_request.test_hours,
                subtotal=card_type.hourly_rate * quotation_request.test_hours
            ))
    
    # Auxiliary equipment
    for equipment_id in quotation_request.auxiliary_equipment_ids:
        equipment = get_auxiliary_equipment(db, equipment_id)
        if equipment:
            items.append(schemas.QuotationItem(
                name=f"Auxiliary Equipment: {equipment.name}",
                rate=equipment.hourly_rate,
                quantity=quotation_request.test_hours,
                subtotal=equipment.hourly_rate * quotation_request.test_hours
            ))
    
    # Personnel
    for personnel_id in quotation_request.personnel_ids:
        personnel = get_personnel(db, personnel_id)
        if personnel:
            items.append(schemas.QuotationItem(
                name=f"Personnel: {personnel.name} ({personnel.role})",
                rate=personnel.hourly_rate,
                quantity=quotation_request.test_hours,
                subtotal=personnel.hourly_rate * quotation_request.test_hours
            ))
    
    # Calculate total
    total = sum(item.subtotal for item in items)
    
    return schemas.QuotationResponse(items=items, total=total)
"@

# machines.py endpoint
Set-Content -Path "backend/app/api/v1/endpoints/machines.py" -Value @"
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas
from ....database import get_db

router = APIRouter(prefix="/machines", tags=["machines"])

@router.get("/", response_model=List[schemas.Machine])
def read_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    machines = crud.get_machines(db, skip=skip, limit=limit)
    return machines

@router.get("/{machine_id}", response_model=schemas.Machine)
def read_machine(machine_id: int, db: Session = Depends(get_db)):
    db_machine = crud.get_machine(db, machine_id=machine_id)
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
"@

# quotations.py endpoint
Set-Content -Path "backend/app/api/v1/endpoints/quotations.py" -Value @"
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .... import crud, schemas
from ....database import get_db

router = APIRouter(prefix="/quotations", tags=["quotations"])

@router.post("/calculate", response_model=schemas.QuotationResponse)
def calculate_quotation(quotation_request: schemas.QuotationRequest, db: Session = Depends(get_db)):
    try:
        return crud.calculate_quotation(db, quotation_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"@

# api.py
Set-Content -Path "backend/app/api/v1/api.py" -Value @"
from fastapi import APIRouter
from .endpoints import machines, quotations

api_router = APIRouter()
api_router.include_router(machines.router)
api_router.include_router(quotations.router)
"@

# main.py
Set-Content -Path "backend/app/main.py" -Value @"
from fastapi import FastAPI
from .database import engine, Base
from .api.v1.api import api_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chip Testing Quotation System", version="0.1.0")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to Chip Testing Quotation System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"@

# init_data.py
Set-Content -Path "backend/init_data.py" -Value @"
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app import models, schemas, crud

def init_db():
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if data already exists
    existing_machines = crud.get_machines(db)
    if existing_machines:
        print('Database already initialized. Skipping data creation.')
        db.close()
        return
    
    # Create sample machines
    machines_data = [
        schemas.MachineCreate(
            name='ATE-1000',
            description='Basic Automatic Test Equipment',
            base_hourly_rate=150.0
        ),
        schemas.MachineCreate(
            name='ATE-2000',
            description='Advanced Automatic Test Equipment with high precision',
            base_hourly_rate=250.0
        ),
        schemas.MachineCreate(
            name='ATE-3000',
            description='Premium Automatic Test Equipment with multi-site testing',
            base_hourly_rate=400.0
        )
    ]
    
    created_machines = []
    for machine_data in machines_data:
        machine = crud.create_machine(db, machine_data)
        created_machines.append(machine)
    
    # Create sample configurations
    configurations_data = [
        schemas.ConfigurationCreate(
            name='Basic',
            description='Standard configuration',
            additional_rate=0.0
        ),
        schemas.ConfigurationCreate(
            name='Enhanced',
            description='Enhanced configuration with additional features',
            additional_rate=50.0
        ),
        schemas.ConfigurationCreate(
            name='Premium',
            description='Premium configuration with all features',
            additional_rate=100.0
        )
    ]
    
    created_configurations = []
    for config_data in configurations_data:
        config = crud.create_configuration(db, config_data)
        created_configurations.append(config)
    
    # Create sample card types
    card_types_data = [
        schemas.CardTypeCreate(
            name='Digital Card',
            description='Digital signal testing card',
            hourly_rate=20.0
        ),
        schemas.CardTypeCreate(
            name='Analog Card',
            description='Analog signal testing card',
            hourly_rate=30.0
        ),
        schemas.CardTypeCreate(
            name='RF Card',
            description='Radio frequency testing card',
            hourly_rate=50.0
        ),
        schemas.CardTypeCreate(
            name='Mixed Signal Card',
            description='Mixed signal testing card',
            hourly_rate=40.0
        )
    ]
    
    created_card_types = []
    for card_data in card_types_data:
        card_type = crud.create_card_type(db, card_data)
        created_card_types.append(card_type)
    
    # Create sample auxiliary equipment
    equipment_data = [
        schemas.AuxiliaryEquipmentCreate(
            name='Temperature Chamber',
            description='Environmental temperature testing chamber',
            hourly_rate=30.0
        ),
        schemas.AuxiliaryEquipmentCreate(
            name='Handler',
            description='Device handling equipment',
            hourly_rate=25.0
        ),
        schemas.AuxiliaryEquipmentCreate(
            name='Prober',
            description='Wafer probing equipment',
            hourly_rate=40.0
        )
    ]
    
    created_equipment = []
    for equip_data in equipment_data:
        equipment = crud.create_auxiliary_equipment(db, equip_data)
        created_equipment.append(equipment)
    
    # Create sample personnel
    personnel_data = [
        schemas.PersonnelCreate(
            name='Test Engineer',
            role='Engineer',
            hourly_rate=80.0
        ),
        schemas.PersonnelCreate(
            name='Senior Test Engineer',
            role='Senior Engineer',
            hourly_rate=120.0
        ),
        schemas.PersonnelCreate(
            name='Test Technician',
            role='Technician',
            hourly_rate=50.0
        )
    ]
    
    created_personnel = []
    for person_data in personnel_data:
        personnel = crud.create_personnel(db, person_data)
        created_personnel.append(personnel)
    
    db.close()
    print('Database initialized with sample data.')

if __name__ == '__main__':
    init_db()
"@

# Create frontend React app
Write-Host "Setting up frontend React app..." -ForegroundColor Yellow

# Change to frontend directory
Set-Location -Path "frontend"

# Create package.json to define the create-react-app command
Set-Content -Path "package.json" -Value @"
{
  "name": "chip-quotation-frontend",
  "version": "0.1.0",
  "scripts": {
    "setup": "npx create-react-app chip-quotation-frontend --template typescript && cd chip-quotation-frontend && npm install antd axios react-router-dom"
  }
}
"@

# Since we can't directly run create-react-app from PowerShell script, we'll create a batch file
Set-Content -Path "setup_frontend.bat" -Value @"
@echo off
npx create-react-app chip-quotation-frontend --template typescript
cd chip-quotation-frontend
npm install antd axios react-router-dom
"@

# Back to root directory
Set-Location -Path ".."

# Create startup scripts
Write-Host "Creating startup scripts..." -ForegroundColor Yellow

# start_backend.ps1
Set-Content -Path "start_backend.ps1" -Value @"
# Navigate to backend directory
Set-Location -Path 'backend'

# Check if virtual environment exists
if (-not (Test-Path 'venv')) {
    Write-Host 'Creating virtual environment...' -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host 'Activating virtual environment...' -ForegroundColor Yellow
& venv/Scripts/Activate.ps1

# Install dependencies
Write-Host 'Installing dependencies...' -ForegroundColor Yellow
pip install -r requirements.txt

# Initialize database with sample data
Write-Host 'Initializing database...' -ForegroundColor Yellow
python init_data.py

# Start the backend server
Write-Host 'Starting backend server...' -ForegroundColor Yellow
Write-Host 'Backend API will be available at http://localhost:8000' -ForegroundColor Cyan
Write-Host 'API Documentation at http://localhost:8000/docs' -ForegroundColor Cyan
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

# start_frontend.ps1
Set-Content -Path "start_frontend.ps1" -Value @"
# Navigate to frontend directory
Set-Location -Path 'frontend/chip-quotation-frontend'

# Start the frontend development server
Write-Host 'Starting frontend server...' -ForegroundColor Yellow
Write-Host 'Frontend will be available at http://localhost:3000' -ForegroundColor Cyan
npm start
"@

# Create README.md
Write-Host "Creating documentation..." -ForegroundColor Yellow

Set-Content -Path "README.md" -Value @"
# Chip Testing Hourly Rate Quotation System

A full-stack web application for automatically calculating chip testing hourly rates based on selected equipment, configurations, and resources.

## Features

- Machine selection with different capabilities and rates
- Configuration options with additional costs
- Card type selection for specific testing needs
- Auxiliary equipment options
- Personnel allocation with different skill levels
- Real-time quotation calculation

## Technology Stack

### Backend
- FastAPI (Python)
- PostgreSQL (can use SQLite for development)
- SQLAlchemy ORM

### Frontend
- React.js (TypeScript)
- Ant Design
- Axios for API requests

## Project Structure
chip-quotation-system/ 
├── backend/ # FastAPI backend 
│ ├── app/ # Application source code 
│ │ ├── api/ # API endpoints 
│ │ ├── models.py # Database models 
│ │ ├── schemas.py # Pydantic schemas 
│ │ ├── crud.py # Database operations 
│ │ ├── database.py # Database configuration 
│ │ └── main.py # FastAPI application 
│ ├── requirements.txt # Python dependencies 
│ └── init_data.py # Sample data initialization 
├── frontend/ # React frontend 
│ └── chip-quotation-frontend/ 
├── start_backend.ps1 # Backend startup script 
├── start_frontend.ps1 # Frontend startup script 
└── README.md


## Getting Started

### Prerequisites

- Python 3.7+
- Node.js 14+
- PostgreSQL (optional, can use SQLite for development)

### Installation

1. Clone or create the project:
   ```bash
   # If you're reading this, you've already done this step

"@