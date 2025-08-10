import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.database import SessionLocal, engine
    from app import models, schemas, crud
    
    def init_db():
        # Create tables
        print("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Check if data already exists
        existing_machines = crud.get_machines(db)
        if existing_machines:
            print("Database already initialized. Skipping data creation.")
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
        
        # Create sample configurations for each machine
        configurations_data = [
            schemas.ConfigurationCreate(
                name='Basic',
                description='Standard configuration',
                additional_rate=0.0,
                machine_id=created_machines[0].id
            ),
            schemas.ConfigurationCreate(
                name='Enhanced',
                description='Enhanced configuration with additional features',
                additional_rate=50.0,
                machine_id=created_machines[0].id
            ),
            schemas.ConfigurationCreate(
                name='Premium',
                description='Premium configuration with all features',
                additional_rate=100.0,
                machine_id=created_machines[1].id
            )
        ]
        
        created_configurations = []
        for config_data in configurations_data:
            config = crud.create_configuration(db, config_data)
            created_configurations.append(config)
        
        # Create sample card configs
        card_configs_data = [
            schemas.CardConfigCreate(
                part_number='DIG-001',
                board_name='Digital Card',
                unit_price=20.0,
                machine_id=created_machines[0].id
            ),
            schemas.CardConfigCreate(
                part_number='ANA-001',
                board_name='Analog Card',
                unit_price=30.0,
                machine_id=created_machines[1].id
            ),
            schemas.CardConfigCreate(
                part_number='RF-001',
                board_name='RF Card',
                unit_price=50.0,
                machine_id=created_machines[2].id
            ),
            schemas.CardConfigCreate(
                part_number='MIX-001',
                board_name='Mixed Signal Card',
                unit_price=40.0,
                machine_id=created_machines[0].id
            )
        ]
        
        created_card_configs = []
        for card_data in card_configs_data:
            card_config = crud.create_card_config(db, card_data)
            created_card_configs.append(card_config)
        
        # Create sample auxiliary equipment
        equipment_data = [
            schemas.AuxiliaryEquipmentCreate(
                name='Temperature Chamber',
                description='Environmental temperature testing chamber',
                hourly_rate=30.0,
                type='chamber'
            ),
            schemas.AuxiliaryEquipmentCreate(
                name='Handler',
                description='Device handling equipment',
                hourly_rate=25.0,
                type='handler'
            ),
            schemas.AuxiliaryEquipmentCreate(
                name='Prober',
                description='Wafer probing equipment',
                hourly_rate=40.0,
                type='prober'
            )
        ]
        
        created_equipment = []
        for equip_data in equipment_data:
            equipment = crud.create_auxiliary_equipment(db, equip_data)
            created_equipment.append(equipment)
        
        # Personnel model has been removed - using standard values instead
        print("Personnel data will be handled using standard values in quotation logic")
        
        db.close()
        print('Database initialized with sample data.')

    if __name__ == '__main__':
        init_db()
        
except Exception as e:
    print(f"Error initializing database: {e}")
    import traceback
    traceback.print_exc()