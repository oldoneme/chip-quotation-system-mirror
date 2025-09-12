# CLAUDE.md - 渐进式智能开发系统配置

## 🎯 项目哲学基础

### 核心信念体系
基于 Chris Dzombak 的编程哲学，结合 XP 极限编程和 TDD 实践，本项目遵循以下根本信念：

#### 1. 渐进优于跃进 (Incremental Progress Over Big Bangs)
- 每次改动必须可编译、可测试、可验证
- 功能分解为 3-5 个独立的小步骤
- 每步都设定明确的成功标准和验证点
- 持续集成，频繁交付可工作的软件

#### 2. 清晰优于聪明 (Clear Intent Over Clever Code)
- 选择无聊但明显的解决方案
- 代码应该自我解释，无需额外注释
- 如果需要解释工作原理，说明太复杂了
- 命名要准确表达意图，不怕长

#### 3. 实用优于教条 (Pragmatic Over Dogmatic)
- 根据项目实际情况调整方法
- 不追求技术完美，追求业务价值
- 技术债务要有意识地管理和记录
- 适应变化，拥抱反馈

#### 4. 学习优于创造 (Learn From Existing Code)
- 深入研究现有代码后再规划
- 复用项目中已验证的模式
- 遵循既定的编码约定
- 站在巨人的肩膀上

### 决策框架
面临技术选择时，按以下优先级评估：

```
1. 可测试性 (Testability)
   └─> 代码必须易于编写测试
   └─> 依赖注入优于硬编码
   └─> 纯函数优于副作用

2. 可读性 (Readability)  
   └─> 6个月后的你能理解
   └─> 新团队成员能快速上手
   └─> 意图明确胜过简洁

3. 一致性 (Consistency)
   └─> 与项目风格保持一致
   └─> 遵循团队约定
   └─> 统一的错误处理

4. 简单性 (Simplicity)
   └─> 最少的概念和抽象
   └─> YAGNI (You Aren't Gonna Need It)
   └─> 避免过早优化
```

## 📋 标准开发工作流

### Phase 1: 理解与规划 (Understand & Plan)
```yaml
目标: 深入理解问题，制定渐进式实施计划
步骤:
  1. 研究需求和问题域
  2. 探索现有代码库
  3. 创建 IMPLEMENTATION_PLAN.md
  4. 定义 3-5 个可验证的里程碑
  5. 识别风险和依赖项
验证:
  - [ ] 能够清晰解释问题
  - [ ] 计划得到相关方认可
  - [ ] 每个步骤都有明确产出
```

### Phase 2: 测试驱动开发 (Test-Driven Development)
```yaml
目标: 通过 TDD 确保代码质量和设计
循环:
  RED (写测试):
    - 编写失败的测试
    - 定义期望行为
    - 不写实现代码
    
  GREEN (写代码):
    - 最简实现通过测试
    - 不优化，不重构
    - 专注于功能实现
    
  REFACTOR (重构):
    - 保持测试通过
    - 消除重复代码
    - 改善代码结构
    
提交:
  - 清晰的提交信息
  - 原子性提交
  - 包含测试的完整功能
```

### Phase 3: 验证与优化 (Verify & Optimize)
```yaml
目标: 确保代码质量，性能达标
检查清单:
  - [ ] 所有测试通过
  - [ ] Lint 检查无警告
  - [ ] 类型检查通过
  - [ ] 代码覆盖率达标
  - [ ] 性能基准测试通过
  - [ ] 文档已更新
  - [ ] PR 已创建并审查
```

## 🚨 问题解决策略

### 三次尝试规则 (Three-Strike Rule)
```
尝试 1: 直接实现最简单的方案
尝试 2: 调整参数或轻微修改方法
尝试 3: 尝试完全不同的方案

三次失败后必须停止并重新评估：
□ 我真的理解问题吗？
□ 是否遗漏了关键上下文？
□ 问题是否太大需要分解？
□ 是否需要寻求团队帮助？
□ 是否在解决正确的问题？
```

### 调试策略
1. **复现问题** - 创建最小可复现案例
2. **隔离变量** - 逐个排除可能原因
3. **二分查找** - 缩小问题范围
4. **日志追踪** - 添加详细日志
5. **寻求帮助** - 及时升级问题

## 🛠️ 技术规范

### 代码组织原则
```
src/
├── core/           # 核心业务逻辑（纯函数）
├── adapters/       # 外部系统适配器
├── interfaces/     # 接口定义
├── utils/          # 工具函数
└── tests/          # 测试文件
```

### 命名约定
- **变量**: camelCase, 描述性名称
- **常量**: UPPER_SNAKE_CASE
- **函数**: 动词开头，说明做什么
- **类**: PascalCase, 名词
- **文件**: kebab-case 或 camelCase

### 测试规范
```javascript
// 测试结构
describe('ComponentName', () => {
  describe('methodName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      // Act  
      // Assert
    });
  });
});
```

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>

类型:
- feat: 新功能
- fix: 错误修复
- refactor: 重构（不改变功能）
- test: 测试相关
- docs: 文档更新
- style: 格式调整
- perf: 性能优化
- chore: 构建/工具链相关
```

## ✅ 完成定义 (Definition of Done)

一个任务只有满足以下所有条件才算完成：

```yaml
代码质量:
  - [ ] 所有测试通过
  - [ ] 新功能有对应测试
  - [ ] 代码覆盖率 >= 80%
  - [ ] 无 linter 警告
  - [ ] 类型检查通过

代码规范:
  - [ ] 遵循项目编码约定
  - [ ] 代码自解释，必要处有注释
  - [ ] 没有调试代码
  - [ ] 没有 TODO 没有 issue 编号

文档:
  - [ ] README 已更新（如需要）
  - [ ] API 文档已更新
  - [ ] CHANGELOG 已更新

流程:
  - [ ] 代码已审查
  - [ ] 分支已合并
  - [ ] CI/CD 通过
```

## 🤖 AI 协作指南

### Claude 的职责
1. **深入理解后行动**
   - 先读取和分析相关代码
   - 理解项目架构和约定
   - 识别潜在影响范围

2. **遵循标准流程**
   - 严格执行 TDD 循环
   - 遵守三次尝试规则
   - 保持渐进式开发节奏

3. **提供高质量输出**
   - 代码必须通过所有检查
   - 保持风格一致性
   - 编写清晰的测试用例

4. **主动验证和测试**
   - 每次修改后运行测试
   - 执行 lint 和类型检查
   - 验证边界条件

5. **清晰沟通进展**
   - 使用 TodoWrite 跟踪任务
   - 及时报告问题和阻塞
   - 提供多个解决方案选项

### 期望行为模式
```yaml
开始任务时:
  1. 理解需求和上下文
  2. 研究相关代码
  3. 创建实施计划
  4. 获得确认后开始

开发过程中:
  1. 小步前进，频繁验证
  2. 先测试，后实现
  3. 保持代码可工作状态
  4. 及时提交和推送

遇到问题时:
  1. 执行三次尝试规则
  2. 重新评估问题定义
  3. 寻求澄清和帮助
  4. 记录学到的经验
```

### 禁止的行为
- ❌ 跳过测试直接实现功能
- ❌ 引入未经验证的第三方库
- ❌ 创建过度复杂的抽象
- ❌ 忽略项目既定约定
- ❌ 在三次失败后继续盲目尝试
- ❌ 修改测试来通过实现
- ❌ 提交包含调试代码
- ❌ 创建没有测试的新功能

## 📚 项目特定配置

### 技术栈
```yaml
语言: [项目使用的编程语言]
框架: [主要框架和版本]
测试: [测试框架]
构建: [构建工具]
依赖: [关键依赖]
```

### 核心命令
```bash
# 安装依赖
npm install

# 运行测试
npm test
npm run test:watch  # 监听模式
npm run test:coverage  # 覆盖率报告

# 代码质量
npm run lint
npm run typecheck
npm run format

# 构建和运行
npm run build
npm run dev
npm run start

# 提交前检查
npm run precommit
```

### 项目结构
```
项目特定的目录结构和说明
```

## 🔗 相关资源

### 内部文档
- [PHILOSOPHY.md](../docs/PHILOSOPHY.md) - 深度哲学解释
- [WORKFLOW.md](../docs/WORKFLOW.md) - 详细流程图解
- [BEST_PRACTICES.md](../docs/BEST_PRACTICES.md) - 最佳实践案例

### 外部参考
- [Chris Dzombak 的 Claude Code 最佳实践](https://www.dzombak.com/blog/2025/08/getting-good-results-from-claude-code/)
- [Anthropic Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)
- [极限编程实践指南](https://agilealliance.org/glossary/xp/)
- [测试驱动开发](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

*此配置基于业界最佳实践和成功项目经验总结，持续迭代优化中。*