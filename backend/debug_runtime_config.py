#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 首先加载main.py来设置环境变量（模拟服务器启动）
print("🔧 模拟服务器启动配置...")
# 设置环境变量供认证模块使用（必须在导入之前设置）
os.environ["WECOM_CORP_ID"] = "ww3bf2288344490c5c"
os.environ["WECOM_AGENT_ID"] = "1000029"
os.environ["WECOM_CORP_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"
os.environ["WECOM_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"
os.environ["WECOM_APPROVAL_TEMPLATE_ID"] = "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh"

print("✅ 环境变量已设置")

# 现在测试WeComOAuth
from app.wecom_auth import WeComOAuth

def test_wecom_oauth_config():
    """测试WeComOAuth配置"""
    print("\n🔧 测试WeComOAuth配置")
    print("=" * 50)

    oauth = WeComOAuth()

    print(f"📊 WeComOAuth配置:")
    print(f"   corp_id: {oauth.corp_id}")
    print(f"   agent_id: {oauth.agent_id}")
    print(f"   corp_secret: {oauth.corp_secret[:10]}..." if oauth.corp_secret else "   corp_secret: 未设置")

    if oauth.corp_id and oauth.agent_id and oauth.corp_secret:
        print("✅ WeComOAuth配置完整")

        # 测试获取access_token
        try:
            print("\n🚀 测试获取access_token...")
            token = oauth.get_access_token()
            if token:
                print(f"✅ 成功获取access_token: {token[:20]}...")
                return True
            else:
                print("❌ 获取access_token失败: 返回空值")
                return False
        except Exception as e:
            print(f"❌ 获取access_token异常: {e}")
            return False
    else:
        print("❌ WeComOAuth配置不完整")
        return False

if __name__ == "__main__":
    print("🎯 运行时配置调试")

    success = test_wecom_oauth_config()

    print(f"\n🎯 配置测试结果: {'成功' if success else '失败'}")

    if success:
        print("\n🎉 企业微信配置正常，API调用应该能正常工作")
    else:
        print("\n❌ 企业微信配置有问题，需要检查：")
        print("1. 企业微信应用配置")
        print("2. secret是否正确")
        print("3. 网络连接问题")