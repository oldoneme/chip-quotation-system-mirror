import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import engine
from app import models

def check_machines():
    # Create a database session
    db = Session(bind=engine)
    
    try:
        # Get all existing machines
        machines = db.query(models.Machine).all()
        
        print("Machines in database:")
        print("-" * 50)
        for machine in machines:
            print(f"ID: {machine.id:2d} | Name: {machine.name:15s} | Manufacturer: {machine.manufacturer or 'None':15s} | Rate: {machine.base_hourly_rate}")
            
        # Count machines with and without manufacturers
        with_manufacturer = sum(1 for machine in machines if machine.manufacturer)
        without_manufacturer = sum(1 for machine in machines if not machine.manufacturer)
        
        print("-" * 50)
        print(f"Total machines: {len(machines)}")
        print(f"Machines with manufacturer: {with_manufacturer}")
        print(f"Machines without manufacturer: {without_manufacturer}")
        
        # List unique manufacturers
        manufacturers = list(set(machine.manufacturer for machine in machines if machine.manufacturer))
        print(f"Unique manufacturers: {manufacturers}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_machines()