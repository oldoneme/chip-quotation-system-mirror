# 最佳实践指南：实战经验总结

## 前言

本文档收集了在实际项目中验证有效的最佳实践。每个实践都包含具体的代码示例、使用场景和注意事项。这些不是教条，而是经过实战检验的经验总结。

## 目录
1. [代码组织最佳实践](#代码组织最佳实践)
2. [测试最佳实践](#测试最佳实践)
3. [性能优化最佳实践](#性能优化最佳实践)
4. [安全最佳实践](#安全最佳实践)
5. [团队协作最佳实践](#团队协作最佳实践)
6. [AI 辅助开发最佳实践](#ai-辅助开发最佳实践)
7. [故障处理最佳实践](#故障处理最佳实践)
8. [文档编写最佳实践](#文档编写最佳实践)

---

## 代码组织最佳实践

### 1. 模块化设计

#### ✅ 好的实践：高内聚、低耦合
```javascript
// user/user.service.js
class UserService {
  constructor(userRepository, emailService) {
    this.userRepository = userRepository;
    this.emailService = emailService;
  }
  
  async createUser(userData) {
    // 单一职责：只负责用户创建逻辑
    const user = await this.userRepository.create(userData);
    await this.emailService.sendWelcome(user);
    return user;
  }
}

// user/user.repository.js
class UserRepository {
  async create(userData) {
    // 单一职责：只负责数据持久化
    return await db.users.insert(userData);
  }
}

// email/email.service.js
class EmailService {
  async sendWelcome(user) {
    // 单一职责：只负责邮件发送
    return await this.send(user.email, 'welcome', { user });
  }
}
```

#### ❌ 错误的实践：职责混乱
```javascript
// 不要这样做：所有逻辑混在一起
class UserManager {
  async createUser(userData) {
    // 验证逻辑
    if (!userData.email.includes('@')) {
      throw new Error('Invalid email');
    }
    
    // 数据库操作
    const user = await db.query('INSERT INTO users...');
    
    // 邮件发送
    await smtp.send({
      to: user.email,
      subject: 'Welcome',
      body: `<h1>Welcome ${user.name}</h1>`
    });
    
    // 日志记录
    console.log('User created:', user);
    
    return user;
  }
}
```

### 2. 文件和目录结构

#### 推荐的项目结构
```
src/
├── modules/           # 业务模块
│   ├── user/
│   │   ├── user.controller.js
│   │   ├── user.service.js
│   │   ├── user.repository.js
│   │   ├── user.validator.js
│   │   ├── user.types.js
│   │   └── user.test.js
│   └── product/
│       └── ...
├── shared/           # 共享组件
│   ├── utils/
│   ├── constants/
│   └── types/
├── infrastructure/   # 基础设施
│   ├── database/
│   ├── cache/
│   └── messaging/
└── config/          # 配置
    ├── default.js
    ├── development.js
    └── production.js
```

### 3. 命名规范

#### 文件命名
```javascript
// ✅ 好的命名
user.service.js         // 服务类
user.controller.js      // 控制器
user.repository.js      // 数据访问
user.validator.js       // 验证器
user.types.ts          // 类型定义
user.test.js           // 测试文件
user.mock.js           // 模拟数据

// ❌ 不好的命名
userSvc.js            // 缩写不清晰
UserController.js     // 不一致的大小写
test.js              // 太通用
misc.js              // 不明确的用途
```

#### 变量和函数命名
```javascript
// ✅ 好的命名实践
const MAX_RETRY_COUNT = 3;              // 常量：大写蛇形
const userEmail = 'user@example.com';   // 变量：小驼峰
const getUserById = (id) => {};         // 函数：动词开头
class UserService {}                     // 类：大驼峰

// 布尔值命名
const isActive = true;
const hasPermission = false;
const canEdit = true;

// 数组命名使用复数
const users = [];
const products = [];

// ❌ 不好的命名
const max = 3;              // 太简短
const e = 'email';          // 单字母变量
const getData = () => {};   // 太通用
const flag = true;          // 不明确的布尔值
```

## 测试最佳实践

### 1. 测试结构 - AAA 模式

```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a user with valid data', async () => {
      // Arrange - 准备测试数据和环境
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      const mockRepository = {
        create: jest.fn().mockResolvedValue({ id: 1, ...userData })
      };
      const service = new UserService(mockRepository);
      
      // Act - 执行被测试的动作
      const result = await service.createUser(userData);
      
      // Assert - 验证结果
      expect(result).toHaveProperty('id');
      expect(result.email).toBe(userData.email);
      expect(mockRepository.create).toHaveBeenCalledWith(userData);
    });
  });
});
```

### 2. 测试隔离

```javascript
// ✅ 好的实践：每个测试独立
describe('ShoppingCart', () => {
  let cart;
  
  beforeEach(() => {
    // 每个测试前重置状态
    cart = new ShoppingCart();
  });
  
  afterEach(() => {
    // 清理资源
    jest.clearAllMocks();
  });
  
  it('should add item to cart', () => {
    cart.addItem({ id: 1, price: 10 });
    expect(cart.getTotal()).toBe(10);
  });
  
  it('should calculate total correctly', () => {
    cart.addItem({ id: 1, price: 10 });
    cart.addItem({ id: 2, price: 20 });
    expect(cart.getTotal()).toBe(30);
  });
});

// ❌ 错误的实践：测试相互依赖
describe('ShoppingCart', () => {
  const cart = new ShoppingCart(); // 共享状态
  
  it('should add item', () => {
    cart.addItem({ id: 1, price: 10 });
    expect(cart.items.length).toBe(1);
  });
  
  it('should have two items', () => {
    // 依赖上一个测试的状态
    cart.addItem({ id: 2, price: 20 });
    expect(cart.items.length).toBe(2); // 脆弱的测试
  });
});
```

### 3. 测试数据构建器

```javascript
// 测试数据构建器模式
class UserBuilder {
  constructor() {
    this.user = {
      id: Math.random(),
      email: 'default@test.com',
      name: 'Default User',
      age: 25,
      isActive: true
    };
  }
  
  withEmail(email) {
    this.user.email = email;
    return this;
  }
  
  withAge(age) {
    this.user.age = age;
    return this;
  }
  
  inactive() {
    this.user.isActive = false;
    return this;
  }
  
  build() {
    return { ...this.user };
  }
}

// 使用构建器创建测试数据
it('should handle inactive users', () => {
  const inactiveUser = new UserBuilder()
    .withEmail('inactive@test.com')
    .inactive()
    .build();
    
  expect(canLogin(inactiveUser)).toBe(false);
});
```

## 性能优化最佳实践

### 1. 避免 N+1 查询问题

```javascript
// ❌ 错误：N+1 查询
async function getUsersWithPosts() {
  const users = await db.query('SELECT * FROM users');
  
  for (const user of users) {
    // 每个用户一次查询 = N 次额外查询
    user.posts = await db.query(
      'SELECT * FROM posts WHERE user_id = ?',
      [user.id]
    );
  }
  
  return users;
}

// ✅ 正确：使用 JOIN 或批量查询
async function getUsersWithPosts() {
  const users = await db.query('SELECT * FROM users');
  const userIds = users.map(u => u.id);
  
  // 一次查询获取所有帖子
  const posts = await db.query(
    'SELECT * FROM posts WHERE user_id IN (?)',
    [userIds]
  );
  
  // 在内存中关联数据
  const postsByUser = posts.reduce((acc, post) => {
    if (!acc[post.user_id]) acc[post.user_id] = [];
    acc[post.user_id].push(post);
    return acc;
  }, {});
  
  users.forEach(user => {
    user.posts = postsByUser[user.id] || [];
  });
  
  return users;
}
```

### 2. 缓存策略

```javascript
// 实现一个简单的缓存装饰器
function cache(ttl = 60000) { // 默认 60 秒
  const cache = new Map();
  
  return function(target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function(...args) {
      const key = `${propertyKey}:${JSON.stringify(args)}`;
      const cached = cache.get(key);
      
      if (cached && Date.now() - cached.timestamp < ttl) {
        console.log(`Cache hit: ${key}`);
        return cached.value;
      }
      
      console.log(`Cache miss: ${key}`);
      const result = await originalMethod.apply(this, args);
      
      cache.set(key, {
        value: result,
        timestamp: Date.now()
      });
      
      return result;
    };
    
    return descriptor;
  };
}

// 使用缓存装饰器
class UserService {
  @cache(5000) // 缓存 5 秒
  async getUser(id) {
    console.log(`Fetching user ${id} from database`);
    return await db.users.findById(id);
  }
}
```

### 3. 防抖和节流

```javascript
// 防抖：在停止触发后执行
function debounce(func, wait) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 节流：固定时间间隔执行
function throttle(func, limit) {
  let inThrottle;
  
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// 实际应用
const searchInput = document.getElementById('search');

// 搜索防抖：用户停止输入 500ms 后搜索
searchInput.addEventListener('input', 
  debounce((e) => {
    performSearch(e.target.value);
  }, 500)
);

// 滚动节流：每 200ms 最多执行一次
window.addEventListener('scroll',
  throttle(() => {
    updateScrollPosition();
  }, 200)
);
```

## 安全最佳实践

### 1. 输入验证和清理

```javascript
// 使用验证库（如 Joi）进行输入验证
const Joi = require('joi');

const userSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/).required(),
  age: Joi.number().integer().min(13).max(120),
  username: Joi.string().alphanum().min(3).max(30).required()
});

async function createUser(req, res) {
  try {
    // 验证输入
    const { error, value } = userSchema.validate(req.body);
    
    if (error) {
      return res.status(400).json({
        error: 'Validation failed',
        details: error.details.map(d => d.message)
      });
    }
    
    // 使用验证后的值，而不是原始输入
    const user = await userService.create(value);
    res.json(user);
    
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
}
```

### 2. SQL 注入防护

```javascript
// ❌ 危险：SQL 注入漏洞
async function getUser(req, res) {
  const userId = req.params.id;
  // 永远不要这样做！
  const user = await db.query(
    `SELECT * FROM users WHERE id = ${userId}`
  );
  res.json(user);
}

// ✅ 安全：使用参数化查询
async function getUser(req, res) {
  const userId = req.params.id;
  
  // 参数化查询防止 SQL 注入
  const user = await db.query(
    'SELECT * FROM users WHERE id = ?',
    [userId]
  );
  
  res.json(user);
}

// ✅ 使用 ORM 的安全方法
async function getUser(req, res) {
  const user = await User.findOne({
    where: { id: req.params.id }
  });
  
  res.json(user);
}
```

### 3. 密码安全

```javascript
const bcrypt = require('bcrypt');
const crypto = require('crypto');

class AuthService {
  // 密码哈希
  async hashPassword(password) {
    const saltRounds = 10;
    return await bcrypt.hash(password, saltRounds);
  }
  
  // 密码验证
  async verifyPassword(password, hash) {
    return await bcrypt.compare(password, hash);
  }
  
  // 生成安全的随机 Token
  generateSecureToken() {
    return crypto.randomBytes(32).toString('hex');
  }
  
  // JWT Token 生成
  generateJWT(userId) {
    return jwt.sign(
      { userId },
      process.env.JWT_SECRET,
      { 
        expiresIn: '24h',
        issuer: 'myapp',
        audience: 'myapp-users'
      }
    );
  }
}

// ❌ 永远不要这样存储密码
// const password = 'plaintext'; // 绝对不行！
// const password = md5('password'); // MD5 已被破解
// const password = sha1('password'); // SHA1 不适合密码
```

## 团队协作最佳实践

### 1. Git 提交规范

```bash
# 好的提交信息格式
<type>(<scope>): <subject>

<body>

<footer>

# 示例
feat(user): add password reset functionality

- Implement forgot password API endpoint
- Add email template for password reset
- Include token expiration logic

Closes #123
```

#### 提交类型
```
feat:     新功能
fix:      修复 bug
docs:     文档修改
style:    代码格式修改（不影响功能）
refactor: 重构（不是新功能也不是修复）
perf:     性能优化
test:     测试相关
chore:    构建过程或辅助工具的变动
```

### 2. 代码审查清单

```markdown
## 代码审查要点

### 功能性
- [ ] 代码是否实现了预期功能？
- [ ] 边界条件处理了吗？
- [ ] 错误处理完善吗？

### 可维护性
- [ ] 代码是否易于理解？
- [ ] 是否有适当的注释？
- [ ] 命名是否清晰？

### 性能
- [ ] 是否有明显的性能问题？
- [ ] 数据库查询是否优化？
- [ ] 是否有内存泄漏风险？

### 安全性
- [ ] 输入是否经过验证？
- [ ] 是否有 SQL 注入风险？
- [ ] 敏感信息是否得到保护？

### 测试
- [ ] 是否有对应的测试？
- [ ] 测试覆盖率是否足够？
- [ ] 测试是否可靠？
```

### 3. 分支管理策略

```bash
# Git Flow 分支模型
main/master     # 生产环境代码
├── develop     # 开发主分支
│   ├── feature/user-auth    # 功能分支
│   ├── feature/payment      # 功能分支
│   └── feature/search       # 功能分支
├── release/1.2.0            # 发布分支
└── hotfix/critical-bug      # 紧急修复分支

# 分支命名规范
feature/issue-123-user-authentication
bugfix/issue-456-login-error
hotfix/critical-security-patch
release/v1.2.0
```

## AI 辅助开发最佳实践

### 1. 提示工程技巧

```markdown
# 有效的 AI 提示模板

## 任务
[明确描述要完成的任务]

## 上下文
- 使用的技术栈：[Node.js, Express, PostgreSQL]
- 项目类型：[REST API]
- 约束条件：[性能要求、安全要求]

## 要求
1. [具体要求1]
2. [具体要求2]
3. [具体要求3]

## 示例
输入：[示例输入]
输出：[期望的输出]

## 注意事项
- [特别需要注意的点]
- [要避免的问题]
```

### 2. AI 代码审查流程

```javascript
// 1. 让 AI 生成初始代码
// Prompt: "创建一个用户认证服务，包含注册、登录和 Token 刷新功能"

// 2. 人工审查和调整
// - 检查业务逻辑正确性
// - 验证安全性
// - 确保符合项目规范

// 3. 让 AI 优化代码
// Prompt: "优化这段代码的性能，特别是数据库查询部分"

// 4. 让 AI 生成测试
// Prompt: "为这个服务生成完整的单元测试，覆盖所有边界条件"

// 5. 最终人工验证
// - 运行测试
// - 代码审查
// - 集成测试
```

### 3. AI 辅助调试

```javascript
// 调试问题时的提示模板
const debugPrompt = `
我遇到了以下错误：
${errorMessage}

代码片段：
${codeSnippet}

环境信息：
- Node.js 版本：${process.version}
- 相关依赖：${dependencies}

这个错误出现在：${context}

请帮我：
1. 解释错误原因
2. 提供修复方案
3. 说明如何避免类似问题
`;
```

## 故障处理最佳实践

### 1. 错误处理模式

```javascript
// 集中式错误处理
class AppError extends Error {
  constructor(message, statusCode, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    Error.captureStackTrace(this, this.constructor);
  }
}

// 全局错误处理中间件
function errorHandler(err, req, res, next) {
  let { statusCode, message } = err;
  
  // 默认值
  statusCode = statusCode || 500;
  message = message || 'Internal Server Error';
  
  // 记录错误
  logger.error({
    error: err,
    request: req.url,
    method: req.method,
    ip: req.ip
  });
  
  // 开发环境返回详细错误
  if (process.env.NODE_ENV === 'development') {
    res.status(statusCode).json({
      status: 'error',
      message,
      stack: err.stack
    });
  } else {
    // 生产环境只返回必要信息
    res.status(statusCode).json({
      status: 'error',
      message: err.isOperational ? message : 'Something went wrong'
    });
  }
}

// 使用示例
router.post('/user', async (req, res, next) => {
  try {
    if (!req.body.email) {
      throw new AppError('Email is required', 400);
    }
    
    const user = await userService.create(req.body);
    res.json(user);
  } catch (error) {
    next(error);
  }
});
```

### 2. 优雅降级

```javascript
// 实现断路器模式
class CircuitBreaker {
  constructor(request, options = {}) {
    this.request = request;
    this.state = 'CLOSED';
    this.failureCount = 0;
    this.successCount = 0;
    this.failureThreshold = options.failureThreshold || 5;
    this.successThreshold = options.successThreshold || 2;
    this.timeout = options.timeout || 60000;
    this.nextAttempt = Date.now();
  }
  
  async call(...args) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }
    
    try {
      const result = await this.request(...args);
      return this.onSuccess(result);
    } catch (err) {
      return this.onFailure(err);
    }
  }
  
  onSuccess(result) {
    this.failureCount = 0;
    
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= this.successThreshold) {
        this.state = 'CLOSED';
        this.successCount = 0;
      }
    }
    
    return result;
  }
  
  onFailure(err) {
    this.failureCount++;
    
    if (this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
    }
    
    throw err;
  }
}

// 使用断路器
const dbBreaker = new CircuitBreaker(
  async (query) => await database.query(query),
  { failureThreshold: 3, timeout: 30000 }
);

// 带有降级的服务调用
async function getUserData(userId) {
  try {
    // 尝试从主数据库获取
    return await dbBreaker.call('SELECT * FROM users WHERE id = ?', [userId]);
  } catch (err) {
    logger.warn('Primary database failed, falling back to cache');
    
    // 降级到缓存
    const cached = await cache.get(`user:${userId}`);
    if (cached) {
      return cached;
    }
    
    // 最后的降级：返回基本信息
    return {
      id: userId,
      status: 'limited',
      message: 'Service temporarily unavailable'
    };
  }
}
```

### 3. 监控和告警

```javascript
// 实现健康检查端点
router.get('/health', async (req, res) => {
  const health = {
    uptime: process.uptime(),
    timestamp: Date.now(),
    status: 'OK',
    checks: []
  };
  
  // 检查数据库连接
  try {
    await db.query('SELECT 1');
    health.checks.push({ name: 'database', status: 'OK' });
  } catch (err) {
    health.status = 'ERROR';
    health.checks.push({ 
      name: 'database', 
      status: 'ERROR',
      error: err.message 
    });
  }
  
  // 检查 Redis 连接
  try {
    await redis.ping();
    health.checks.push({ name: 'redis', status: 'OK' });
  } catch (err) {
    health.status = 'WARNING';
    health.checks.push({ 
      name: 'redis', 
      status: 'ERROR',
      error: err.message 
    });
  }
  
  // 检查内存使用
  const memUsage = process.memoryUsage();
  health.memory = {
    heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)} MB`,
    heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)} MB`
  };
  
  const statusCode = health.status === 'OK' ? 200 : 503;
  res.status(statusCode).json(health);
});
```

## 文档编写最佳实践

### 1. README 模板

```markdown
# 项目名称

简短的项目描述，说明项目的目的和主要功能。

## 特性

- ✨ 特性 1
- 🚀 特性 2
- 🔒 特性 3

## 快速开始

### 前置要求

- Node.js >= 14.0
- PostgreSQL >= 12
- Redis >= 6.0

### 安装

​```bash
# 克隆仓库
git clone https://github.com/username/project.git

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
npm run migrate

# 启动开发服务器
npm run dev
​```

## 使用方法

​```javascript
const api = require('project-name');

// 示例代码
api.doSomething();
​```

## API 文档

详细的 API 文档请参见 [API.md](./docs/API.md)

## 贡献指南

请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何贡献代码。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](./LICENSE) 文件
```

### 2. 代码注释规范

```javascript
/**
 * 计算两个日期之间的天数差
 * @param {Date} startDate - 开始日期
 * @param {Date} endDate - 结束日期
 * @returns {number} 天数差，如果结束日期早于开始日期返回负数
 * @throws {TypeError} 如果参数不是有效的日期对象
 * @example
 * const days = daysBetween(new Date('2024-01-01'), new Date('2024-01-10'));
 * console.log(days); // 9
 */
function daysBetween(startDate, endDate) {
  if (!(startDate instanceof Date) || !(endDate instanceof Date)) {
    throw new TypeError('Both arguments must be Date objects');
  }
  
  const oneDay = 24 * 60 * 60 * 1000;
  return Math.round((endDate - startDate) / oneDay);
}

// 复杂逻辑的行内注释
function processOrder(order) {
  // 验证订单状态
  if (order.status !== 'pending') {
    return { error: 'Invalid order status' };
  }
  
  // 计算折扣
  // 注意：VIP 用户享受额外 10% 折扣
  const discount = order.user.isVIP ? 0.1 : 0;
  const finalPrice = order.total * (1 - discount);
  
  // 处理支付
  // TODO: 添加支付失败的重试逻辑
  const payment = processPayment(finalPrice);
  
  return { success: true, payment };
}
```

### 3. API 文档示例

```markdown
## API 端点

### 创建用户

创建一个新的用户账号。

**端点**

`POST /api/users`

**请求头**

| 名称 | 必需 | 描述 |
|------|------|------|
| Content-Type | 是 | application/json |
| Authorization | 否 | Bearer token（管理员创建用户时需要）|

**请求体**

​```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "role": "user"
}
​```

**参数说明**

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| email | string | 是 | 用户邮箱，必须唯一 |
| password | string | 是 | 密码，至少8位，包含大小写字母和数字 |
| name | string | 是 | 用户姓名 |
| role | string | 否 | 用户角色，默认为 "user" |

**响应**

成功 (201 Created)
​```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "createdAt": "2024-01-15T08:30:00Z"
}
​```

错误 (400 Bad Request)
​```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "email",
      "message": "Email already exists"
    }
  ]
}
​```

**示例调用**

​```bash
curl -X POST https://api.example.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePassword123!","name":"John Doe"}'
​```
```

## 总结

这些最佳实践不是死板的规则，而是经过验证的指导原则。关键是：

1. **理解原理**：知道为什么要这样做
2. **灵活应用**：根据实际情况调整
3. **持续改进**：从实践中学习和优化
4. **团队共识**：确保团队成员理解和认同
5. **文档化**：记录决策和经验教训

记住：最佳实践是起点，不是终点。持续学习、实践和改进才是通向卓越的道路。