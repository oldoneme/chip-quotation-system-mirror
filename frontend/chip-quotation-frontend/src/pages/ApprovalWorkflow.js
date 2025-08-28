import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Tag, Tabs, Modal, message, Badge,
  Row, Col, Statistic, Alert, Descriptions, Empty
} from 'antd';
import { 
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
  SendOutlined, FileTextOutlined, EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import QuoteApiService from '../services/quoteApi';
import '../styles/ApprovalWorkflow.css';

const ApprovalWorkflow = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [quoteList, setQuoteList] = useState([]);
  const [activeTab, setActiveTab] = useState('my_quotes');
  
  // 统计数据
  const [statistics, setStatistics] = useState({
    draft: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    total: 0
  });

  useEffect(() => {
    fetchQuotes();
    fetchStatistics();
  }, [activeTab]);

  const fetchQuotes = async () => {
    setLoading(true);
    try {
      let statusFilter = null;
      if (activeTab !== 'my_quotes') {
        statusFilter = activeTab;
      }

      const params = {};
      if (statusFilter) {
        params.status = statusFilter;
      }

      const response = await QuoteApiService.getQuotes(params);
      const quotesData = response.items || [];
      
      // 格式化数据显示
      const formattedQuotes = quotesData.map(quote => ({
        id: quote.quote_number,
        quoteId: quote.id,  // 保存实际ID用于操作
        title: quote.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quote.quote_type),
        customer: quote.customer_name,
        status: QuoteApiService.mapStatusFromBackend(quote.status),
        createdBy: quote.created_by_name || `用户${quote.created_by}`,
        createdAt: new Date(quote.created_at).toLocaleString('zh-CN'),
        approvedAt: quote.approved_at ? new Date(quote.approved_at).toLocaleString('zh-CN') : null,
        approvedBy: quote.approved_by_name,
        rejectedAt: quote.rejection_reason ? '已拒绝' : null,
        rejectedBy: quote.rejection_reason
      }));
      
      setQuoteList(formattedQuotes);
    } catch (error) {
      console.error('获取报价单列表失败:', error);
      message.error('获取报价单列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const stats = await QuoteApiService.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('获取统计信息失败:', error);
      message.error('获取统计信息失败');
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <FileTextOutlined /> },
      pending: { color: 'processing', text: '审批中', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    };
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const getTypeTag = (type) => {
    const typeColors = {
      '询价报价': 'blue',
      '工装夹具报价': 'purple',
      '工程机时报价': 'cyan',
      '量产机时报价': 'green',
      '量产工序报价': 'orange',
      '综合报价': 'magenta'
    };
    return <Tag color={typeColors[type] || 'default'}>{type}</Tag>;
  };

  const handleSubmitApproval = (record) => {
    Modal.confirm({
      title: '提交审批',
      content: (
        <div>
          <p>确定要提交以下报价单进行审批吗？</p>
          <Descriptions column={1} size="small" style={{ marginTop: 16 }}>
            <Descriptions.Item label="报价单号">{record.id}</Descriptions.Item>
            <Descriptions.Item label="标题">{record.title}</Descriptions.Item>
            <Descriptions.Item label="客户">{record.customer}</Descriptions.Item>
          </Descriptions>
        </div>
      ),
      onOk: async () => {
        try {
          await QuoteApiService.submitForApproval(record.quoteId);
          message.success('审批提交成功！审批人将在企业微信中收到通知。');
          fetchQuotes();
          fetchStatistics(); // 重新获取统计数据
        } catch (error) {
          console.error('提交审批失败:', error);
          message.error('提交审批失败');
        }
      }
    });
  };

  const handleViewDetail = (record) => {
    // 导航到报价详情页面
    navigate(`/quote-detail/${record.id}`);
  };

  const columns = [
    {
      title: '报价单号',
      dataIndex: 'id',
      key: 'id',
      render: (text) => (
        <a onClick={() => handleViewDetail({ id: text })}>{text}</a>
      )
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => getTypeTag(type)
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status)
    },
    {
      title: '创建人',
      dataIndex: 'createdBy',
      key: 'createdBy'
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          {record.status === 'draft' && (
            <Button 
              type="primary"
              size="small"
              icon={<SendOutlined />}
              onClick={() => handleSubmitApproval(record)}
            >
              提交审批
            </Button>
          )}
        </Space>
      )
    }
  ];

  const tabItems = [
    { key: 'my_quotes', label: '全部报价', count: statistics.total },
    { key: 'draft', label: '草稿', count: statistics.draft },
    { key: 'pending', label: '审批中', count: statistics.pending },
    { key: 'approved', label: '已批准', count: statistics.approved },
    { key: 'rejected', label: '已拒绝', count: statistics.rejected }
  ].map(item => ({
    key: item.key,
    label: (
      <Badge count={item.count} offset={[10, 0]}>
        <span>{item.label}</span>
      </Badge>
    )
  }));

  return (
    <div className="approval-workflow">
      {/* 页面标题 */}
      <div className="page-header">
        <h1>审批管理</h1>
        <p>管理报价单审批流程，查看审批状态</p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="草稿" 
              value={statistics.draft}
              valueStyle={{ color: '#666' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="审批中" 
              value={statistics.pending}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="已批准" 
              value={statistics.approved}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="已拒绝" 
              value={statistics.rejected}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 企业微信提示 */}
      <Alert
        message="企业微信审批集成"
        description="草稿状态的报价单可以提交到企业微信审批系统。审批人将在企业微信中收到通知并进行审批。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* 报价单列表 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={tabItems}
        />
        {quoteList.length > 0 ? (
          <Table
            columns={columns}
            dataSource={quoteList}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`
            }}
          />
        ) : (
          <Empty description="暂无数据" />
        )}
      </Card>
    </div>
  );
};

export default ApprovalWorkflow;