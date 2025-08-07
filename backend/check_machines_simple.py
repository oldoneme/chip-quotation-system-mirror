from app.database import SessionLocal
from app.models import Machine

db = SessionLocal()
machines = db.query(Machine).all()
print(f'总机器数: {len(machines)}')

for m in machines[:10]:
    machine_type_name = "未知"
    if m.supplier and m.supplier.machine_type:
        machine_type_name = m.supplier.machine_type.name
    print(f'{m.name} - 类型: {machine_type_name}')

db.close()