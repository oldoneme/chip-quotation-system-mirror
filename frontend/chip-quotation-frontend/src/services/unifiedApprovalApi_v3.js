/**
 * 统一审批API服务 V3 - Step 4实施
 * 对接Step 3创建的V2 API端点 (/api/v2/approval/)
 * 提供完整的统一审批操作接口
 */

import axios from 'axios';

const BASE_URL = '/api/v2/approval';

class UnifiedApprovalApiV3 {
  /**
   * 获取审批状态 - V2 API
   * @param {number} quoteId 报价单ID
   * @returns {Promise} 审批状态信息
   */
  async getApprovalStatus(quoteId) {
    try {
      const response = await axios.get(`${BASE_URL}/${quoteId}/status`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 获取审批列表 - V2 API
   * @param {Object} params 查询参数
   * @param {string} params.statusFilter 状态过滤
   * @param {number} params.page 页码
   * @param {number} params.pageSize 页大小
   * @returns {Promise} 审批列表
   */
  async getApprovalList(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (params.statusFilter) queryParams.append('status_filter', params.statusFilter);
      if (params.page) queryParams.append('page', params.page);
      if (params.pageSize) queryParams.append('page_size', params.pageSize);

      const response = await axios.get(`${BASE_URL}/list?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 执行统一审批操作 - V2 API核心端点
   * @param {number} quoteId 报价单ID
   * @param {Object} operation 操作详情
   * @param {string} operation.action 操作类型: submit, approve, reject, withdraw, delegate
   * @param {string} operation.comments 操作备注
   * @param {string} operation.reason 拒绝原因 (仅reject时需要)
   * @param {string} operation.channel 操作渠道: auto, internal, wecom, api
   * @param {number} operation.delegateTo 委托给用户ID (仅delegate时需要)
   * @returns {Promise} 操作结果
   */
  async executeOperation(quoteId, operation) {
    try {
      const response = await axios.post(`${BASE_URL}/${quoteId}/operate`, operation);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 提交审批 - 便捷方法
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {string} options.comments 提交备注
   * @param {string} options.channel 操作渠道
   * @returns {Promise} 操作结果
   */
  async submitApproval(quoteId, options = {}) {
    return this.executeOperation(quoteId, {
      action: 'submit',
      comments: options.comments || null,
      channel: options.channel || 'auto'
    });
  }

  /**
   * 批准报价单 - 便捷方法
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {string} options.comments 批准备注
   * @param {string} options.channel 操作渠道
   * @returns {Promise} 操作结果
   */
  async approveQuote(quoteId, options = {}) {
    return this.executeOperation(quoteId, {
      action: 'approve',
      comments: options.comments || '批准',
      channel: options.channel || 'auto'
    });
  }

  /**
   * 拒绝报价单 - 便捷方法
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {string} options.reason 拒绝原因 (必填)
   * @param {string} options.comments 拒绝备注
   * @param {string} options.channel 操作渠道
   * @returns {Promise} 操作结果
   */
  async rejectQuote(quoteId, options = {}) {
    if (!options.reason) {
      throw new Error('拒绝操作必须提供原因');
    }

    return this.executeOperation(quoteId, {
      action: 'reject',
      reason: options.reason,
      comments: options.comments || null,
      channel: options.channel || 'auto'
    });
  }

  /**
   * 撤回审批 - 便捷方法
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {string} options.comments 撤回备注
   * @param {string} options.channel 操作渠道
   * @returns {Promise} 操作结果
   */
  async withdrawApproval(quoteId, options = {}) {
    return this.executeOperation(quoteId, {
      action: 'withdraw',
      comments: options.comments || null,
      channel: options.channel || 'auto'
    });
  }

  /**
   * 委托审批 - 便捷方法
   * @param {number} quoteId 报价单ID
   * @param {Object} options 选项
   * @param {number} options.delegateTo 委托给用户ID (必填)
   * @param {string} options.comments 委托备注
   * @param {string} options.channel 操作渠道
   * @returns {Promise} 操作结果
   */
  async delegateApproval(quoteId, options = {}) {
    if (!options.delegateTo) {
      throw new Error('委托操作必须指定委托用户');
    }

    return this.executeOperation(quoteId, {
      action: 'delegate',
      delegate_to: options.delegateTo,
      comments: options.comments || null,
      channel: options.channel || 'auto'
    });
  }

  /**
   * 使用V2兼容端点 - 批准
   * @param {number} quoteId 报价单ID
   * @param {string} comments 批准备注
   * @returns {Promise} 操作结果
   */
  async quickApprove(quoteId, comments = null) {
    try {
      const response = await axios.post(`${BASE_URL}/${quoteId}/approve`, {
        comments: comments || '批准'
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 使用V2兼容端点 - 拒绝
   * @param {number} quoteId 报价单ID
   * @param {string} reason 拒绝原因
   * @param {string} comments 拒绝备注
   * @returns {Promise} 操作结果
   */
  async quickReject(quoteId, reason, comments = null) {
    try {
      const response = await axios.post(`${BASE_URL}/${quoteId}/reject`, {
        reason: reason,
        comments: comments
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 使用V2兼容端点 - 提交
   * @param {number} quoteId 报价单ID
   * @param {string} comments 提交备注
   * @returns {Promise} 操作结果
   */
  async quickSubmit(quoteId, comments = null) {
    try {
      const response = await axios.post(`${BASE_URL}/${quoteId}/submit`, {
        comments: comments
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 检查API健康状态
   * @returns {Promise} 健康状态信息
   */
  async checkHealth() {
    try {
      const response = await axios.get(`${BASE_URL}/health`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * 错误处理
   * @param {Error} error 错误对象
   * @returns {Error} 标准化错误
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
      customError.details = data;
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
   * 检查审批权限
   * @param {Object} approvalData 审批数据
   * @param {Object} currentUser 当前用户
   * @returns {Object} 权限检查结果
   */
  checkApprovalPermissions(approvalData, currentUser) {
    const result = {
      canSubmit: false,
      canApprove: false,
      canReject: false,
      canWithdraw: false,
      canDelegate: false,
      canView: true,
      reason: ''
    };

    if (!approvalData || !currentUser) {
      result.reason = '数据不完整';
      return result;
    }

    // 从V2 API响应中获取权限信息
    if (approvalData.can_approve !== undefined) {
      result.canApprove = approvalData.can_approve;
    }
    if (approvalData.can_reject !== undefined) {
      result.canReject = approvalData.can_reject;
    }
    if (approvalData.can_withdraw !== undefined) {
      result.canWithdraw = approvalData.can_withdraw;
    }

    // 提交权限：草稿状态且是创建者
    if (approvalData.current_status === 'draft' ||
        approvalData.approval_status === 'draft') {
      result.canSubmit = true;
    }

    return result;
  }

  /**
   * 获取审批状态显示配置
   * @param {string} status 审批状态
   * @returns {Object} 显示配置
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
      },
      'cancelled': {
        text: '已取消',
        color: 'default',
        icon: 'StopOutlined'
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
   * @param {string} action 操作类型
   * @returns {Object} 按钮配置
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
      },
      'delegate': {
        text: '委托',
        type: 'default',
        icon: 'UserSwitchOutlined',
        color: '#722ed1'
      }
    };
    return actionMap[action] || {
      text: action,
      type: 'default',
      icon: 'QuestionCircleOutlined'
    };
  }

  /**
   * 格式化审批历史数据
   * @param {Array} historyList 历史记录列表
   * @returns {Array} 格式化后的历史记录
   */
  formatApprovalHistory(historyList) {
    if (!Array.isArray(historyList)) {
      return [];
    }

    return historyList.map(item => ({
      id: item.id,
      action: item.action,
      status: item.status,
      operator: item.operator || '系统',
      comments: item.comments,
      createdAt: item.created_at,
      channel: item.channel || 'internal',
      actionText: this.getActionText(item.action),
      statusConfig: this.getApprovalStatusConfig(item.status)
    }));
  }

  /**
   * 获取操作文本
   * @param {string} action 操作类型
   * @returns {string} 操作文本
   */
  getActionText(action) {
    const actionTextMap = {
      'submit': '提交审批',
      'approve': '批准',
      'reject': '拒绝',
      'withdraw': '撤回',
      'delegate': '委托',
      'create': '创建',
      'update': '更新'
    };
    return actionTextMap[action] || action;
  }
}

// 导出单例实例
export default new UnifiedApprovalApiV3();