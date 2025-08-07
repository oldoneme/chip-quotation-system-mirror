from sqlalchemy.orm import Session
from . import models

def init_db_data(db: Session):
    # Check if data already exists
    existing_suppliers = db.query(models.Supplier).count()
    if existing_suppliers > 0:
        return  # Data already initialized

    # Create sample suppliers
    suppliers = [
        models.Supplier(name="Teradyne"),
        models.Supplier(name="Advantest"),
        models.Supplier(name="LTX-Credence"),
        models.Supplier(name="Cohu")
    ]
    
    for supplier in suppliers:
        db.add(supplier)
    
    # Commit suppliers first
    db.commit()
    
    # Get all suppliers
    all_suppliers = db.query(models.Supplier).all()
    
    # Create sample machines
    machines = [
        models.Machine(
            model="J750",
            supplier_id=all_suppliers[0].id  # Teradyne
        ),
        models.Machine(
            model="J750EX",
            supplier_id=all_suppliers[0].id  # Teradyne
        ),
        models.Machine(
            model="T2000",
            supplier_id=all_suppliers[1].id  # Advantest
        ),
        models.Machine(
            model="S3000",
            supplier_id=all_suppliers[1].id  # Advantest
        ),
        models.Machine(
            model="U1000",
            supplier_id=all_suppliers[2].id  # LTX-Credence
        ),
        models.Machine(
            model="Fusion",
            supplier_id=all_suppliers[3].id  # Cohu
        )
    ]
    
    for machine in machines:
        db.add(machine)
    
    # Commit machines
    db.commit()
    
    # Get all machines
    all_machines = db.query(models.Machine).all()
    
    # Create sample cards
    cards = [
        models.Card(model="APU12"),
        models.Card(model="SPU112"),
        models.Card(model="HSD80"),
        models.Card(model="HDM800"),
        models.Card(model="HDM800D")
    ]
    
    for card in cards:
        db.add(card)
    
    # Commit cards
    db.commit()
    
    # Get all cards
    all_cards = db.query(models.Card).all()
    
    # Associate machines with cards (Many-to-Many relationship)
    # J750 uses APU12, SPU112, HSD80
    all_machines[0].cards.extend([all_cards[0], all_cards[1], all_cards[2]])
    
    # J750EX uses APU12, SPU112, HSD80
    all_machines[1].cards.extend([all_cards[0], all_cards[1], all_cards[2]])
    
    # T2000 uses HDM800, HDM800D
    all_machines[2].cards.extend([all_cards[3], all_cards[4]])
    
    # S3000 uses HDM800, HDM800D
    all_machines[3].cards.extend([all_cards[3], all_cards[4]])
    
    # Commit relationships
    db.commit()
    
    # Create sample configurations (保持现有结构)
    configurations = [
        models.Configuration(
            name="Basic",
            description="Standard configuration",
            additional_rate=0.0
        ),
        models.Configuration(
            name="Enhanced",
            description="Enhanced configuration with additional features",
            additional_rate=50.0
        ),
        models.Configuration(
            name="Premium",
            description="Premium configuration with all features enabled",
            additional_rate=100.0
        )
    ]
    
    for config in configurations:
        db.add(config)
    
    # Create sample card types with new fields (保持现有结构)
    card_types = [
        models.CardType(
            name="Digital Card",
            description="Digital signal testing card",
            hourly_rate=20.0,
            part_number="DC-1000",
            board_name="Digital Card Board",
            unit_price=500.0
        ),
        models.CardType(
            name="Analog Card",
            description="Analog signal testing card",
            hourly_rate=30.0,
            part_number="AC-2000",
            board_name="Analog Card Board",
            unit_price=750.0
        ),
        models.CardType(
            name="RF Card",
            description="Radio frequency testing card",
            hourly_rate=40.0,
            part_number="RF-3000",
            board_name="RF Card Board",
            unit_price=1200.0
        ),
        models.CardType(
            name="Power Card",
            description="High power testing card",
            hourly_rate=35.0,
            part_number="PC-4000",
            board_name="Power Card Board",
            unit_price=1000.0
        )
    ]
    
    for card in card_types:
        db.add(card)
    
    # Create sample auxiliary equipment
    aux_equipments = [
        models.AuxiliaryEquipment(
            name="Temperature Chamber",
            description="Environmental temperature testing chamber",
            hourly_rate=30.0
        ),
        models.AuxiliaryEquipment(
            name="Handler",
            description="Device handling equipment",
            hourly_rate=25.0
        ),
        models.AuxiliaryEquipment(
            name="Prober",
            description="Wafer probing equipment",
            hourly_rate=40.0
        )
    ]
    
    for equipment in aux_equipments:
        db.add(equipment)
    
    # Commit all changes
    db.commit()
    
    # Create relationships for existing structure
    # Get all objects
    all_configs = db.query(models.Configuration).all()
    all_card_types = db.query(models.CardType).all()
    
    # Associate machines with configurations (保持现有结构)
    for i, machine in enumerate(all_machines):
        # Each machine gets 2 configurations
        machine.configurations.append(all_configs[i % len(all_configs)])
        if i < len(all_configs):
            machine.configurations.append(all_configs[(i + 1) % len(all_configs)])
    
    # Associate configurations with card types (保持现有结构)
    for i, config in enumerate(all_configs):
        # Each configuration gets 2 card types
        config.card_types.append(all_card_types[i % len(all_card_types)])
        if i < len(all_card_types):
            config.card_types.append(all_card_types[(i + 1) % len(all_card_types)])
    
    # Commit relationship changes
    db.commit()