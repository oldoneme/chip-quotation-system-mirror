/**
 * 报价单API服务
 * 连接前端和后端的数据接口
 */

import api from './api';

const QUOTE_BASE_URL = '/quotes';

export class QuoteApiService {
  
  /**
   * 获取报价单统计信息
   */
  static async getStatistics() {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/statistics`);
      return response.data;
    } catch (error) {
      console.error('获取统计信息失败:', error);
      throw error;
    }
  }

  /**
   * 获取报价单列表
   * @param {Object} params - 查询参数
   * @param {string} params.status - 状态筛选
   * @param {string} params.quote_type - 类型筛选 
   * @param {string} params.customer_name - 客户名称筛选
   * @param {number} params.page - 页码
   * @param {number} params.size - 每页大小
   */
  static async getQuotes(params = {}) {
    try {
      // 暂时使用测试端点
      const response = await api.get(`${QUOTE_BASE_URL}/test`);
      return response.data;
    } catch (error) {
      console.error('获取报价单列表失败:', error);
      throw error;
    }
  }

  /**
   * 根据ID获取报价单详情
   * @param {number} id - 报价单ID
   */
  static async getQuoteById(id) {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/${id}`);
      return response.data;
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      throw error;
    }
  }

  /**
   * 根据报价单号获取报价单详情
   * @param {string} quoteNumber - 报价单号
   */
  static async getQuoteByNumber(quoteNumber) {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/number/${quoteNumber}`);
      return response.data;
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      throw error;
    }
  }

  /**
   * 根据报价单号获取报价单详情（测试端点，包含创建者姓名）
   * @param {string} quoteNumber - 报价单号
   */
  static async getQuoteDetailTest(quoteNumber) {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/detail/${quoteNumber}`);
      return response.data;
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      throw error;
    }
  }

  /**
   * 根据报价单ID获取报价单详情（包含创建者姓名）
   * @param {number} quoteId - 报价单ID
   */
  static async getQuoteDetailById(quoteId) {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/detail/by-id/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      throw error;
    }
  }

  /**
   * 创建新报价单
   * @param {Object} quoteData - 报价单数据
   */
  static async createQuote(quoteData) {
    try {
      const response = await api.post(`${QUOTE_BASE_URL}/`, quoteData);
      return response.data;
    } catch (error) {
      console.error('创建报价单失败:', error);
      throw error;
    }
  }

  /**
   * 更新报价单
   * @param {number} id - 报价单ID
   * @param {Object} updateData - 更新数据
   */
  static async updateQuote(id, updateData) {
    try {
      const response = await api.put(`${QUOTE_BASE_URL}/${id}`, updateData);
      return response.data;
    } catch (error) {
      console.error('更新报价单失败:', error);
      throw error;
    }
  }

  /**
   * 删除报价单
   * @param {number} id - 报价单ID
   */
  static async deleteQuote(id) {
    try {
      const response = await api.delete(`${QUOTE_BASE_URL}/${id}`);
      return response.data;
    } catch (error) {
      console.error('删除报价单失败:', error);
      throw error;
    }
  }

  /**
   * 更新报价单状态
   * @param {number} id - 报价单ID
   * @param {string} status - 新状态
   * @param {string} comments - 状态更新说明
   */
  static async updateQuoteStatus(id, status, comments = '') {
    try {
      const response = await api.patch(`${QUOTE_BASE_URL}/${id}/status`, {
        status,
        comments
      });
      return response.data;
    } catch (error) {
      console.error('更新报价单状态失败:', error);
      throw error;
    }
  }

  /**
   * 提交报价单审批
   * @param {number} id - 报价单ID
   */
  static async submitForApproval(id) {
    try {
      const response = await api.post(`${QUOTE_BASE_URL}/${id}/submit`);
      return response.data;
    } catch (error) {
      console.error('提交审批失败:', error);
      throw error;
    }
  }

  /**
   * 获取报价单审批记录
   * @param {number} id - 报价单ID
   */
  static async getApprovalRecords(id) {
    try {
      const response = await api.get(`${QUOTE_BASE_URL}/${id}/approval-records`);
      return response.data;
    } catch (error) {
      console.error('获取审批记录失败:', error);
      throw error;
    }
  }

  /**
   * 状态转换映射（后端 -> 前端）
   */
  static mapStatusFromBackend(backendStatus) {
    const statusMap = {
      'draft': 'draft',
      'pending': 'pending', 
      'approved': 'approved',
      'rejected': 'rejected'
    };
    return statusMap[backendStatus] || backendStatus;
  }

  /**
   * 状态转换映射（前端 -> 后端）
   */
  static mapStatusToBackend(frontendStatus) {
    const statusMap = {
      'draft': 'draft',
      'pending': 'pending',
      'approved': 'approved', 
      'rejected': 'rejected'
    };
    return statusMap[frontendStatus] || frontendStatus;
  }

  /**
   * 报价类型转换映射（后端 -> 前端）
   */
  static mapQuoteTypeFromBackend(backendType) {
    const typeMap = {
      'inquiry': '询价报价',
      'tooling': '工装夹具报价',
      'engineering': '工程机时报价',
      'mass_production': '量产机时报价',
      'process': '量产工序报价',
      '工序报价': '量产工序报价',  // 兼容中文类型
      'comprehensive': '综合报价'
    };
    return typeMap[backendType] || backendType;
  }

  /**
   * 报价类型转换映射（前端 -> 后端）
   */
  static mapQuoteTypeToBackend(frontendType) {
    const typeMap = {
      '询价报价': 'inquiry',
      '工装夹具报价': 'tooling',
      '工程机时报价': 'engineering',
      '量产机时报价': 'mass_production',
      '量产工序报价': 'process',
      '工序报价': 'process',  // 兼容简称
      '综合报价': 'comprehensive'
    };
    return typeMap[frontendType] || frontendType;
  }

  /**
   * 格式化报价单数据（后端 -> 前端）
   */
  static formatQuoteFromBackend(backendQuote) {
    return {
      ...backendQuote,
      status: this.mapStatusFromBackend(backendQuote.status),
      type: this.mapQuoteTypeFromBackend(backendQuote.quote_type),
      customer: backendQuote.customer_name,
      createdBy: backendQuote.created_by,
      createdAt: backendQuote.created_at,
      updatedAt: backendQuote.updated_at,
      totalAmount: backendQuote.total_amount,
      validUntil: backendQuote.valid_until,
      approvedAt: backendQuote.approved_at,
      approvedBy: backendQuote.approved_by
    };
  }

  /**
   * 格式化报价单数据（前端 -> 后端）
   */
  static formatQuoteToBackend(frontendQuote) {
    return {
      title: frontendQuote.title,
      quote_type: this.mapQuoteTypeToBackend(frontendQuote.type),
      customer_name: frontendQuote.customer || frontendQuote.customer_name,
      customer_contact: frontendQuote.customer_contact,
      customer_phone: frontendQuote.customer_phone,
      customer_email: frontendQuote.customer_email,
      customer_address: frontendQuote.customer_address,
      currency: frontendQuote.currency,
      subtotal: frontendQuote.subtotal,
      discount: frontendQuote.discount,
      tax_rate: frontendQuote.tax_rate,
      tax_amount: frontendQuote.tax_amount,
      total_amount: frontendQuote.totalAmount || frontendQuote.total_amount,
      valid_until: frontendQuote.validUntil || frontendQuote.valid_until,
      payment_terms: frontendQuote.payment_terms,
      description: frontendQuote.description,
      notes: frontendQuote.notes,
      version: frontendQuote.version,
      items: frontendQuote.items || []
    };
  }

  /**
   * 批准报价单
   * @param {number} id - 报价单ID
   * @param {Object} approvalData - 批准数据
   */
  static async approveQuote(id, approvalData) {
    try {
      const response = await api.post(`${QUOTE_BASE_URL}/${id}/approve`, approvalData);
      return response.data;
    } catch (error) {
      console.error('批准报价单失败:', error);
      throw error;
    }
  }

  /**
   * 拒绝报价单  
   * @param {number} id - 报价单ID
   * @param {Object} rejectionData - 拒绝数据
   */
  static async rejectQuote(id, rejectionData) {
    try {
      const response = await api.post(`${QUOTE_BASE_URL}/${id}/reject`, rejectionData);
      return response.data;
    } catch (error) {
      console.error('拒绝报价单失败:', error);
      throw error;
    }
  }
}

export default QuoteApiService;