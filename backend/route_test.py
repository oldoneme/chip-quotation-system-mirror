import sys
import os

# Add the project root directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.main import app

def print_routes():
    print("注册的路由:")
    for route in app.routes:
        print(f"  {route.methods} {route.path}")

if __name__ == "__main__":
    print_routes()