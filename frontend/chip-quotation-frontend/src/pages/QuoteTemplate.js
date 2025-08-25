import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Input, 
  Select, 
  Modal, 
  Form, 
  message,
  Tag,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Tooltip
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  CopyOutlined, 
  SearchOutlined,
  FileTextOutlined,
  LayoutOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import '../styles/QuoteTemplate.css';

const { Option } = Select;

const QuoteTemplate = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [filters, setFilters] = useState({
    searchText: '',
    type: 'all',
    status: 'all'
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [form] = Form.useForm();
  const [statistics, setStatistics] = useState({
    total: 0,
    active: 0,
    inactive: 0
  });

  // 模板类型
  const templateTypes = {
    inquiry: '询价报价',
    engineering: '工程报价',
    massProduction: '量产报价',
    tooling: '工装夹具报价',
    comprehensive: '综合报价'
  };

  // 模板状态
  const templateStatuses = {
    active: { text: '启用', color: 'success' },
    inactive: { text: '停用', color: 'default' }
  };

  useEffect(() => {
    loadTemplates();
  }, [filters]);

  const loadTemplates = () => {
    setLoading(true);
    // 模拟数据
    setTimeout(() => {
      const mockData = [
        {
          id: 1,
          name: '标准工程测试模板',
          type: 'engineering',
          description: '用于常规芯片工程测试的标准报价模板',
          status: 'active',
          config: {
            defaultMachines: ['J750', 'V93000'],
            defaultCards: ['Digital Board', 'Analog Board'],
            engineeringRate: 1.2,
            validDays: 30
          },
          createdBy: user?.name || '张三',
          createdAt: '2024-12-20 14:30',
          updatedAt: '2024-12-22 09:15',
          usageCount: 15
        },
        {
          id: 2,
          name: '快速询价模板',
          type: 'inquiry',
          description: '用于快速报价的简化模板',
          status: 'active',
          config: {
            defaultMachines: ['J750'],
            defaultCards: [],
            inquiryFactor: 0.8,
            validDays: 15
          },
          createdBy: user?.name || '李四',
          createdAt: '2024-12-21 10:00',
          updatedAt: '2024-12-23 16:30',
          usageCount: 28
        },
        {
          id: 3,
          name: '量产标准模板',
          type: 'massProduction',
          description: '大批量生产测试的标准配置',
          status: 'active',
          config: {
            defaultMachines: ['V93000', 'Handler-3000'],
            defaultCards: ['Digital Board'],
            productionRate: 0.9,
            validDays: 45
          },
          createdBy: user?.name || '王五',
          createdAt: '2024-12-19 11:20',
          updatedAt: '2024-12-20 14:00',
          usageCount: 8
        }
      ];

      // 应用筛选
      let filteredData = [...mockData];
      
      if (filters.type !== 'all') {
        filteredData = filteredData.filter(t => t.type === filters.type);
      }
      
      if (filters.status !== 'all') {
        filteredData = filteredData.filter(t => t.status === filters.status);
      }
      
      if (filters.searchText) {
        const searchLower = filters.searchText.toLowerCase();
        filteredData = filteredData.filter(t => 
          t.name.toLowerCase().includes(searchLower) ||
          t.description.toLowerCase().includes(searchLower)
        );
      }

      setTemplates(filteredData);

      // 更新统计数据
      setStatistics({
        total: mockData.length,
        active: mockData.filter(t => t.status === 'active').length,
        inactive: mockData.filter(t => t.status === 'inactive').length
      });

      setLoading(false);
    }, 500);
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    form.setFieldsValue({
      name: template.name,
      type: template.type,
      description: template.description,
      status: template.status
    });
    setModalVisible(true);
  };

  const handleSubmit = () => {
    form.validateFields().then(values => {
      if (editingTemplate) {
        message.success('模板已更新');
      } else {
        message.success('模板已创建');
      }
      setModalVisible(false);
      loadTemplates();
    }).catch(error => {
      console.error('表单验证失败:', error);
    });
  };

  const handleDelete = (id) => {
    message.success('模板已删除');
    loadTemplates();
  };

  const handleCopy = (template) => {
    setEditingTemplate(null);
    form.setFieldsValue({
      name: `${template.name} (副本)`,
      type: template.type,
      description: template.description,
      status: 'inactive'
    });
    setModalVisible(true);
  };

  const handleUseTemplate = (template) => {
    // 根据模板类型跳转到对应的报价页面
    const routeMap = {
      inquiry: '/inquiry-quote',
      engineering: '/engineering-quote',
      massProduction: '/mass-production-quote',
      tooling: '/tooling-quote',
      comprehensive: '/comprehensive-quote'
    };
    
    const route = routeMap[template.type];
    if (route) {
      // 传递模板配置给报价页面
      navigate(route, { 
        state: { 
          template: template,
          fromTemplate: true 
        } 
      });
    }
  };

  // 表格列配置
  const columns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#999' }}>
            使用次数：{record.usageCount}
          </div>
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type) => (
        <span style={{ fontSize: '13px' }}>{templateTypes[type]}</span>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: false,
      },
      render: (description) => (
        <Tooltip title={description}>
          <span>{description}</span>
        </Tooltip>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 70,
      render: (status) => (
        <Tag color={templateStatuses[status].color} size="small">
          {templateStatuses[status].text}
        </Tag>
      )
    },
    {
      title: '创建人',
      dataIndex: 'createdBy',
      key: 'createdBy',
      width: 80
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 120,
      render: (text) => (
        <span style={{ fontSize: '12px' }}>{text}</span>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small" wrap>
          <Button 
            type="primary" 
            size="small" 
            onClick={() => handleUseTemplate(record)}
            style={{ fontSize: '12px' }}
          >
            使用
          </Button>
          <Button 
            size="small" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
            style={{ fontSize: '12px' }}
          />
          <Button 
            size="small" 
            icon={<CopyOutlined />} 
            onClick={() => handleCopy(record)}
            style={{ fontSize: '12px' }}
          />
          <Popconfirm
            title="确定要删除这个模板吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              size="small" 
              danger 
              icon={<DeleteOutlined />}
              style={{ fontSize: '12px' }}
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div className="quote-template">
      {/* 页面标题 */}
      <div className="page-header">
        <h1>报价模板管理</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          新建模板
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col span={8}>
          <Card size="small">
            <Statistic 
              title="全部模板" 
              value={statistics.total}
              prefix={<LayoutOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic 
              title="启用中" 
              value={statistics.active}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic 
              title="已停用" 
              value={statistics.inactive}
              valueStyle={{ color: '#999' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和搜索栏 */}
      <Card className="filter-card">
        <Space size="middle" wrap>
          <Input
            placeholder="搜索模板名称或描述"
            prefix={<SearchOutlined />}
            style={{ width: 280 }}
            value={filters.searchText}
            onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
            allowClear
          />
          
          <Select
            placeholder="模板类型"
            style={{ width: 140 }}
            value={filters.type}
            onChange={(value) => setFilters({ ...filters, type: value })}
          >
            <Option value="all">全部类型</Option>
            {Object.entries(templateTypes).map(([key, value]) => (
              <Option key={key} value={key}>{value}</Option>
            ))}
          </Select>

          <Select
            placeholder="模板状态"
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Option value="all">全部状态</Option>
            <Option value="active">启用</Option>
            <Option value="inactive">停用</Option>
          </Select>
        </Space>
      </Card>

      {/* 模板表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={templates}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 创建/编辑模板对话框 */}
      <Modal
        title={editingTemplate ? '编辑模板' : '新建模板'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: 'active'
          }}
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>

          <Form.Item
            name="type"
            label="报价类型"
            rules={[{ required: true, message: '请选择报价类型' }]}
          >
            <Select placeholder="请选择报价类型">
              {Object.entries(templateTypes).map(([key, value]) => (
                <Option key={key} value={key}>{value}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="模板描述"
            rules={[{ required: true, message: '请输入模板描述' }]}
          >
            <Input.TextArea 
              rows={3} 
              placeholder="请输入模板描述" 
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="模板状态"
            rules={[{ required: true, message: '请选择模板状态' }]}
          >
            <Select>
              <Option value="active">启用</Option>
              <Option value="inactive">停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QuoteTemplate;