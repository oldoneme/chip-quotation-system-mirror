import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Descriptions,
  Row,
  Col,
  Statistic,
  Input,
  Select,
  message,
  Tooltip,
  Divider,
  Badge
} from 'antd';
import { 
  HistoryOutlined,
  BranchesOutlined,
  SwapOutlined,
  TagOutlined,
  GitlabOutlined,
  FileTextOutlined,
  UserOutlined,
  CalendarOutlined,
  EyeOutlined,
  ReloadOutlined,
  ForkOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import '../styles/VersionControl.css';

const { Search } = Input;
const { Option } = Select;

const VersionControl = () => {
  useAuth();
  const [loading, setLoading] = useState(false);
  const [versions, setVersions] = useState([]);
  const [compareModalVisible, setCompareModalVisible] = useState(false);
  const [versionDetailVisible, setVersionDetailVisible] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [filters, setFilters] = useState({
    quoteId: '',
    changeType: 'all',
    author: 'all'
  });
  const [statistics, setStatistics] = useState({
    totalVersions: 0,
    activeQuotes: 0,
    pendingChanges: 0,
    todayChanges: 0
  });

  const loadVersionData = useCallback(() => {
    setLoading(true);
    
    // 模拟版本数据
    setTimeout(() => {
      const mockVersions = [
        {
          id: 1,
          quoteId: 'QT-20241224-001',
          version: '1.3',
          title: '5G射频芯片测试报价',
          changeType: 'major',
          author: '张三',
          createdAt: '2024-12-24 14:30',
          description: '更新设备配置，增加J750测试机',
          status: 'approved',
          changes: [
            { field: '设备配置', oldValue: 'V93000', newValue: 'V93000 + J750', type: 'modified' },
            { field: '总费用', oldValue: '¥480,000', newValue: '¥580,000', type: 'modified' }
          ],
          tags: ['production', 'approved'],
          parentVersion: '1.2',
          branches: []
        },
        {
          id: 2,
          quoteId: 'QT-20241224-001',
          version: '1.2',
          title: '5G射频芯片测试报价',
          changeType: 'minor',
          author: '张三',
          createdAt: '2024-12-23 16:45',
          description: '调整测试参数和时间估算',
          status: 'approved',
          changes: [
            { field: '测试时间', oldValue: '8小时', newValue: '10小时', type: 'modified' },
            { field: '参数配置', oldValue: '标准参数', newValue: '高精度参数', type: 'modified' }
          ],
          tags: ['testing'],
          parentVersion: '1.1',
          branches: []
        },
        {
          id: 3,
          quoteId: 'QT-20241224-002',
          version: '2.1',
          title: 'MCU芯片量产测试',
          changeType: 'major',
          author: '李四',
          createdAt: '2024-12-24 10:15',
          description: '重新设计测试方案，优化成本结构',
          status: 'pending',
          changes: [
            { field: '测试方案', oldValue: '全功能测试', newValue: '核心功能测试', type: 'modified' },
            { field: '测试数量', oldValue: '1000片', newValue: '10000片', type: 'modified' },
            { field: '单价', oldValue: '¥120', newValue: '¥95', type: 'modified' }
          ],
          tags: ['mass-production', 'cost-optimization'],
          parentVersion: '2.0',
          branches: ['feature/cost-reduction']
        },
        {
          id: 4,
          quoteId: 'QT-20241224-003',
          version: '1.1',
          title: 'AI芯片测试夹具',
          changeType: 'patch',
          author: '王五',
          createdAt: '2024-12-24 09:00',
          description: '修复价格计算错误',
          status: 'draft',
          changes: [
            { field: '材料成本', oldValue: '¥45,000', newValue: '¥42,000', type: 'modified' },
            { field: '备注', oldValue: '', newValue: '已核实供应商报价', type: 'added' }
          ],
          tags: ['bugfix'],
          parentVersion: '1.0',
          branches: []
        }
      ];

      // 应用筛选
      let filteredVersions = mockVersions;
      if (filters.quoteId) {
        filteredVersions = filteredVersions.filter(v => 
          v.quoteId.toLowerCase().includes(filters.quoteId.toLowerCase()) ||
          v.title.toLowerCase().includes(filters.quoteId.toLowerCase())
        );
      }
      if (filters.changeType !== 'all') {
        filteredVersions = filteredVersions.filter(v => v.changeType === filters.changeType);
      }
      if (filters.author !== 'all') {
        filteredVersions = filteredVersions.filter(v => v.author === filters.author);
      }

      setVersions(filteredVersions);
      setStatistics({
        totalVersions: mockVersions.length,
        activeQuotes: new Set(mockVersions.map(v => v.quoteId)).size,
        pendingChanges: mockVersions.filter(v => v.status === 'pending').length,
        todayChanges: mockVersions.filter(v => v.createdAt.includes('2024-12-24')).length
      });

      setLoading(false);
    }, 800);
  }, [filters]);

  useEffect(() => {
    loadVersionData();
  }, [loadVersionData]);

  const handleViewVersion = (record) => {
    setCurrentVersion(record);
    setVersionDetailVisible(true);
  };

  const handleCompareVersions = () => {
    if (selectedVersions.length !== 2) {
      message.warning('请选择两个版本进行比较');
      return;
    }
    setCompareModalVisible(true);
  };

  const handleRestoreVersion = (record) => {
    Modal.confirm({
      title: '恢复版本',
      content: `确定要将报价单恢复到版本 ${record.version} 吗？这将创建一个新版本。`,
      onOk: () => {
        message.success(`已恢复到版本 ${record.version}`);
        loadVersionData();
      }
    });
  };

  const handleCreateBranch = (record) => {
    Modal.confirm({
      title: '创建分支',
      content: `基于版本 ${record.version} 创建新的分支进行并行开发？`,
      onOk: () => {
        message.success('分支创建成功');
        loadVersionData();
      }
    });
  };

  // 变更类型配置
  const changeTypeConfig = {
    major: { text: '重大变更', color: 'red', icon: '🔴' },
    minor: { text: '功能变更', color: 'orange', icon: '🟡' },
    patch: { text: '修复变更', color: 'green', icon: '🟢' }
  };

  // 状态配置
  const statusConfig = {
    draft: { text: '草稿', color: 'default' },
    pending: { text: '待审核', color: 'processing' },
    approved: { text: '已批准', color: 'success' },
    rejected: { text: '已拒绝', color: 'error' }
  };

  // 表格列配置
  const columns = [
    {
      title: '报价单',
      key: 'quote',
      width: 200,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
            {record.quoteId}
          </div>
          <div style={{ fontSize: '12px', color: '#999' }}>
            {record.title}
          </div>
        </div>
      )
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (version, record) => (
        <div style={{ textAlign: 'center' }}>
          <Tag icon={<TagOutlined />} color="blue">
            v{version}
          </Tag>
          {record.tags.includes('production') && (
            <div style={{ marginTop: '4px' }}>
              <Badge status="success" text="生产" />
            </div>
          )}
        </div>
      )
    },
    {
      title: '变更类型',
      dataIndex: 'changeType',
      key: 'changeType',
      width: 100,
      render: (type) => (
        <Tag color={changeTypeConfig[type].color}>
          {changeTypeConfig[type].icon} {changeTypeConfig[type].text}
        </Tag>
      )
    },
    {
      title: '变更描述',
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
      width: 80,
      render: (status) => (
        <Tag color={statusConfig[status].color}>
          {statusConfig[status].text}
        </Tag>
      )
    },
    {
      title: '作者',
      key: 'author',
      width: 100,
      render: (_, record) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserOutlined style={{ color: '#1890ff' }} />
          <span>{record.author}</span>
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      render: (time) => (
        <div style={{ fontSize: '12px' }}>
          <CalendarOutlined style={{ marginRight: '4px', color: '#999' }} />
          {time}
        </div>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small" wrap>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewVersion(record)}
          >
            查看
          </Button>
          <Button 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={() => handleRestoreVersion(record)}
          >
            恢复
          </Button>
          <Button 
            size="small" 
            icon={<ForkOutlined />}
            onClick={() => handleCreateBranch(record)}
          >
            分支
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className="version-control">
      {/* 页面标题 */}
      <div className="page-header">
        <div className="header-left">
          <h1>版本管理</h1>
          <span className="subtitle">跟踪和管理报价单的版本变更</span>
        </div>
        <Space>
          <Button 
            type="primary" 
            icon={<SwapOutlined />}
            onClick={handleCompareVersions}
            disabled={selectedVersions.length !== 2}
          >
            比较版本
          </Button>
          <Button icon={<BranchesOutlined />}>
            分支管理
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col span={6}>
          <Card size="small">
            <Statistic 
              title="总版本数" 
              value={statistics.totalVersions}
              prefix={<HistoryOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic 
              title="活跃报价单" 
              value={statistics.activeQuotes}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic 
              title="待审核变更" 
              value={statistics.pendingChanges}
              valueStyle={{ color: '#fa8c16' }}
              prefix={<GitlabOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic 
              title="今日变更" 
              value={statistics.todayChanges}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选区域 */}
      <Card className="filter-card">
        <Space size="middle" wrap>
          <Search
            placeholder="搜索报价单号或标题"
            style={{ width: 280 }}
            value={filters.quoteId}
            onChange={(e) => setFilters({ ...filters, quoteId: e.target.value })}
            allowClear
          />
          
          <Select
            placeholder="变更类型"
            style={{ width: 140 }}
            value={filters.changeType}
            onChange={(value) => setFilters({ ...filters, changeType: value })}
          >
            <Option value="all">全部类型</Option>
            <Option value="major">重大变更</Option>
            <Option value="minor">功能变更</Option>
            <Option value="patch">修复变更</Option>
          </Select>

          <Select
            placeholder="作者"
            style={{ width: 120 }}
            value={filters.author}
            onChange={(value) => setFilters({ ...filters, author: value })}
          >
            <Option value="all">全部作者</Option>
            <Option value="张三">张三</Option>
            <Option value="李四">李四</Option>
            <Option value="王五">王五</Option>
          </Select>
        </Space>
      </Card>

      {/* 版本表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={versions}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          rowSelection={{
            selectedRowKeys: selectedVersions,
            onChange: setSelectedVersions,
            type: 'checkbox'
          }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 版本详情模态框 */}
      <Modal
        title={
          <Space>
            <HistoryOutlined />
            版本详情
          </Space>
        }
        open={versionDetailVisible}
        onCancel={() => setVersionDetailVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setVersionDetailVisible(false)}>
            关闭
          </Button>,
          <Button key="restore" type="primary" icon={<ReloadOutlined />}>
            恢复此版本
          </Button>
        ]}
      >
        {currentVersion && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="报价单号">{currentVersion.quoteId}</Descriptions.Item>
              <Descriptions.Item label="版本号">v{currentVersion.version}</Descriptions.Item>
              <Descriptions.Item label="变更类型">
                <Tag color={changeTypeConfig[currentVersion.changeType].color}>
                  {changeTypeConfig[currentVersion.changeType].text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusConfig[currentVersion.status].color}>
                  {statusConfig[currentVersion.status].text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="作者">{currentVersion.author}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{currentVersion.createdAt}</Descriptions.Item>
              <Descriptions.Item label="变更描述" span={2}>
                {currentVersion.description}
              </Descriptions.Item>
            </Descriptions>

            <Divider>变更详情</Divider>

            <Table
              columns={[
                { title: '字段', dataIndex: 'field', key: 'field' },
                { title: '原值', dataIndex: 'oldValue', key: 'oldValue' },
                { title: '新值', dataIndex: 'newValue', key: 'newValue' },
                { 
                  title: '操作类型', 
                  dataIndex: 'type', 
                  key: 'type',
                  render: (type) => (
                    <Tag color={type === 'added' ? 'green' : type === 'modified' ? 'orange' : 'red'}>
                      {type === 'added' ? '新增' : type === 'modified' ? '修改' : '删除'}
                    </Tag>
                  )
                }
              ]}
              dataSource={currentVersion.changes}
              pagination={false}
              size="small"
            />
          </div>
        )}
      </Modal>

      {/* 版本比较模态框 */}
      <Modal
        title={
          <Space>
            <SwapOutlined />
            版本比较
          </Space>
        }
        open={compareModalVisible}
        onCancel={() => setCompareModalVisible(false)}
        width={1000}
        footer={[
          <Button key="close" onClick={() => setCompareModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div>比较功能开发中...</div>
      </Modal>
    </div>
  );
};

export default VersionControl;
