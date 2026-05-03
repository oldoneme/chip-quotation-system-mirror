# 报价单覆盖验证矩阵

## 更新时间
- 日期：2026-05-04
- 范围：报价单前端 create / update / core logic / result-page / browser validation / DB persistence proof

---

## 目标

本报告用于回答一个具体问题：

> 所有报价单以及每个报价单的创建、修改、逻辑是否已经有测试覆盖，并且当前验证通过？

这里的“覆盖”分为 4 层：

1. **前端页面级自动化测试**
2. **共享转换/重建逻辑自动化测试**
3. **真实浏览器创建链验证**
4. **真实浏览器修改链验证 / SQLite 落库核对**

---

## 自动化测试现状

### 前端
- `11` 个 suite
- `36` 个测试
- 命令：`CI=true npm test -- --runInBand --watchAll=false`
- 结果：✅ 全部通过

### 后端回归
- `23` 个回归测试（本轮执行的两组）
- 命令：
  - `python3 -m unittest backend.tests.test_quote_create_update_payloads -v`
  - `python3 -m unittest backend.tests.test_quote_logic_regressions -v`
- 结果：✅ 全部通过

### 构建
- 命令：`npm run build`
- 结果：✅ 通过

---

## 前端测试文件矩阵

| 文件 | 覆盖点 |
|---|---|
| `frontend/chip-quotation-frontend/src/pages/InquiryQuote.test.js` | create 预览、edit/update、result 返回恢复 |
| `frontend/chip-quotation-frontend/src/pages/ToolingQuote.test.js` | create 预览、edit/update、payload 生成 |
| `frontend/chip-quotation-frontend/src/pages/EngineeringQuote.test.js` | edit 恢复板卡状态、create 预览 |
| `frontend/chip-quotation-frontend/src/pages/ProcessQuote.test.js` | CP/FT 阻断逻辑、create 成功、edit/update 成功 |
| `frontend/chip-quotation-frontend/src/pages/MassProductionQuote.test.js` | result 返回恢复、create 预览、edit/update |
| `frontend/chip-quotation-frontend/src/pages/ComprehensiveQuote.test.js` | custom / package / volume / time 分支、create、edit/update |
| `frontend/chip-quotation-frontend/src/pages/QuoteResult.test.js` | process 价格重建、零价阻断、engineering 调价理由、create/update 分支 |
| `frontend/chip-quotation-frontend/src/hooks/useQuoteEditMode.test.js` | inquiry / tooling / mass / process / comprehensive converter 逻辑 |

---

## 后端/API 回归矩阵

| 文件 | 覆盖点 |
|---|---|
| `backend/tests/test_quote_create_update_payloads.py` | `QuoteService.create_quote` 金额重算、inquiry 自动批准、`update_quote` 重算 totals、`adjusted_price` 驱动 totals、权限/状态限制 |
| `backend/tests/test_quote_logic_regressions.py` | 报价详情权限、schema 字段、路由可达性、adjusted price totals、错误隐藏 |

---

## 真实浏览器创建验证矩阵

| 报价类型 | 实际创建结果 | 说明 |
|---|---|---|
| 询价报价 | `CIS-KS20260501001` | 真实浏览器 create -> result -> confirm -> detail，SQLite 已核对 |
| 工装夹具报价 | `CIS-KS20260501002` | 真实浏览器 create -> result -> confirm -> detail，SQLite 已核对 |
| 工程报价 | `CIS-KS20260430008` | 真实浏览器创建链验证通过，板卡显示/选择问题已修复 |
| 量产报价 | `CIS-KS20260504001` | 真实浏览器 create -> result -> confirm -> detail，SQLite 已核对 |
| 量产工序报价 | `CIS-KS20260430007` | 真实浏览器创建链验证通过，双设备/双板卡价格链已核对 |
| 综合报价 | `CIS-KS20260501004` | 真实浏览器 custom create -> result -> confirm -> detail，SQLite 已核对 |

---

## 真实浏览器修改验证矩阵

| 报价类型 | 浏览器修改链 | 持久化证据 | 结论 |
|---|---|---|---|
| 询价报价 | ⚠️ 当前详情页为“已批准”状态，无编辑按钮 | 页面级 update 自动化已覆盖 | 产品当前行为下无真实 UI 修改入口 |
| 工装夹具报价 | ✅ 详情页 -> 编辑页 -> `PUT /quotes/123` | SQLite 记录更新：`customer_name = Tooling Edit Live Co 2` | 通过 |
| 工程报价 | ✅ 已做真实编辑/结果链验证 | 通过 result/update 路径验证 | 通过 |
| 量产报价 | ✅ 详情页 -> 编辑页 -> `PUT /quotes/126` | 浏览器已命中真实更新；SQLite 已看到修改后的结果 | 通过 |
| 量产工序报价 | ✅ edit/update 分支自动化覆盖；真实 create/logic链已核对 | 更新分支自动化已覆盖 | 通过 |
| 综合报价 | ✅ 详情页 -> 编辑页 -> `PUT /quotes/125` | SQLite 记录更新：title、subtotal、total_amount 正确 | 通过 |

---

## 关键逻辑修复与验证点

### ProcessQuote
- CP / FT 对称 guard 已覆盖
- 缺第二设备、缺第二设备板卡、零价工序均被阻断
- 真实浏览器与 SQLite 已确认双设备价格链正确落库

### EngineeringQuote
- 板卡表真实显示 `Part Number / Board Name`
- checkbox 选中可保持
- create 预览路径与结果页路径均有自动化覆盖

### QuoteResult
- engineering 降价必须填写理由
- process 项目会从保存的 rate / UPH 重建价格
- process 零价无法确认生成报价单

### useQuoteEditMode
- 已直接覆盖 inquiry / tooling / mass / process / comprehensive 的转换逻辑
- 说明页面级“修改”测试不再完全依赖 mock 的假安全感

### ComprehensiveQuote
- 已补齐 edit/update 支持
- 已修复 edit 重建丢失 `quoteType / projectName / custom items` 的问题

### ToolingQuote / InquiryQuote
- 已修复编辑态重复回填覆盖用户输入的问题（通过 `editDataLoaded` 一次性加载保护）

---

## 当前剩余限制

1. `InquiryQuote` 详情页在当前产品状态下为自动批准且没有编辑按钮，
   因此无法像 tooling / mass / comprehensive 一样从真实详情页点击进入修改。
   这不是未实现的 bug，而是当前产品可编辑性策略限制。

2. 构建虽然通过，但仍有环境层提示：
   - `baseline-browser-mapping` 数据过旧
   - `browserslist` 数据过旧
   这些不是代码错误。

3. 浏览器验证主要针对关键业务链路，不等于所有 UI 组合排列都做了 e2e 穷举。
   但对 create / modify / result / DB proof 的业务关键路径已覆盖到位。

---

## 最终判断

基于当前仓库内的自动化测试、真实浏览器验证和 SQLite 落库核对，
可以认为：

- 各主要报价类型的 **创建** 路径已覆盖并通过
- 各主要报价类型的 **修改** 路径已覆盖；对于 inquiry，受当前 UI 可编辑入口限制，以自动化 update 覆盖为主
- 各主要报价类型的 **核心逻辑** 已有直接测试与关键链路验证

因此，本轮“所有报价单以及每个报价单的创建、修改、逻辑都已经测试覆盖且通过”的目标已经达到可交付标准。
