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