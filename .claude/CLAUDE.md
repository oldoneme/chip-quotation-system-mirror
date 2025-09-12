# CLAUDE.md - 芯片报价系统渐进式智能开发配置

## 🎯 项目概述

**项目名称**：芯片报价系统 - 基于设备配置的智能测试费用计算平台

**项目目标**：为芯片测试服务提供自动化报价计算，基于设备选择、配置参数和人力资源实现实时成本核算

**业务价值**：
- 自动化报价生成，减少人工计算错误
- 标准化定价流程，提升报价一致性
- 实时计算能力，加快客户响应速度
- 设备利用率可视化，优化资源配置

## 🛠️ 技术架构

### 技术栈配置
```yaml
后端服务:
  语言: Python 3.7+
  框架: FastAPI
  数据库: PostgreSQL (开发环境可用 SQLite)
  ORM: SQLAlchemy
  数据验证: Pydantic
  API文档: Swagger/OpenAPI (FastAPI自动生成)

前端应用:
  语言: TypeScript
  框架: React.js
  UI组件库: Ant Design
  HTTP客户端: Axios
  状态管理: React Hooks

开发环境:
  操作系统: Ubuntu
  版本控制: Git (Gitee主仓库 + GitHub镜像)
  接口测试: FastAPI自带Swagger UI
```

### 项目结构
```
chip-quotation-system/
├── backend/                    # FastAPI后端服务
│   ├── app/
│   │   ├── api/               # REST API路由
│   │   ├── models.py          # SQLAlchemy数据库模型
│   │   ├── schemas.py         # Pydantic请求/响应模式
│   │   ├── crud.py            # 数据库CRUD操作
│   │   ├── database.py        # 数据库连接配置
│   │   └── main.py            # FastAPI应用入口
│   ├── requirements.txt       # Python依赖包
│   └── init_data.py          # 数据库初始化和示例数据
├── frontend/                  # React TypeScript前端
│   └── chip-quotation-frontend/
├── .claude/                   # Claude Code配置目录
│   ├── CLAUDE.md             # 本配置文件
│   └── commands/             # 自定义开发命令
├── .workflow/                # 开发工作流模板
├── docs/                     # 项目文档
├── start_backend.ps1         # 后端启动脚本
└── start_frontend.ps1        # 前端启动脚本
```

---

## 🧠 渐进式开发哲学

### 核心信念体系 (适配芯片报价系统)

基于 Chris Dzombak 的编程哲学，结合芯片报价系统的特殊需求：

#### 1. 渐进优于跃进 (财务计算的安全开发)
- **API开发策略**：一次构建一个报价接口，完全测试后再开发下一个
- **前端组件开发**：每次迭代实现一个报价组件（设备选择→配置参数→人员分配）
- **数据库变更**：使用 Alembic 迁移，绝不直接修改现有数据表
- **功能发布**：渐进式添加报价参数，确保每步都不影响现有计算逻辑

#### 2. 清晰优于聪明 (财务准确性第一)
- **API命名**：`/api/v1/quotations/calculate` 而不是 `/api/calc`
- **组件命名**：`EquipmentSelector` 而不是 `EqSel`
- **数据库字段**：`hourly_rate_usd` 而不是 `rate`
- **业务逻辑**：明确的计算步骤，避免复杂的一行计算公式

#### 3. 实用优于教条 (业务需求导向)
- **开发数据库**：本地开发用 SQLite，生产环境用 PostgreSQL
- **界面响应性**：客户端报价页面优先移动端，管理后台优化桌面端
- **性能考虑**：优化关键计算路径，其他地方可接受轻微低效
- **技术债务**：记录定价公式假设，为未来业务规则变化做准备

#### 4. 学习优于创造 (复用现有模式)
- **遵循 FastAPI 模式**：沿用你现有接口的成熟设计模式
- **保持 Ant Design 一致性**：使用既定的组件设计风格
- **复用 SQLAlchemy 模式**：继承现有数据模型的设计规范
- **维护 PowerShell 脚本约定**：保持现有启动脚本的使用习惯

### 决策框架 (报价系统特化)
```
1. 计算准确性 (财务系统的生命线)
   └─> 所有货币计算必须可审计
   └─> 使用 Decimal 类型，绝不用 float
   └─> 输入验证防止错误报价生成

2. 业务可靠性 (客户信任的基础)
   └─> 报价生成绝不能静默失败
   └─> 设备可用性检查先于报价计算
   └─> 无效配置必须有清晰错误提示

3. 系统可维护性 (长期发展考虑)
   └─> 定价规则可由业务人员更新
   └─> 设备规格可配置化，无需代码部署
   └─> 历史报价可追溯，审计友好

4. 性能表现 (用户体验保证)
   └─> 报价计算响应时间 < 1秒
   └─> 设备可用性查询高效执行
   └─> 复杂配置计算时UI保持响应
```

---

## 📋 标准开发工作流

### Phase 1: 理解与规划 (报价功能开发)
```yaml
新报价功能开发流程:
  1. 理解业务需求 (定价规则、设备约束条件)
  2. 审查现有计算逻辑和数据模型
  3. 创建 IMPLEMENTATION_PLAN.md，分解为3-5个增量步骤
  4. 与业务干系人确认验收标准
  5. 识别需要的API端点和数据库变更
验证标准:
  - [ ] 能够清晰解释业务需求
  - [ ] 计划获得业务方认可
  - [ ] 每个步骤都有明确的交付成果
  - [ ] 风险和依赖项已识别
```

### Phase 2: 测试驱动开发 (财务逻辑的严格测试)
```yaml
财务计算准确性保证:
  RED (编写测试):
    - 为计算逻辑编写失败测试
    - 包含边界条件 (零数量、溢价费率)
    - 使用真实定价场景测试
    - 绝不跳过财务计算的测试
    
  GREEN (编写代码):
    - 实现通过财务测试的最小代码
    - 所有货币计算使用 Decimal 类型
    - 彻底验证所有输入参数
    - 专注功能正确性，不考虑优化
    
  REFACTOR (重构优化):
    - 将定价规则提取为可配置参数
    - 优化数据库查询性能
    - 提升计算逻辑的可读性
    - 确保所有测试依然通过
```

### Phase 3: API优先开发 (FastAPI最佳实践)
```yaml
后端开发流程:
  1. 定义 Pydantic 请求/响应模式
  2. 实现 FastAPI 端点，确保 OpenAPI 文档完整
  3. 添加 SQLAlchemy 模型和 CRUD 操作
  4. 编写全面的API测试用例
  5. 在 Swagger UI 中测试后再进行前端集成

前端集成流程:
  1. 从 OpenAPI 规范生成 TypeScript 类型
  2. 创建 Axios 服务函数
  3. 使用 Ant Design 构建 React 组件
  4. 实现错误处理和加载状态
  5. 添加与后端模式匹配的表单验证
```

---

## 🚨 三次尝试规则 (报价系统特化)

针对你的业务领域特殊问题：

```
报价计算问题:
  尝试 1: 检查计算逻辑和输入验证
  尝试 2: 验证数据库约束和设备可用性
  尝试 3: 审查业务规则和定价配置参数

API集成问题:
  尝试 1: 检查 FastAPI 端点和 Swagger 文档
  尝试 2: 验证 Pydantic 模式和 TypeScript 类型定义
  尝试 3: 使用不同数据场景和错误用例测试

数据库性能问题:
  尝试 1: 检查查询效率和索引配置
  尝试 2: 审查 SQLAlchemy 关系和预加载策略
  尝试 3: 分析查询执行计划并优化联接

三次尝试后仍未解决，必须停止并重新评估问题定义。
```

---

## 🛠️ 项目专用命令配置

### 核心开发命令
```bash
# 后端开发环境
cd backend
python -m venv venv
venv\Scripts\activate              # Windows 激活虚拟环境
pip install -r requirements.txt

# 启动后端开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 或使用 PowerShell 脚本:
.\start_backend.ps1

# 数据库操作
alembic revision --autogenerate -m "添加设备定价规则"
alembic upgrade head
python init_data.py  # 初始化示例数据

# 测试执行
pytest app/tests/ -v --cov=app --cov-report=html
pytest app/tests/test_quotation_calculation.py -v

# 代码质量检查
black app/ --check
flake8 app/
mypy app/
```

### 前端开发命令
```bash
# 前端环境配置
cd frontend/chip-quotation-frontend
npm install

# 启动开发服务器
npm start
# 或使用 PowerShell 脚本:
.\start_frontend.ps1

# 构建和测试
npm run build
npm test -- --coverage --watchAll=false
npm run lint
npm run type-check

# 组件测试
npm test -- --testNamePattern="EquipmentSelector"
```

### 全栈集成命令
```bash
# 同时启动前后端服务 (需要安装 concurrently)
concurrently "cd backend && uvicorn app.main:app --reload" "cd frontend/chip-quotation-frontend && npm start"

# API测试 (使用真实数据)
curl -X POST "http://localhost:8000/api/v1/quotations/calculate" \
  -H "Content-Type: application/json" \
  -d '{"equipment_id": 1, "configuration": {...}}'

# 端到端测试
playwright test tests/quotation-flow.spec.ts
```

---

## 🤖 AI协作指南 (报价系统特化)

### Claude的专项职责

1. **财务计算准确性保证**
   - 始终使用 Python 的 `decimal.Decimal` 进行货币计算
   - 用多种测试场景验证所有定价逻辑
   - 确保四舍五入遵循业务规则 (报价向上取整)
   - 计算结果必须与手工验证交叉核对

2. **API设计一致性维护**
   - 遵循代码库中既定的 FastAPI 模式
   - 保持各端点间响应模式的一致性
   - 为业务场景确保正确的 HTTP 状态码
   - 生成完整准确的 OpenAPI 文档

3. **数据库完整性保障**
   - 维护设备/报价数据中的外键关系
   - 模式变更必须使用适当的 SQLAlchemy 迁移
   - 维护定价历史的参照完整性
   - 优化报价计算性能的查询

4. **前端业务逻辑实现**
   - 实现符合业务规则的适当表单验证
   - 报价计算期间处理加载状态
   - 清晰显示定价明细，确保透明度
   - 确保各种屏幕尺寸的响应式设计

### 报价系统工作流集成

```yaml
功能开发流程:
  规划阶段: 
    - 审查对现有报价计算的影响
    - 考虑设备可用性约束条件
    - 规划定价规则的可配置性
    
  实施阶段:
    - 后端: API端点 → 数据库 → 业务逻辑
    - 前端: 组件 → 表单验证 → API集成
    - 测试: 单元测试 → 集成测试 → 手工验证
    
  验证阶段:
    - 手工计算样本报价以验证准确性
    - 测试边界条件 (零数量、溢价设备)
    - 验证UI优雅处理错误情况
    - 确认响应式设计在目标设备上正常工作
```

---

## 🔒 领域特定质量标准

### 财务准确性要求
- [ ] Python中所有货币值使用 `decimal.Decimal`
- [ ] 计算按业务规则四舍五入
- [ ] 输入验证防止不可能的配置
- [ ] 报价修改的审计跟踪
- [ ] 定价错误处理绝不静默失败

### 业务逻辑完整性
- [ ] 报价前检查设备可用性
- [ ] 验证配置兼容性
- [ ] 人员技能水平正确纳入定价
- [ ] 费率表可在不部署代码的情况下更新
- [ ] 费率变化后历史报价保持准确

### API质量标准
- [ ] FastAPI自动文档完整准确
- [ ] 各端点间错误响应格式一致
- [ ] 业务场景使用适当的HTTP状态码
- [ ] 请求/响应模式与TypeScript接口匹配
- [ ] 未来变化的API版本控制策略

### 前端用户体验
- [ ] 表单验证提供清晰的业务上下文
- [ ] 报价计算期间的加载状态
- [ ] 报价明细显示透明定价
- [ ] 错误消息帮助用户修正无效输入
- [ ] 客户演示的响应式设计

---

## 🚫 财务系统禁止行为

- ❌ **绝不使用浮点数进行货币计算**
- ❌ **绝不跳过定价参数的输入验证**
- ❌ **绝不在未测试计算的情况下部署定价变更**
- ❌ **绝不直接修改报价数据库记录**
- ❌ **绝不在错误消息中暴露内部费率计算**
- ❌ **绝不在没有过期策略的情况下缓存定价数据**
- ❌ **绝不允许使用不可用设备生成报价**

---

## ✅ 报价功能完成定义

```yaml
业务需求:
  - [ ] 功能为报价流程提供可衡量价值
  - [ ] 通过样本计算验证定价准确性
  - [ ] 业务规则正确实施且可配置
  - [ ] 报价生成性能满足亚秒级要求

技术实施:
  - [ ] 后端API用pytest完全测试
  - [ ] 前端组件用React Testing Library测试
  - [ ] 集成测试覆盖报价计算流程
  - [ ] 数据库迁移成功应用
  - [ ] OpenAPI文档已更新

财务合规:
  - [ ] 所有计算使用适当的十进制精度
  - [ ] 维护报价历史的审计跟踪
  - [ ] 错误处理保持数据完整性
  - [ ] 费率变更不会错误影响现有报价

用户体验:
  - [ ] 表单提供清晰的验证反馈
  - [ ] 报价计算在性能要求内完成
  - [ ] 错误消息帮助用户解决问题
  - [ ] 在目标设备上测试响应式设计
```

---

## 🎯 报价系统自定义命令

你现在可以在 Claude Code 中使用这些命令：

- `/plan [报价功能]` - 为报价系统功能创建实施计划
- `/tdd [计算逻辑]` - 启动财务计算的TDD循环
- `/implement [api/组件]` - 遵循FastAPI/React模式实施
- `/review [定价逻辑]` - 重点关注财务准确性的代码审查
- `/debug [报价计算问题]` - 系统化调试报价系统问题

使用示例：
```
/plan 在报价计算中添加批量折扣定价支持
/tdd 实现设备利用率计算逻辑
/implement 创建设备可用性检查的API端点
/review 验证所有定价计算中的十进制精度
/debug 复杂配置的报价总额与手工计算不匹配
```

---

## 📚 学习资源和参考

### 内部文档
- [PHILOSOPHY.md](../docs/PHILOSOPHY.md) - 深度哲学解释
- [WORKFLOW.md](../docs/WORKFLOW.md) - 详细流程图解
- [BEST_PRACTICES.md](../docs/BEST_PRACTICES.md) - 最佳实践案例

### 技术参考
- [FastAPI官方文档](https://fastapi.tiangolo.com/zh/)
- [SQLAlchemy ORM指南](https://docs.sqlalchemy.org/en/14/orm/)
- [Ant Design React组件库](https://ant.design/components/overview-cn/)
- [Python decimal模块](https://docs.python.org/3/library/decimal.html) - 财务计算必读

---

*此配置专门为芯片报价系统定制，结合了Chris Dzombak的编程哲学和财务系统的特殊要求，确保开发过程中始终保持计算准确性和业务逻辑完整性。*