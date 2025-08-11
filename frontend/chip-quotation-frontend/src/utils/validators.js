/**
 * 前端数据验证工具
 */
import { VALIDATION_RULES, DEFAULT_VALUES } from '../config/constants';

/**
 * 机器数据验证器
 */
export const MachineValidator = {
  /**
   * 验证机器名称
   */
  validateName: (value) => {
    if (!value || value.trim().length < VALIDATION_RULES.MACHINE_NAME.MIN_LENGTH) {
      return `机器名称至少需要${VALIDATION_RULES.MACHINE_NAME.MIN_LENGTH}个字符`;
    }
    if (value.trim().length > VALIDATION_RULES.MACHINE_NAME.MAX_LENGTH) {
      return `机器名称不能超过${VALIDATION_RULES.MACHINE_NAME.MAX_LENGTH}个字符`;
    }
    return null;
  },

  /**
   * 验证折扣率
   */
  validateDiscountRate: (value) => {
    if (value === null || value === undefined) {
      return null; // 允许空值，使用默认值
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
      return '折扣率必须是数字';
    }
    if (num < DEFAULT_VALUES.MIN_DISCOUNT_RATE || num > DEFAULT_VALUES.MAX_DISCOUNT_RATE) {
      return `折扣率必须在${DEFAULT_VALUES.MIN_DISCOUNT_RATE}到${DEFAULT_VALUES.MAX_DISCOUNT_RATE}之间`;
    }
    return null;
  },

  /**
   * 验证汇率
   */
  validateExchangeRate: (value, currency) => {
    if (currency === 'RMB') {
      return null; // 人民币不需要汇率
    }
    const num = parseFloat(value);
    if (isNaN(num) || num <= 0) {
      return '汇率必须大于0';
    }
    if (num > 100) {
      return '汇率值异常，请检查';
    }
    return null;
  },

  /**
   * 验证货币类型
   */
  validateCurrency: (value) => {
    const validCurrencies = ['RMB', 'USD'];
    if (!validCurrencies.includes(value)) {
      return '无效的货币类型';
    }
    return null;
  }
};

/**
 * 供应商数据验证器
 */
export const SupplierValidator = {
  /**
   * 验证供应商名称
   */
  validateName: (value) => {
    if (!value || value.trim().length < VALIDATION_RULES.SUPPLIER_NAME.MIN_LENGTH) {
      return `供应商名称至少需要${VALIDATION_RULES.SUPPLIER_NAME.MIN_LENGTH}个字符`;
    }
    if (value.trim().length > VALIDATION_RULES.SUPPLIER_NAME.MAX_LENGTH) {
      return `供应商名称不能超过${VALIDATION_RULES.SUPPLIER_NAME.MAX_LENGTH}个字符`;
    }
    return null;
  }
};

/**
 * 板卡配置验证器
 */
export const CardConfigValidator = {
  /**
   * 验证Part Number
   */
  validatePartNumber: (value) => {
    if (value && value.length > VALIDATION_RULES.PART_NUMBER.MAX_LENGTH) {
      return `Part Number不能超过${VALIDATION_RULES.PART_NUMBER.MAX_LENGTH}个字符`;
    }
    return null;
  },

  /**
   * 验证板卡名称
   */
  validateBoardName: (value) => {
    if (value && value.length > VALIDATION_RULES.BOARD_NAME.MAX_LENGTH) {
      return `板卡名称不能超过${VALIDATION_RULES.BOARD_NAME.MAX_LENGTH}个字符`;
    }
    return null;
  },

  /**
   * 验证单价
   */
  validateUnitPrice: (value) => {
    const num = parseFloat(value);
    if (isNaN(num)) {
      return '单价必须是数字';
    }
    if (num < 0) {
      return '单价不能为负数';
    }
    if (num > 10000000) {
      return '单价超出合理范围';
    }
    return null;
  }
};

/**
 * 报价验证器
 */
export const QuotationValidator = {
  /**
   * 验证测试小时数
   */
  validateTestHours: (value) => {
    const num = parseFloat(value);
    if (isNaN(num) || num <= 0) {
      return '测试小时数必须大于0';
    }
    if (num < VALIDATION_RULES.TEST_HOURS.MIN) {
      return `测试小时数不能少于${VALIDATION_RULES.TEST_HOURS.MIN}小时`;
    }
    if (num > VALIDATION_RULES.TEST_HOURS.MAX) {
      return `测试小时数不能超过${VALIDATION_RULES.TEST_HOURS.MAX}小时`;
    }
    return null;
  },

  /**
   * 验证数量
   */
  validateQuantity: (value) => {
    const num = parseInt(value);
    if (isNaN(num) || num <= 0) {
      return '数量必须是正整数';
    }
    if (num < VALIDATION_RULES.QUANTITY.MIN) {
      return `数量不能少于${VALIDATION_RULES.QUANTITY.MIN}`;
    }
    if (num > VALIDATION_RULES.QUANTITY.MAX) {
      return `数量不能超过${VALIDATION_RULES.QUANTITY.MAX}`;
    }
    return null;
  },

  /**
   * 验证工程系数
   */
  validateEngineeringRate: (value) => {
    const num = parseFloat(value);
    if (isNaN(num) || num <= 0) {
      return '工程系数必须大于0';
    }
    if (num > 10) {
      return '工程系数超出合理范围';
    }
    return null;
  }
};

/**
 * 表单验证工具
 */
export const FormValidator = {
  /**
   * 验证必填字段
   */
  required: (value, fieldName = '该字段') => {
    if (value === null || value === undefined || value === '' || 
        (typeof value === 'string' && value.trim() === '')) {
      return `${fieldName}不能为空`;
    }
    return null;
  },

  /**
   * 验证邮箱
   */
  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return '请输入有效的邮箱地址';
    }
    return null;
  },

  /**
   * 验证手机号
   */
  phone: (value) => {
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(value)) {
      return '请输入有效的手机号码';
    }
    return null;
  },

  /**
   * 验证密码强度
   */
  password: (value) => {
    if (value.length < 8) {
      return '密码至少需要8个字符';
    }
    if (!/[A-Z]/.test(value)) {
      return '密码需要包含至少一个大写字母';
    }
    if (!/[a-z]/.test(value)) {
      return '密码需要包含至少一个小写字母';
    }
    if (!/[0-9]/.test(value)) {
      return '密码需要包含至少一个数字';
    }
    return null;
  },

  /**
   * 批量验证
   */
  validateForm: (formData, rules) => {
    const errors = {};
    let hasError = false;

    Object.keys(rules).forEach(field => {
      const fieldRules = rules[field];
      const value = formData[field];
      
      for (const rule of fieldRules) {
        const error = rule(value);
        if (error) {
          errors[field] = error;
          hasError = true;
          break;
        }
      }
    });

    return { errors, hasError };
  }
};

/**
 * 创建自定义验证规则
 */
export const createValidator = (validationFn, errorMessage) => {
  return (value) => {
    if (!validationFn(value)) {
      return errorMessage;
    }
    return null;
  };
};

/**
 * 组合多个验证规则
 */
export const composeValidators = (...validators) => {
  return (value) => {
    for (const validator of validators) {
      const error = validator(value);
      if (error) {
        return error;
      }
    }
    return null;
  };
};