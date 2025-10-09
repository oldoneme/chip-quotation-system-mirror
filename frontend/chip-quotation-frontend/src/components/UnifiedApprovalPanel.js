/**
 * 统一审批面板组件
 * 整合内部审批和企业微信审批功能，提供一致的用户体验
 * 自动检测和切换审批方式，统一状态显示
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Alert,
  Descriptions,
  Spin,
  Row,
  Col,
  Divider
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  ClockCircleOutlined,
  SendOutlined,
  ExclamationCircleOutlined,
  RollbackOutlined
} from '@ant-design/icons';
import UnifiedApprovalApiV3 from '../services/unifiedApprovalApi_v3';
import ApprovalHistory from './ApprovalHistory';

const { TextArea } = Input;
const { Option } = Select;
const { confirm } = Modal;

const UnifiedApprovalPanel = ({
  quote,
  currentUser,
  onApprovalStatusChange,
  showHistory = true,
  layout = 'desktop', // 'desktop' | 'mobile'
  enableRealTimeUpdate = true,
  updateInterval = 30000 // 30秒刷新一次
}) => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [actionType, setActionType] = useState('');
  const [approvalStatus, setApprovalStatus] = useState(null);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [form] = Form.useForm();

  // 获取权限检查结果 - 将在状态加载后更新
  const [permissions, setPermissions] = useState({
    canSubmit: false,
    canApprove: false,
    canReject: false,
    canWithdraw: false,
    canDelegate: false,
    canView: true,
    reason: ''
  });

  useEffect(() => {
    if (quote?.id) {
      fetchApprovalStatus();
    }
  }, [quote?.id, showHistory]);

  // 实时更新 useEffect - 优化性能
  useEffect(() => {
    let intervalId;

    // 只有在启用实时更新、有报价ID、非加载状态，且页面可见时才启动轮询
    if (enableRealTimeUpdate && quote?.id && !loading && !document.hidden) {
      // 增加轮询间隔到60秒以减少服务器负载
      intervalId = setInterval(() => {
        // 检查页面是否仍然可见
        if (!document.hidden) {
          fetchApprovalStatus(true); // 静默刷新
        }
      }, Math.max(updateInterval, 60000)); // 最小60秒间隔
    }

    // 监听页面可见性变化
    const handleVisibilityChange = () => {
      if (document.hidden && intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      } else if (!document.hidden && enableRealTimeUpdate && quote?.id && !loading) {
        if (!intervalId) {
          intervalId = setInterval(() => {
            if (!document.hidden) {
              fetchApprovalStatus(true);
            }
          }, Math.max(updateInterval, 60000));
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enableRealTimeUpdate, quote?.id, loading, updateInterval]);

  // 获取审批状态
  const fetchApprovalStatus = async (silent = false) => {
    try {
      const status = await UnifiedApprovalApiV3.getApprovalStatus(quote.quoteId || quote.id);
      setApprovalStatus(status);
      setLastUpdated(new Date());

      // 更新权限状态
      const newPermissions = UnifiedApprovalApiV3.checkApprovalPermissions(status, currentUser);
      setPermissions(newPermissions);

      // 处理审批历史 - V2 API已包含历史记录在状态响应中
      if (showHistory && status?.approval_history) {
        const formattedHistory = UnifiedApprovalApiV3.formatApprovalHistory(status.approval_history);
        setApprovalHistory(formattedHistory);
      }
    } catch (error) {
      console.error('获取审批状态失败:', error);
      if (!silent) {
        message.error(error.message || '获取审批状态失败');
      }
    }
  };

  // 获取审批历史 - 已废弃，直接从fetchApprovalStatus中处理
  const fetchApprovalHistory = async () => {
    // 此函数已整合到fetchApprovalStatus中，保留仅为兼容性
    console.log('fetchApprovalHistory: 审批历史已从fetchApprovalStatus中获取');
  };

  // 处理审批操作
  const handleApprovalAction = async (action, data) => {
    setLoading(true);
    try {
      let result;

      switch (action) {
        case 'submit':
          result = await UnifiedApprovalApiV3.submitApproval(quote.quoteId || quote.id, data);
          message.success('审批申请已提交');
          break;
        case 'approve':
          result = await UnifiedApprovalApiV3.approveQuote(quote.quoteId || quote.id, data);
          message.success('报价单已批准');
          break;
        case 'reject':
          result = await UnifiedApprovalApiV3.rejectQuote(quote.quoteId || quote.id, data);
          message.success('报价单已拒绝');
          break;
        case 'withdraw':
          result = await UnifiedApprovalApiV3.withdrawApproval(quote.quoteId || quote.id, data);
          message.success('审批已撤回');
          break;
        default:
          throw new Error('未知的审批操作');
      }

      // 刷新状态
      await fetchApprovalStatus();
      if (showHistory) {
        await fetchApprovalHistory();
      }

      // 通知父组件状态变化
      if (onApprovalStatusChange) {
        onApprovalStatusChange(result);
      }

      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error(`${action}操作失败:`, error);
      message.error(error.message || `${action}操作失败`);
    } finally {
      setLoading(false);
    }
  };

  // 显示操作确认框
  const showActionConfirm = (action) => {
    const isRejected = (approvalStatus?.current_status === 'rejected' || approvalStatus?.approval_status === 'rejected');
    const actionTexts = {
      submit: isRejected ? '重新提交' : '提交审批',
      approve: '批准',
      reject: '拒绝',
      withdraw: '撤回'
    };

    if (action === 'reject') {
      // 拒绝操作需要填写原因
      setActionType(action);
      setModalVisible(true);
    } else {
      confirm({
        title: `确认${actionTexts[action]}?`,
        icon: <ExclamationCircleOutlined />,
        content: `确定要${actionTexts[action]}这个报价单吗？`,
        okText: '确认',
        cancelText: '取消',
        onOk: () => handleApprovalAction(action, {})
      });
    }
  };

  // 处理模态框提交
  const handleModalSubmit = async () => {
    try {
      const values = await form.validateFields();
      await handleApprovalAction(actionType, values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 获取状态标签
  const getStatusTag = (status) => {
    const config = UnifiedApprovalApiV3.getApprovalStatusConfig(status);
    return (
      <Tag color={config.color} icon={<config.icon />}>
        {config.text}
      </Tag>
    );
  };

  // 渲染审批方式信息和同步状态
  const renderApprovalMethodInfo = () => {
    if (!approvalStatus) {
      return null;
    }

    const syncRequired = approvalStatus.sync_required || false;

    if (!syncRequired && !approvalStatus.operation_id) {
      return null;
    }

    return (
      <div style={{ marginBottom: 16 }}>
        {syncRequired && (
          <Alert
            type="warning"
            showIcon
            message="同步状态"
            description="检测到状态变化，正在同步到企业微信审批系统..."
            style={{ marginBottom: 8 }}
          />
        )}

        {approvalStatus.operation_id && (
          <Alert
            type="success"
            showIcon
            message="操作已完成"
            description={`操作ID: ${approvalStatus.operation_id}`}
            closable
          />
        )}
      </div>
    );
  };

  // 渲染操作按钮
  const renderActionButtons = () => {
    if (!permissions.canSubmit && !permissions.canApprove && !permissions.canReject && !permissions.canWithdraw) {
      return null;
    }

    const buttonSize = layout === 'mobile' ? 'large' : 'default';

    return (
      <Space wrap size="middle">
        {permissions.canSubmit && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            size={buttonSize}
            onClick={() => showActionConfirm('submit')}
            loading={loading}
          >
            {(approvalStatus?.current_status === 'rejected' || approvalStatus?.approval_status === 'rejected') ? '重新提交' : '提交审批'}
          </Button>
        )}

        {permissions.canApprove && (
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            size={buttonSize}
            onClick={() => showActionConfirm('approve')}
            loading={loading}
            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
          >
            批准
          </Button>
        )}

        {permissions.canReject && (
          <Button
            danger
            icon={<CloseCircleOutlined />}
            size={buttonSize}
            onClick={() => showActionConfirm('reject')}
            loading={loading}
          >
            拒绝
          </Button>
        )}

        {permissions.canWithdraw && (
          <Button
            type="default"
            icon={<RollbackOutlined />}
            size={buttonSize}
            onClick={() => showActionConfirm('withdraw')}
            loading={loading}
            style={{ color: '#faad14', borderColor: '#faad14' }}
          >
            撤回
          </Button>
        )}
      </Space>
    );
  };

  // 渲染审批状态详情
  const renderStatusDetails = () => {
    if (!approvalStatus) return null;

    return (
      <Descriptions
        column={layout === 'mobile' ? 1 : 2}
        size="small"
        bordered={layout === 'desktop'}
      >
        <Descriptions.Item label="报价单号">
          {approvalStatus.quote_number}
        </Descriptions.Item>
        <Descriptions.Item label="当前状态">
          {getStatusTag(approvalStatus.approval_status)}
        </Descriptions.Item>
        {approvalStatus.submitted_at && (
          <Descriptions.Item label="提交时间">
            {new Date(approvalStatus.submitted_at).toLocaleString()}
          </Descriptions.Item>
        )}
        {approvalStatus.approved_at && (
          <Descriptions.Item label="批准时间">
            {new Date(approvalStatus.approved_at).toLocaleString()}
          </Descriptions.Item>
        )}
        {approvalStatus.approved_by && (
          <Descriptions.Item label="批准人">
            {approvalStatus.approved_by}
          </Descriptions.Item>
        )}
        {approvalStatus.rejection_reason && (
          <Descriptions.Item label="拒绝原因" span={2}>
            {approvalStatus.rejection_reason}
          </Descriptions.Item>
        )}
        {lastUpdated && (
          <Descriptions.Item label="最后更新时间" span={layout === 'mobile' ? 1 : 2}>
            {lastUpdated.toLocaleString()}
            {enableRealTimeUpdate && ' (自动刷新)'}
          </Descriptions.Item>
        )}
      </Descriptions>
    );
  };

  if (!quote) {
    return (
      <Card title="审批状态">
        <Alert type="warning" message="请选择要查看的报价单" />
      </Card>
    );
  }

  return (
    <div>
      <Card
        title="审批状态"
        extra={renderActionButtons()}
        loading={!approvalStatus}
        data-approval-loaded={!!approvalStatus}
      >
        {renderApprovalMethodInfo()}
        {renderStatusDetails()}
      </Card>

      {showHistory && (
        <Card
          title="审批历史"
          style={{ marginTop: 16 }}
          size={layout === 'mobile' ? 'small' : 'default'}
        >
          <ApprovalHistory
            quoteId={quote.quoteId || quote.id}
            history={approvalHistory}
            layout={layout}
          />
        </Card>
      )}

      {/* 拒绝原因输入模态框 */}
      <Modal
        title="拒绝审批"
        open={modalVisible}
        onOk={handleModalSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        okText="确认拒绝"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="拒绝原因"
            name="reason"
            rules={[{ required: true, message: '请输入拒绝原因' }]}
          >
            <TextArea
              rows={4}
              placeholder="请详细说明拒绝的原因..."
              maxLength={500}
              showCount
            />
          </Form.Item>
          <Form.Item
            label="补充说明"
            name="comments"
          >
            <TextArea
              rows={2}
              placeholder="可选：补充说明..."
              maxLength={200}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UnifiedApprovalPanel;
