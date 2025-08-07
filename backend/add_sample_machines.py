import sys
import os
import requests
import json

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_sample_machines():
    # API base URL
    base_url = "http://localhost:8000/api/v1"
    
    # Sample machines with manufacturer information
    sample_machines = [
        {
            "name": "J750",
            "description": "High-performance test platform for complex semiconductor devices",
            "base_hourly_rate": 200.0,
            "active": True,
            "manufacturer": "Teradyne"
        },
        {
            "name": "J750EX",
            "description": "Enhanced version of J750 with additional capabilities",
            "base_hourly_rate": 250.0,
            "active": True,
            "manufacturer": "Teradyne"
        },
        {
            "name": "T2000",
            "description": "High-performance test platform for complex semiconductor devices",
            "base_hourly_rate": 300.0,
            "active": True,
            "manufacturer": "Advantest"
        },
        {
            "name": "S3000",
            "description": "Scalable test solution for mixed-signal devices",
            "base_hourly_rate": 250.0,
            "active": True,
            "manufacturer": "Advantest"
        },
        {
            "name": "U1000",
            "description": "Universal test platform for digital and analog devices",
            "base_hourly_rate": 180.0,
            "active": True,
            "manufacturer": "LTX-Credence"
        },
        {
            "name": "Fusion",
            "description": "High throughput test platform",
            "base_hourly_rate": 220.0,
            "active": True,
            "manufacturer": "Cohu"
        }
    ]
    
    print("Adding sample machines with manufacturer information...")
    
    for machine in sample_machines:
        try:
            response = requests.post(
                f"{base_url}/machines/",
                headers={"Content-Type": "application/json"},
                data=json.dumps(machine)
            )
            
            if response.status_code == 200:
                print(f"Successfully added machine: {machine['name']}")
            elif response.status_code == 422:
                print(f"Machine {machine['name']} may already exist")
            else:
                print(f"Failed to add machine {machine['name']}: {response.status_code}")
        except Exception as e:
            print(f"Error adding machine {machine['name']}: {e}")
    
    print("Finished adding sample machines.")

if __name__ == "__main__":
    add_sample_machines()