/**
 * 审批API服务
 * 提供企业微信审批系统相关的API调用功能
 */

import axios from 'axios';

const BASE_URL = '/api/v1/wecom-approval';

class ApprovalApiService {
  /**
   * 获取报价单审批状态
   * @param {number} quoteId 报价单ID
   * @returns {Promise} 审批状态信息
   */
  async getApprovalStatus(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/status/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('获取审批状态失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 获取审批历史记录
   * @param {number} quoteId 报价单ID
   * @returns {Promise} 审批历史记录
   */
  async getApprovalHistory(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/history/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('获取审批历史失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 批准报价单
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async approveQuote(quoteId, data = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/approve/${quoteId}`, {
        comments: data.comments,
        modified_data: data.modified_data,
        change_summary: data.change_summary
      });
      return response.data;
    } catch (error) {
      console.error('批准操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 拒绝报价单
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async rejectQuote(quoteId, data = {}) {
    try {
      if (!data.comments) {
        throw new Error('拒绝时必须提供拒绝原因');
      }
      
      const response = await axios.post(`${BASE_URL}/reject/${quoteId}`, {
        comments: data.comments
      });
      return response.data;
    } catch (error) {
      console.error('拒绝操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 修改后批准
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async approveWithChanges(quoteId, data = {}) {
    try {
      if (!data.modified_data) {
        throw new Error('修改后批准必须提供修改数据');
      }
      
      const response = await axios.post(`${BASE_URL}/approve-with-changes/${quoteId}`, {
        comments: data.comments,
        modified_data: data.modified_data,
        change_summary: data.change_summary
      });
      return response.data;
    } catch (error) {
      console.error('修改后批准操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 退回修改
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async returnForRevision(quoteId, data = {}) {
    try {
      if (!data.comments) {
        throw new Error('退回修改时必须提供修改建议');
      }
      
      const response = await axios.post(`${BASE_URL}/return-for-revision/${quoteId}`, {
        comments: data.comments,
        change_summary: data.change_summary
      });
      return response.data;
    } catch (error) {
      console.error('退回修改操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 转交审批
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async forwardApproval(quoteId, data = {}) {
    try {
      if (!data.forwarded_to_id) {
        throw new Error('转交时必须指定转交对象');
      }
      if (!data.forward_reason) {
        throw new Error('转交时必须提供转交原因');
      }
      
      const response = await axios.post(`${BASE_URL}/forward/${quoteId}`, {
        forwarded_to_id: data.forwarded_to_id,
        forward_reason: data.forward_reason,
        comments: data.comments
      });
      return response.data;
    } catch (error) {
      console.error('转交操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 征求意见
   * @param {number} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async requestInput(quoteId, data = {}) {
    try {
      if (!data.comments) {
        throw new Error('征求意见时必须说明需要什么信息');
      }
      
      const response = await axios.post(`${BASE_URL}/request-input/${quoteId}`, {
        comments: data.comments,
        input_deadline: data.input_deadline
      });
      return response.data;
    } catch (error) {
      console.error('征求意见操作失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 手动同步审批状态
   * @param {number} quoteId 报价单ID
   * @returns {Promise} 同步结果
   */
  async syncApprovalStatus(quoteId) {
    try {
      const response = await axios.post(`${BASE_URL}/sync/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('同步审批状态失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 生成审批链接
   * @param {number} quoteId 报价单ID
   * @returns {Promise} 审批链接信息
   */
  async generateApprovalLink(quoteId) {
    try {
      const response = await axios.post(`${BASE_URL}/generate-approval-link/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('生成审批链接失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 通过Token获取审批信息
   * @param {string} token 审批Token
   * @returns {Promise} 审批信息
   */
  async getApprovalByToken(token) {
    try {
      const response = await axios.get(`${BASE_URL}/approval-link/${token}`);
      return response.data;
    } catch (error) {
      console.error('获取审批信息失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 统一的审批操作方法
   * @param {string} action 操作类型
   * @param {number} quoteId 报价单ID
   * @param {Object} data 操作数据
   * @returns {Promise} 操作结果
   */
  async performApprovalAction(action, quoteId, data = {}) {
    const actions = {
      approve: () => this.approveQuote(quoteId, data),
      reject: () => this.rejectQuote(quoteId, data),
      approve_with_changes: () => this.approveWithChanges(quoteId, data),
      return_for_revision: () => this.returnForRevision(quoteId, data),
      forward: () => this.forwardApproval(quoteId, data),
      request_input: () => this.requestInput(quoteId, data)
    };

    const actionMethod = actions[action];
    if (!actionMethod) {
      throw new Error(`不支持的操作类型: ${action}`);
    }

    return await actionMethod();
  }

  /**
   * 错误处理
   * @param {Error} error 错误对象
   * @returns {Error} 处理后的错误
   */
  handleError(error) {
    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response;
      const message = data?.detail || data?.message || `HTTP ${status} 错误`;
      return new Error(message);
    } else if (error.request) {
      // 网络错误
      return new Error('网络连接失败，请检查网络状态');
    } else {
      // 其他错误
      return error;
    }
  }

  /**
   * 获取审批状态中文描述
   * @param {string} status 审批状态
   * @returns {string} 中文描述
   */
  getApprovalStatusText(status) {
    const statusMap = {
      not_submitted: '未提交',
      pending: '待审批',
      approved: '已批准',
      rejected: '已拒绝',
      returned: '已退回',
      forwarded: '已转交'
    };
    return statusMap[status] || '未知状态';
  }

  /**
   * 获取审批操作中文描述
   * @param {string} action 操作类型
   * @returns {string} 中文描述
   */
  getActionText(action) {
    const actionMap = {
      approve: '批准',
      reject: '拒绝',
      approve_with_changes: '修改后批准',
      return_for_revision: '退回修改',
      forward: '转交',
      request_input: '征求意见',
      submit: '提交审批'
    };
    return actionMap[action] || '未知操作';
  }
}

// 创建单例实例
const approvalApiService = new ApprovalApiService();

export default approvalApiService;