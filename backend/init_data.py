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
        
except Exception as e:
    print(f"Error initializing database: {e}")
    import traceback
    traceback.print_exc()