from app.database import SessionLocal
from app import models

def check_database_content():
    db = SessionLocal()
    
    print("Checking database content...")
    
    # Check machines
    machines = db.query(models.Machine).all()
    print(f"\nMachines ({len(machines)}):")
    for machine in machines:
        print(f"  {machine.id}: {machine.name} (supplier_id: {machine.supplier_id})")
        
        # Check card configs for this machine
        card_configs = db.query(models.CardConfig).filter(
            models.CardConfig.machine_id == machine.id
        ).all()
        print(f"    Card configs ({len(card_configs)}):")
        for card in card_configs:
            print(f"      {card.id}: {card.part_number} - {card.board_name} (¥{card.unit_price})")
    
    # Check auxiliary equipment
    aux_equipments = db.query(models.AuxiliaryEquipment).all()
    print(f"\nAuxiliary Equipment ({len(aux_equipments)}):")
    for equipment in aux_equipments:
        print(f"  {equipment.id}: {equipment.name} (type: {equipment.type}, hourly_rate: {equipment.hourly_rate})")
    
    db.close()

if __name__ == "__main__":
    check_database_content()