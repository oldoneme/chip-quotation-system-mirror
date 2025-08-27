import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Space, Tag, Input, Select, DatePicker, 
  Row, Col, Statistic, Tabs, Dropdown, message, Modal, Badge
} from 'antd';
import { 
  SearchOutlined, PlusOutlined, FilterOutlined, ExportOutlined,
  EditOutlined, DeleteOutlined, EyeOutlined, CopyOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined, DownloadOutlined, PrinterOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/QuoteManagement.css';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

const QuoteManagement = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  
  // 过滤器状态
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    type: 'all',
    dateRange: null
  });

  // 统计数据
  const [statistics, setStatistics] = useState({
    total: 0,
    draft: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  // 模拟数据
  const mockQuotes = [
    {
      id: 'QT202408001',
      title: '华为技术有限公司芯片测试报价',
      type: '量产机时报价',
      customer: '华为技术有限公司',
      amount: 1250000,
      currency: 'CNY',
      status: 'approved',
      createdBy: '张三',
      createdAt: '2024-08-20 14:30',
      updatedAt: '2024-08-21 10:15',
      validUntil: '2024-09-20'
    },
    {
      id: 'QT202408002',
      title: '中兴通讯工程测试报价',
      type: '工程机时报价',
      customer: '中兴通讯股份有限公司',
      amount: 850000,
      currency: 'CNY',
      status: 'pending',
      createdBy: '李四',
      createdAt: '2024-08-21 09:00',
      updatedAt: '2024-08-21 09:00',
      validUntil: '2024-09-21'
    },
    {
      id: 'QT202408003',
      title: '小米科技询价报价单',
      type: '询价报价',
      customer: '小米科技有限责任公司',
      amount: 450000,
      currency: 'CNY',
      status: 'draft',
      createdBy: '王五',
      createdAt: '2024-08-22 11:20',
      updatedAt: '2024-08-22 15:30',
      validUntil: '2024-09-22'
    },
    {
      id: 'QT202408004',
      title: 'OPPO综合测试服务报价',
      type: '综合报价',
      customer: 'OPPO广东移动通信有限公司',
      amount: 2100000,
      currency: 'CNY',
      status: 'approved',
      createdBy: '赵六',
      createdAt: '2024-08-18 13:45',
      updatedAt: '2024-08-19 16:20',
      validUntil: '2024-09-18'
    },
    {
      id: 'QT202408005',
      title: '比亚迪汽车芯片测试报价',
      type: '量产工序报价',
      customer: '比亚迪股份有限公司',
      amount: 180000,
      currency: 'USD',
      status: 'rejected',
      createdBy: '钱七',
      createdAt: '2024-08-19 10:00',
      updatedAt: '2024-08-20 14:00',
      validUntil: '2024-09-19'
    }
  ];

  useEffect(() => {
    fetchQuotes();
    calculateStatistics();
  }, []);

  const fetchQuotes = () => {
    setLoading(true);
    // 模拟API调用
    setTimeout(() => {
      setQuotes(mockQuotes);
      setLoading(false);
    }, 500);
  };

  const calculateStatistics = () => {
    // 计算统计数据
    const stats = mockQuotes.reduce((acc, quote) => {
      acc.total++;
      acc[quote.status]++;
      return acc;
    }, { total: 0, draft: 0, pending: 0, approved: 0, rejected: 0 });
    setStatistics(stats);
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
      fixed: 'left',
      width: 120,
      render: (text) => <a onClick={() => handleView(text)}>{text}</a>
    },
    {
      title: '报价标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true
    },
    {
      title: '报价类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => getTypeTag(type)
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      width: 180,
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status)
    },
    {
      title: '创建人',
      dataIndex: 'createdBy',
      key: 'createdBy',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150
    },
    {
      title: '有效期至',
      dataIndex: 'validUntil',
      key: 'validUntil',
      width: 120
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'edit',
                  icon: <EditOutlined />,
                  label: '编辑',
                  disabled: record.status !== 'draft'
                },
                {
                  key: 'copy',
                  icon: <CopyOutlined />,
                  label: '复制'
                },
                {
                  key: 'export',
                  icon: <ExportOutlined />,
                  label: '导出'
                },
                {
                  type: 'divider'
                },
                {
                  key: 'delete',
                  icon: <DeleteOutlined />,
                  label: '删除',
                  danger: true,
                  disabled: record.status === 'approved'
                }
              ],
              onClick: ({ key }) => handleAction(key, record)
            }}
          >
            <Button type="link">更多</Button>
          </Dropdown>
        </Space>
      )
    }
  ];

  const handleView = (id) => {
    navigate(`/quote-detail/${id}`);
  };

  const handleAction = (action, record) => {
    switch(action) {
      case 'edit':
        navigate(`/quote-edit/${record.id}`);
        break;
      case 'copy':
        handleCopy(record);
        break;
      case 'export':
        handleExport(record);
        break;
      case 'delete':
        handleDelete(record);
        break;
      default:
        break;
    }
  };

  const handleCopy = (record) => {
    message.success(`已复制报价单 ${record.id}`);
  };

  const handleExport = (record) => {
    message.success(`正在导出报价单 ${record.id}`);
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      content: `确定要删除报价单 ${record.id} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk() {
        message.success('删除成功');
        fetchQuotes();
      }
    });
  };

  const handleBatchExport = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要导出的报价单');
      return;
    }
    message.success(`正在导出 ${selectedRowKeys.length} 个报价单`);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys)
  };

  const tabItems = [
    { key: 'all', label: '全部', count: statistics.total },
    { key: 'draft', label: '草稿', count: statistics.draft },
    { key: 'pending', label: '待审批', count: statistics.pending },
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
    <div className="quote-management">
      {/* 页面标题 */}
      <div className="page-header">
        <h1>报价单管理</h1>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/quote-type-selection')}>
            新建报价单
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleBatchExport}>
            批量导出
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
              title="本月新增" 
              value={12}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 过滤器 */}
      <Card className="filter-card">
        <Space size="middle" wrap>
          <Search
            placeholder="搜索报价单号、标题、客户"
            allowClear
            style={{ width: 250 }}
            onSearch={(value) => setFilters({...filters, search: value})}
          />
          <Select
            placeholder="选择类型"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({...filters, type: value})}
          >
            <Option value="all">全部类型</Option>
            <Option value="询价报价">询价报价</Option>
            <Option value="工装夹具报价">工装夹具报价</Option>
            <Option value="工程机时报价">工程机时报价</Option>
            <Option value="量产机时报价">量产机时报价</Option>
            <Option value="量产工序报价">量产工序报价</Option>
            <Option value="综合报价">综合报价</Option>
          </Select>
          <RangePicker 
            placeholder={['开始日期', '结束日期']}
            onChange={(dates) => setFilters({...filters, dateRange: dates})}
          />
          <Button icon={<FilterOutlined />}>高级筛选</Button>
        </Space>
      </Card>

      {/* 标签页和表格 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={tabItems}
        />
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={quotes}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1500 }}
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