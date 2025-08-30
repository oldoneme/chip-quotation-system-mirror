import React, { useState } from 'react';
import {
  Card,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  message,
  Divider,
  Tag,
  Row,
  Col
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  RetweetOutlined,
  ForwardOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { TextArea } = Input;
const { Option } = Select;

const ApprovalPanel = ({ 
  quote, 
  currentUser, 
  onApprovalAction, 
  loading = false,
  approvers = []
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [actionType, setActionType] = useState('');
  const [form] = Form.useForm();

  // 检查是否有审批权限
  const hasApprovalPermission = () => {
    return quote?.current_approver_id === currentUser?.id || 
           currentUser?.role === 'admin' || 
           currentUser?.role === 'super_admin';
  };

  // 获取审批状态标签
  const getApprovalStatusTag = (status) => {
    const statusConfig = {
      not_submitted: { color: 'default', text: '未提交', icon: null },
      pending: { color: 'processing', text: '待审批', icon: <QuestionCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> },
      returned: { color: 'warning', text: '已退回', icon: <RetweetOutlined /> },
      forwarded: { color: 'blue', text: '已转交', icon: <ForwardOutlined /> }
    };
    
    const config = statusConfig[status] || statusConfig.not_submitted;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 打开审批操作模态框
  const openApprovalModal = (type) => {
    setActionType(type);
    setModalVisible(true);
    form.resetFields();
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setActionType('');
    form.resetFields();
  };

  // 处理审批操作
  const handleApprovalAction = async (values) => {
    try {
      const actionData = {
        ...values,
        action: actionType
      };

      // 处理日期格式
      if (values.input_deadline) {
        actionData.input_deadline = values.input_deadline.toISOString();
      }

      await onApprovalAction(actionType, actionData);
      closeModal();
      message.success('操作成功');
    } catch (error) {
      message.error('操作失败: ' + error.message);
    }
  };

  // 获取模态框标题和配置
  const getModalConfig = () => {
    const configs = {
      approve: {
        title: '批准报价单',
        color: '#52c41a',
        icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />
      },
      reject: {
        title: '拒绝报价单',
        color: '#ff4d4f',
        icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      },
      approve_with_changes: {
        title: '修改后批准',
        color: '#1890ff',
        icon: <EditOutlined style={{ color: '#1890ff' }} />
      },
      return_for_revision: {
        title: '退回修改',
        color: '#faad14',
        icon: <RetweetOutlined style={{ color: '#faad14' }} />
      },
      forward: {
        title: '转交审批',
        color: '#722ed1',
        icon: <ForwardOutlined style={{ color: '#722ed1' }} />
      },
      request_input: {
        title: '征求意见',
        color: '#13c2c2',
        icon: <QuestionCircleOutlined style={{ color: '#13c2c2' }} />
      }
    };
    return configs[actionType] || configs.approve;
  };

  // 如果没有审批权限，不显示审批面板
  if (!hasApprovalPermission() || quote?.approval_status !== 'pending') {
    return null;
  }

  return (
    <>
      <Card title="审批操作" style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[16, 8]}>
            <Col>
              <span style={{ fontWeight: 'bold' }}>当前状态：</span>
              {getApprovalStatusTag(quote?.approval_status)}
            </Col>
            <Col>
              <span style={{ fontWeight: 'bold' }}>当前审批人：</span>
              <span>{quote?.current_approver_name || '未指定'}</span>
            </Col>
          </Row>
        </div>

        <Divider />

        <Space wrap size="middle">
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={() => openApprovalModal('approve')}
            loading={loading}
            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
          >
            批准
          </Button>

          <Button
            danger
            icon={<CloseCircleOutlined />}
            onClick={() => openApprovalModal('reject')}
            loading={loading}
          >
            拒绝
          </Button>

          <Button
            icon={<EditOutlined />}
            onClick={() => openApprovalModal('approve_with_changes')}
            loading={loading}
            style={{ color: '#1890ff', borderColor: '#1890ff' }}
          >
            修改后批准
          </Button>

          <Button
            icon={<RetweetOutlined />}
            onClick={() => openApprovalModal('return_for_revision')}
            loading={loading}
            style={{ color: '#faad14', borderColor: '#faad14' }}
          >
            退回修改
          </Button>

          <Button
            icon={<ForwardOutlined />}
            onClick={() => openApprovalModal('forward')}
            loading={loading}
            style={{ color: '#722ed1', borderColor: '#722ed1' }}
          >
            转交
          </Button>

          <Button
            icon={<QuestionCircleOutlined />}
            onClick={() => openApprovalModal('request_input')}
            loading={loading}
            style={{ color: '#13c2c2', borderColor: '#13c2c2' }}
          >
            征求意见
          </Button>
        </Space>
      </Card>

      {/* 审批操作模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {getModalConfig().icon}
            <span>{getModalConfig().title}</span>
          </div>
        }
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleApprovalAction}
          autoComplete="off"
        >
          {/* 审批意见 */}
          <Form.Item
            label="审批意见"
            name="comments"
            rules={
              actionType === 'reject' || actionType === 'return_for_revision' || actionType === 'request_input'
                ? [{ required: true, message: '请填写审批意见' }]
                : []
            }
          >
            <TextArea
              rows={4}
              placeholder={
                actionType === 'reject' ? '请说明拒绝原因...' :
                actionType === 'return_for_revision' ? '请说明需要修改的内容...' :
                actionType === 'request_input' ? '请说明需要征求的意见...' :
                '请填写审批意见（可选）...'
              }
            />
          </Form.Item>

          {/* 修改数据 - 仅修改后批准时显示 */}
          {actionType === 'approve_with_changes' && (
            <>
              <Form.Item
                label="修改数据"
                name="modified_data"
                rules={[{ required: true, message: '请输入修改的数据' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="请输入修改的数据（JSON格式）..."
                />
              </Form.Item>
              <Form.Item
                label="修改摘要"
                name="change_summary"
              >
                <Input placeholder="请简要描述修改内容..." />
              </Form.Item>
            </>
          )}

          {/* 转交对象 - 仅转交时显示 */}
          {actionType === 'forward' && (
            <>
              <Form.Item
                label="转交给"
                name="forwarded_to_id"
                rules={[{ required: true, message: '请选择转交对象' }]}
              >
                <Select placeholder="请选择审批人">
                  {approvers.map(approver => (
                    <Option key={approver.id} value={approver.id}>
                      {approver.name} ({approver.role})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item
                label="转交原因"
                name="forward_reason"
                rules={[{ required: true, message: '请填写转交原因' }]}
              >
                <TextArea
                  rows={3}
                  placeholder="请说明转交原因..."
                />
              </Form.Item>
            </>
          )}

          {/* 意见征求截止时间 - 仅征求意见时显示 */}
          {actionType === 'request_input' && (
            <Form.Item
              label="截止时间"
              name="input_deadline"
            >
              <DatePicker
                showTime
                placeholder="请选择截止时间（可选）"
                disabledDate={(current) => current && current < moment().startOf('day')}
              />
            </Form.Item>
          )}

          {/* 操作按钮 */}
          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <Space style={{ float: 'right' }}>
              <Button onClick={closeModal}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{
                  backgroundColor: getModalConfig().color,
                  borderColor: getModalConfig().color
                }}
              >
                确认{getModalConfig().title}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ApprovalPanel;