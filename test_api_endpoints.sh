#!/bin/bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
AUTH_TOKEN="${CHIP_QUOTE_AUTH_TOKEN:-}"

if [[ -z "$AUTH_TOKEN" ]]; then
  echo "请先设置 CHIP_QUOTE_AUTH_TOKEN 再执行，例如："
  echo "  export CHIP_QUOTE_AUTH_TOKEN=<token>"
  exit 1
fi

AUTH_HEADER=( -H "Authorization: Bearer ${AUTH_TOKEN}" )

echo "=== 企业微信审批系统 API 测试 ==="
echo

echo "1. 测试统一审批状态查询..."
curl -s "${BASE_URL}/api/v1/approval/status/31" "${AUTH_HEADER[@]}" | jq '.'
echo

echo "2. 测试统一审批历史查询..."
curl -s "${BASE_URL}/api/v1/approval/history/31" "${AUTH_HEADER[@]}" | jq '.'
echo

echo "3. 生成审批链接..."
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/wecom-approval/generate-approval-link/31" "${AUTH_HEADER[@]}")
echo "$RESPONSE" | jq '.'
TOKEN=$(echo "$RESPONSE" | jq -r '.approval_link.token // empty')
echo

if [[ -n "$TOKEN" ]]; then
  echo "4. 使用 Token 获取审批信息..."
  curl -s "${BASE_URL}/api/v1/wecom-approval/approval-link/${TOKEN}" | jq '.'
  echo
fi

echo "5. 查询报价单审批记录..."
curl -s "${BASE_URL}/api/v1/quotes/31/approval-records" "${AUTH_HEADER[@]}" | jq '.'
echo

echo "6. 测试错误处理 - 不存在的报价单..."
curl -s "${BASE_URL}/api/v1/approval/status/999999" "${AUTH_HEADER[@]}" | jq '.'
echo

echo "7. 测试错误处理 - 无效 Token..."
curl -s "${BASE_URL}/api/v1/wecom-approval/approval-link/invalid-token" | jq '.'
echo

echo "8. 测试提交审批（若已提交/无权限，返回业务错误也属正常）..."
curl -s -X POST "${BASE_URL}/api/v1/quotes/31/submit" "${AUTH_HEADER[@]}" | jq '.'
echo

echo "=== API 测试完成 ==="
