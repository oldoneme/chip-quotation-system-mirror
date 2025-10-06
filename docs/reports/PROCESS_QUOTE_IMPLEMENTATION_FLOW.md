# 量产工序报价优化实施流程

## 📋 快速参考

**文档**: [`PROCESS_QUOTE_OPTIMIZATION_PLAN.md`](./PROCESS_QUOTE_OPTIMIZATION_PLAN.md)（详细计划）
**状态**: 🔄 计划已制定，等待执行指令
**预计**: 10步优化，~10-12次提交，~600行改动

---

## 🚀 实施流程（参考量产报价成功模式）

### 第一阶段：核心功能（3-4次提交）

#### Commit 1: 板卡JSON序列化存储
```
feat: 工序报价应用板卡JSON序列化模式

修改：
- ProcessQuote.js: 新增 generateProcessQuoteItems() 函数
- 遍历 cpProcesses + ftProcesses 生成报价项
- 每个工序的 configuration 包含：
  * process_type（工序名称）
  * test_machine（含板卡数组）
  * prober/handler（含板卡数组）
  * uph, unit_cost
- 添加 machine_id 关联主设备
```

#### Commit 2: 价格向上取整
```
feat: 工序报价价格向上取整（保留单颗成本精度）

修改：
- 保留 formatUnitPrice 万分位取整（业务要求）
- 总价应用 ceilByCurrency(totalPrice, currency)
- CNY 总价取整到元
- USD 总价取整到分
```

#### Commit 3: 编辑模式数据预填充（核心）
```
feat: 实现工序报价编辑模式完整数据预填充

修改：
- useQuoteEditMode.js: 新增 parseProcessQuoteDevicesFromItems()
- ProcessQuote.js: useEffect 预填充逻辑
- 解析所有工序、设备、板卡数量
- 支持新旧格式双路径解析
```

---

### 第二阶段：用户体验（2-3次提交）

#### Commit 4: 单页面模式 + 无分页表格
```
refactor: 工序报价单页面模式优化

修改：
- 移除 StepIndicator（如有）
- 工序表格 pagination={false}
- 所有字段同时显示
```

#### Commit 5: 编辑模式标题 + "上一步"
```
feat: 工序报价编辑模式UI优化

修改：
- 页面标题显示报价单号
- QuoteResult.js 保存工序数据到 sessionStorage
- ProcessQuote.js 恢复工序数组
```

---

### 第三阶段：完善和验证（3-4次提交）

#### Commit 6: Null安全检查
```
refactor: 工序报价添加完整null安全检查

修改：
- 所有设备访问添加可选链
- 供应商字段防御性检查
- 板卡数组长度检查
```

#### Commit 7-8: 辅助设备/特殊情况修复（如需要）
```
fix: 修复工序报价[具体问题]

- 根据测试发现的问题修复
- 参考量产报价辅助设备修复模式
```

#### Commit 9: 代码清理
```
chore: 移除工序报价调试日志，清理代码

- 移除所有 console.log
- 代码整洁，生产就绪
```

#### Commit 10: 文档更新
```
docs: 更新工序报价实施总结文档

- 创建 PROCESS_QUOTE_IMPLEMENTATION_SUMMARY.md
- 更新 IMPLEMENTATION_PLAN.md 标记完成
- 更新 README.md
```

---

## ✅ 每步验收检查

### Step 1: 板卡JSON序列化
- [ ] 工序报价项包含 configuration JSON
- [ ] configuration 包含完整设备和板卡信息
- [ ] 每个工序有 machine_id
- [ ] 报价详情不显示重复板卡

### Step 2: 价格取整
- [ ] 单颗成本保持4位小数（万分位）
- [ ] CNY 总价为整数
- [ ] USD 总价为2位小数

### Step 3: 编辑预填充
- [ ] 所有工序正确恢复
- [ ] 每个工序的设备正确选中
- [ ] 板卡数量正确显示
- [ ] UPH 和单颗成本正确

### Step 4-5: 用户体验
- [ ] 单页面模式
- [ ] 工序表格无分页
- [ ] 编辑标题显示报价单号
- [ ] "上一步"功能完整

### Step 6: 代码质量
- [ ] 无 null 引用错误
- [ ] 无调试日志
- [ ] 代码风格一致

---

## 🎯 关键注意事项

### 1. 多工序处理
```javascript
// 遍历所有工序生成报价项
const items = [];

formData.cpProcesses.forEach(process => {
  if (process.testMachine) {
    items.push({
      item_name: `CP工序 - ${process.name}`,
      configuration: JSON.stringify({
        process_type: process.name,
        test_machine: {
          id: process.testMachineData.id,
          name: process.testMachine,
          cards: getCardsInfo(process.testMachineCardQuantities)
        },
        prober: {
          id: process.proberData?.id,
          name: process.prober,
          cards: getCardsInfo(process.proberCardQuantities)
        },
        uph: process.uph,
        unit_cost: process.unitCost
      }),
      machine_id: process.testMachineData.id,
      category_type: 'process',
      unit_price: process.unitCost,
      total_price: ceilByCurrency(process.unitCost * totalQuantity, currency)
    });
  }
});

// FT 工序同理
formData.ftProcesses.forEach(process => { /* ... */ });
```

### 2. 单颗成本精度
```javascript
// 保留业务要求的万分位取整
const formatUnitPrice = (number) => {
  const ceiledToFourDecimals = Math.ceil(number * 10000) / 10000;
  return ceiledToFourDecimals.toFixed(4);
};

// 总价按币种取整
const totalPrice = ceilByCurrency(unitCost * quantity, currency);
```

### 3. 编辑模式解析
```javascript
const parseProcessQuoteDevicesFromItems = (items, availableCardTypes, availableMachines) => {
  const cpProcesses = [];
  const ftProcesses = [];

  items.forEach(item => {
    // 双路径解析
    let configData = item.configuration ? JSON.parse(item.configuration) : null;

    if (!configData) {
      // 旧格式：从 item 字段推断
      configData = {
        process_type: item.item_name,
        // ... 通过名称匹配设备
      };
    }

    // 构建工序对象
    if (configData.process_type.includes('CP')) {
      cpProcesses.push({
        id: cpProcesses.length + 1,
        name: configData.process_type,
        testMachine: configData.test_machine?.name,
        testMachineData: availableMachines.find(m => m.id === item.machine_id),
        // ... 其他字段
      });
    }
  });

  return { cpProcesses, ftProcesses };
};
```

---

## 📚 参考文档

**代码参考**:
- `/frontend/src/pages/MassProductionQuote.js` - JSON序列化模式
- `/frontend/src/pages/EngineeringQuote.js` - 编辑预填充模式
- `/frontend/src/hooks/useQuoteEditMode.js` - 解析函数模式

**文档参考**:
- [`MASS_PRODUCTION_QUOTE_IMPLEMENTATION_SUMMARY.md`](./MASS_PRODUCTION_QUOTE_IMPLEMENTATION_SUMMARY.md)
- [`ENGINEERING_QUOTE_SUMMARY.md`](./ENGINEERING_QUOTE_SUMMARY.md)
- [`AUXILIARY_DEVICE_FIX_SUMMARY.md`](./AUXILIARY_DEVICE_FIX_SUMMARY.md)

---

## 🚦 开始实施

**准备清单**:
- [x] 计划文档已创建
- [x] 参考代码已识别
- [x] 验收标准已明确
- [ ] 等待执行指令

**执行指令**:
```
请开始实施量产工序报价优化，按照计划逐步进行
```

---

*此流程基于工程报价和量产报价的成功经验，确保稳定、高效、可验证*
