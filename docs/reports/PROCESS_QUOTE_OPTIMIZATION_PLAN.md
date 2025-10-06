# 量产工序报价优化实施计划

## 📅 计划时间
**创建时间**: 2025-10-06
**分支**: `quote-detail-editable-claude`
**参考模式**: 工程机时报价 + 量产机时报价

---

## 🎯 优化目标

将工程机时报价和量产机时报价已验证的**8大优化模式**完整应用到量产工序报价（ProcessQuote），实现功能对等和用户体验统一。

**核心原则**:
1. 参考已验证的成功模式（EngineeringQuote + MassProductionQuote）
2. 保持代码风格一致
3. 确保向后兼容（新旧报价单）
4. 渐进式实施，每步验证

---

## 📊 当前状况分析

### ProcessQuote 特点

**业务模型**：
- 支持 CP 和 FT 两种测试类型
- 每种类型可包含多个工序（CP1/CP2/CP3、FT1/FT2/FT3等）
- 每个工序包含：
  - **测试工序**：测试机 + 探针台/分选机 + 板卡
  - **非测试工序**：单设备（烘烤、编带、包装等）
  - UPH（每小时产量）
  - 单颗成本计算

**当前代码特征**（ProcessQuote.js, 1085行）：
- ✅ 已有编辑模式基础（useQuoteEditMode Hook）
- ❌ **没有板卡JSON序列化**（板卡数据未单独存储）
- ❌ **没有价格向上取整**（使用固定4位小数格式）
- ❌ **没有单页面模式**（可能有分步）
- ❌ **没有完整编辑预填充**（设备和板卡未恢复）
- ✅ 支持多工序动态添加/删除
- ✅ 单颗成本计算（万分位取整）

### 数据结构

**formData 核心字段**：
```javascript
{
  selectedTypes: ['cp', 'ft'],
  cpProcesses: [
    {
      id: 1,
      name: 'CP1测试',
      testMachine: '',
      testMachineData: null,
      testMachineCardQuantities: {},
      prober: '',
      proberData: null,
      proberCardQuantities: {},
      uph: 1000,
      unitCost: 0
    }
  ],
  ftProcesses: [
    {
      id: 1,
      name: 'FT1测试',
      testMachine: '',
      testMachineData: null,
      testMachineCardQuantities: {},
      handler: '',
      handlerData: null,
      handlerCardQuantities: {},
      uph: 1000,
      unitCost: 0
    }
  ],
  currency: 'CNY',
  exchangeRate: 7.2
}
```

---

## 🔧 待优化问题对照表

| 优化项 | 当前状态 | 期望状态 | 参考来源 |
|--------|---------|---------|---------|
| **1. 板卡JSON序列化** | ❌ 板卡数据在formData中，未序列化到报价项 | ✅ configuration字段存储JSON，包含设备和板卡信息 | EngineeringQuote.js |
| **2. 价格向上取整** | ❌ 使用固定4位小数，未按币种取整 | ✅ CNY取整到元，USD到分，UnitCost到万分位 | MassProductionQuote.js |
| **3. 单页面模式** | ⚠️ 当前是单页，但可能有步骤逻辑 | ✅ 确保无StepIndicator，所有字段同时显示 | MassProductionQuote.js |
| **4. 表格分页** | ⚠️ 需检查工序表格是否分页 | ✅ pagination={false}，所有工序一次显示 | MassProductionQuote.js |
| **5. 编辑模式标题** | ❌ 未显示报价单号 | ✅ "编辑量产工序报价 - CIS-XXX" | EngineeringQuote.js |
| **6. "上一步"状态保持** | ⚠️ 需检查QuoteResult.js处理 | ✅ customerInfo、projectInfo、工序数据完整保存 | MassProductionQuote.js |
| **7. 编辑模式数据预填充** | ❌ 工序设备和板卡未恢复 | ✅ 所有工序、设备、板卡完整预填充 | MassProductionQuote.js |
| **8. Null安全检查** | ⚠️ 需审查所有设备访问 | ✅ 可选链和防御性检查 | All |

---

## 📋 分步实施计划

### Step 1: 板卡JSON序列化存储（最关键） 🔴

**目标**: 将每个工序的设备和板卡信息序列化为 JSON 存储在 configuration 字段

**修改位置**: ProcessQuote.js `handleSubmit` 函数

**实施步骤**:
1. 创建 `generateProcessQuoteItems()` 函数
2. 遍历所有工序（CP + FT）
3. 为每个工序创建报价项：
   ```javascript
   {
     item_name: '工序名称 - CP1测试',
     configuration: JSON.stringify({
       process_type: 'CP1测试',
       test_machine: { id, name, cards: [...] },
       prober: { id, name, cards: [...] },  // 或 handler
       uph: 1000,
       unit_cost: 0.0123
     }),
     machine_id: testMachine.id,  // 主设备ID
     category_type: 'process',
     quantity: 1,
     unit: '颗',
     unit_price: unitCost,  // 单颗成本
     total_price: unitCost * totalQuantity
   }
   ```

4. 应用价格取整：
   - 单颗成本（UnitCost）：万分位向上取整（已有）
   - 总价：按币种取整（CNY到元，USD到分）

**验收**:
- [ ] 工序报价项包含完整 configuration JSON
- [ ] 报价详情不显示重复板卡项
- [ ] 每个工序有 machine_id 关联

---

### Step 2: 价格向上取整应用到所有项目 🔴

**目标**: 所有价格按币种正确取整

**修改位置**:
- `formatUnitPrice` - 单颗成本格式化（已有万分位取整，保留）
- `generateProcessQuoteItems` - 总价应用 `ceilByCurrency()`

**实施步骤**:
1. 保留 `formatUnitPrice` 的万分位取整逻辑（工序报价特有）
2. 在生成报价项时，总价应用 `ceilByCurrency(totalPrice, currency)`
3. 确保：
   - CNY：总价取整到元
   - USD：总价取整到分
   - UnitCost：保持万分位精度（业务需求）

**验收**:
- [ ] CNY 总价为整数
- [ ] USD 总价为两位小数
- [ ] UnitCost 保持4位小数（万分位）

---

### Step 3: 单页面模式确认 🟡

**目标**: 确保无分步导航，所有字段同时显示

**检查项**:
- [ ] 检查是否有 `StepIndicator` 组件
- [ ] 检查是否有 `currentStep` 状态
- [ ] 检查是否有基于步骤的条件渲染

**修改**（如果需要）:
- 移除 StepIndicator 相关代码
- 所有表单字段在同一页面显示
- 简化按钮为"退出报价"和"确认报价"

---

### Step 4: 移除表格分页 🟡

**目标**: 工序表格全部显示，无需翻页

**检查位置**:
- CP工序表格
- FT工序表格
- 板卡选择表格（如果有）

**修改**:
```javascript
// 从
pagination={{ pageSize: 5, showSizeChanger: false }}

// 改为
pagination={false}
```

---

### Step 5: 编辑模式完整数据预填充 🔴

**目标**: 编辑工序报价时，所有工序、设备、板卡完整恢复

**修改位置**:
1. `useQuoteEditMode.js` - 新增 `parseProcessQuoteDevicesFromItems()` 函数
2. `ProcessQuote.js` - useEffect 编辑模式数据预填充

**实施步骤**:

#### 5.1 实现解析函数（useQuoteEditMode.js）

```javascript
const parseProcessQuoteDevicesFromItems = (items, availableCardTypes = [], availableMachines = []) => {
  const config = {
    selectedTypes: [],
    cpProcesses: [],
    ftProcesses: []
  };

  items.forEach(item => {
    // 解析 configuration JSON
    let configData = null;
    if (item.configuration) {
      try {
        configData = JSON.parse(item.configuration);
      } catch (e) {
        console.warn('无法解析configuration JSON:', item.configuration);
      }
    }

    // 从 configData 或 item 推断工序类型
    const processType = configData?.process_type || item.item_name;

    if (processType.includes('CP')) {
      // 解析 CP 工序
      const process = {
        id: cpProcesses.length + 1,
        name: processType,
        testMachine: configData?.test_machine?.name || '',
        testMachineData: availableMachines.find(m => m.id === item.machine_id),
        testMachineCardQuantities: {},
        prober: configData?.prober?.name || '',
        proberData: availableMachines.find(m => m.id === configData?.prober?.id),
        proberCardQuantities: {},
        uph: configData?.uph || 1000,
        unitCost: item.unit_price || 0
      };

      // 解析板卡
      configData?.test_machine?.cards?.forEach(card => {
        process.testMachineCardQuantities[card.id] = card.quantity || 1;
      });

      config.cpProcesses.push(process);
      if (!config.selectedTypes.includes('cp')) {
        config.selectedTypes.push('cp');
      }
    } else if (processType.includes('FT')) {
      // 解析 FT 工序（类似逻辑）
      // ...
    }
  });

  return config;
};
```

#### 5.2 ProcessQuote.js 预填充逻辑

```javascript
useEffect(() => {
  if (isEditMode && editingQuote && !editLoading && !editDataLoaded &&
      cardTypes.length > 0 && machines.length > 0) {

    const formData = convertQuoteToFormData(editingQuote, 'process', cardTypes, machines);

    if (formData?.deviceConfig) {
      setFormData(prev => ({
        ...prev,
        selectedTypes: formData.deviceConfig.selectedTypes,
        cpProcesses: formData.deviceConfig.cpProcesses,
        ftProcesses: formData.deviceConfig.ftProcesses
      }));
    }

    setEditDataLoaded(true);
  }
}, [isEditMode, editingQuote, editLoading, editDataLoaded, cardTypes, machines]);
```

**验收**:
- [ ] 编辑工序报价时，所有工序正确显示
- [ ] 每个工序的设备正确预填充
- [ ] 板卡数量正确恢复
- [ ] UPH和单颗成本正确显示

---

### Step 6: 编辑模式标题和报价单号 🟡

**目标**: 页面标题动态显示报价单号

**修改位置**: ProcessQuote.js 页面标题

```javascript
<h2>{isEditMode ? `编辑量产工序报价 - ${editingQuote?.quote_number}` : '量产工序报价'}</h2>
```

**传递报价单号到 QuoteResult**:
```javascript
const quoteData = {
  // ...
  isEditMode,
  editingQuoteId: editingQuote?.id,
  quoteNumber: editingQuote?.quote_number
};
```

---

### Step 7: "上一步"状态保持 🟡

**目标**: 从结果页返回时，保留所有工序数据

**修改位置**: QuoteResult.js

```javascript
// 工序报价："上一步"逻辑
if (quoteData.type === '工序报价') {
  const previousStepData = {
    customerInfo: quoteData.customerInfo || {},
    projectInfo: quoteData.projectInfo || {},
    selectedTypes: quoteData.selectedTypes || ['cp'],
    cpProcesses: quoteData.cpProcesses || [],
    ftProcesses: quoteData.ftProcesses || [],
    currency: quoteData.currency || 'CNY',
    exchangeRate: quoteData.exchangeRate || 7.2,
    // 编辑模式信息
    isEditMode: quoteData.isEditMode || false,
    editingQuoteId: quoteData.editingQuoteId || null,
    editingQuoteNumber: quoteData.quoteNumber || null,
    fromResultPage: true
  };

  sessionStorage.setItem('processQuoteData', JSON.stringify(previousStepData));
  navigate('/process-quote', { state: previousStepData });
}
```

**ProcessQuote.js 接收**:
```javascript
useEffect(() => {
  const savedData = sessionStorage.getItem('processQuoteData');
  if (savedData && location.state?.fromResultPage) {
    const parsedData = JSON.parse(savedData);
    setFormData(prev => ({ ...prev, ...parsedData }));
    sessionStorage.removeItem('processQuoteData');
  }
}, []);
```

---

### Step 8: Null安全检查 🟢

**目标**: 所有设备和板卡访问添加防御性检查

**审查位置**:
- 所有 `process.testMachineData` 访问
- 所有 `process.proberData` / `process.handlerData` 访问
- 所有 `cardTypes` 数组访问
- 供应商字段访问

**修改模式**:
```javascript
// 从
const hourlyRate = testMachineData.hourly_rate;

// 改为
const hourlyRate = testMachineData?.hourly_rate || 0;

// 供应商访问
const supplier = typeof device.supplier === 'object'
  ? device.supplier?.name || ''
  : device.supplier || '';
```

---

### Step 9: 向后兼容（新旧格式） 🟢

**目标**: 支持编辑旧报价单（无 configuration 字段）

**实施**:
1. `parseProcessQuoteDevicesFromItems` 支持双路径解析
2. 有 configuration：从 JSON 提取
3. 无 configuration：从 item 字段推断

```javascript
// 路径1: 新格式
if (item.configuration) {
  configData = JSON.parse(item.configuration);
  processType = configData.process_type;
}

// 路径2: 旧格式
if (!configData) {
  processType = item.item_name;  // "CP1测试" 或 "FT1测试"
  // 通过名称匹配设备
  testMachineData = availableMachines.find(m => m.name === item.machine_model);
}
```

---

### Step 10: 测试和验证 ✅

**新建工序报价**:
- [ ] 创建 CP 工序报价（单工序）
- [ ] 创建 FT 工序报价（单工序）
- [ ] 创建 CP+FT 混合报价（多工序）
- [ ] 验证 configuration JSON 正确
- [ ] 验证价格取整正确

**编辑工序报价**:
- [ ] 编辑新报价单，所有数据正确预填充
- [ ] 编辑旧报价单，兼容无 configuration 格式
- [ ] 修改工序，保存后正确更新
- [ ] "上一步"功能，数据完整保留

**报价详情验证**:
- [ ] 报价详情不显示重复板卡项
- [ ] 展开 configuration 查看设备信息
- [ ] 单颗成本显示4位小数
- [ ] 总价按币种正确取整

---

## 🚨 风险控制

### 遵循 CLAUDE_WORKFLOW.md 强制检查

**Phase 1: 修改前风险评估**
- [ ] 备份当前代码（git stash 或创建备份分支）
- [ ] 不涉及认证功能 ✅
- [ ] 不涉及核心路由 ✅
- [ ] 修改范围：ProcessQuote.js（主要）+ useQuoteEditMode.js + QuoteResult.js

**Phase 2: 修改实施**
- [ ] 最小变更原则：一次只改一个优化点
- [ ] 渐进式验证：每改一部分就测试
- [ ] 11次提交（参考量产报价）

**Phase 3: 完成后验证**
- [ ] 新建报价单功能正常
- [ ] 编辑报价单功能正常
- [ ] 报价单详情显示正确
- [ ] 价格计算准确

### 财务准确性检查（CLAUDE.md要求）

- [ ] 单颗成本使用万分位取整（业务要求，保留）
- [ ] 总价使用 `ceilByCurrency`（CNY到元，USD到分）
- [ ] 不使用浮点数进行货币计算
- [ ] 输入验证防止错误配置

---

## ✅ 验收标准

### 功能完整性
- [ ] 工序报价支持完整的新建流程
- [ ] 工序报价支持完整的编辑流程
- [ ] 工序和板卡信息序列化存储在 configuration 字段
- [ ] 报价单详情不显示重复板卡项
- [ ] 支持多工序动态添加/删除

### 价格准确性
- [ ] 单颗成本保持4位小数（万分位）
- [ ] CNY 总价为整数
- [ ] USD 总价为两位小数
- [ ] 总价等于各工序之和（取整后）

### 用户体验
- [ ] 单页面模式，所有字段同时显示
- [ ] 工序表格无分页，所有工序一次显示
- [ ] 编辑模式页面标题正确显示报价单号
- [ ] "上一步"功能保留所有工序数据
- [ ] 编辑成功后跳转到详情页
- [ ] 无 null 引用错误

### 技术质量
- [ ] 代码风格与工程/量产报价一致
- [ ] 使用已验证的优化模式
- [ ] 无调试 console.log
- [ ] 完整的 null 安全检查
- [ ] 向后兼容旧报价单

---

## 🎯 实施优先级总结

**第一优先级（必须完成）**:
1. 板卡JSON序列化存储
2. 价格向上取整应用到所有项目
3. 编辑模式数据预填充

**第二优先级（重要）**:
4. 编辑模式标题和报价单号
5. "上一步"状态保持
6. 向后兼容（新旧格式）

**第三优先级（优化）**:
7. 单页面模式确认
8. 移除表格分页
9. Null安全检查

---

## 📚 参考文档

- **工程报价**: `/docs/reports/ENGINEERING_QUOTE_SUMMARY.md` - 7大特性参考
- **量产报价**: `/docs/reports/MASS_PRODUCTION_QUOTE_IMPLEMENTATION_SUMMARY.md` - 8大优化实施
- **量产报价计划**: `/docs/reports/MASS_PRODUCTION_OPTIMIZATION_PLAN.md` - 详细步骤
- **代码参考**:
  - `/frontend/chip-quotation-frontend/src/pages/EngineeringQuote.js`
  - `/frontend/chip-quotation-frontend/src/pages/MassProductionQuote.js`
- **工作流**: `/CLAUDE_WORKFLOW.md` - 强制性检查清单
- **开发哲学**: `/.claude/CLAUDE.md` - 渐进式开发原则

---

## 📊 工序报价 vs 量产报价对比

| 特性 | 量产机时报价 | 量产工序报价 | 差异点 |
|------|------------|------------|--------|
| **设备结构** | FT/CP 各1组设备 | 每个工序1组设备 | ⚠️ 多工序动态 |
| **板卡存储** | 设备 configuration | 工序 configuration | ⚠️ 工序级别 |
| **价格计算** | 小时费率 | 单颗成本 | ⚠️ 万分位精度 |
| **总价单位** | 小时 | 颗 | ⚠️ 不同单位 |
| **工序管理** | 无 | 动态增删 | ⚠️ 需额外处理 |

**关键差异处理**:
1. 工序数组遍历生成多个报价项
2. 每个工序有独立的 configuration
3. 单颗成本保留万分位（业务要求）
4. 总价仍按币种取整

---

*此计划遵循渐进式开发哲学，参考已验证的成功模式，确保每一步都不破坏现有功能*
