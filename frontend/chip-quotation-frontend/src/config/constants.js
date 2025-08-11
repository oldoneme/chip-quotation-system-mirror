/**
 * 应用常量配置
 */

// API配置
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
export const API_TIMEOUT = 30000; // 30秒

// 业务配置
export const PERSONNEL_RATES = {
  ENGINEER: 350,
  TECHNICIAN: 200
};

export const DEFAULT_VALUES = {
  ENGINEERING_RATE: 1.2,
  EXCHANGE_RATE_USD: 7.0,
  MIN_DISCOUNT_RATE: 0.1,
  MAX_DISCOUNT_RATE: 2.0
};

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100]
};

// 缓存配置
export const CACHE = {
  TTL: 5 * 60 * 1000, // 5分钟
  STALE_TIME: 3 * 60 * 1000 // 3分钟
};

// 表单验证规则
export const VALIDATION_RULES = {
  MACHINE_NAME: {
    MIN_LENGTH: 2,
    MAX_LENGTH: 100
  },
  SUPPLIER_NAME: {
    MIN_LENGTH: 2,
    MAX_LENGTH: 100
  },
  DESCRIPTION: {
    MAX_LENGTH: 500
  },
  PART_NUMBER: {
    MAX_LENGTH: 50
  },
  BOARD_NAME: {
    MAX_LENGTH: 100
  },
  TEST_HOURS: {
    MIN: 0.1,
    MAX: 10000
  },
  QUANTITY: {
    MIN: 1,
    MAX: 1000000
  }
};

// 货币类型
export const CURRENCIES = [
  { value: 'RMB', label: '人民币 (¥)', symbol: '¥' },
  { value: 'USD', label: '美元 ($)', symbol: '$' }
];

// 机器类型
export const MACHINE_TYPES = {
  TEST_MACHINE: '测试机',
  HANDLER: '分选机',
  PROBER: '探针台'
};

// 测试类型
export const TEST_TYPES = {
  FT: { value: 'ft', label: 'FT (Final Test)', description: '最终测试' },
  CP: { value: 'cp', label: 'CP (Circuit Probe)', description: '电路探测' }
};

// 消息提示
export const MESSAGES = {
  SUCCESS: {
    CREATE: '创建成功',
    UPDATE: '更新成功',
    DELETE: '删除成功',
    SAVE: '保存成功',
    SUBMIT: '提交成功',
    RESET: '重置成功'
  },
  ERROR: {
    NETWORK: '网络连接失败，请检查网络设置',
    SERVER: '服务器错误，请稍后重试',
    VALIDATION: '数据验证失败，请检查输入',
    NOT_FOUND: '请求的资源未找到',
    PERMISSION: '权限不足',
    UNKNOWN: '发生未知错误'
  },
  CONFIRM: {
    DELETE: '确定要删除吗？此操作不可恢复。',
    RESET: '确定要重置吗？所有未保存的数据将丢失。',
    EXIT: '确定要退出吗？未保存的更改将丢失。'
  }
};

// 键盘快捷键
export const KEYBOARD_SHORTCUTS = {
  SAVE: 'ctrl+s',
  NEW: 'ctrl+n',
  DELETE: 'ctrl+d',
  SEARCH: 'ctrl+f',
  HELP: 'f1',
  ESC: 'escape'
};

// 颜色主题
export const THEME = {
  PRIMARY_COLOR: '#1890ff',
  SUCCESS_COLOR: '#52c41a',
  WARNING_COLOR: '#faad14',
  ERROR_COLOR: '#f5222d',
  INFO_COLOR: '#1890ff',
  BACKGROUND_COLOR: '#f0f2f5',
  BORDER_COLOR: '#d9d9d9'
};

// 导出格式
export const EXPORT_FORMATS = {
  PDF: 'pdf',
  EXCEL: 'excel',
  CSV: 'csv'
};

// 状态映射
export const STATUS_MAP = {
  ACTIVE: { value: true, label: '激活', color: 'success' },
  INACTIVE: { value: false, label: '未激活', color: 'default' },
  DRAFT: { value: 'draft', label: '草稿', color: 'default' },
  SUBMITTED: { value: 'submitted', label: '已提交', color: 'processing' },
  APPROVED: { value: 'approved', label: '已批准', color: 'success' },
  REJECTED: { value: 'rejected', label: '已拒绝', color: 'error' }
};