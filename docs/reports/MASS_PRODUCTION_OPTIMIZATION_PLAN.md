# 量产机时报价优化实施计划

## 🎯 优化目标

参考工程机时报价（EngineeringQuote）已完成的优化模式，对量产机时报价（MassProductionQuote）进行同样的优化升级。

**核心原则**: 从底层来说，新建和编辑应该是相同的底层逻辑，只是初始数据不同而已。

## 📊 当前状况分析

### 量产机时报价现有功能
- ✅ 支持FT/CP测试类型选择
- ✅ 机器选择（测试机、分选机、探针台）
- ✅ 板卡选择和数量配置
- ✅ 辅助设备选择
- ✅ 多币种支持（CNY/USD）
- ✅ sessionStorage状态保存
- ✅ 基础编辑模式支持（useQuoteEditMode）

### 待优化问题对照工程报价

| 优化项 | 工程报价状态 | 量产报价状态 | 优先级 |
|--------|--------------|--------------|--------|
| 统一新建/编辑逻辑 | ✅ 完成 | ❌ 待实现 | 🔴 高 |
| 板卡JSON序列化存储 | ✅ 完成 | ❌ 待实现 | 🔴 高 |
| 价格向上取整到所有项目 | ✅ 完成 | ⚠️ 部分（仅总费用） | 🔴 高 |
| "上一步"保持完整状态 | ✅ 完成 | ⚠️ 部分（缺customerInfo/projectInfo） | 🟡 中 |
| 编辑模式页面标题 | ✅ 完成 | ❌ 待实现 | 🟡 中 |
| 报价单号正确显示 | ✅ 完成 | ❌ 待实现 | 🟡 中 |
| Null安全检查 | ✅ 完成 | ⚠️ 待审查 | 🟢 低 |

## 🔧 技术实施方案

### 优化1: 应用板卡JSON序列化存储 🔴

**问题**: 当前量产报价生成报价项目时，板卡信息可能显示为独立条目

**解决方案**: 参考 EngineeringQuote.js 的 generateEngineeringQuoteItems 函数

```javascript
// 当前问题代码位置: MassProductionQuote.js lines 633-829
// 需要修改: generateMassProductionQuoteItems()

// 工程报价的成功模式 (EngineeringQuote.js:366-401)
items.push({
  item_name: testMachine.name,
  item_description: `机器 - 测试机`,
  machine_type: '测试机',
  configuration: JSON.stringify({
    device_type: '测试机',
    device_model: testMachine.name,
    cards: cardsInfo  // 板卡信息作为JSON存储在configuration字段
  }),
  machine_id: testMachine.id,
  // ...
});
```

**修改文件**:
- `/frontend/chip-quotation-frontend/src/pages/MassProductionQuote.js` (lines 633-829)

**修改要点**:
1. FT测试机项目（lines 639-678）: 添加 `configuration` 和 `machine_id` 字段
2. FT分选机项目（lines 681-720）: 添加 `configuration` 和 `machine_id` 字段
3. CP测试机项目（lines 726-765）: 添加 `configuration` 和 `machine_id` 字段
4. CP探针台项目（lines 768-807）: 添加 `configuration` 和 `machine_id` 字段
5. 辅助设备项目（lines 810-826）: 保持现有逻辑（辅助设备不需要板卡信息）

### 优化2: 应用价格向上取整到所有项目 🔴

**问题**: 当前仅在总费用计算中使用 `ceilByCurrency`，单个项目价格未取整

**解决方案**: 参考 EngineeringQuote.js lines 366-513

```javascript
// 工程报价的成功模式
const testMachineRate = calculateTestMachineFee() * engineeringRate;
const ceiledRate = ceilByCurrency(testMachineRate, quoteCurrency);

items.push({
  unit_price: ceiledRate,
  total_price: ceiledRate,
  // ...
});
```

**修改文件**:
- `/frontend/chip-quotation-frontend/src/pages/MassProductionQuote.js` (lines 633-829)

**修改要点**:
1. 对每个设备项目的 `testMachineFee`, `handlerFee`, `proberFee` 应用 `ceilByCurrency`
2. 对辅助设备的 `device.hourlyFee` 应用 `ceilByCurrency`
3. 确保 CNY 取整到元，USD 取整到分

### 优化3: 完善"上一步"功能的状态保持 🟡

**问题**: 从结果页返回时，客户信息和项目信息可能丢失

**当前代码**: MassProductionQuote.js lines 95-149 已有 sessionStorage 恢复逻辑

**需要检查**:
1. QuoteResult.js 是否正确保存量产报价的 customerInfo 和 projectInfo
2. fromResultPage 逻辑是否完整

**参考**: QuoteResult.js lines 1572-1605（工程报价的"上一步"逻辑）

### 优化4: 编辑模式页面标题和报价单号显示 🟡

**问题**: 编辑模式下页面标题未显示报价单号

**解决方案**: 参考 EngineeringQuote.js

```javascript
// 工程报价的成功模式 (EngineeringQuote.js:558)
quoteNumber: isEditMode && editingQuote ? editingQuote.quote_number : null,

// 页面标题显示
<h2>{isEditMode ? `编辑量产机时报价 - ${editingQuote?.quote_number || editingQuote?.id}` : '量产报价'}</h2>
```

**修改文件**:
- `/frontend/chip-quotation-frontend/src/pages/MassProductionQuote.js`

**修改要点**:
1. Line 1086: 修改页面标题动态显示
2. Line 852-877: 在 quoteData 中添加 quoteNumber 字段
3. Line 879-900: 确保编辑模式正确识别

### 优化5: Null安全检查 🟢

**当前状况**: 需要审查所有数据访问，添加防御性编程

**参考**: EngineeringQuote.js lines 372, 404, 436, 470-473

```javascript
// 工程报价的成功模式
if (testMachine && testMachine.name && testMachineCards.length > 0) {
  // 安全操作
}

supplier: typeof testMachine.supplier === 'object'
  ? testMachine.supplier?.name || ''
  : testMachine.supplier || ''
```

**检查位置**:
- Lines 639-807: 所有设备和板卡访问
- Lines 563-566, 992-1022: 辅助设备计算

## 📋 分步实施计划

### Step 1: 板卡JSON序列化存储（最关键） 🔴
- [ ] 修改 FT 测试机项目生成逻辑（添加 configuration + machine_id）
- [ ] 修改 FT 分选机项目生成逻辑
- [ ] 修改 CP 测试机项目生成逻辑
- [ ] 修改 CP 探针台项目生成逻辑
- [ ] 测试报价单详情展开不再显示重复板卡

### Step 2: 价格向上取整应用到所有项目 🔴
- [ ] FT 测试机费用应用 `ceilByCurrency(testMachineFee, quoteCurrency)`
- [ ] FT 分选机费用应用 `ceilByCurrency(handlerFee, quoteCurrency)`
- [ ] CP 测试机费用应用 `ceilByCurrency(testMachineFee, quoteCurrency)`
- [ ] CP 探针台费用应用 `ceilByCurrency(proberFee, quoteCurrency)`
- [ ] 辅助设备费用应用取整
- [ ] 测试 CNY 显示整数，USD 显示两位小数

### Step 3: 编辑模式标题和报价单号 🟡
- [ ] 页面标题动态显示 "编辑量产机时报价 - CIS-XXX"
- [ ] quoteData 添加 quoteNumber 字段
- [ ] 确保编辑模式与新建模式UI一致

### Step 4: 完善"上一步"状态保持 🟡
- [ ] 检查 QuoteResult.js 对量产报价的处理
- [ ] 确保 customerInfo 和 projectInfo 正确保存到 sessionStorage
- [ ] 测试从结果页返回数据完整性

### Step 5: Null安全检查 🟢
- [ ] 审查所有设备对象访问，添加 null 检查
- [ ] 审查所有板卡数组访问，添加长度检查
- [ ] 审查供应商字段访问，使用可选链

### Step 6: 测试和验证
- [ ] 创建新量产报价（FT）
- [ ] 创建新量产报价（CP）
- [ ] 创建新量产报价（FT+CP）
- [ ] 编辑已有报价单
- [ ] 验证报价单详情不显示重复板卡
- [ ] 验证价格正确取整（CNY整数，USD两位小数）
- [ ] 验证"上一步"功能完整性

## 🚨 风险控制

### 遵循 CLAUDE_WORKFLOW.md 强制检查

**Phase 1: 修改前风险评估**
- ✅ 不涉及认证功能
- ✅ 不涉及核心路由
- ✅ 修改范围：1个主要文件（MassProductionQuote.js）+ 可能需要微调 QuoteResult.js
- ⚠️ 需要备份当前工作状态

**Phase 2: 修改实施**
- [ ] git status 检查当前状态
- [ ] git stash 或创建备份分支
- [ ] 最小变更原则：一次只改一个优化点
- [ ] 渐进式验证：每改一部分就测试

**Phase 3: 完成后验证**
- [ ] 新建报价单功能正常
- [ ] 编辑报价单功能正常
- [ ] 报价单详情显示正确
- [ ] 价格计算准确

### 财务准确性检查（CLAUDE.md要求）

- [ ] 所有价格计算使用 `ceilByCurrency`
- [ ] CNY 向上取整到元（个位）
- [ ] USD 向上取整到分（百分位）
- [ ] 不使用浮点数进行货币计算
- [ ] 输入验证防止错误配置

## ✅ 验收标准

### 功能完整性
- [ ] 量产报价支持完整的新建流程
- [ ] 量产报价支持完整的编辑流程
- [ ] 板卡信息序列化存储在 configuration 字段
- [ ] 报价单详情不显示重复板卡项

### 价格准确性
- [ ] CNY 报价所有项目价格为整数
- [ ] USD 报价所有项目价格为两位小数
- [ ] 总价等于各项之和（取整后）

### 用户体验
- [ ] 编辑模式页面标题正确显示报价单号
- [ ] "上一步"功能保留所有表单数据
- [ ] 编辑成功后跳转到详情页
- [ ] 无 null 引用错误

### 技术质量
- [ ] 代码风格与工程报价一致
- [ ] 使用工程报价验证过的模式
- [ ] 无调试 console.log
- [ ] 完整的 null 安全检查

## 🎯 实施优先级总结

**第一优先级（必须完成）**:
1. 板卡JSON序列化存储
2. 价格向上取整应用到所有项目

**第二优先级（重要）**:
3. 编辑模式标题和报价单号
4. "上一步"状态保持

**第三优先级（优化）**:
5. Null安全检查

## 📚 参考文档

- **主要参考**: `/docs/reports/ENGINEERING_QUOTE_SUMMARY.md` - 工程报价完整特性总结
- **代码参考**: `/frontend/chip-quotation-frontend/src/pages/EngineeringQuote.js`
- **工作流**: `/CLAUDE_WORKFLOW.md` - 强制性检查清单
- **开发哲学**: `/.claude/CLAUDE.md` - 渐进式开发原则

---

*此计划遵循渐进式开发哲学，确保每一步都不破坏现有功能*
