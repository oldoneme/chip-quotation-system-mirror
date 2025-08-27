import React, { useState, useEffect } from 'react';
import { 
  Card, Descriptions, Table, Timeline, Button, Space, Tag, 
  Tabs, Divider, Row, Col, Statistic, Modal, message, Badge,
  Avatar, Typography, Steps, Result, Spin
} from 'antd';
import { 
  ArrowLeftOutlined, PrinterOutlined, DownloadOutlined, 
  EditOutlined, DeleteOutlined, CopyOutlined, SendOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  UserOutlined, CalendarOutlined, FileTextOutlined, CommentOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/QuoteDetail.css';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;
const { confirm } = Modal;

const QuoteDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [quoteData, setQuoteData] = useState(null);
  const [activeTab, setActiveTab] = useState('details');

  // 模拟报价单详情数据
  const mockQuoteData = {
    id: 'QT202408001',
    title: '华为技术有限公司芯片测试报价',
    type: '量产机时报价',
    status: 'approved',
    version: 'V1.2',
    customer: {
      name: '华为技术有限公司',
      contact: '张经理',
      phone: '138-1234-5678',
      email: 'zhang@huawei.com',
      address: '深圳市龙岗区坂田华为基地'
    },
    financial: {
      subtotal: 1150000,
      discount: 50000,
      tax: 150000,
      total: 1250000,
      currency: 'CNY',
      paymentTerms: '30天账期',
      validUntil: '2024-09-20'
    },
    items: [
      {
        key: '1',
        name: 'Advantest V93000测试机时',
        specification: 'Pin Scale 1024, 6.4Gbps',
        quantity: 500,
        unit: '小时',
        unitPrice: 1200,
        amount: 600000
      },
      {
        key: '2',
        name: 'Teradyne J750测试机时',
        specification: '512通道, 100MHz',
        quantity: 400,
        unit: '小时',
        unitPrice: 800,
        amount: 320000
      },
      {
        key: '3',
        name: '工程支持服务',
        specification: '测试程序开发与调试',
        quantity: 100,
        unit: '小时',
        unitPrice: 500,
        amount: 50000
      },
      {
        key: '4',
        name: '配套辅助设备',
        specification: 'Handler + Prober',
        quantity: 600,
        unit: '小时',
        unitPrice: 300,
        amount: 180000
      }
    ],
    timeline: [
      {
        time: '2024-08-20 14:30',
        user: '张三',
        action: '创建报价单',
        status: 'success',
        description: '创建初始报价单草稿'
      },
      {
        time: '2024-08-20 16:45',
        user: '张三',
        action: '提交审批',
        status: 'processing',
        description: '提交给部门经理审批'
      },
      {
        time: '2024-08-21 09:00',
        user: '李经理',
        action: '审批通过',
        status: 'success',
        description: '部门经理审批通过'
      },
      {
        time: '2024-08-21 10:15',
        user: '王总',
        action: '最终批准',
        status: 'success',
        description: '总经理最终批准，报价单生效'
      }
    ],
    comments: [
      {
        id: 1,
        user: '李经理',
        time: '2024-08-21 09:00',
        content: '价格合理，建议通过',
        avatar: null
      },
      {
        id: 2,
        user: '王总',
        time: '2024-08-21 10:15',
        content: '同意，请跟进后续合同签订',
        avatar: null
      }
    ],
    attachments: [
      {
        name: '技术规格说明书.pdf',
        size: '2.5MB',
        uploadTime: '2024-08-20 14:35'
      },
      {
        name: '测试方案.docx',
        size: '1.2MB',
        uploadTime: '2024-08-20 14:36'
      }
    ],
    createdBy: '张三',
    createdAt: '2024-08-20 14:30',
    updatedAt: '2024-08-21 10:15',
    approvedBy: '王总',
    approvedAt: '2024-08-21 10:15'
  };

  useEffect(() => {
    fetchQuoteDetail();
  }, [id]);

  const fetchQuoteDetail = () => {
    setLoading(true);
    // 模拟API调用
    setTimeout(() => {
      setQuoteData(mockQuoteData);
      setLoading(false);
    }, 500);
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <EditOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    };
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon} style={{ fontSize: 14, padding: '4px 12px' }}>
        {config.text}
      </Tag>
    );
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExport = () => {
    message.success('正在导出PDF...');
  };

  const handleEdit = () => {
    if (quoteData.status === 'approved') {
      confirm({
        title: '提示',
        icon: <ExclamationCircleOutlined />,
        content: '该报价单已批准，编辑将创建新版本，是否继续？',
        onOk() {
          navigate(`/quote-edit/${id}`);
        }
      });
    } else {
      navigate(`/quote-edit/${id}`);
    }
  };

  const handleDelete = () => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个报价单吗？此操作不可恢复。',
      okText: '确定',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        message.success('删除成功');
        navigate('/quote-management');
      }
    });
  };

  const handleSubmitApproval = () => {
    confirm({
      title: '提交审批',
      content: '确定要提交审批吗？提交后将无法编辑。',
      onOk() {
        message.success('已提交审批');
        fetchQuoteDetail();
      }
    });
  };

  const itemColumns = [
    {
      title: '序号',
      dataIndex: 'key',
      key: 'key',
      width: 60,
      align: 'center'
    },
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '规格',
      dataIndex: 'specification',
      key: 'specification'
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right'
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 60,
      align: 'center'
    },
    {
      title: '单价',
      dataIndex: 'unitPrice',
      key: 'unitPrice',
      width: 100,
      align: 'right',
      render: (value) => `¥${value.toLocaleString()}`
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (value) => `¥${value.toLocaleString()}`
    }
  ];

  const tabItems = [
    {
      key: 'details',
      label: '报价详情',
      children: quoteData && (
        <div>
          <Descriptions bordered column={{ xs: 1, sm: 2, md: 2, lg: 3 }}>
            <Descriptions.Item label="报价单号">{quoteData.id}</Descriptions.Item>
            <Descriptions.Item label="版本号">{quoteData.version}</Descriptions.Item>
            <Descriptions.Item label="报价类型">{quoteData.type}</Descriptions.Item>
            <Descriptions.Item label="客户名称">{quoteData.customer.name}</Descriptions.Item>
            <Descriptions.Item label="联系人">{quoteData.customer.contact}</Descriptions.Item>
            <Descriptions.Item label="联系电话">{quoteData.customer.phone}</Descriptions.Item>
            <Descriptions.Item label="电子邮箱">{quoteData.customer.email}</Descriptions.Item>
            <Descriptions.Item label="客户地址" span={2}>{quoteData.customer.address}</Descriptions.Item>
            <Descriptions.Item label="付款条件">{quoteData.financial.paymentTerms}</Descriptions.Item>
            <Descriptions.Item label="有效期至">{quoteData.financial.validUntil}</Descriptions.Item>
            <Descriptions.Item label="币种">{quoteData.financial.currency}</Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">报价明细</Divider>
          <Table
            columns={itemColumns}
            dataSource={quoteData.items}
            pagination={false}
            footer={() => (
              <div style={{ textAlign: 'right' }}>
                <Space direction="vertical" size="small" style={{ width: 300 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>小计：</Text>
                    <Text strong>¥{quoteData.financial.subtotal.toLocaleString()}</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>折扣：</Text>
                    <Text type="danger">-¥{quoteData.financial.discount.toLocaleString()}</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>税额：</Text>
                    <Text>¥{quoteData.financial.tax.toLocaleString()}</Text>
                  </div>
                  <Divider style={{ margin: '8px 0' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Title level={5} style={{ margin: 0 }}>总计：</Title>
                    <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                      ¥{quoteData.financial.total.toLocaleString()}
                    </Title>
                  </div>
                </Space>
              </div>
            )}
          />

          <Divider orientation="left">附件</Divider>
          <Space direction="vertical">
            {quoteData.attachments.map((file, index) => (
              <div key={index}>
                <FileTextOutlined /> {file.name} ({file.size}) - {file.uploadTime}
                <Button type="link" size="small">下载</Button>
              </div>
            ))}
          </Space>
        </div>
      )
    },
    {
      key: 'timeline',
      label: '审批记录',
      children: quoteData && (
        <Timeline
          items={quoteData.timeline.map(item => ({
            color: item.status === 'success' ? 'green' : item.status === 'processing' ? 'blue' : 'gray',
            dot: item.status === 'success' ? <CheckCircleOutlined /> : <ClockCircleOutlined />,
            children: (
              <div>
                <Text strong>{item.action}</Text>
                <br />
                <Text type="secondary">{item.user} · {item.time}</Text>
                <br />
                <Text>{item.description}</Text>
              </div>
            )
          }))}
        />
      )
    },
    {
      key: 'comments',
      label: (
        <Badge count={quoteData?.comments.length || 0} offset={[10, 0]}>
          评论
        </Badge>
      ),
      children: quoteData && (
        <div>
          {quoteData.comments.map(comment => (
            <Card key={comment.id} style={{ marginBottom: 16 }} size="small">
              <Space align="start">
                <Avatar icon={<UserOutlined />} />
                <div style={{ flex: 1 }}>
                  <Space>
                    <Text strong>{comment.user}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{comment.time}</Text>
                  </Space>
                  <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
                    {comment.content}
                  </Paragraph>
                </div>
              </Space>
            </Card>
          ))}
        </div>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!quoteData) {
    return (
      <Result
        status="404"
        title="404"
        subTitle="抱歉，报价单不存在"
        extra={<Button type="primary" onClick={() => navigate('/quote-management')}>返回列表</Button>}
      />
    );
  }

  return (
    <div className="quote-detail">
      {/* 页面头部 */}
      <Card className="detail-header">
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
                返回
              </Button>
              <Divider type="vertical" />
              <Title level={4} style={{ margin: 0 }}>{quoteData.title}</Title>
              {getStatusTag(quoteData.status)}
            </Space>
          </Col>
          <Col>
            <Space>
              {quoteData.status === 'draft' && (
                <Button type="primary" icon={<SendOutlined />} onClick={handleSubmitApproval}>
                  提交审批
                </Button>
              )}
              <Button icon={<EditOutlined />} onClick={handleEdit}>
                编辑
              </Button>
              <Button icon={<CopyOutlined />}>
                复制
              </Button>
              <Button icon={<PrinterOutlined />} onClick={handlePrint}>
                打印
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                导出
              </Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                删除
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总金额" 
              value={quoteData.financial.total} 
              prefix={quoteData.financial.currency}
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="项目数" 
              value={quoteData.items.length}
              suffix="项"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="创建时间" 
              value={quoteData.createdAt}
              formatter={(value) => value}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="有效期至" 
              value={quoteData.financial.validUntil}
              formatter={(value) => value}
            />
          </Card>
        </Col>
      </Row>

      {/* 详情内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>
    </div>
  );
};

export default QuoteDetail;