import React, { useState } from 'react';
import { Modal, message, Alert, Space } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import api from '../services/api';

const SubmitApprovalModal = ({ visible, onCancel, onSuccess, quoteData }) => {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    try {
      setLoading(true);

      const response = await api.post(`/quotes/${quoteData.id}/submit`);
      const result = response.data;

      if (result.success) {
        message.success('审批申请已提交到企业微信，审批人将收到通知');
        onSuccess(result);
      } else {
        message.error(result.message || '提交审批失败');
      }
    } catch (error) {
      console.error('提交审批失败:', error);
      message.error('提交审批失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <span>
          <FileTextOutlined style={{ marginRight: 8 }} />
          提交企业微信审批
        </span>
      }
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      okText="提交审批"
      cancelText="取消"
      width={500}
    >
      <div style={{ padding: '16px 0' }}>
        <div style={{ 
          padding: '16px', 
          background: '#f5f5f5', 
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>报价单信息</h4>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div><strong>报价单号:</strong> {quoteData?.quote_number}</div>
            <div><strong>客户名称:</strong> {quoteData?.customer_name}</div>
            <div><strong>报价类型:</strong> {quoteData?.quote_type}</div>
            {quoteData?.total_amount && 
              <div><strong>报价金额:</strong> ¥{quoteData.total_amount.toFixed(2)}</div>
            }
            {quoteData?.description && 
              <div><strong>描述:</strong> {quoteData.description}</div>
            }
          </Space>
        </div>

        <Alert
          message="企业微信审批流程"
          description={
            <div style={{ color: '#666', fontSize: '14px' }}>
              <p>✅ 使用企业微信审批模板中预设的审批人</p>
              <p>📱 审批人将在企业微信中收到审批通知</p>
              <p>🔗 审批通知包含报价单详情链接</p>
              <p>⚡ 审批完成后系统将自动更新状态</p>
            </div>
          }
          type="info"
          showIcon
        />
      </div>
    </Modal>
  );
};

export default SubmitApprovalModal;
