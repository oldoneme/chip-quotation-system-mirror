#!/usr/bin/env python3
"""
测试认证重定向流程
"""
import requests

def test_auth_redirect_flow():
    """测试浏览器访问时的认证重定向流程"""
    base_url = "https://wecom-dev.chipinfos.com.cn"
    
    print("🔍 测试浏览器认证重定向流程")
    print("=" * 50)
    
    # 1. 测试前端页面加载
    print("\n1. 访问前端主页")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ 前端页面加载成功: {response.status_code}")
        else:
            print(f"   ❌ 前端页面加载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False
    
    # 2. 测试前端会调用的API
    print("\n2. 测试/api/me端点（前端认证检查）")
    try:
        response = requests.get(f"{base_url}/api/me", timeout=10)
        if response.status_code == 401:
            print(f"   ✅ 未认证API正确返回401: {response.json()}")
        else:
            print(f"   ❌ 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API请求失败: {e}")
        return False
    
    # 3. 测试OAuth重定向
    print("\n3. 测试OAuth登录重定向")
    try:
        response = requests.get(f"{base_url}/auth/login", allow_redirects=False, timeout=10)
        if response.status_code == 302:
            redirect_url = response.headers.get('location', '')
            print(f"   ✅ OAuth重定向成功: {response.status_code}")
            print(f"   ✅ 重定向URL: {redirect_url[:100]}...")
            
            # 验证重定向URL包含关键参数
            if "open.weixin.qq.com/connect/oauth2/authorize" in redirect_url:
                print("   ✅ 重定向到企业微信OAuth正确")
                return True
            else:
                print("   ❌ 重定向URL不正确")
                return False
        else:
            print(f"   ❌ OAuth重定向失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ OAuth请求失败: {e}")
        return False

    print(f"\n📱 测试结果:")
    print("✅ 浏览器访问流程:")
    print("   1. 访问 https://wecom-dev.chipinfos.com.cn/")
    print("   2. 前端加载并执行认证检查")
    print("   3. 检测到未认证(401)后重定向到 /auth/login")
    print("   4. 后端重定向到企业微信OAuth页面")
    print("   5. 用户在企业微信中完成认证")

if __name__ == "__main__":
    try:
        success = test_auth_redirect_flow()
        if success:
            print("\n🎉 认证重定向流程测试通过！")
        else:
            print("\n❌ 认证重定向流程存在问题")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
        exit(1)