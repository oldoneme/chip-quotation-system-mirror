/**
 * 统一审批API服务 V2
 * 基于新的统一审批引擎，真正实现双渠道统一操作
 */

import axios from 'axios';

const BASE_URL = '/api/v1/approval/v2';

class UnifiedApprovalApiV2 {
  /**
   * 提交审批 - 统一版本
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {string} options.comments 提交说明
   * @param {boolean} options.useWecom 是否同时创建企业微信审批
   */
  async submitApproval(quoteId, options = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/submit/${quoteId}`, {
        comments: options.comments || null,
        use_wecom: options.useWecom !== false // 默认true
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 批准报价单 - 统一版本
   * 自动同步到企业微信
   */
  async approveQuote(quoteId, options = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/approve/${quoteId}`, {
        comments: options.comments || '批准'
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 拒绝报价单 - 统一版本
   * 自动同步到企业微信
   */
  async rejectQuote(quoteId, options = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/reject/${quoteId}`, {
        reason: options.reason || '拒绝',
        comments: options.comments || null
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 撤回审批 - 新功能
   * 同时撤回企业微信审批
   */
  async withdrawApproval(quoteId, options = {}) {
    try {
      const response = await axios.post(`${BASE_URL}/withdraw/${quoteId}`, {
        reason: options.reason || null
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 获取审批状态 - 增强版本
   * 包含企业微信同步状态
   */
  async getApprovalStatus(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/status/${quoteId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 获取可用操作列表
   * 根据当前状态和权限返回可执行的操作
   */
  async getAvailableActions(quoteId) {
    try {
      const status = await this.getApprovalStatus(quoteId);
      return status.available_actions || [];
    } catch (error) {
      console.error('获取可用操作失败:', error);
      return [];
    }
  }

  /**
   * 检查企业微信同步状态
   */
  async checkWeComSyncStatus(quoteId) {
    try {
      const status = await this.getApprovalStatus(quoteId);
      return {
        hasSynced: status.has_wecom_integration,
        syncStatus: status.wecom_sync_status,
        wecomApprovalId: status.wecom_approval_id
      };
    } catch (error) {
      console.error('检查企业微信同步状态失败:', error);
      return { hasSynced: false, syncStatus: 'unknown' };
    }
  }

  /**
   * 错误处理
   */
  handleError(error) {
    if (error.response) {
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
      const customError = new Error('网络连接失败，请检查网络');
      customError.originalError = error;
      return customError;
    } else {
      return error;
    }
  }

  /**
   * 获取审批状态显示配置
   */
  getApprovalStatusConfig(status) {
    const statusMap = {
      'draft': {
        text: '草稿',
        color: 'default',
        icon: 'EditOutlined'
      },
      'pending': {
        text: '审批中',
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
      },
      'withdrawn': {
        text: '已撤回',
        color: 'warning',
        icon: 'RollbackOutlined'
      }
    };
    return statusMap[status] || {
      text: status,
      color: 'default',
      icon: 'QuestionCircleOutlined'
    };
  }

  /**
   * 获取操作按钮配置
   */
  getActionButtonConfig(action) {
    const actionMap = {
      'submit': {
        text: '提交审批',
        type: 'primary',
        icon: 'SendOutlined',
        color: '#1890ff'
      },
      'approve': {
        text: '批准',
        type: 'primary',
        icon: 'CheckCircleOutlined',
        color: '#52c41a'
      },
      'reject': {
        text: '拒绝',
        type: 'danger',
        icon: 'CloseCircleOutlined',
        color: '#ff4d4f'
      },
      'withdraw': {
        text: '撤回',
        type: 'default',
        icon: 'RollbackOutlined',
        color: '#faad14'
      }
    };
    return actionMap[action] || {
      text: action,
      type: 'default',
      icon: 'QuestionCircleOutlined'
    };
  }
}

// 导出单例实例
export default new UnifiedApprovalApiV2();