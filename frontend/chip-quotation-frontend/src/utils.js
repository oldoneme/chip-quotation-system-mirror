/**
 * 格式化数字，添加千位分隔符并保留两位小数
 * @param {number} num - 需要格式化的数字
 * @returns {string} 格式化后的字符串，例如: 1,234.56
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0.00';
  return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/**
 * 格式化货币金额，添加千位分隔符、货币符号并保留两位小数
 * @param {number} amount - 需要格式化的金额
 * @param {string} currency - 货币符号，默认为¥
 * @returns {string} 格式化后的货币字符串，例如: ¥1,234.56
 */
export const formatCurrency = (amount, currency = '¥') => {
  return `${currency}${formatNumber(amount)}`;
};

/**
 * 格式化机时价格，精确到个位（无小数位）- 最终取整
 * @param {number} num - 需要格式化的数字
 * @returns {string} 格式化后的字符串，例如: 1,234
 */
export const formatHourlyRate = (num) => {
  if (num === null || num === undefined) return '0';
  return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/**
 * 格式化机时价格显示，保留两位小数 - 中间计算用
 * @param {number} num - 需要格式化的数字
 * @returns {string} 格式化后的字符串，例如: ¥1,234.56
 */
export const formatHourlyPrice = (num) => {
  if (num === null || num === undefined) return '¥0.00';
  return `¥${num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
};

/**
 * 根据货币类型进行向上取整的价格格式化
 * CNY: 向上取整到个位
 * USD: 向上取整到百分位（只有当千分位及以下存在时才向上取整）
 * @param {number} num - 需要格式化的数字
 * @param {string} currency - 货币类型 'CNY' 或 'USD'
 * @returns {number} 向上取整后的数字
 */
export const ceilByCurrency = (num, currency) => {
  if (num === null || num === undefined) return 0;
  
  if (currency === 'USD') {
    // USD: 检查是否有千分位及以下的数值
    const rounded = Math.round(num * 100) / 100;  // 四舍五入到百分位
    const hasDecimalsBelow = Math.abs(num - rounded) > 0.000001; // 检查是否有千分位以下的数值
    
    if (hasDecimalsBelow) {
      // 有千分位及以下数值时才向上取整到百分位
      return Math.ceil(num * 100) / 100;
    } else {
      // 无千分位及以下数值时保持原值（精确到百分位）
      return rounded;
    }
  } else {
    // CNY: 向上取整到个位
    return Math.ceil(num);
  }
};

/**
 * 格式化中间价格
 * CNY: 显示两位小数（四舍五入）
 * USD: 显示两位小数（向上取整到百分位）
 * @param {number} num - 需要格式化的数字
 * @param {string} currency - 货币类型 'CNY' 或 'USD'
 * @returns {string} 格式化后的字符串
 */
export const formatIntermediatePrice = (num, currency) => {
  if (num === null || num === undefined || isNaN(num)) return '0.00';

  let displayNum;
  if (currency === 'USD') {
    // 美元：向上取整到百分位
    displayNum = Math.ceil(num * 100) / 100;
  } else {
    // 人民币：四舍五入到百分位
    displayNum = Math.round(num * 100) / 100;
  }

  return displayNum.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/**
 * 根据货币类型格式化报价价格（向上取整）
 * CNY: 向上取整到个位，无小数位
 * USD: 向上取整到百分位，两位小数
 * @param {number} num - 需要格式化的数字
 * @param {string} currency - 货币类型 'CNY' 或 'USD'
 * @returns {string} 格式化后的字符串
 */
export const formatQuotePrice = (num, currency) => {
  if (num === null || num === undefined) return '0';

  const ceiledNum = ceilByCurrency(num, currency);

  if (currency === 'USD') {
    // USD: 显示两位小数
    return ceiledNum.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  } else {
    // CNY: 显示整数
    return ceiledNum.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
};