/**
 * 数据库报价单管理页面
 * 管理员专用 - 包含软删除数据的完整报价单管理
 */
import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Select,
  Input,
  Space,
  Tag,
  Modal,
  Checkbox,
  message,
  Statistic,
  Row,
  Col,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  DeleteOutlined,
  RollbackOutlined, // 使用RollbackOutlined代替RollbackOutlined
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import {
  getAllQuotes,
  getDetailedStatistics,
  hardDeleteQuote,
  batchRestoreQuotes,
  batchSoftDeleteQuotes
} from '../services/adminApi';

const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;

const DatabaseQuoteManagement = () => {
  const { user } = useAuth();
  const [quotes, setQuotes] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [filters, setFilters] = useState({
    include_deleted: false,
    status_filter: '',
    search: ''
  });

  // 检查管理员权限
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const isSuperAdmin = user?.role === 'super_admin' || user?.role === 'admin'; // 临时允许admin也能硬删除

  useEffect(() => {
    if (!isAdmin) {
      message.error('需要管理员权限才能访问此页面');
      return;
    }
    loadData();
  }, [isAdmin, filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadData = async () => {
    setLoading(true);
    try {
      const [quotesData, statsData] = await Promise.all([
        getAllQuotes({
          include_deleted: filters.include_deleted,
          status_filter: filters.status_filter,
          page: 1,
          size: 100 // 获取更多数据用于管理
        }),
        getDetailedStatistics()
      ]);

      setQuotes(quotesData.items || []);
      setStatistics(statsData);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 硬删除确认
  const handleHardDelete = (record) => {
    if (!isSuperAdmin) {
      message.error('只有超级管理员才能执行硬删除操作');
      return;
    }

    confirm({
      title: '确认硬删除',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>警告：硬删除操作不可恢复！</strong></p>
          <p>报价单: {record.quote_number} - {record.title}</p>
          <p>客户: {record.customer_name}</p>
          <p>金额: {record.total_amount} {record.currency}</p>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await hardDeleteQuote(record.id);
          message.success('硬删除成功');
          loadData();
        } catch (error) {
          message.error('硬删除失败');
        }
      },
    });
  };

  // 批量操作
  const handleBatchOperation = (operation) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要操作的报价单');
      return;
    }

    const selectedQuotes = quotes.filter(quote => selectedRowKeys.includes(quote.id));

    if (operation === 'restore') {
      confirm({
        title: `确认恢复 ${selectedQuotes.length} 个报价单？`,
        content: '恢复后报价单将重新显示在正常列表中',
        onOk: async () => {
          try {
            await batchRestoreQuotes(selectedRowKeys);
            message.success(`成功恢复 ${selectedRowKeys.length} 个报价单`);
            setSelectedRowKeys([]);
            loadData();
          } catch (error) {
            message.error('批量恢复失败');
          }
        },
      });
    } else if (operation === 'soft_delete') {
      confirm({
        title: `确认软删除 ${selectedQuotes.length} 个报价单？`,
        content: '软删除后可以通过恢复功能找回',
        onOk: async () => {
          try {
            await batchSoftDeleteQuotes(selectedRowKeys);
            message.success(`成功删除 ${selectedRowKeys.length} 个报价单`);
            setSelectedRowKeys([]);
            loadData();
          } catch (error) {
            message.error('批量删除失败');
          }
        },
      });
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '报价单号',
      dataIndex: 'quote_number',
      key: 'quote_number',
      width: 180,
      fixed: 'left',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {record.is_deleted && (
            <Tag color="red" size="small">已删除</Tag>
          )}
        </Space>
      )
    },
    {
      title: '标题/客户',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <span title={text}>{text}</span>
          <span style={{ fontSize: '12px', color: '#666' }}>
            {record.customer_name}
          </span>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'quote_type',
      key: 'quote_type',
      width: 100,
      render: (type) => {
        const typeMap = {
          inquiry: { text: '询价', color: 'blue' },
          tooling: { text: '工装', color: 'green' },
          engineering: { text: '工程', color: 'orange' },
          mass_production: { text: '量产', color: 'purple' },
          process: { text: '工序', color: 'cyan' },
          comprehensive: { text: '综合', color: 'magenta' }
        };
        const config = typeMap[type] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      align: 'right',
      render: (amount, record) => (
        <span style={{ fontWeight: 'bold' }}>
          {amount?.toLocaleString()} {record.currency}
        </span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusMap = {
          draft: { text: '草稿', color: 'default' },
          pending: { text: '待审批', color: 'processing' },
          approved: { text: '已批准', color: 'success' },
          rejected: { text: '已拒绝', color: 'error' }
        };
        const config = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '创建信息',
      key: 'creator_info',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontSize: '12px' }}>
            {record.creator_name || '未知'}
          </span>
          <span style={{ fontSize: '11px', color: '#999' }}>
            {record.created_at ? new Date(record.created_at).toLocaleDateString() : ''}
          </span>
        </Space>
      )
    },
    {
      title: '删除信息',
      key: 'delete_info',
      width: 150,
      render: (_, record) => {
        if (!record.is_deleted) return '-';
        return (
          <Space direction="vertical" size={0}>
            <span style={{ fontSize: '12px', color: '#f5222d' }}>
              {record.deleter_name || '未知'}
            </span>
            <span style={{ fontSize: '11px', color: '#999' }}>
              {record.deleted_at ? new Date(record.deleted_at).toLocaleDateString() : ''}
            </span>
          </Space>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          {record.is_deleted ? (
            <Tooltip title="恢复报价单">
              <Button
                type="link"
                size="small"
                icon={<RollbackOutlined />}
                onClick={() => handleBatchOperation('restore')}
                disabled={!selectedRowKeys.includes(record.id)}
              />
            </Tooltip>
          ) : (
            <Tooltip title="软删除报价单">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => {
                  setSelectedRowKeys([record.id]);
                  setTimeout(() => handleBatchOperation('soft_delete'), 100);
                }}
              />
            </Tooltip>
          )}

          {isSuperAdmin && (
            <Tooltip title="硬删除（不可恢复）">
              <Popconfirm
                title="确认硬删除？"
                description="此操作不可恢复！"
                onConfirm={() => handleHardDelete(record)}
                okText="确认"
                cancelText="取消"
                okType="danger"
              >
                <Button
                  type="link"
                  size="small"
                  danger
                  icon={<ExclamationCircleOutlined />}
                />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record) => ({
      disabled: false,
      name: record.quote_number,
    }),
  };

  if (!isAdmin) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <ExclamationCircleOutlined style={{ fontSize: '48px', color: '#ff4d4f' }} />
          <h2>权限不足</h2>
          <p>您需要管理员权限才能访问此页面</p>
        </div>
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="数据库报价单管理" style={{ marginBottom: '24px' }}>
        <div style={{ marginBottom: '16px' }}>
          <p style={{ color: '#666', marginBottom: '8px' }}>
            <InfoCircleOutlined /> 管理员专用页面，可查看包含软删除在内的所有报价单数据
          </p>
          <div style={{ fontSize: '12px', color: '#999', padding: '8px', background: '#f5f5f5', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              📋 当前用户: {user?.name || '未知'} | 角色: {user?.role || '未知'} |
              权限: {isAdmin ? '✅ 管理员' : '❌ 普通用户'} |
              {isSuperAdmin ?
                <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>🔥 超级管理员 (可硬删除)</span> :
                <span style={{ color: '#faad14' }}>⚠️ 硬删除需要超级管理员权限</span>
              }
            </span>
            <Button size="small" onClick={() => window.location.reload()} style={{ fontSize: '10px' }}>
              🔄 刷新认证
            </Button>
          </div>
        </div>

        {/* 统计信息 */}
        {statistics && (
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="总报价单"
                  value={statistics.all_data?.total || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="正常报价单"
                  value={statistics.normal_data?.total || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="已删除报价单"
                  value={statistics.deleted_data?.total || 0}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="待审批"
                  value={filters.include_deleted
                    ? (statistics.normal_data?.pending || 0) + (statistics.deleted_data?.pending || 0)
                    : (statistics.normal_data?.pending || 0)
                  }
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* 操作栏 */}
        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={16}>
            <Space>
              <Search
                placeholder="搜索报价单号、标题、客户名称"
                style={{ width: 300 }}
                onSearch={(value) => setFilters({ ...filters, search: value })}
                allowClear
              />

              <Select
                placeholder="状态筛选"
                style={{ width: 120 }}
                allowClear
                onChange={(value) => setFilters({ ...filters, status_filter: value || '' })}
              >
                <Option value="draft">草稿</Option>
                <Option value="pending">待审批</Option>
                <Option value="approved">已批准</Option>
                <Option value="rejected">已拒绝</Option>
              </Select>

              <Checkbox
                checked={filters.include_deleted}
                onChange={(e) => setFilters({ ...filters, include_deleted: e.target.checked })}
              >
                包含已删除
              </Checkbox>

              <Button
                icon={<ReloadOutlined />}
                onClick={loadData}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>

          <Col span={8} style={{ textAlign: 'right' }}>
            <Space>
              {selectedRowKeys.length > 0 && (
                <>
                  <span style={{ color: '#666' }}>
                    已选择 {selectedRowKeys.length} 项
                  </span>

                  <Button
                    type="primary"
                    size="small"
                    icon={<RollbackOutlined />}
                    onClick={() => handleBatchOperation('restore')}
                    disabled={!quotes.some(q => selectedRowKeys.includes(q.id) && q.is_deleted)}
                  >
                    批量恢复
                  </Button>

                  <Button
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={() => handleBatchOperation('soft_delete')}
                    disabled={!quotes.some(q => selectedRowKeys.includes(q.id) && !q.is_deleted)}
                  >
                    批量删除
                  </Button>
                </>
              )}
            </Space>
          </Col>
        </Row>

        {/* 数据表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={quotes}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            total: quotes.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          rowClassName={(record) => record.is_deleted ? 'deleted-row' : ''}
        />
      </Card>

      <style jsx>{`
        .deleted-row {
          background-color: #fff1f0;
        }
        .deleted-row:hover {
          background-color: #ffebe8 !important;
        }
      `}</style>
    </div>
  );
};

export default DatabaseQuoteManagement;