import React, { useState, useEffect } from 'react';
import {
  Card,
  Timeline,
  Tag,
  Space,
  Button,
  Collapse,
  Typography,
  Empty,
  Spin,
  Tooltip
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  RetweetOutlined,
  ForwardOutlined,
  QuestionCircleOutlined,
  UserOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  MessageOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

const ApprovalHistory = ({
  quoteId,
  history: externalHistory,
  onRefresh,
  approvalService,
  layout = 'desktop'
}) => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [expanded, setExpanded] = useState(true);

  // 如果传递了外部的history，使用外部history；否则通过API获取
  useEffect(() => {
    if (externalHistory) {
      setHistory(externalHistory);
    } else if (quoteId && approvalService) {
      fetchApprovalHistory();
    }
  }, [quoteId, externalHistory, approvalService]);

  // 获取审批历史
  const fetchApprovalHistory = async () => {
    if (!approvalService) {
      console.warn('未提供approvalService，无法获取审批历史');
      return;
    }
    setLoading(true);
    try {
      const response = await approvalService.getApprovalHistory(quoteId);
      setHistory(response.history || []);
    } catch (error) {
      console.error('获取审批历史失败:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取操作类型配置
  const getActionConfig = (action) => {
    const configs = {
      approve: {
        color: '#52c41a',
        icon: <CheckCircleOutlined />,
        text: '批准',
        bgColor: '#f6ffed'
      },
      reject: {
        color: '#ff4d4f',
        icon: <CloseCircleOutlined />,
        text: '拒绝',
        bgColor: '#fff2f0'
      },
      approve_with_changes: {
        color: '#1890ff',
        icon: <EditOutlined />,
        text: '修改后批准',
        bgColor: '#f0f9ff'
      },
      return_for_revision: {
        color: '#faad14',
        icon: <RetweetOutlined />,
        text: '退回修改',
        bgColor: '#fffbe6'
      },
      forward: {
        color: '#722ed1',
        icon: <ForwardOutlined />,
        text: '转交',
        bgColor: '#f9f0ff'
      },
      request_input: {
        color: '#13c2c2',
        icon: <QuestionCircleOutlined />,
        text: '征求意见',
        bgColor: '#e6fffb'
      },
      submit: {
        color: '#1890ff',
        icon: <MessageOutlined />,
        text: '提交审批',
        bgColor: '#f0f9ff'
      }
    };
    
    return configs[action] || {
      color: '#666',
      icon: <ClockCircleOutlined />,
      text: '未知操作',
      bgColor: '#f5f5f5'
    };
  };

  // 渲染审批记录卡片
  const renderApprovalRecord = (record) => {
    const config = getActionConfig(record.action);
    
    return (
      <div 
        style={{
          backgroundColor: config.bgColor,
          border: `1px solid ${config.color}20`,
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '12px'
        }}
      >
        {/* 操作标题行 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag color={config.color} icon={config.icon}>
              {config.text}
            </Tag>
            <Text strong style={{ color: '#333' }}>
              {record.approver_name || '系统'}
            </Text>
          </div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {moment(record.created_at).format('YYYY-MM-DD HH:mm')}
          </Text>
        </div>

        {/* 审批意见 */}
        {record.comments && (
          <div style={{ marginBottom: '8px' }}>
            <Text style={{ fontSize: '13px', lineHeight: '1.5' }}>
              <MessageOutlined style={{ marginRight: '4px', color: '#666' }} />
              {record.comments}
            </Text>
          </div>
        )}

        {/* 转交信息 */}
        {record.action === 'forward' && record.forwarded_to_name && (
          <div style={{ marginBottom: '8px' }}>
            <Tag color="blue" size="small">
              <UserOutlined /> 转交给：{record.forwarded_to_name}
            </Tag>
            {record.forward_reason && (
              <Text style={{ fontSize: '12px', color: '#666', marginLeft: '8px' }}>
                原因：{record.forward_reason}
              </Text>
            )}
          </div>
        )}

        {/* 修改摘要 */}
        {record.change_summary && (
          <div style={{ marginBottom: '8px' }}>
            <Text style={{ fontSize: '12px', color: '#666' }}>
              <EditOutlined style={{ marginRight: '4px' }} />
              修改摘要：{record.change_summary}
            </Text>
          </div>
        )}

        {/* 截止时间 */}
        {record.input_deadline && (
          <div style={{ marginBottom: '8px' }}>
            <Tag color="orange" size="small">
              <ClockCircleOutlined /> 截止时间：{moment(record.input_deadline).format('YYYY-MM-DD HH:mm')}
            </Tag>
          </div>
        )}

        {/* 修改数据详情 - 可展开 */}
        {record.modified_data && (
          <Collapse size="small" ghost>
            <Panel 
              header={
                <Text style={{ fontSize: '12px', color: config.color }}>
                  <EyeOutlined /> 查看修改详情
                </Text>
              } 
              key="modified_data"
            >
              <pre style={{ 
                fontSize: '11px', 
                backgroundColor: '#f8f8f8', 
                padding: '8px',
                borderRadius: '4px',
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}>
                {typeof record.modified_data === 'string' 
                  ? record.modified_data 
                  : JSON.stringify(record.modified_data, null, 2)}
              </pre>
            </Panel>
          </Collapse>
        )}

        {/* 步骤信息 */}
        {record.step_order && (
          <div style={{ marginTop: '8px' }}>
            <Text style={{ fontSize: '11px', color: '#999' }}>
              审批步骤：第{record.step_order}步
              {record.is_final_step && ' (最终步骤)'}
            </Text>
          </div>
        )}
      </div>
    );
  };

  // 渲染时间线视图
  const renderTimelineView = () => {
    if (history.length === 0) {
      return (
        <Empty 
          description="暂无审批记录" 
          style={{ padding: '40px 0' }}
        />
      );
    }

    // 按时间倒序排列
    const sortedHistory = [...history].sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    );

    return (
      <Timeline mode="left" style={{ marginTop: '16px' }}>
        {sortedHistory.map((record, index) => {
          const config = getActionConfig(record.action);
          
          return (
            <Timeline.Item
              key={record.id || index}
              color={config.color}
              dot={config.icon}
            >
              <div style={{ marginLeft: '8px' }}>
                {renderApprovalRecord(record)}
              </div>
            </Timeline.Item>
          );
        })}
      </Timeline>
    );
  };

  // 渲染内容区域
  const renderContent = () => (
    <Spin spinning={loading}>
      {renderTimelineView()}
    </Spin>
  );

  return renderContent();
};

export default ApprovalHistory;