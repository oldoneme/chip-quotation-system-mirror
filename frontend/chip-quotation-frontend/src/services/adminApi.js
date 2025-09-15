/**
 * 管理员API服务
 * 提供报价单数据库管理功能
 */
import api from './api';

const ADMIN_API_BASE = '/admin';

/**
 * 获取所有报价单（管理员专用）
 * @param {Object} params - 查询参数
 * @param {boolean} params.include_deleted - 是否包含软删除数据
 * @param {string} params.status_filter - 状态筛选
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页大小
 */
export const getAllQuotes = async (params = {}) => {
  try {
    const response = await api.get(`${ADMIN_API_BASE}/quotes/all`, {
      params: {
        include_deleted: false,
        page: 1,
        size: 20,
        ...params
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取所有报价单失败:', error);
    throw error;
  }
};

/**
 * 获取详细统计信息
 */
export const getDetailedStatistics = async () => {
  try {
    const response = await api.get(`${ADMIN_API_BASE}/quotes/statistics/detailed`);
    return response.data;
  } catch (error) {
    console.error('获取统计信息失败:', error);
    throw error;
  }
};

/**
 * 硬删除报价单（不可恢复）
 * @param {string} quoteId - 报价单ID
 */
export const hardDeleteQuote = async (quoteId) => {
  try {
    const response = await api.delete(`${ADMIN_API_BASE}/quotes/${quoteId}/hard-delete`, {
      withCredentials: true
    });
    return response.data;
  } catch (error) {
    console.error('硬删除报价单失败:', error);
    throw error;
  }
};

/**
 * 批量恢复报价单
 * @param {string[]} quoteIds - 报价单ID数组
 */
export const batchRestoreQuotes = async (quoteIds) => {
  try {
    const response = await api.post(`${ADMIN_API_BASE}/quotes/batch-restore`, quoteIds);
    return response.data;
  } catch (error) {
    console.error('批量恢复报价单失败:', error);
    throw error;
  }
};

/**
 * 批量软删除报价单
 * @param {string[]} quoteIds - 报价单ID数组
 */
export const batchSoftDeleteQuotes = async (quoteIds) => {
  try {
    const response = await api.delete(`${ADMIN_API_BASE}/quotes/batch-soft-delete`, {
      data: quoteIds
    });
    return response.data;
  } catch (error) {
    console.error('批量软删除报价单失败:', error);
    throw error;
  }
};

/**
 * 获取报价单统计状态
 * 用于验证数据一致性
 */
export const getQuoteStatistics = async () => {
  try {
    const [normalQuotes, deletedQuotes, statistics] = await Promise.all([
      getAllQuotes({ include_deleted: false }),
      getAllQuotes({ include_deleted: true }),
      getDetailedStatistics()
    ]);

    return {
      normalCount: normalQuotes.total,
      totalCount: deletedQuotes.total,
      deletedCount: deletedQuotes.total - normalQuotes.total,
      statusBreakdown: statistics
    };
  } catch (error) {
    console.error('获取报价单统计失败:', error);
    throw error;
  }
};

/**
 * 导出报价单数据
 * @param {Object} params - 导出参数
 * @param {boolean} params.include_deleted - 是否包含软删除数据
 * @param {string} params.format - 导出格式
 */
export const exportQuotes = async (params = {}) => {
  try {
    const response = await api.get(`${ADMIN_API_BASE}/quotes/export`, {
      params: {
        include_deleted: false,
        format: 'json',
        ...params
      }
    });
    return response.data;
  } catch (error) {
    console.error('导出报价单数据失败:', error);
    throw error;
  }
};

const adminApi = {
  getAllQuotes,
  getDetailedStatistics,
  hardDeleteQuote,
  batchRestoreQuotes,
  batchSoftDeleteQuotes,
  getQuoteStatistics,
  exportQuotes
};

export default adminApi;