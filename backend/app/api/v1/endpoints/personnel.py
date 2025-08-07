from fastapi import APIRouter, HTTPException
from typing import List

from app import schemas

router = APIRouter(prefix="/personnel", tags=["personnel"])

# 标准人员列表
PERSONNEL_LIST = [
    schemas.Personnel(
        id=1,
        name="Test Engineer",
        role="Engineer",
        hourly_rate=50.0,
        hours_per_day=8,
        days_per_week=5,
        weeks_per_year=48,
        vacation_weeks=4,
        sick_weeks=2,
        hourly_rate_currency="USD",
        hourly_rate_usd=50.0
    ),
    schemas.Personnel(
        id=2,
        name="Senior Test Engineer",
        role="Engineer",
        hourly_rate=75.0,
        hours_per_day=8,
        days_per_week=5,
        weeks_per_year=48,
        vacation_weeks=4,
        sick_weeks=2,
        hourly_rate_currency="USD",
        hourly_rate_usd=75.0
    ),
    schemas.Personnel(
        id=3,
        name="Test Technician",
        role="Technician",
        hourly_rate=35.0,
        hours_per_day=8,
        days_per_week=5,
        weeks_per_year=48,
        vacation_weeks=4,
        sick_weeks=2,
        hourly_rate_currency="USD",
        hourly_rate_usd=35.0
    ),
    schemas.Personnel(
        id=4,
        name="Senior Test Technician",
        role="Technician",
        hourly_rate=45.0,
        hours_per_day=8,
        days_per_week=5,
        weeks_per_year=48,
        vacation_weeks=4,
        sick_weeks=2,
        hourly_rate_currency="USD",
        hourly_rate_usd=45.0
    ),
    schemas.Personnel(
        id=5,
        name="Test Manager",
        role="Manager",
        hourly_rate=85.0,
        hours_per_day=8,
        days_per_week=5,
        weeks_per_year=48,
        vacation_weeks=4,
        sick_weeks=2,
        hourly_rate_currency="USD",
        hourly_rate_usd=85.0
    )
]

@router.get("/", response_model=List[schemas.Personnel])
def read_personnel(skip: int = 0, limit: int = 100):
    return PERSONNEL_LIST[skip : skip + limit]

@router.get("/{personnel_id}", response_model=schemas.Personnel)
def read_personnel_by_id(personnel_id: int):
    for personnel in PERSONNEL_LIST:
        if personnel.id == personnel_id:
            return personnel
    raise HTTPException(status_code=404, detail="Personnel not found")

@router.post("/", response_model=schemas.Personnel)
def create_personnel(personnel: schemas.PersonnelCreate):
    new_id = max([p.id for p in PERSONNEL_LIST]) + 1 if PERSONNEL_LIST else 1
    new_personnel = schemas.Personnel(
        id=new_id,
        name=personnel.name,
        role=personnel.role,
        hourly_rate=personnel.hourly_rate,
        hours_per_day=personnel.hours_per_day,
        days_per_week=personnel.days_per_week,
        weeks_per_year=personnel.weeks_per_year,
        vacation_weeks=personnel.vacation_weeks,
        sick_weeks=personnel.sick_weeks,
        hourly_rate_currency=personnel.hourly_rate_currency,
        hourly_rate_usd=personnel.hourly_rate_usd
    )
    PERSONNEL_LIST.append(new_personnel)
    return new_personnel

@router.put("/{personnel_id}", response_model=schemas.Personnel)
def update_personnel(personnel_id: int, personnel_update: schemas.PersonnelCreate):
    for i, personnel in enumerate(PERSONNEL_LIST):
        if personnel.id == personnel_id:
            updated_personnel = schemas.Personnel(
                id=personnel_id,
                name=personnel_update.name,
                role=personnel_update.role,
                hourly_rate=personnel_update.hourly_rate,
                hours_per_day=personnel_update.hours_per_day,
                days_per_week=personnel_update.days_per_week,
                weeks_per_year=personnel_update.weeks_per_year,
                vacation_weeks=personnel_update.vacation_weeks,
                sick_weeks=personnel_update.sick_weeks,
                hourly_rate_currency=personnel_update.hourly_rate_currency,
                hourly_rate_usd=personnel_update.hourly_rate_usd
            )
            PERSONNEL_LIST[i] = updated_personnel
            return updated_personnel
    raise HTTPException(status_code=404, detail="Personnel not found")

@router.delete("/{personnel_id}", response_model=schemas.Personnel)
def delete_personnel(personnel_id: int):
    for i, personnel in enumerate(PERSONNEL_LIST):
        if personnel.id == personnel_id:
            deleted_personnel = PERSONNEL_LIST.pop(i)
            return deleted_personnel
    raise HTTPException(status_code=404, detail="Personnel not found")