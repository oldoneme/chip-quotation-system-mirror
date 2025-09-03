#!/usr/bin/env python3
"""
企业微信审批状态自动同步守护进程
每30秒自动同步一次所有待审批的报价单状态
"""

import asyncio
import sys
import os
import signal
from datetime import datetime

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.wecom_approval_sync import run_sync_service

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print('\n停止同步服务...')
    sys.exit(0)

async def main():
    """主函数"""
    print("="*60)
    print("企业微信审批状态自动同步服务")
    print("="*60)
    print(f"启动时间: {datetime.now()}")
    print("同步间隔: 30秒")
    print("按 Ctrl+C 停止服务")
    print("="*60)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 运行同步服务
        await run_sync_service()
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"\n服务异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())