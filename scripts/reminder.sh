#!/bin/bash

# 网络环境切换提醒脚本

echo "🔄 网络环境切换提醒"
echo "===================="
echo ""
echo "检测到你可能切换了网络环境!"
echo ""
echo "请运行以下命令之一："
echo ""
echo "1. 自动检测并配置:"
echo "   ./scripts/network-env-manager.sh --auto"
echo ""
echo "2. 手动选择环境:"
echo "   ./scripts/network-env-manager.sh --office   # 公司环境"
echo "   ./scripts/network-env-manager.sh --home     # 家庭环境"
echo ""
echo "3. 查看当前状态:"
echo "   ./scripts/network-env-manager.sh --status"
echo ""
echo "详细说明请查看: NETWORK-SETUP.md"
echo ""