import urllib.request
import json

def test_backend():
    try:
        print("Testing backend API...")
        req = urllib.request.Request('http://localhost:8000/api/v1/machines/')
        response = urllib.request.urlopen(req, timeout=5)
        data = response.read()
        encoding = response.info().get_content_charset('utf-8')
        machines = json.loads(data.decode(encoding))
        
        print(f"Success! Retrieved {len(machines)} machines")
        print("First machine details:")
        if machines:
            machine = machines[0]
            print(json.dumps(machine, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend()