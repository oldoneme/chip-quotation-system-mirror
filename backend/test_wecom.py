#!/usr/bin/env python3
import os
os.environ['WECOM_TOKEN'] = 'cN9bXxcD80'
os.environ['WECOM_AES_KEY'] = 'S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl'
os.environ['WECOM_CORP_ID'] = 'ww3bf2288344490c'

from app.main import app
import uvicorn

if __name__ == "__main__":
    # 打印所有路由
    print("注册的路由：")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path} -> {route.methods if hasattr(route, 'methods') else 'N/A'}")
    
    # 检查/wecom/callback是否存在
    wecom_routes = [r for r in app.routes if hasattr(r, 'path') and '/wecom/callback' in r.path]
    if wecom_routes:
        print(f"\n✓ /wecom/callback 路由已注册 ({len(wecom_routes)} 个方法)")
    else:
        print("\n✗ /wecom/callback 路由未找到")
    
    print("\n启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)