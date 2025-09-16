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
  InfoCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import UnifiedApprovalApiService from '../services/unifiedApprovalApi';
import ApprovalHistory from './ApprovalHistory';

const { TextArea } = Input;
const { Option } = Select;
const { confirm } = Modal;

const UnifiedApprovalPanel = ({
  quote,
  currentUser,
  onApprovalStatusChange,
  showHistory = true,
  layout = 'desktop' // 'desktop' | 'mobile'
}) => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [actionType, setActionType] = useState('');
  const [approvalStatus, setApprovalStatus] = useState(null);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [form] = Form.useForm();

  // 获取权限检查结果
  const permissions = UnifiedApprovalApiService.checkApprovalPermissions(quote, currentUser);

  useEffect(() => {
    if (quote?.id) {
      fetchApprovalStatus();
      if (showHistory) {
        fetchApprovalHistory();
      }
    }
  }, [quote?.id, showHistory]);

  // 获取审批状态
  const fetchApprovalStatus = async () => {
    try {
      const status = await UnifiedApprovalApiService.getApprovalStatus(quote.id);
      setApprovalStatus(status);
    } catch (error) {
      console.error('获取审批状态失败:', error);
      message.error(error.message || '获取审批状态失败');
    }
  };

  // 获取审批历史
  const fetchApprovalHistory = async () => {
    try {
      const history = await UnifiedApprovalApiService.getApprovalHistory(quote.id);
      setApprovalHistory(history.history || []);
    } catch (error) {
      console.error('获取审批历史失败:', error);
    }
  };

  // 处理审批操作
  const handleApprovalAction = async (action, data) => {
    setLoading(true);
    try {
      let result;

      switch (action) {
        case 'submit':
          result = await UnifiedApprovalApiService.submitApproval(quote.id, data);
          message.success('审批申请已提交');
          break;
        case 'approve':
          result = await UnifiedApprovalApiService.approveQuote(quote.id, data);
          message.success('报价单已批准');
          break;
        case 'reject':
          result = await UnifiedApprovalApiService.rejectQuote(quote.id, data);
          message.success('报价单已拒绝');
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
    const actionTexts = {
      submit: '提交审批',
      approve: '批准',
      reject: '拒绝'
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
    const config = UnifiedApprovalApiService.getApprovalStatusConfig(status);
    return (
      <Tag color={config.color} icon={<config.icon />}>
        {config.text}
      </Tag>
    );
  };

  // 渲染审批方式信息
  const renderApprovalMethodInfo = () => {
    if (!approvalStatus?.has_wecom_approval && !approvalStatus?.approval_status) {
      return null;
    }

    const hasWeComApproval = approvalStatus.has_wecom_approval;

    return (
      <Alert
        type={hasWeComApproval ? 'info' : 'warning'}
        showIcon
        message={`当前审批方式: ${hasWeComApproval ? '企业微信审批' : '内部审批'}`}
        description={
          hasWeComApproval
            ? '此报价单正在使用企业微信审批流程，支持移动端操作'
            : '此报价单使用内部审批流程，请在系统内完成审批'
        }
        style={{ marginBottom: 16 }}
      />
    );
  };

  // 渲染操作按钮
  const renderActionButtons = () => {
    if (!permissions.canSubmit && !permissions.canApprove && !permissions.canReject) {
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
            提交审批
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
        title={
          <Space>
            <InfoCircleOutlined />
            统一审批面板
          </Space>
        }
        extra={renderActionButtons()}
        loading={!approvalStatus}
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
            quoteId={quote.id}
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