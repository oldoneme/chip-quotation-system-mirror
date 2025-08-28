import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Space, Tag, Row, Col, Statistic, message, Modal
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, CopyOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import QuoteApiService from '../services/quoteApi';
import '../styles/QuoteManagement.css';

const { confirm } = Modal;

const QuoteManagement = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState([]);
  
  // 统计数据
  const [statistics, setStatistics] = useState({
    total: 0,
    draft: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  const fetchQuotes = async () => {
    setLoading(true);
    try {
      const response = await QuoteApiService.getQuotes();
      const quotesData = response.items || [];
      
      // 格式化数据显示
      const formattedQuotes = quotesData.map(quote => ({
        id: quote.quote_number,
        quoteId: quote.id,  // 保存实际ID用于操作
        title: quote.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quote.quote_type),
        customer: quote.customer_name,
        currency: quote.currency || 'CNY',
        status: QuoteApiService.mapStatusFromBackend(quote.status),
        createdBy: quote.created_by_name || `用户${quote.created_by}`,
        createdAt: new Date(quote.created_at).toLocaleString('zh-CN'),
        updatedAt: new Date(quote.updated_at).toLocaleString('zh-CN'),
        validUntil: quote.valid_until ? new Date(quote.valid_until).toLocaleDateString('zh-CN') : '-'
      }));
      
      setQuotes(formattedQuotes);
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

  useEffect(() => {
    fetchQuotes();
    fetchStatistics();
  }, []);

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <EditOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
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
    return <Tag color={typeColors[type]}>{type}</Tag>;
  };

  const columns = [
    {
      title: '报价单号',
      dataIndex: 'id',
      key: 'id',
      render: (text) => <a onClick={() => handleView(text)}>{text}</a>
    },
    {
      title: '报价标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: '报价类型',
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
      title: '有效期至',
      dataIndex: 'validUntil',
      key: 'validUntil'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          {record.status === 'draft' && (
            <>
              <Button 
                type="link" 
                icon={<EditOutlined />} 
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Button 
                type="link" 
                danger
                icon={<DeleteOutlined />} 
                onClick={() => handleDelete(record)}
              >
                删除
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  const handleView = (id) => {
    navigate(`/quote-detail/${id}`);
  };

  const handleEdit = (record) => {
    message.info(`编辑报价单 ${record.id}`);
    // 根据类型导航到对应的编辑页面
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      content: `确定要删除报价单 ${record.id} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await QuoteApiService.deleteQuote(record.quoteId);
          message.success('删除成功');
          fetchQuotes();
          fetchStatistics(); // 重新获取统计数据
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  return (
    <div className="quote-management">
      {/* 页面标题 */}
      <div className="page-header">
        <h1>报价单管理</h1>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => navigate('/quote-type-selection')}
          >
            新建报价单
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="总报价单" value={statistics.total} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="待审批" 
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

      {/* 表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={quotes}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>
    </div>
  );
};

export default QuoteManagement;