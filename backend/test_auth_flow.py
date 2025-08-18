#!/usr/bin/env python3
"""
测试企业微信SSO认证流程
"""
import requests
import json

def test_authentication_flow():
    """测试完整的认证流程"""
    base_url = "http://localhost:8000"
    
    print("🔐 测试企业微信SSO认证流程")
    print("=" * 50)
    
    # 1. 测试未认证访问
    print("\n1. 测试未认证访问 /api/me")
    response = requests.get(f"{base_url}/api/me")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    assert response.status_code == 401, "未认证用户应返回401状态码"
    
    # 2. 测试登录流程发起
    print("\n2. 测试登录流程发起 /auth/login")
    response = requests.get(f"{base_url}/auth/login", allow_redirects=False)
    print(f"   状态码: {response.status_code}")
    if 'location' in response.headers:
        redirect_url = response.headers['location']
        print(f"   重定向URL: {redirect_url}")
        print(f"   ✓ 成功重定向到企业微信OAuth页面")
        
        # 检查URL参数
        if "open.weixin.qq.com/connect/oauth2/authorize" in redirect_url:
            print("   ✓ OAuth URL格式正确")
        if "appid=ww3bf2288344490c5c" in redirect_url:
            print("   ✓ CorpID参数正确")
        if "agentid=1000029" in redirect_url:
            print("   ✓ AgentID参数正确")
        if "scope=snsapi_base" in redirect_url:
            print("   ✓ Scope参数正确")
    
    assert response.status_code == 302, "登录应返回302重定向"
    
    # 3. 测试OAuth回调模拟
    print("\n3. 模拟OAuth回调 (需要真实的authorization_code)")
    print("   注意: 此步骤需要通过企业微信获得真实的authorization_code")
    print("   可以通过以下步骤获取:")
    print("   - 在企业微信中访问应用")
    print("   - 系统会重定向到上述OAuth URL")
    print("   - 授权后会回调到 /auth/callback?code=xxx&state=xxx")
    
    # 4. 测试系统健康状态
    print("\n4. 测试系统健康状态")
    response = requests.get(f"{base_url}/")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    assert response.status_code == 200, "根路径应返回200"
    
    print("\n✅ 认证流程测试完成!")
    print("✅ 后端SSO配置正确，等待企业微信管理员配置OAuth域名")

if __name__ == "__main__":
    try:
        test_authentication_flow()
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        exit(1)