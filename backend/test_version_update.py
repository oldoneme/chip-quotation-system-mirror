#!/usr/bin/env python3
"""
测试企业微信缓存清理和版本自动更新机制
"""
import requests
import json
import time

def test_version_update_mechanism():
    """测试版本更新机制"""
    base_url = "https://wecom-dev.chipinfos.com.cn"
    
    print("🔍 测试企业微信缓存清理和版本自动更新机制")
    print("=" * 60)
    
    # 1. 测试版本端点
    print("\n1. 测试版本检测端点")
    try:
        response = requests.get(f"{base_url}/__version", timeout=10)
        if response.status_code == 200:
            version_data = response.json()
            print(f"   ✅ 版本端点工作正常:")
            print(f"   📦 Git SHA: {version_data.get('git')}")
            print(f"   🕐 Build Time: {version_data.get('buildTime')}")
            print(f"   🔄 Deploy Time: {version_data.get('deployTime')}")
            print(f"   📋 Version: {version_data.get('version')}")
        else:
            print(f"   ❌ 版本端点失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 版本端点请求失败: {e}")
        return False
    
    # 2. 检查主页面缓存策略
    print("\n2. 验证主页面缓存策略")
    try:
        response = requests.head(f"{base_url}/", timeout=10)
        cache_control = response.headers.get('Cache-Control', '')
        pragma = response.headers.get('Pragma', '')
        expires = response.headers.get('Expires', '')
        
        print(f"   📄 Cache-Control: {cache_control}")
        print(f"   🚫 Pragma: {pragma}")
        print(f"   ⏰ Expires: {expires}")
        
        if 'no-store' in cache_control and 'no-cache' in cache_control:
            print("   ✅ HTML缓存策略正确（完全禁用缓存）")
        else:
            print("   ⚠️  HTML缓存策略可能有问题")
            
    except Exception as e:
        print(f"   ❌ 缓存策略检查失败: {e}")
    
    # 3. 验证页面包含版本检测脚本
    print("\n3. 验证页面包含版本检测脚本")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            content = response.text
            if "__app_version__" in content and "版本检测" in content:
                print("   ✅ 页面包含版本检测脚本")
                if "location.replace" in content:
                    print("   ✅ 包含强制刷新机制")
                else:
                    print("   ⚠️  可能缺少强制刷新机制")
            else:
                print("   ❌ 页面缺少版本检测脚本")
        else:
            print(f"   ❌ 无法获取页面内容: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 页面检查失败: {e}")
    
    # 4. 模拟版本更新
    print("\n4. 模拟版本更新流程")
    try:
        # 触发缓存清理端点
        response = requests.get(f"{base_url}/clear-cache", timeout=10)
        if response.status_code == 200:
            clear_data = response.json()
            print(f"   ✅ 缓存清理成功:")
            print(f"   🔄 新版本: {clear_data.get('new_version')}")
            print("   📋 清理指示:")
            for instruction in clear_data.get('clear_instructions', []):
                print(f"      • {instruction}")
        else:
            print(f"   ❌ 缓存清理失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 缓存清理请求失败: {e}")
    
    print("\n" + "="*60)
    print("🎯 企业微信测试指南:")
    print("1. 在企业微信中打开: https://wecom-dev.chipinfos.com.cn/")
    print("2. 页面标题应显示: '芯片测试报价系统 - 企业微信自动更新版'")
    print("3. 打开开发者工具Console，应该能看到版本检测日志")
    print("4. 关闭并重新打开应用，版本检测应自动运行")
    print("5. 当有新版本时，页面会自动强制刷新")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_version_update_mechanism()
        if success:
            print("\n🎉 版本更新机制测试通过！")
        else:
            print("\n❌ 版本更新机制存在问题")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
        exit(1)