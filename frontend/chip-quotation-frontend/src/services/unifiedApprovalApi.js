/**
 * 统一审批API服务
 * 调用Step 3创建的统一审批API端点
 * 提供一致的审批操作接口，自动选择最佳审批方式
 */

import axios from 'axios';

const BASE_URL = '/api/v1/approval';

class UnifiedApprovalApiService {
  /**
   * 获取报价单审批状态
   * @param {string} quoteId 报价单ID (支持UUID格式)
   * @returns {Promise} 统一格式的审批状态信息
   */
  async getApprovalStatus(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/status/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('获取统一审批状态失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 获取审批历史记录
   * @param {string} quoteId 报价单ID
   * @returns {Promise} 标准化的审批历史记录
   */
  async getApprovalHistory(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/history/${quoteId}`);
      return response.data;
    } catch (error) {
      console.error('获取统一审批历史失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 提交审批申请
   * @param {string} quoteId 报价单ID
   * @param {Object} data 提交数据
   * @returns {Promise} 操作结果
   */
  async submitApproval(quoteId, data = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/submit/${quoteId}`, {
        comments: data.comments || null,
        method: data.method || null  // null表示自动选择
      });
      return response.data;
    } catch (error) {
      console.error('统一提交审批失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 批准报价单
   * @param {string} quoteId 报价单ID
   * @param {Object} data 审批数据
   * @returns {Promise} 操作结果
   */
  async approveQuote(quoteId, data = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/approve/${quoteId}`, {
        comments: data.comments || '批准',
        method: data.method || null
      });
      return response.data;
    } catch (error) {
      console.error('统一批准失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 拒绝报价单
   * @param {string} quoteId 报价单ID
   * @param {Object} data 拒绝数据
   * @returns {Promise} 操作结果
   */
  async rejectQuote(quoteId, data = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/reject/${quoteId}`, {
        reason: data.reason || '拒绝',
        comments: data.comments || null,
        method: data.method || null
      });
      return response.data;
    } catch (error) {
      console.error('统一拒绝失败:', error);
      throw this.handleError(error);
    }
  }

  /**
   * 错误处理统一方法
   * @param {Error} error 错误对象
   * @returns {Error} 标准化的错误对象
   */
  handleError(error) {
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;
      let message = '操作失败';

      switch (status) {
        case 400:
          message = data?.detail || '请求参数错误';
          break;
        case 401:
          message = '认证失败，请重新登录';
          break;
        case 403:
          message = '没有操作权限';
          break;
        case 404:
          message = '报价单不存在';
          break;
        case 422:
          message = data?.detail || '数据验证失败';
          break;
        case 500:
          message = '服务器内部错误';
          break;
        default:
          message = data?.detail || `请求失败 (${status})`;
      }

      const customError = new Error(message);
      customError.status = status;
      customError.originalError = error;
      return customError;
    } else if (error.request) {
      // 网络错误
      const customError = new Error('网络连接失败，请检查网络');
      customError.originalError = error;
      return customError;
    } else {
      // 其他错误
      return error;
    }
  }

  /**
   * 获取审批方式显示名称
   * @param {string} method 审批方式 ('wecom' | 'internal')
   * @returns {string} 显示名称
   */
  getApprovalMethodName(method) {
    const methodMap = {
      'wecom': '企业微信审批',
      'internal': '内部审批',
      'auto': '自动选择'
    };
    return methodMap[method] || '未知方式';
  }

  /**
   * 获取审批状态显示信息
   * @param {string} status 审批状态
   * @returns {Object} 状态显示配置
   */
  getApprovalStatusConfig(status) {
    const statusMap = {
      'draft': {
        text: '草稿',
        color: 'default',
        icon: 'EditOutlined'
      },
      'pending': {
        text: '待审批',
        color: 'processing',
        icon: 'ClockCircleOutlined'
      },
      'approved': {
        text: '已批准',
        color: 'success',
        icon: 'CheckCircleOutlined'
      },
      'rejected': {
        text: '已拒绝',
        color: 'error',
        icon: 'CloseCircleOutlined'
      }
    };
    return statusMap[status] || {
      text: status,
      color: 'default',
      icon: 'QuestionCircleOutlined'
    };
  }

  /**
   * 检查是否可以执行审批操作
   * @param {Object} quote 报价单数据
   * @param {Object} user 当前用户
   * @returns {Object} 权限检查结果
   */
  checkApprovalPermissions(quote, user) {
    const result = {
      canSubmit: false,
      canApprove: false,
      canReject: false,
      canView: true,
      reason: ''
    };

    if (!quote || !user) {
      result.reason = '数据不完整';
      return result;
    }

    // 查看权限：所有认证用户都可以查看
    result.canView = true;

    // 提交权限：只有创建者且状态为草稿时可以提交
    if (quote.creator_id === user.id && quote.approval_status === 'draft') {
      result.canSubmit = true;
    }

    // 审批权限：管理员或超级管理员可以审批待审状态的报价单
    if (quote.approval_status === 'pending' &&
        (user.role === 'admin' || user.role === 'super_admin')) {
      result.canApprove = true;
      result.canReject = true;
    }

    return result;
  }
}

// 导出单例实例
export default new UnifiedApprovalApiService();