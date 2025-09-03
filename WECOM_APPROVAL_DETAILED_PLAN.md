# 企业微信审批集成 - 详细实施计划

**项目名称**: WeCom 原生审批 + 规则治理层 + 生效报价单生成  
**基于方案**: 更新版规范化实施方案  
**项目周期**: 2025-09-01 ~ 2025-09-30 (4周)  
**当前状态**: 📋 详细计划制定中

---

## 📋 总体实施策略

按照**阶段A → 阶段B → 阶段C**的顺序执行，每个阶段都有明确的验收标准。
- **阶段A**: 规则外置 + 模型与迁移 + 快照机制 (1周)
- **阶段B**: 审批提交流程 + 短效deeplink + 幂等回调 (1.5周)  
- **阶段C**: 导出占位 + 前端改造 + 文档完善 (1.5周)

---

## 🎯 阶段A: 规则外置 + 模型与迁移 + 快照机制 (1周)

### A1: 配置与规则外置 (1天)

#### A1.1 补齐环境配置 (2小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 补齐.env配置项 | `backend/.env.example` | 添加DEEPLINK_JWT_SECRET等新配置项 | ⏳ | 0.5h | - |
| 验证config.py配置读取 | `backend/app/config.py` | 确保新配置项可正确读取 | ⏳ | 0.5h | - |
| 本地环境配置检查 | `backend/.env` | 复制.env.example并配置测试值 | ⏳ | 1h | - |

#### A1.2 创建规则配置文件 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建approval_rules.yaml | `backend/app/config/approval_rules.yaml` | 定义模板映射和审批规则 | ⏳ | 1h | - |
| 实现rules_loader.py | `backend/app/services/rules_loader.py` | YAML读取和缓存机制 | ⏳ | 2h | - |
| 实现expr_eval.py | `backend/app/services/expr_eval.py` | 安全表达式求值(白名单) | ⏳ | 1h | - |

#### A1.3 配置验证测试 (2小时)
| 任务 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|
| 规则加载测试 | 验证YAML可正确加载和解析 | ⏳ | 0.5h | - |
| 表达式求值测试 | 测试amount_total>=500000等表达式 | ⏳ | 0.5h | - |
| 模板选择测试 | 测试6种报价类型映射 | ⏳ | 1h | - |

### A2: 数据模型扩展 (2天)

#### A2.1 扩展Quote模型 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 检查Quote字段完整性 | `backend/app/models.py` | 确认amount_total、approval_status字段 | ⏳ | 0.5h | - |
| 添加缺失字段 | `backend/app/models.py` | 添加amount_total计算属性等 | ⏳ | 1.5h | - |
| 更新Quote关系映射 | `backend/app/models.py` | 与新模型的外键关系 | ⏳ | 1h | - |
| Quote模型测试 | 单元测试 | 验证字段和关系正确性 | ⏳ | 1h | - |

#### A2.2 创建QuoteSnapshot模型 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 设计QuoteSnapshot模型 | `backend/app/models.py` | id, quote_id, data(JSON), hash等字段 | ⏳ | 1h | - |
| 实现数据序列化方法 | `backend/app/models.py` | to_snapshot()方法 | ⏳ | 1.5h | - |
| 实现hash计算方法 | `backend/app/models.py` | calc_hash()稳定哈希算法 | ⏳ | 1h | - |
| QuoteSnapshot测试 | 单元测试 | 验证快照和哈希功能 | ⏳ | 0.5h | - |

#### A2.3 创建EffectiveQuote模型 (4小时)  
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 设计EffectiveQuote模型 | `backend/app/models.py` | id, quote_id, snapshot_id, version等 | ⏳ | 1h | - |
| 实现版本管理逻辑 | `backend/app/models.py` | 自动版本递增机制 | ⏳ | 1.5h | - |
| 添加导出文件字段 | `backend/app/models.py` | export_file_url, checksum等 | ⏳ | 1h | - |
| EffectiveQuote测试 | 单元测试 | 验证版本管理和字段完整性 | ⏳ | 0.5h | - |

#### A2.4 完善ApprovalRecord模型 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 检查ApprovalRecord字段 | `backend/app/models.py` | 确认所需字段完整性 | ⏳ | 0.5h | - |
| 添加企业微信集成字段 | `backend/app/models.py` | wecom_instance_id, payload等 | ⏳ | 1.5h | - |
| 添加幂等性支持字段 | `backend/app/models.py` | event_time, processed等 | ⏳ | 1h | - |
| ApprovalRecord测试 | 单元测试 | 验证字段和约束 | ⏳ | 1h | - |

### A3: 数据库迁移 (1天)

#### A3.1 初始化Alembic (4小时)
| 任务 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|
| 检查Alembic状态 | 确认项目是否已使用Alembic | ⏳ | 0.5h | - |
| 初始化Alembic配置 | alembic init alembic (如需要) | ⏳ | 1h | - |
| 配置alembic.ini | 数据库URL和配置项 | ⏳ | 0.5h | - |
| 创建基础迁移 | 基于现有模型生成初始迁移 | ⏳ | 2h | - |

#### A3.2 创建增量迁移 (4小时)
| 任务 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|
| 生成新模型迁移 | QuoteSnapshot, EffectiveQuote迁移 | ⏳ | 1.5h | - |
| 生成字段变更迁移 | Quote和ApprovalRecord字段变更 | ⏳ | 1.5h | - |
| 验证迁移脚本 | 检查SQL语法和逻辑正确性 | ⏳ | 0.5h | - |
| 迁移回滚测试 | 确保可安全回滚 | ⏳ | 0.5h | - |

### A4: 快照服务实现 (1天)

#### A4.1 实现snapshot_service.py (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建SnapshotService类 | `backend/app/services/snapshot_service.py` | 基础服务类结构 | ⏳ | 1h | - |
| 实现create_snapshot() | `backend/app/services/snapshot_service.py` | 创建报价快照 | ⏳ | 2h | - |
| 实现calc_hash()方法 | `backend/app/services/snapshot_service.py` | 稳定哈希计算 | ⏳ | 1h | - |
| 实现数据序列化 | `backend/app/services/snapshot_service.py` | Quote对象转JSON | ⏳ | 1.5h | - |
| 快照服务集成测试 | 单元测试 | 端到端测试快照创建 | ⏳ | 0.5h | - |

#### A4.2 快照功能验证 (2小时)
| 任务 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|
| 快照创建测试 | 从Quote创建快照并验证数据 | ⏳ | 1h | - |
| 哈希一致性测试 | 相同数据生成相同哈希 | ⏳ | 0.5h | - |
| 数据完整性测试 | 快照包含所有必要字段 | ⏳ | 0.5h | - |

### 阶段A验收标准

**必须全部通过才能进入阶段B**:

- [ ] ✅ approval_rules.yaml可被正确加载，by_amount路由可被解析
- [ ] ✅ 能创建Quote对象，调用create_snapshot()，生成QuoteSnapshot并计算正确hash
- [ ] ✅ Alembic迁移可顺利执行且回滚安全，数据库包含新表和字段
- [ ] ✅ 所有新增模型的单元测试通过
- [ ] ✅ 规则加载、表达式求值、模板选择功能正常

---

## 🔄 阶段B: 审批提交流程 + 短效deeplink + 幂等回调 (1.5周)

### B1: 审批服务层实现 (2天)

#### B1.1 实现WeComApprovalService (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建WeComApprovalService | `backend/app/services/wecom_approval_service.py` | 基础服务类 | ⏳ | 0.5h | - |
| 实现select_template() | `backend/app/services/wecom_approval_service.py` | 根据报价类型选择模板 | ⏳ | 1h | - |
| 实现select_approvers() | `backend/app/services/wecom_approval_service.py` | 根据规则选择审批人 | ⏳ | 1.5h | - |
| 实现build_message_payload() | `backend/app/services/wecom_approval_service.py` | 构建审批消息内容 | ⏳ | 1.5h | - |
| 集成rules_loader | `backend/app/services/wecom_approval_service.py` | 使用规则配置 | ⏳ | 1h | - |
| 审批服务单元测试 | 测试文件 | 模板选择和审批人选择测试 | ⏳ | 0.5h | - |

#### B1.2 扩展WeComIntegration (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 扩展create_approval_instance() | `backend/app/services/wecom_integration.py` | 增强审批创建功能 | ⏳ | 2h | - |
| 实现parse_callback() | `backend/app/services/wecom_integration.py` | 解析回调数据 | ⏳ | 1.5h | - |
| 实现send_notify() | `backend/app/services/wecom_integration.py` | 发送通知消息 | ⏳ | 1.5h | - |
| 添加错误处理和重试 | `backend/app/services/wecom_integration.py` | 提高可靠性 | ⏳ | 1h | - |

#### B1.3 实现deeplink服务 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建DeepLinkService | `backend/app/services/deeplink.py` | JWT token生成和验证 | ⏳ | 2h | - |
| 实现make_token() | `backend/app/services/deeplink.py` | 生成短效JWT | ⏳ | 1h | - |
| 实现verify_token() | `backend/app/services/deeplink.py` | 验证token有效性 | ⏳ | 0.5h | - |
| 实现build_deeplink() | `backend/app/services/deeplink.py` | 构建前端链接 | ⏳ | 0.5h | - |

#### B1.4 实现outbox服务 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建Outbox模型 | `backend/app/models.py` | 事务型outbox表 | ⏳ | 1h | - |
| 实现OutboxService | `backend/app/services/outbox.py` | 外部副作用管理 | ⏳ | 2h | - |
| 实现worker_tick() | `backend/app/services/outbox.py` | 批处理外部调用 | ⏳ | 1h | - |

### B2: API端点实现 (3天)

#### B2.1 实现submit-approval端点 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建pydantic schemas | `backend/app/schemas.py` | SubmitApprovalReq/Resp模型 | ⏳ | 1h | - |
| 实现submit_approval端点 | `backend/app/api/v1/endpoints/quotes.py` | 完整审批提交流程 | ⏳ | 3h | - |
| 添加权限校验 | `backend/app/api/v1/endpoints/quotes.py` | guard_can_submit逻辑 | ⏳ | 1h | - |
| 添加状态验证 | `backend/app/api/v1/endpoints/quotes.py` | 确保草稿状态 | ⏳ | 0.5h | - |
| 集成快照创建 | `backend/app/api/v1/endpoints/quotes.py` | 调用snapshot_service | ⏳ | 0.5h | - |

#### B2.2 实现回调处理端点 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建回调schemas | `backend/app/schemas.py` | WeComCallbackEvent模型 | ⏳ | 1h | - |
| 实现approval_callback端点 | `backend/app/api/v1/endpoints/wecom_callback.py` | 回调处理逻辑 | ⏳ | 2.5h | - |
| 实现幂等性处理 | `backend/app/api/v1/endpoints/wecom_callback.py` | 防重复处理 | ⏳ | 1.5h | - |
| 集成生效报价单创建 | `backend/app/api/v1/endpoints/wecom_callback.py` | approved状态处理 | ⏳ | 1h | - |

#### B2.3 实现辅助端点 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 实现export端点 | `backend/app/api/v1/endpoints/quotes.py` | 导出功能占位 | ⏳ | 2h | - |
| 实现deeplink端点 | `backend/app/api/v1/endpoints/quotes.py` | 生成访问链接 | ⏳ | 1h | - |
| 实现状态查询端点 | `backend/app/api/v1/endpoints/quotes.py` | 审批状态查询 | ⏳ | 1h | - |
| 添加OpenAPI文档 | 所有端点 | 完善接口文档注释 | ⏳ | 2h | - |

### B3: 生效报价单服务 (2天)

#### B3.1 实现EffectiveQuoteService (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建EffectiveQuoteService | `backend/app/services/effective_quote_service.py` | 基础服务类 | ⏳ | 0.5h | - |
| 实现create_effective_quote() | `backend/app/services/effective_quote_service.py` | 创建生效报价单 | ⏳ | 2.5h | - |
| 实现版本管理 | `backend/app/services/effective_quote_service.py` | 自动版本递增 | ⏳ | 1h | - |
| 集成导出服务 | `backend/app/services/effective_quote_service.py` | 调用export_service | ⏳ | 1h | - |
| 实现checksum计算 | `backend/app/services/effective_quote_service.py` | 数据完整性校验 | ⏳ | 1h | - |

#### B3.2 实现导出服务占位 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建ExportService | `backend/app/services/export_service.py` | 导出服务基础框架 | ⏳ | 1h | - |
| 实现PDF导出占位 | `backend/app/services/export_service.py` | 使用reportlab生成简单PDF | ⏳ | 3h | - |
| 实现Excel导出占位 | `backend/app/services/export_service.py` | 使用xlsxwriter生成Excel | ⏳ | 1.5h | - |
| 配置静态文件服务 | 配置文件 | 确保导出文件可下载 | ⏳ | 0.5h | - |

### 阶段B验收标准

**必须全部通过才能进入阶段C**:

- [ ] ✅ Postman: submit-approval端点返回deeplink_url
- [ ] ✅ mock_wecom_callback.sh脚本调用approved后，生成EffectiveQuote和导出URL  
- [ ] ✅ 回调处理具有幂等性，重复调用不产生重复副作用
- [ ] ✅ deeplink的JWT token可正确验证，过期token被拒绝
- [ ] ✅ 生效报价单包含版本号和导出文件URL

---

## 🎨 阶段C: 导出占位 + 前端改造 + 文档完善 (1.5周)

### C1: 前端组件改造 (3天)

#### C1.1 优化SubmitApprovalModal (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 显示模板信息 | `frontend/src/components/SubmitApprovalModal.js` | 显示将使用的审批模板 | ⏳ | 1.5h | - |
| 显示审批人预览 | `frontend/src/components/SubmitApprovalModal.js` | 根据规则显示拟定审批人 | ⏳ | 2h | - |
| 添加金额阈值提示 | `frontend/src/components/SubmitApprovalModal.js` | 显示金额对应的审批级别 | ⏳ | 1h | - |
| 优化提交后反馈 | `frontend/src/components/SubmitApprovalModal.js` | 显示企业微信deeplink | ⏳ | 1.5h | - |

#### C1.2 完善ApprovalHistory组件 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 实现时间轴显示 | `frontend/src/components/ApprovalHistory.js` | 使用AntD Timeline组件 | ⏳ | 2h | - |
| 添加状态图标 | `frontend/src/components/ApprovalHistory.js` | 不同状态显示不同图标 | ⏳ | 1h | - |
| 实现轮询刷新 | `frontend/src/components/ApprovalHistory.js` | 定期检查状态更新 | ⏳ | 2h | - |
| 添加详情展示 | `frontend/src/components/ApprovalHistory.js` | 展开显示详细信息 | ⏳ | 1h | - |

#### C1.3 改造QuoteDetail页面 (8小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 添加状态条显示 | `frontend/src/pages/QuoteDetail.js` | 顶部状态条 | ⏳ | 1.5h | - |
| 实现三个操作按钮 | `frontend/src/pages/QuoteDetail.js` | 提交审批/打开企业微信/下载导出 | ⏳ | 2h | - |
| 支持快照参数 | `frontend/src/pages/QuoteDetail.js` | 处理?snap=&t=参数 | ⏳ | 2h | - |
| 添加token验证 | `frontend/src/pages/QuoteDetail.js` | JWT token校验处理 | ⏳ | 1.5h | - |
| 集成ApprovalHistory | `frontend/src/pages/QuoteDetail.js` | 显示审批历史 | ⏳ | 1h | - |

#### C1.4 前端API服务层 (4小时)  
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 扩展approvalApi.js | `frontend/src/services/approvalApi.js` | 新增API方法封装 | ⏳ | 2h | - |
| 添加错误处理 | `frontend/src/services/approvalApi.js` | 统一错误处理和提示 | ⏳ | 1h | - |
| 添加loading状态管理 | `frontend/src/services/approvalApi.js` | API调用状态管理 | ⏳ | 1h | - |

### C2: 测试脚本和工具 (2天)

#### C2.1 创建测试脚本 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建dev_run.sh | `scripts/dev_run.sh` | 一键启动开发环境 | ⏳ | 1h | - |
| 创建mock回调脚本 | `scripts/mock_wecom_callback.sh` | 模拟企业微信回调 | ⏳ | 2h | - |
| 创建数据库重置脚本 | `scripts/reset_db.sh` | 重置测试数据 | ⏳ | 1h | - |
| 创建环境检查脚本 | `scripts/check_env.sh` | 验证环境配置 | ⏳ | 0.5h | - |
| 权限设置和测试 | 脚本权限 | 确保脚本可执行 | ⏳ | 0.5h | - |
| 脚本集成测试 | 端到端测试 | 验证脚本功能正常 | ⏳ | 1h | - |

#### C2.2 创建单元测试 (8小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 规则和快照测试 | `tests/test_rules_and_snapshot.py` | 规则选择、快照hash测试 | ⏳ | 2h | - |
| 提交和回调测试 | `tests/test_submit_and_callback.py` | 端到端审批流程测试 | ⏳ | 3h | - |  
| Deeplink测试 | `tests/test_deeplink.py` | JWT生成和验证测试 | ⏳ | 1.5h | - |
| 导出功能测试 | `tests/test_export.py` | 导出文件生成测试 | ⏳ | 1.5h | - |

#### C2.3 创建API测试集合 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |  
|------|------|------|------|------|------|
| 创建Postman集合 | `docs/postman_collection.json` | 完整API测试用例 | ⏳ | 2h | - |
| 添加环境变量配置 | `docs/postman_environment.json` | 测试环境配置 | ⏳ | 0.5h | - |
| 创建测试数据样本 | `docs/test_data/` | Mock数据和回调示例 | ⏳ | 1h | - |
| 测试用例文档 | `docs/api_testing_guide.md` | API测试使用说明 | ⏳ | 0.5h | - |

### C3: 文档和部署 (2天)

#### C3.1 创建集成文档 (6小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 创建主文档框架 | `docs/approval_integration.md` | 文档结构和目录 | ⏳ | 0.5h | - |
| 编写配置说明 | `docs/approval_integration.md` | 环境配置和规则配置 | ⏳ | 1.5h | - |
| 绘制架构图 | `docs/approval_integration.md` | ASCII/Mermaid架构图 | ⏳ | 1h | - |
| 编写时序图 | `docs/approval_integration.md` | 审批流程时序说明 | ⏳ | 1.5h | - |
| 编写故障排查指南 | `docs/approval_integration.md` | 常见问题和解决方案 | ⏳ | 1h | - |
| 创建回归用例清单 | `docs/approval_integration.md` | 验收测试清单 | ⏳ | 0.5h | - |

#### C3.2 运维支持文档 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 部署指南 | `docs/deployment_guide.md` | 生产环境部署说明 | ⏳ | 1.5h | - |
| 监控和告警 | `docs/monitoring_guide.md` | 系统监控要点 | ⏳ | 1h | - |
| 备份和恢复 | `docs/backup_recovery.md` | 数据备份策略 | ⏳ | 1h | - |
| 性能调优 | `docs/performance_tuning.md` | 性能优化建议 | ⏳ | 0.5h | - |

#### C3.3 用户使用文档 (4小时)
| 任务 | 文件 | 内容 | 状态 | 预计 | 实际 |
|------|------|------|------|------|------|
| 用户操作手册 | `docs/user_manual.md` | 前端操作流程说明 | ⏳ | 2h | - |
| 管理员手册 | `docs/admin_manual.md` | 审批规则配置说明 | ⏳ | 1.5h | - |
| FAQ文档 | `docs/faq.md` | 常见问题答疑 | ⏳ | 0.5h | - |

### 阶段C验收标准

**项目最终验收标准**:

- [ ] ✅ 前端完整展示状态、历史、导出下载，交互无明显报错
- [ ] ✅ 从企业微信消息deeplink可正确进入报价详情页
- [ ] ✅ SubmitApprovalModal显示模板和审批人信息
- [ ] ✅ ApprovalHistory组件显示时间轴并支持轮询刷新
- [ ] ✅ pytest测试全部通过，Mock回调脚本可正常运行
- [ ] ✅ Postman集合可导入并执行所有测试用例
- [ ] ✅ docs/approval_integration.md文档完整，包含配置、时序、故障排查
- [ ] ✅ 团队可按文档自助配置和回归测试

---

## 📊 项目跟踪表

### 整体进度概览

| 阶段 | 任务数 | 预计工时 | 已完成 | 进行中 | 待开始 | 完成率 | 状态 |
|------|-------|----------|-------|--------|--------|--------|------|
| 阶段A | 15 | 40h | 0 | 0 | 15 | 0% | ⏳ 待开始 |
| 阶段B | 18 | 60h | 0 | 0 | 18 | 0% | ⏳ 待开始 |  
| 阶段C | 22 | 50h | 0 | 0 | 22 | 0% | ⏳ 待开始 |
| **总计** | **55** | **150h** | **0** | **0** | **55** | **0%** | 🚀 **准备开始** |

### 里程碑时间表

| 里程碑 | 计划完成时间 | 实际完成时间 | 状态 | 关键交付物 |
|--------|--------------|--------------|------|-----------|
| 阶段A验收 | 2025-09-08 | - | ⏳ | 规则配置+数据模型+快照机制 |
| 阶段B验收 | 2025-09-18 | - | ⏳ | 审批流程+回调处理+生效报价单 |
| 阶段C验收 | 2025-09-30 | - | ⏳ | 前端改造+测试+文档 |
| 项目完成 | 2025-09-30 | - | ⏳ | 完整可用的企业微信审批系统 |

---

## 📝 使用说明

1. **开始工作前**：从阶段A的A1.1开始，按顺序执行每个任务
2. **完成任务后**：在对应表格中更新状态为✅，记录实际用时
3. **遇到问题时**：在状态列标记⚠️，并在备注中说明问题
4. **阶段完成后**：必须通过所有验收标准才能进入下一阶段
5. **项目跟踪**：定期更新进度概览表和里程碑状态

## 📚 代码模板参考

详细的实施代码模板请查看: `CODE_TEMPLATES_REFERENCE.md`

该文件包含了所有关键任务的完整代码示例：
- 配置文件和规则加载器
- 数据模型定义  
- 服务层实现
- API端点实现
- 前端组件代码
- 测试脚本模板

在执行具体任务时，可直接参考对应的代码模板进行实施。

**下一步行动**：等待确认后，从阶段A.1.1"补齐.env配置项"开始执行。