import urllib.request
import json

def test_api():
    try:
        # 测试机器类型API
        print("Testing Machine Types API...")
        req = urllib.request.Request('http://localhost:8000/api/v1/machine-types/')
        response = urllib.request.urlopen(req)
        data = response.read()
        encoding = response.info().get_content_charset('utf-8')
        machine_types = json.loads(data.decode(encoding))
        print("Machine Types:", json.dumps(machine_types, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()