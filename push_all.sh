#!/bin/bash

# 芯片报价系统 - 统一推送到Gitee和GitHub脚本
# 用法: ./push_all.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "  同步推送到 Gitee 和 GitHub"
echo "======================================"
echo ""

# 获取当前分支名
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 当前分支: $CURRENT_BRANCH"
echo ""

# 检查是否有未提交的更改
if [[ -n $(git status -s | grep -v "backend/app/test.db") ]]; then
    echo "⚠️  警告: 存在未提交的更改"
    git status -s | grep -v "backend/app/test.db"
    echo ""
    read -p "是否继续推送? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消推送"
        exit 1
    fi
fi

echo "📤 推送到 Gitee (origin)..."
if git push origin "$CURRENT_BRANCH"; then
    echo "✅ Gitee 推送成功"
else
    echo "❌ Gitee 推送失败"
    exit 1
fi

echo ""
echo "📤 推送到 GitHub (github)..."
if git push github "$CURRENT_BRANCH"; then
    echo "✅ GitHub 推送成功"
else
    echo "❌ GitHub 推送失败"
    exit 1
fi

echo ""
echo "======================================"
echo "🎉 所有远程仓库推送完成！"
echo "======================================"
echo ""
echo "分支状态:"
git branch -vv | grep "$CURRENT_BRANCH"
