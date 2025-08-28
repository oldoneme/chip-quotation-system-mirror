import React, { useState, useEffect } from 'react';
import { 
  Card, Descriptions, Table, Button, Space, Tag, 
  Divider, Row, Col, Statistic, Modal, message, 
  Result, Spin, Empty
} from 'antd';
import { 
  ArrowLeftOutlined, DownloadOutlined, 
  EditOutlined, DeleteOutlined, SendOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import QuoteApiService from '../services/quoteApi';
import '../styles/QuoteDetail.css';

const { confirm } = Modal;

const QuoteDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [quote, setQuote] = useState(null);

  useEffect(() => {
    fetchQuoteDetail();
  }, [id]);

  const fetchQuoteDetail = async () => {
    setLoading(true);
    try {
      const quoteData = await QuoteApiService.getQuoteDetailTest(id);
      
      if (quoteData.error) {
        throw new Error(quoteData.error);
      }
      
      // 格式化数据显示
      const formattedQuote = {
        id: quoteData.quote_number,
        quoteId: quoteData.id,  // 保存实际ID用于操作
        title: quoteData.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quoteData.quote_type),
        customer: quoteData.customer_name,
        currency: quoteData.currency || 'CNY',
        status: QuoteApiService.mapStatusFromBackend(quoteData.status),
        createdBy: quoteData.creator_name || `用户${quoteData.created_by}`,
        createdAt: new Date(quoteData.created_at).toLocaleString('zh-CN'),
        updatedAt: new Date(quoteData.updated_at).toLocaleString('zh-CN'),
        validUntil: quoteData.valid_until ? new Date(quoteData.valid_until).toLocaleDateString('zh-CN') : '-',
        approvedBy: quoteData.approved_by_name,
        approvedAt: quoteData.approved_at ? new Date(quoteData.approved_at).toLocaleString('zh-CN') : null,
        totalAmount: quoteData.total_amount || 0,
        discount: quoteData.discount || 0,
        description: quoteData.description,
        items: quoteData.items?.map(item => ({
          key: item.id?.toString(),
          itemName: item.item_name,
          machineType: item.machine_type,
          supplier: item.supplier,
          machine: item.machine_model,
          quantity: item.quantity,
          unit: item.unit,
          unitPrice: item.unit_price,
          totalPrice: item.total_price
        })) || []
      };
      
      setQuote(formattedQuote);
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      message.error('获取报价单详情失败');
      setQuote(null);
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <FileTextOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    };
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon} style={{ fontSize: '14px', padding: '4px 12px' }}>
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
    return <Tag color={typeColors[type]} style={{ fontSize: '14px', padding: '4px 12px' }}>{type}</Tag>;
  };

  const handleEdit = () => {
    message.info(`编辑报价单 ${quote.id}`);
  };

  const handleDelete = () => {
    confirm({
      title: '确认删除',
      content: `确定要删除报价单 ${quote.id} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await QuoteApiService.deleteQuote(quote.quoteId);
          message.success('删除成功');
          navigate(-1);
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  const handleDownload = () => {
    message.info(`下载报价单 ${quote.id}`);
  };

  const handleSubmitApproval = async () => {
    try {
      await QuoteApiService.submitForApproval(quote.quoteId);
      message.success('审批提交成功！审批人将在企业微信中收到通知。');
      fetchQuoteDetail(); // 重新获取数据
    } catch (error) {
      console.error('提交审批失败:', error);
      message.error('提交审批失败');
    }
  };

  const itemColumns = [
    {
      title: '测试类型',
      dataIndex: 'itemName',
      key: 'itemName',
      render: (text) => text || '-'
    },
    {
      title: '设备类型',
      dataIndex: 'machineType',
      key: 'machineType',
      render: (text) => text || '-'
    },
    {
      title: '设备型号',
      dataIndex: 'machine',
      key: 'machine',
      render: (text) => text || '-'
    },
    {
      title: '小时费率',
      dataIndex: 'unitPrice',
      key: 'unitPrice',
      render: (price) => price ? `¥${price.toLocaleString()}/小时` : '-'
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!quote) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Empty description="报价单不存在" />
        <Button type="primary" onClick={() => navigate(-1)} style={{ marginTop: '16px' }}>
          返回
        </Button>
      </div>
    );
  }

  return (
    <div className="quote-detail">
      {/* Header */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
              返回
            </Button>
            <h2 style={{ margin: 0 }}>{quote.title}</h2>
            {getStatusTag(quote.status)}
            {getTypeTag(quote.type)}
          </div>
          
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleDownload}>
              下载
            </Button>
            {quote.status === 'draft' && (
              <>
                <Button icon={<EditOutlined />} onClick={handleEdit}>
                  编辑
                </Button>
                <Button 
                  type="primary" 
                  icon={<SendOutlined />} 
                  onClick={handleSubmitApproval}
                >
                  提交审批
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                  删除
                </Button>
              </>
            )}
          </Space>
        </div>
      </Card>

      <Row gutter={16} style={{ marginTop: '16px' }}>
        {/* Basic Information */}
        <Col xs={24}>
          <Card title="基本信息">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="报价单号">{quote.id}</Descriptions.Item>
              <Descriptions.Item label="客户">{quote.customer}</Descriptions.Item>
              <Descriptions.Item label="报价类型">{quote.type}</Descriptions.Item>
              <Descriptions.Item label="币种">{quote.currency}</Descriptions.Item>
              <Descriptions.Item label="创建人">{quote.createdBy}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{quote.createdAt}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{quote.updatedAt}</Descriptions.Item>
              <Descriptions.Item label="有效期至">{quote.validUntil}</Descriptions.Item>
              {quote.approvedBy && (
                <>
                  <Descriptions.Item label="审批人">{quote.approvedBy}</Descriptions.Item>
                  <Descriptions.Item label="审批时间">{quote.approvedAt}</Descriptions.Item>
                </>
              )}
            </Descriptions>
            
            {quote.description && (
              <>
                <Divider />
                <div>
                  <h4>报价说明：</h4>
                  <p>{quote.description}</p>
                </div>
              </>
            )}
          </Card>
        </Col>
      </Row>

      {/* Items Detail */}
      <Card title="报价明细" style={{ marginTop: '16px' }}>
        <Table
          columns={itemColumns}
          dataSource={quote.items}
          pagination={false}
          bordered
        />
      </Card>
    </div>
  );
};

export default QuoteDetail;