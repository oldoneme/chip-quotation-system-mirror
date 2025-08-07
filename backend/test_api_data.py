import requests
import json

def test_api_data():
    # 测试获取机器数据
    try:
        response = requests.get('http://localhost:8000/api/v1/machines/')
        if response.status_code == 200:
            machines = response.json()
            print("Machines data:")
            print(json.dumps(machines, indent=2, ensure_ascii=False))
            
            # 检查机器数据结构
            print("\nMachine data structure analysis:")
            for machine in machines[:3]:  # 只检查前3个
                print(f"\nMachine ID: {machine.get('id')}")
                print(f"Machine Name: {machine.get('name')}")
                print(f"Supplier: {machine.get('supplier')}")
                if machine.get('supplier'):
                    print(f"Supplier Machine Type: {machine['supplier'].get('machine_type')}")
        else:
            print(f"Error fetching machines: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_api_data()