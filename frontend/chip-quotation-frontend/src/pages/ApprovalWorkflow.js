import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Tag, Input, Select, DatePicker,
  Row, Col, Statistic, Tabs, Modal, message, Badge, Avatar,
  Timeline, Form, Radio, Divider, Alert, Progress,
  Tooltip, Dropdown, Descriptions
} from 'antd';
import { 
  CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
  UserOutlined, FileTextOutlined, SearchOutlined, FilterOutlined,
  CheckOutlined, CloseOutlined, RollbackOutlined, CommentOutlined,
  ExclamationCircleOutlined, TeamOutlined, SolutionOutlined,
  AuditOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/ApprovalWorkflow.css';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

const ApprovalWorkflow = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [approvalList, setApprovalList] = useState([]);
  const [activeTab, setActiveTab] = useState('pending');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [approvalModal, setApprovalModal] = useState(false);
  const [approvalForm] = Form.useForm();
  
  // 统计数据
  const [statistics, setStatistics] = useState({
    pending: 8,
    approved: 45,
    rejected: 3,
    total: 56,
    avgTime: '2.5天',
    onTime: '92%'
  });

  // 模拟审批数据
  const mockApprovals = [
    {
      id: 'AP202408001',
      quoteId: 'QT202408001',
      title: '华为技术有限公司芯片测试报价',
      type: '量产机时报价',
      amount: 1250000,
      currency: 'CNY',
      applicant: '张三',
      department: '销售部',
      submitTime: '2024-08-20 16:45',
      currentNode: '部门经理',
      currentApprover: '李经理',
      status: 'pending',
      priority: 'high',
      dueDate: '2024-08-23',
      progress: 50
    },
    {
      id: 'AP202408002',
      quoteId: 'QT202408002',
      title: '中兴通讯工程测试报价',
      type: '工程机时报价',
      amount: 850000,
      currency: 'CNY',
      applicant: '李四',
      department: '技术部',
      submitTime: '2024-08-21 09:00',
      currentNode: '技术总监',
      currentApprover: '王总监',
      status: 'pending',
      priority: 'normal',
      dueDate: '2024-08-24',
      progress: 30
    },
    {
      id: 'AP202408003',
      quoteId: 'QT202408003',
      title: '小米科技询价报价单',
      type: '询价报价',
      amount: 450000,
      currency: 'CNY',
      applicant: '王五',
      department: '销售部',
      submitTime: '2024-08-22 11:20',
      currentNode: '财务经理',
      currentApprover: '赵经理',
      status: 'pending',
      priority: 'urgent',
      dueDate: '2024-08-22',
      progress: 70
    }
  ];

  // 审批流程节点
  const workflowNodes = [
    { key: 'submit', title: '提交申请', user: '申请人' },
    { key: 'dept_manager', title: '部门经理审批', user: '部门经理' },
    { key: 'tech_review', title: '技术评审', user: '技术总监' },
    { key: 'finance_review', title: '财务审核', user: '财务经理' },
    { key: 'final_approval', title: '总经理审批', user: '总经理' },
    { key: 'complete', title: '审批完成', user: '系统' }
  ];

  useEffect(() => {
    fetchApprovals();
  }, [activeTab]);

  const fetchApprovals = () => {
    setLoading(true);
    setTimeout(() => {
      let filteredData = [...mockApprovals];
      if (activeTab !== 'all') {
        filteredData = filteredData.filter(item => {
          if (activeTab === 'pending') return item.status === 'pending';
          if (activeTab === 'myApproval') return item.currentApprover === user?.name;
          if (activeTab === 'mySubmit') return item.applicant === user?.name;
          return true;
        });
      }
      setApprovalList(filteredData);
      setLoading(false);
    }, 500);
  };

  const getPriorityTag = (priority) => {
    const config = {
      urgent: { color: 'error', text: '紧急' },
      high: { color: 'warning', text: '高' },
      normal: { color: 'default', text: '普通' },
      low: { color: 'default', text: '低' }
    };
    return <Tag color={config[priority]?.color}>{config[priority]?.text}</Tag>;
  };

  const getStatusTag = (status) => {
    const config = {
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已通过', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> },
      withdrawn: { color: 'default', text: '已撤回', icon: <RollbackOutlined /> }
    };
    const item = config[status];
    return <Tag color={item.color} icon={item.icon}>{item.text}</Tag>;
  };

  const columns = [
    {
      title: '审批编号',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      fixed: 'left',
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text}</a>
      )
    },
    {
      title: '报价单号',
      dataIndex: 'quoteId',
      key: 'quoteId',
      width: 120,
      render: (text) => (
        <a onClick={() => navigate(`/quote-detail/${text}`)}>{text}</a>
      )
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (amount, record) => (
        <span>{record.currency} {amount.toLocaleString()}</span>
      )
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => getPriorityTag(priority)
    },
    {
      title: '申请人',
      dataIndex: 'applicant',
      key: 'applicant',
      width: 100,
      render: (name) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          {name}
        </Space>
      )
    },
    {
      title: '当前节点',
      dataIndex: 'currentNode',
      key: 'currentNode',
      width: 120
    },
    {
      title: '当前审批人',
      dataIndex: 'currentApprover',
      key: 'currentApprover',
      width: 100
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress) => (
        <Progress percent={progress} size="small" />
      )
    },
    {
      title: '提交时间',
      dataIndex: 'submitTime',
      key: 'submitTime',
      width: 150
    },
    {
      title: '截止日期',
      dataIndex: 'dueDate',
      key: 'dueDate',
      width: 100,
      render: (date) => {
        const isOverdue = new Date(date) < new Date();
        return (
          <span style={{ color: isOverdue ? 'red' : 'inherit' }}>
            {date}
            {isOverdue && <ExclamationCircleOutlined style={{ marginLeft: 4 }} />}
          </span>
        );
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status)
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.status === 'pending' && record.currentApprover === user?.name && (
            <Button 
              type="primary" 
              size="small"
              onClick={() => handleApprove(record)}
            >
              审批
            </Button>
          )}
          <Button 
            type="link" 
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending' && record.applicant === user?.name && (
            <Button 
              type="link" 
              size="small"
              danger
              onClick={() => handleWithdraw(record)}
            >
              撤回
            </Button>
          )}
        </Space>
      )
    }
  ];

  const handleApprove = (record) => {
    setSelectedRecord(record);
    setApprovalModal(true);
    approvalForm.setFieldsValue({
      action: 'approve',
      comment: ''
    });
  };

  const handleViewDetail = (record) => {
    Modal.info({
      title: '审批详情',
      width: 800,
      content: (
        <div>
          <Descriptions bordered column={2} style={{ marginBottom: 16 }}>
            <Descriptions.Item label="审批编号">{record.id}</Descriptions.Item>
            <Descriptions.Item label="报价单号">{record.quoteId}</Descriptions.Item>
            <Descriptions.Item label="标题" span={2}>{record.title}</Descriptions.Item>
            <Descriptions.Item label="申请人">{record.applicant}</Descriptions.Item>
            <Descriptions.Item label="部门">{record.department}</Descriptions.Item>
            <Descriptions.Item label="金额">{record.currency} {record.amount.toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="优先级">{getPriorityTag(record.priority)}</Descriptions.Item>
          </Descriptions>
          
          <Divider orientation="left">审批流程</Divider>
          <Timeline>
            {workflowNodes.map((node, index) => (
              <Timeline.Item 
                key={node.key}
                color={index <= 2 ? 'green' : 'gray'}
                dot={index === 2 ? <ClockCircleOutlined /> : null}
              >
                <strong>{node.title}</strong> - {node.user}
                {index <= 2 && <Tag color="success" style={{ marginLeft: 8 }}>已完成</Tag>}
                {index === 2 && <Tag color="processing" style={{ marginLeft: 8 }}>进行中</Tag>}
              </Timeline.Item>
            ))}
          </Timeline>
        </div>
      )
    });
  };

  const handleWithdraw = (record) => {
    confirm({
      title: '确认撤回',
      content: `确定要撤回审批申请 ${record.id} 吗？`,
      onOk() {
        message.success('撤回成功');
        fetchApprovals();
      }
    });
  };

  const handleApprovalSubmit = () => {
    approvalForm.validateFields().then(values => {
      const action = values.action === 'approve' ? '通过' : '拒绝';
      message.success(`审批${action}成功`);
      setApprovalModal(false);
      fetchApprovals();
    });
  };

  const tabItems = [
    { key: 'all', label: '全部', count: statistics.total },
    { key: 'pending', label: '待审批', count: statistics.pending },
    { key: 'myApproval', label: '我的审批', count: 5 },
    { key: 'mySubmit', label: '我的申请', count: 12 }
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
        <h1>审批工作流</h1>
        <Space>
          <Button icon={<FilterOutlined />}>高级筛选</Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="待审批" 
              value={statistics.pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="已通过" 
              value={statistics.approved}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="已拒绝" 
              value={statistics.rejected}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="总数" 
              value={statistics.total}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="平均审批时长" 
              value={statistics.avgTime}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8} md={4}>
          <Card>
            <Statistic 
              title="按时完成率" 
              value={statistics.onTime}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 提示信息 */}
      <Alert
        message="待处理提醒"
        description={`您有 ${statistics.pending} 个待审批事项需要处理，其中 2 个即将到期`}
        type="warning"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      {/* 过滤器 */}
      <Card className="filter-card">
        <Space size="middle" wrap>
          <Search
            placeholder="搜索审批编号、报价单号、标题"
            allowClear
            style={{ width: 250 }}
            onSearch={(value) => console.log(value)}
          />
          <Select
            placeholder="优先级"
            style={{ width: 120 }}
            allowClear
          >
            <Option value="urgent">紧急</Option>
            <Option value="high">高</Option>
            <Option value="normal">普通</Option>
            <Option value="low">低</Option>
          </Select>
          <Select
            placeholder="审批节点"
            style={{ width: 150 }}
            allowClear
          >
            <Option value="dept_manager">部门经理</Option>
            <Option value="tech_review">技术评审</Option>
            <Option value="finance_review">财务审核</Option>
            <Option value="final_approval">总经理审批</Option>
          </Select>
          <RangePicker placeholder={['开始日期', '结束日期']} />
        </Space>
      </Card>

      {/* 表格 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={tabItems}
        />
        <Table
          columns={columns}
          dataSource={approvalList}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1800 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 审批弹窗 */}
      <Modal
        title="审批处理"
        open={approvalModal}
        onOk={handleApprovalSubmit}
        onCancel={() => setApprovalModal(false)}
        width={600}
      >
        <Form form={approvalForm} layout="vertical">
          <Form.Item label="审批信息">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="审批编号">{selectedRecord?.id}</Descriptions.Item>
              <Descriptions.Item label="报价单号">{selectedRecord?.quoteId}</Descriptions.Item>
              <Descriptions.Item label="申请人">{selectedRecord?.applicant}</Descriptions.Item>
              <Descriptions.Item label="金额">
                {selectedRecord?.currency} {selectedRecord?.amount.toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Form.Item>
          
          <Form.Item
            name="action"
            label="审批意见"
            rules={[{ required: true, message: '请选择审批意见' }]}
          >
            <Radio.Group>
              <Radio value="approve">
                <Space>
                  <CheckOutlined style={{ color: '#52c41a' }} />
                  同意
                </Space>
              </Radio>
              <Radio value="reject">
                <Space>
                  <CloseOutlined style={{ color: '#f5222d' }} />
                  拒绝
                </Space>
              </Radio>
            </Radio.Group>
          </Form.Item>
          
          <Form.Item
            name="comment"
            label="审批备注"
            rules={[{ required: true, message: '请输入审批备注' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入审批意见..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApprovalWorkflow;