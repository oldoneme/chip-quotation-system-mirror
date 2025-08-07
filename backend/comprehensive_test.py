import requests
import json

def comprehensive_test():
    base_url = 'http://localhost:8000/api/v1'
    
    # 测试机器类型
    print("=== Testing Machine Types ===")
    try:
        response = requests.get(f'{base_url}/machine-types/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            machine_types = response.json()
            print("Machine Types:")
            print(json.dumps(machine_types, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\n=== Testing Machines ===")
    try:
        response = requests.get(f'{base_url}/machines/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            machines = response.json()
            print(f"Total Machines: {len(machines)}")
            print("First 3 Machines:")
            for machine in machines[:3]:
                print(f"  ID: {machine.get('id')}, Name: {machine.get('name')}")
                if machine.get('supplier'):
                    supplier = machine['supplier']
                    print(f"    Supplier: {supplier.get('name')}")
                    if supplier.get('machine_type'):
                        machine_type = supplier['machine_type']
                        print(f"      Machine Type: {machine_type.get('name')}")
                print()
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
        
    print("\n=== Testing Suppliers ===")
    try:
        response = requests.get(f'{base_url}/suppliers/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            suppliers = response.json()
            print(f"Total Suppliers: {len(suppliers)}")
            print("Suppliers:")
            for supplier in suppliers:
                print(f"  ID: {supplier.get('id')}, Name: {supplier.get('name')}, Machine Type ID: {supplier.get('machine_type_id')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    comprehensive_test()