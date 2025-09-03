import sys
import os

# Add the project root directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.database import SessionLocal, engine, Base
from app import models, schemas, crud

def add_sample_data():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Add sample configurations
        machine = db.query(models.Machine).first()
        if machine:
            # Check if configurations already exist
            existing_configs = db.query(models.Configuration).count()
            if existing_configs == 0:
                config1 = models.Configuration(
                    name='Basic Configuration',
                    description='Basic test configuration',
                    additional_rate=1.2,
                    machine_id=machine.id
                )
                config2 = models.Configuration(
                    name='Advanced Configuration',
                    description='Advanced test configuration',
                    additional_rate=1.5,
                    machine_id=machine.id
                )
                db.add(config1)
                db.add(config2)
                print("Added sample configurations")
            else:
                print("Configurations already exist")
        else:
            print("No machines found in database")
            
        # Add sample auxiliary equipment
        existing_aux = db.query(models.AuxiliaryEquipment).count()
        if existing_aux == 0:
            aux1 = models.AuxiliaryEquipment(
                name='Temperature Chamber',
                description='Temperature testing chamber',
                hourly_rate=25.0
            )
            aux2 = models.AuxiliaryEquipment(
                name='Humidity Chamber',
                description='Humidity testing chamber',
                hourly_rate=20.0
            )
            db.add(aux1)
            db.add(aux2)
            print("Added sample auxiliary equipment")
        else:
            print("Auxiliary equipment already exists")
            
        # Commit changes
        db.commit()
        print("Sample data added successfully")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()