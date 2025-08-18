#!/usr/bin/env python3
"""
生产环境就绪测试 - 企业微信SSO系统
"""
import requests
import time

def test_production_system():
    """测试生产环境就绪状态"""
    base_url = "https://wecom-dev.chipinfos.com.cn"
    
    print("🚀 企业微信SSO系统生产环境测试")
    print("=" * 50)
    
    tests = [
        ("前端主页", f"{base_url}/", 200),
        ("未认证API访问", f"{base_url}/api/me", 401),
        ("OAuth登录发起", f"{base_url}/auth/login", 302),
        ("WeChat回调验证", f"{base_url}/wecom/callback?msg_signature=test&timestamp=123&nonce=456&echostr=test", 403),  # 预期403因为签名验证失败
    ]
    
    print("\n🔍 执行系统测试...")
    all_passed = True
    
    for test_name, url, expected_status in tests:
        try:
            response = requests.get(url, allow_redirects=False, timeout=10)
            status = response.status_code
            
            if status == expected_status:
                print(f"  ✅ {test_name}: {status} (符合预期)")
            else:
                print(f"  ❌ {test_name}: {status} (预期 {expected_status})")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ {test_name}: 请求失败 - {str(e)}")
            all_passed = False
    
    # 测试OAuth重定向URL格式
    print(f"\n🔐 测试OAuth重定向...")
    try:
        response = requests.get(f"{base_url}/auth/login", allow_redirects=False)
        if response.status_code == 302:
            redirect_url = response.headers.get('location', '')
            
            # 检查关键参数
            checks = [
                ("appid=ww3bf2288344490c5c", "CorpID参数"),
                ("agentid=1000029", "AgentID参数"),
                ("scope=snsapi_base", "授权范围"),
                ("redirect_uri=https://wecom-dev.chipinfos.com.cn/auth/callback", "回调地址"),
            ]
            
            for param, desc in checks:
                if param in redirect_url:
                    print(f"  ✅ {desc}: 正确")
                else:
                    print(f"  ❌ {desc}: 缺失")
                    all_passed = False
        else:
            print(f"  ❌ OAuth重定向失败: {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"  ❌ OAuth测试失败: {str(e)}")
        all_passed = False
    
    print(f"\n📊 测试结果:")
    if all_passed:
        print("🎉 所有测试通过！系统已准备好生产环境部署")
        print("\n📱 使用说明:")
        print("1. 在企业微信工作台点击应用")
        print("2. 系统将自动跳转到OAuth登录")
        print("3. 授权后完成SSO单点登录")
        print(f"4. 直接访问: {base_url}")
        return True
    else:
        print("❌ 部分测试失败，需要修复后再部署")
        return False

if __name__ == "__main__":
    try:
        success = test_production_system()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
        exit(1)