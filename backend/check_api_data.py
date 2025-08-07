import requests
import json

# 检查机器API数据
response = requests.get('http://localhost:8000/api/v1/machines/')
machines = response.json()

print("机器数据:")
print(json.dumps(machines, indent=2, ensure_ascii=False))

# 检查机器类型
response = requests.get('http://localhost:8000/api/v1/machine-types/')
machine_types = response.json()

print("\n机器类型数据:")
print(json.dumps(machine_types, indent=2, ensure_ascii=False))