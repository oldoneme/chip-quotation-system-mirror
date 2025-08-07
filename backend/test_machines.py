import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, Base
from app import models

def test_machines():
    # Create a database session
    db = Session(bind=engine)
    
    try:
        # Get all existing machines
        machines = db.query(models.Machine).all()
        
        print("Current machines in database:")
        for machine in machines:
            print(f"ID: {machine.id}, Name: {machine.name}, Manufacturer: {machine.manufacturer}")
            
        # If no machines have manufacturer, let's add some
        if all(machine.manufacturer is None for machine in machines):
            print("\nUpdating machines with manufacturer information...")
            
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
                if machine.name in manufacturer_mapping:
                    machine.manufacturer = manufacturer_mapping[machine.name]
                else:
                    machine.manufacturer = "Other"
                    
                print(f"Setting manufacturer for {machine.name} to {machine.manufacturer}")
                
            # Commit changes
            db.commit()
            print("All machines updated successfully!")
            
            # Verify updates
            machines = db.query(models.Machine).all()
            print("\nUpdated machines in database:")
            for machine in machines:
                print(f"ID: {machine.id}, Name: {machine.name}, Manufacturer: {machine.manufacturer}")
        else:
            print("\nMachines already have manufacturer information.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_machines()