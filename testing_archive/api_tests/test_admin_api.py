#!/usr/bin/env python3
"""
管理员API测试脚本
用于验证API端点是否正确注册
"""
import sys
sys.path.append('.')

from app.main import app
from fastapi.testclient import TestClient

def test_admin_api_routes():
    """测试管理员API路由是否正确注册"""
    client = TestClient(app)

    print("🔍 检查管理员API路由注册情况...")

    # 检查所有路由
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes_info.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else [],
                'name': getattr(route, 'name', 'unnamed')
            })

    # 过滤出管理员相关路由
    admin_routes = [r for r in routes_info if '/admin' in r['path']]

    print(f"📊 总共找到 {len(routes_info)} 个路由")
    print(f"📊 管理员相关路由 {len(admin_routes)} 个:")

    for route in admin_routes:
        print(f"  - {route['methods']} {route['path']}")

    # 检查我们新添加的管理员报价单路由
    expected_routes = [
        'GET /api/v1/admin/quotes/all',
        'GET /api/v1/admin/quotes/statistics/detailed',
        'DELETE /api/v1/admin/quotes/{quote_id}/hard-delete',
        'POST /api/v1/admin/quotes/batch-restore',
        'DELETE /api/v1/admin/quotes/batch-soft-delete'
    ]

    print(f"\n✅ 检查期望的管理员报价单API路由:")
    for expected in expected_routes:
        method, path = expected.split(' ', 1)
        found = any(
            method in route['methods'] and route['path'] == path
            for route in admin_routes
        )
        status = "✅" if found else "❌"
        print(f"  {status} {expected}")

    print("\n🧪 尝试无认证API调用（应该返回401）:")

    # 测试无认证访问（应该返回401）
    try:
        response = client.get("/api/v1/admin/quotes/all")
        print(f"  GET /api/v1/admin/quotes/all: {response.status_code}")
        if response.status_code == 401:
            print("    ✅ 正确返回401未认证错误")
        else:
            print(f"    ⚠️ 意外状态码: {response.status_code}")
            print(f"    响应内容: {response.text}")
    except Exception as e:
        print(f"    ❌ 请求失败: {e}")

    # 测试统计接口
    try:
        response = client.get("/api/v1/admin/quotes/statistics/detailed")
        print(f"  GET /api/v1/admin/quotes/statistics/detailed: {response.status_code}")
        if response.status_code == 401:
            print("    ✅ 正确返回401未认证错误")
    except Exception as e:
        print(f"    ❌ 请求失败: {e}")

    print("\n🎉 管理员API路由注册检查完成!")

if __name__ == "__main__":
    test_admin_api_routes()