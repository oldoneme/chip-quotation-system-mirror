from app.database import SessionLocal
from app import models

def check_machine_types():
    db = SessionLocal()
    
    print("Checking machine types and related data...")
    
    # Check machine types
    machine_types = db.query(models.MachineType).all()
    print(f"\nMachine Types ({len(machine_types)}):")
    for mt in machine_types:
        print(f"  {mt.id}: {mt.name}")
        
        # Check suppliers for this machine type
        suppliers = db.query(models.Supplier).filter(
            models.Supplier.machine_type_id == mt.id
        ).all()
        print(f"    Suppliers ({len(suppliers)}):")
        for supplier in suppliers:
            print(f"      {supplier.id}: {supplier.name}")
            
            # Check machines for this supplier
            machines = db.query(models.Machine).filter(
                models.Machine.supplier_id == supplier.id
            ).all()
            print(f"        Machines ({len(machines)}):")
            for machine in machines:
                print(f"          {machine.id}: {machine.name}")

    # Check all machines with their suppliers and machine types
    print(f"\nAll Machines:")
    machines = db.query(models.Machine).all()
    for machine in machines:
        supplier = machine.supplier
        if supplier:
            machine_type = supplier.machine_type
            if machine_type:
                print(f"  {machine.id}: {machine.name} - Supplier: {supplier.name} - Type: {machine_type.name}")
            else:
                print(f"  {machine.id}: {machine.name} - Supplier: {supplier.name} - Type: None")
        else:
            print(f"  {machine.id}: {machine.name} - Supplier: None")
    
    db.close()

if __name__ == "__main__":
    check_machine_types()