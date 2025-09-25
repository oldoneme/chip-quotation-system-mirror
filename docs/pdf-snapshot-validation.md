# PDF 快照生成自测记录（2025-09-23）

## 环境信息
- 后端分支：feature/codex-frontend-snapshot-pdf
- FRONTEND_BASE_URL：`https://wecom-dev.chipinfos.com.cn`
- SNAPSHOT_BROWSER_POOL：3
- SNAPSHOT_READY_SELECTOR：`#quote-ready`
- Playwright Chromium 版本：`headless_shell-1187`

## 调试命令
```bash
# 1. 安装 Playwright 依赖（已执行）
backend/venv/bin/pip install playwright
backend/venv/bin/playwright install --with-deps chromium

# 2. 生成调试快照（超时 90s，自动输出 debug_quote.pdf）
cd backend && timeout 90s sh -c 'PYTHONPATH=. venv/bin/python scripts/debug_snapshot.py CIS-KS20250922003'
```

## 输出结果
- 脚本返回：
  ```json
  {
    "event": "snapshot_debug",
    "quote_id": 77,
    "quote_number": "CIS-KS20250922003",
    "source": "weasyprint",
    "file_size": 312927,
    "pdf_path": "media/quotes/77/quote_CIS-KS20250922003.pdf",
    "output": "/home/qixin/projects_codex/chip-quotation-system-mirror/backend/debug_quote.pdf"
  }
  ⚠️ 已使用 WeasyPrint 兜底，请检查前端快照是否可访问。
  ```
- `debug_quote.pdf` 位于 `backend/debug_quote.pdf`，大小约 305 KB。
- 快照主路径未命中 Playwright，原因：访问 `https://wecom-dev.chipinfos.com.cn/quote-detail/...` 会 302 到 `http://127.0.0.1:8000/v/...`，在本地环境不可达，Playwright 回退为 WeasyPrint。

## 后续建议
1. 在本地验证时可将 `FRONTEND_BASE_URL` 指向本地前端（如 `http://127.0.0.1:3000`），确保 Playwright 能直接访问页面并捕获 `#quote-ready`。
2. 正式部署时需让域名回源到真实可达的前端地址，避免 127.0.0.1 跳转。
3. 生成成功的日志示例（待实际命中后补充）：
   ```json
   {"event":"snapshot_success","quote_id":xxx,"quote_number":"...","pdf_path":"...","file_size":...,"duration_ms":...,"source":"playwright"}
   ```
