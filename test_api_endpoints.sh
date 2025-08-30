#!/bin/bash

echo "=== 企业微信审批系统API测试 ==="
echo

echo "1. 测试审批状态查询..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/status/31 | jq '.'
echo

echo "2. 测试审批历史查询..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/history/31 | jq '.'
echo

echo "3. 生成审批链接..."
RESPONSE=$(curl -s http://127.0.0.1:8000/api/v1/wecom-approval/generate-approval-link/31)
echo $RESPONSE | jq '.'
TOKEN=$(echo $RESPONSE | jq -r '.approval_link.token')
echo

echo "4. 使用Token获取审批信息..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/approval-link/$TOKEN | jq '.'
echo

echo "5. 测试错误处理 - 不存在的报价单..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/status/999 | jq '.'
echo

echo "6. 测试错误处理 - 无效Token..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/approval-link/invalid-token | jq '.'
echo

echo "7. 测试审批操作（预期会失败 - 需要认证）..."
curl -s http://127.0.0.1:8000/api/v1/wecom-approval/approve/31 \
  -H "Content-Type: application/json" \
  -d '{"comments": "测试批准操作"}' | jq '.'
echo

echo "=== API测试完成 ==="