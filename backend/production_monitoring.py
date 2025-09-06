#!/usr/bin/env python3
"""
生产环境监控脚本 - 监控企业微信签名验证失败率
"""

import requests
import json
import sys
import os
from datetime import datetime
import argparse

def check_signature_monitoring(base_url="http://localhost:8000"):
    """
    检查签名验证监控状态
    """
    try:
        response = requests.get(f"{base_url}/api/v1/internal/debug/signature-failures")
        if response.status_code != 200:
            print(f"❌ 监控接口调用失败: {response.status_code}")
            return False
            
        data = response.json()
        monitoring = data.get("monitoring_status", {})
        
        alert_level = monitoring.get("alert_level", "unknown")
        message = monitoring.get("message", "无状态信息")
        failure_rate = monitoring.get("failure_rate_24h", 0)
        failures_today = monitoring.get("failures_today", 0)
        
        print(f"🔍 签名验证监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 60)
        print(f"告警级别: {alert_level.upper()}")
        print(f"状态消息: {message}")
        print(f"24小时失败率: {failure_rate}%")
        print(f"今日失败次数: {failures_today}")
        
        # 根据告警级别返回不同的退出码
        if alert_level == "critical":
            print(f"\n🚨 严重告警: 签名验证失败率过高，需要立即处理！")
            print(f"建议采取的紧急措施:")
            for rec in data.get("recommendations", []):
                print(f"  • {rec}")
            return False
        elif alert_level == "warning":
            print(f"\n⚠️ 警告: 签名验证失败率较高，建议检查配置")
            print(f"建议检查项目:")
            for rec in data.get("recommendations", []):
                print(f"  • {rec}")
            return True
        elif alert_level == "info":
            print(f"\nℹ️ 信息: 有少量签名验证失败，属于正常范围")
            return True
        else:
            print(f"\n✅ 正常: 签名验证工作正常")
            return True
            
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 监控检查异常: {str(e)}")
        return False

def check_system_health(base_url="http://localhost:8000"):
    """
    检查系统整体健康状态
    """
    try:
        response = requests.get(f"{base_url}/api/v1/internal/debug/system")
        if response.status_code != 200:
            print(f"❌ 系统状态接口调用失败: {response.status_code}")
            return False
            
        data = response.json()
        system_info = data.get("system_info", {})
        stats = data.get("statistics", {})
        
        print(f"\n📊 系统健康状态")
        print(f"-" * 40)
        print(f"进程ID: {system_info.get('process_id')}")
        print(f"数据库路径: {system_info.get('db_path')}")
        print(f"总报价单数: {stats.get('total_quotes')}")
        print(f"总审批事件: {stats.get('total_timelines')}")
        print(f"错误记录数: {stats.get('total_errors')}")
        
        # 状态分布
        status_dist = data.get("status_distribution", {})
        if status_dist:
            print(f"\n报价单状态分布:")
            for status, count in status_dist.items():
                print(f"  {status}: {count}")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ 系统状态检查失败: {str(e)}")
        return False

def send_alert(alert_level, message, webhook_url=None):
    """
    发送告警通知（可扩展到企业微信、邮件等）
    """
    if not webhook_url:
        print(f"⚠️ 未配置告警通知URL，跳过通知发送")
        return
    
    alert_data = {
        "alert_level": alert_level,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "service": "chip-quotation-wecom-callback"
    }
    
    try:
        response = requests.post(webhook_url, json=alert_data, timeout=10)
        if response.status_code == 200:
            print(f"✅ 告警通知发送成功")
        else:
            print(f"❌ 告警通知发送失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 告警通知发送异常: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="生产环境监控脚本")
    parser.add_argument("--url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--webhook", help="告警通知Webhook URL")
    parser.add_argument("--no-system", action="store_true", help="跳过系统健康检查")
    
    args = parser.parse_args()
    
    # 检查签名验证监控
    signature_ok = check_signature_monitoring(args.url)
    
    # 检查系统健康状态
    if not args.no_system:
        system_ok = check_system_health(args.url)
    else:
        system_ok = True
    
    # 发送告警（如果需要）
    if not signature_ok and args.webhook:
        send_alert("critical", "签名验证失败率过高", args.webhook)
    
    # 返回适当的退出码
    if signature_ok and system_ok:
        sys.exit(0)  # 成功
    else:
        sys.exit(1)  # 有问题

if __name__ == "__main__":
    main()