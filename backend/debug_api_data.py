import urllib.request
import json

def debug_api_data():
    try:
        # 测试机器API
        print("=== 测试机器API ===")
        req = urllib.request.Request('http://localhost:8000/api/v1/machines/')
        response = urllib.request.urlopen(req)
        data = response.read()
        encoding = response.info().get_content_charset('utf-8')
        machines = json.loads(data.decode(encoding))
        
        print(f"总共获取到 {len(machines)} 台机器:")
        for i, machine in enumerate(machines):
            print(f"\n机器 {i+1}:")
            print(f"  ID: {machine.get('id', 'N/A')}")
            print(f"  名称: {machine.get('name', 'N/A')}")
            print(f"  描述: {machine.get('description', 'N/A')}")
            
            # 检查供应商信息
            supplier = machine.get('supplier')
            if supplier:
                print(f"  供应商:")
                print(f"    ID: {supplier.get('id', 'N/A')}")
                print(f"    名称: {supplier.get('name', 'N/A')}")
                
                # 检查机器类型信息
                machine_type = supplier.get('machine_type')
                if machine_type:
                    print(f"    机器类型:")
                    print(f"      ID: {machine_type.get('id', 'N/A')}")
                    print(f"      名称: {machine_type.get('name', 'N/A')}")
                else:
                    print(f"    机器类型: None")
            else:
                print(f"  供应商: None")
                
            # 其他属性
            print(f"  币种: {machine.get('currency', 'N/A')}")
            print(f"  汇率: {machine.get('exchange_rate', 'N/A')}")
            print(f"  折扣率: {machine.get('discount_rate', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_data()