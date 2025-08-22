#!/usr/bin/env python3
"""
验证URL版本化强制重定向机制
"""
import requests
import json
import subprocess

def main():
    BASE = "https://wecom-dev.chipinfos.com.cn"
    
    print("🔍 验证URL版本化强制重定向机制")
    print("=" * 60)
    
    # 1) 获取当前版本
    try:
        version_response = requests.get(f"{BASE}/__version", timeout=10)
        if version_response.status_code == 200:
            version_data = version_response.json()
            current_version = version_data.get("version")
            print(f"📦 当前APP_VERSION: {current_version}")
            print(f"🕐 Build Time: {version_data.get('buildTime')}")
            print(f"📋 Git SHA: {version_data.get('git')}")
        else:
            print(f"❌ 无法获取版本信息: {version_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 版本请求失败: {e}")
        return False
    
    print(f"\n" + "="*60)
    
    # 2) 测试根路径重定向
    print("🔄 测试1: 访问根路径应该重定向到带版本的URL")
    try:
        response = requests.head(f"{BASE}/", allow_redirects=False, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('location', '')
            print(f"   ✅ 302重定向成功")
            print(f"   🎯 重定向到: {location}")
            
            if f"v={current_version}" in location:
                print(f"   ✅ 版本参数正确")
            else:
                print(f"   ❌ 版本参数不匹配")
                return False
        else:
            print(f"   ❌ 预期302重定向，实际: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 重定向测试失败: {e}")
        return False
    
    # 3) 测试错误版本重定向
    print(f"\n🔄 测试2: 错误版本应该重定向到正确版本")
    try:
        response = requests.head(f"{BASE}/?v=wrong_version", allow_redirects=False, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('location', '')
            print(f"   ✅ 302重定向成功")
            print(f"   🎯 重定向到: {location}")
            
            if f"v={current_version}" in location:
                print(f"   ✅ 版本参数修正正确")
            else:
                print(f"   ❌ 版本参数修正失败")
                return False
        else:
            print(f"   ❌ 预期302重定向，实际: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 版本重定向测试失败: {e}")
        return False
    
    # 4) 测试正确版本的HTML响应
    print(f"\n📄 测试3: 正确版本应该返回HTML内容")
    try:
        response = requests.get(f"{BASE}/?v={current_version}", timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ 200 OK响应成功")
            
            # 检查是否是HTML
            content_type = response.headers.get('content-type', '')
            if 'html' in content_type:
                print(f"   ✅ Content-Type正确: {content_type}")
            else:
                print(f"   ⚠️  Content-Type: {content_type}")
            
            # 检查缓存headers
            cache_control = response.headers.get('cache-control', '')
            if 'no-store' in cache_control:
                print(f"   ✅ Cache-Control正确: {cache_control}")
            else:
                print(f"   ⚠️  Cache-Control: {cache_control}")
            
            # 检查内容
            if 'title>芯片测试报价系统</title>' in response.text:
                print(f"   ✅ HTML内容正确（包含页面标题）")
            else:
                print(f"   ⚠️  HTML内容可能不正确")
            
            if '🔍 用户角色调试' in response.text:
                print(f"   ❌ 页面仍包含调试信息")
                return False
            else:
                print(f"   ✅ 页面已清理调试信息")
                
        else:
            print(f"   ❌ 预期200 OK，实际: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ HTML响应测试失败: {e}")
        return False
    
    print(f"\n" + "="*60)
    print("🎯 企业微信测试指南:")
    print("1. 企业微信打开: https://wecom-dev.chipinfos.com.cn/")
    print("2. 应该自动重定向到: https://wecom-dev.chipinfos.com.cn/?v=" + current_version)
    print("3. 页面标题: '芯片测试报价系统'")
    print("4. 无任何调试信息（🔍、🔄等）")
    print("5. 功能正常工作（用户认证、导航等）")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 URL版本化重定向机制验证通过！")
            exit(0)
        else:
            print("\n❌ URL版本化重定向机制存在问题")
            exit(1)
    except Exception as e:
        print(f"\n💥 验证异常: {str(e)}")
        exit(1)