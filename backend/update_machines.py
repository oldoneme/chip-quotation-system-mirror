import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, Base
from app import models, schemas
from app.crud import get_machines, update_machine

def update_machines_with_manufacturer():
    # Create a database session
    db = Session(bind=engine)
    
    try:
        # Get all existing machines
        machines = get_machines(db)
        
        # Define manufacturer mappings
        manufacturer_mapping = {
            "ATE-1000": "Teradyne",
            "ATE-2000": "Teradyne",
            "J750": "Teradyne",
            "J750EX": "Teradyne",
            "T2000": "Advantest",
            "S3000": "Advantest",
            "U1000": "LTX-Credence",
            "U2000": "LTX-Credence",
            "Fusion": "Cohu",
            "Integra": "Cohu"
        }
        
        # Update each machine with manufacturer information
        for machine in machines:
            manufacturer = manufacturer_mapping.get(machine.name, "Other")
            
            # Update machine with manufacturer
            update_data = schemas.MachineUpdate(
                manufacturer=manufacturer
            )
            
            # Perform the update
            updated_machine = update_machine(db, machine.id, update_data)
            if updated_machine:
                print(f"Updated machine {machine.name} with manufacturer {manufacturer}")
            else:
                print(f"Failed to update machine {machine.name}")
        
        print("All machines updated successfully!")
        
    except Exception as e:
        print(f"Error updating machines: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_machines_with_manufacturer()