import React, { useState, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Spin,
  Empty,
  Result,
  message,
  Modal,
  Form,
  Input,
  Select,
  DatePicker
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  RetweetOutlined,
  ForwardOutlined,
  QuestionCircleOutlined,
  ArrowLeftOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useParams, useSearchParams } from 'react-router-dom';
import ApprovalApiService from '../services/approvalApi';
import ApprovalHistory from '../components/ApprovalHistory';
import moment from 'moment';
import '../styles/QuoteDetail.css';

const { TextArea } = Input;
const { Option } = Select;
const { confirm } = Modal;

/**
 * 企业微信专用审批页面
 * 通过审批链接Token访问，支持移动端优化
 */
const WeComApprovalPage = () => {
  const { token } = useParams();
  const [searchParams] = useSearchParams();
  
  const [loading, setLoading] = useState(true);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [approver, setApprover] = useState(null);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [actionType, setActionType] = useState('');
  const [form] = Form.useForm();
  const [isMobile, setIsMobile] = useState(true); // 企业微信默认移动端

  // 检测移动端
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  useEffect(() => {
    if (token) {
      fetchApprovalData();
    } else {
      setError('无效的审批链接');
      setLoading(false);
    }
  }, [token]);

  // 获取审批数据
  const fetchApprovalData = async () => {
    setLoading(true);
    try {
      const data = await ApprovalApiService.getApprovalByToken(token);
      
      if (!data.quote) {
        throw new Error('审批链接无效或已过期');
      }

      setQuote(data.quote);
      setApprover(data.approver);
      setError(null);
    } catch (error) {
      console.error('获取审批数据失败:', error);
      setError(error.message || '获取审批数据失败');
    } finally {
      setLoading(false);
    }
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
      <Tag color={config.color} icon={config.icon} style={{ fontSize: '14px' }}>
        {config.text}
      </Tag>
    );
  };

  // 获取操作类型配置
  const getActionConfig = (type) => {
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
      request_input: {
        title: '征求意见',
        color: '#13c2c2',
        icon: <QuestionCircleOutlined style={{ color: '#13c2c2' }} />
      }
    };
    return configs[type] || configs.approve;
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
    setApprovalLoading(true);
    
    try {
      const actionData = {
        ...values,
        action: actionType
      };

      // 处理日期格式
      if (values.input_deadline) {
        actionData.input_deadline = values.input_deadline.toISOString();
      }

      await ApprovalApiService.performApprovalAction(actionType, quote.id, actionData);
      
      message.success(`${ApprovalApiService.getActionText(actionType)}成功`);
      closeModal();
      
      // 刷新数据
      await fetchApprovalData();
      
    } catch (error) {
      console.error('审批操作失败:', error);
      message.error('操作失败: ' + error.message);
    } finally {
      setApprovalLoading(false);
    }
  };

  // 确认操作
  const confirmAction = (type) => {
    const config = getActionConfig(type);
    
    confirm({
      title: `确认${config.title}？`,
      icon: <ExclamationCircleOutlined />,
      content: `您确定要${config.title.toLowerCase()}这个报价单吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => openApprovalModal(type)
    });
  };

  // 渲染错误状态
  if (error) {
    return (
      <div style={{ padding: '20px', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        <Result
          status="error"
          title="审批链接无效"
          subTitle={error}
          extra={[
            <Button type="primary" key="back" onClick={() => window.history.back()}>
              <ArrowLeftOutlined /> 返回
            </Button>
          ]}
        />
      </div>
    );
  }

  // 渲染加载状态
  if (loading) {
    return (
      <div style={{ 
        padding: '50px', 
        textAlign: 'center', 
        minHeight: '100vh', 
        backgroundColor: '#f5f5f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Spin size="large" />
      </div>
    );
  }

  // 检查是否可以进行审批操作
  const canApprove = quote?.approval_status === 'pending' && 
                    approver?.id === quote?.current_approver_id;

  return (
    <div style={{ 
      padding: isMobile ? '8px' : '24px',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5'
    }}>
      {/* 页面标题 */}
      <Card style={{ marginBottom: '16px' }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ 
            margin: '0 0 8px 0',
            color: '#1890ff',
            fontSize: isMobile ? '18px' : '24px'
          }}>
            企业微信审批
          </h2>
          <div style={{ color: '#666', fontSize: '14px' }}>
            审批人：{approver?.name || '未知'} | 报价单：{quote?.quote_number}
          </div>
        </div>
      </Card>

      {/* 报价单基本信息 */}
      <Card title="报价单信息" style={{ marginBottom: '16px' }}>
        <Descriptions 
          column={isMobile ? 1 : 2}
          size={isMobile ? "small" : "default"}
          layout={isMobile ? "vertical" : "horizontal"}
        >
          <Descriptions.Item label="报价单号">{quote?.quote_number}</Descriptions.Item>
          <Descriptions.Item label="客户名称">{quote?.customer_name}</Descriptions.Item>
          <Descriptions.Item label="报价类型">{quote?.quote_type_display}</Descriptions.Item>
          <Descriptions.Item label="币种">{quote?.currency || 'CNY'}</Descriptions.Item>
          <Descriptions.Item label="创建人">{quote?.creator_name}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {quote?.created_at ? moment(quote.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="当前状态">
            {getApprovalStatusTag(quote?.approval_status)}
          </Descriptions.Item>
          <Descriptions.Item label="总金额">
            ¥{(quote?.total_amount || 0).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>

        {quote?.description && (
          <div style={{ marginTop: '16px' }}>
            <h4>报价说明：</h4>
            <p style={{ 
              padding: '12px',
              backgroundColor: '#f8f8f8',
              borderRadius: '6px',
              margin: 0,
              wordBreak: 'break-all'
            }}>
              {quote.description}
            </p>
          </div>
        )}
      </Card>

      {/* 审批操作区域 */}
      {canApprove ? (
        <Card title="审批操作" style={{ marginBottom: '16px' }}>
          <div style={{ textAlign: 'center' }}>
            <Space 
              direction={isMobile ? 'vertical' : 'horizontal'}
              size="middle"
              style={{ width: '100%' }}
            >
              <Button
                type="primary"
                icon={<CheckCircleOutlined />}
                size="large"
                onClick={() => confirmAction('approve')}
                loading={approvalLoading}
                style={{ 
                  backgroundColor: '#52c41a', 
                  borderColor: '#52c41a',
                  minWidth: isMobile ? '120px' : '100px'
                }}
              >
                批准
              </Button>

              <Button
                danger
                icon={<CloseCircleOutlined />}
                size="large"
                onClick={() => confirmAction('reject')}
                loading={approvalLoading}
                style={{ minWidth: isMobile ? '120px' : '100px' }}
              >
                拒绝
              </Button>

              <Button
                icon={<EditOutlined />}
                size="large"
                onClick={() => confirmAction('approve_with_changes')}
                loading={approvalLoading}
                style={{ 
                  color: '#1890ff', 
                  borderColor: '#1890ff',
                  minWidth: isMobile ? '120px' : '100px'
                }}
              >
                修改后批准
              </Button>

              <Button
                icon={<RetweetOutlined />}
                size="large"
                onClick={() => confirmAction('return_for_revision')}
                loading={approvalLoading}
                style={{ 
                  color: '#faad14', 
                  borderColor: '#faad14',
                  minWidth: isMobile ? '120px' : '100px'
                }}
              >
                退回修改
              </Button>

              <Button
                icon={<QuestionCircleOutlined />}
                size="large"
                onClick={() => confirmAction('request_input')}
                loading={approvalLoading}
                style={{ 
                  color: '#13c2c2', 
                  borderColor: '#13c2c2',
                  minWidth: isMobile ? '120px' : '100px'
                }}
              >
                征求意见
              </Button>
            </Space>
          </div>
        </Card>
      ) : (
        <Card style={{ marginBottom: '16px' }}>
          <Result
            status="info"
            title={quote?.approval_status === 'pending' ? '等待其他人审批' : '审批已完成'}
            subTitle={
              quote?.approval_status === 'pending' 
                ? `当前审批人：${quote?.current_approver_name || '未指定'}`
                : `审批状态：${ApprovalApiService.getApprovalStatusText(quote?.approval_status)}`
            }
          />
        </Card>
      )}

      {/* 审批历史 */}
      <ApprovalHistory
        quoteId={quote?.id}
        onRefresh={fetchApprovalData}
        approvalService={ApprovalApiService}
      />

      {/* 审批操作模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {getActionConfig(actionType).icon}
            <span>{getActionConfig(actionType).title}</span>
          </div>
        }
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        width={isMobile ? '95%' : 600}
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
                  placeholder="请输入修改的数据..."
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
                style={{ width: '100%' }}
              />
            </Form.Item>
          )}

          {/* 操作按钮 */}
          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Button onClick={closeModal} size="large">
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={approvalLoading}
                size="large"
                style={{
                  backgroundColor: getActionConfig(actionType).color,
                  borderColor: getActionConfig(actionType).color
                }}
              >
                确认{getActionConfig(actionType).title}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default WeComApprovalPage;