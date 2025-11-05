import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Select,
  Switch,
  Tag,
  Space,
  Modal,
  message,
  Statistic,
  Row,
  Col,
  Typography,
  Tooltip,
  Divider,
  Badge
} from 'antd';
import {
  UserOutlined,
  CrownOutlined,
  TeamOutlined,
  EditOutlined,
  UserSwitchOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { usePermissions } from '../hooks/usePermissions';
import { PERMISSIONS, ROLE_LABELS } from '../config/permissions';
import '../styles/UserManagement.css';

const { Title, Text } = Typography;
const { Option } = Select;

const UserManagement = () => {
  const { user } = useAuth();
  const { checkPermission } = usePermissions();
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newRole, setNewRole] = useState('');

  // 权限检查 - 移动 hooks 到检查之前
  const hasPermission = checkPermission(PERMISSIONS.USER_MANAGE);

  useEffect(() => {
    if (hasPermission) {
      fetchUsers();
      fetchStats();
    }
  }, [hasPermission]);

  // 如果没有权限，返回无权限页面
  if (!hasPermission) {
    return (
      <div className="user-management-no-permission">
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <UserOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
            <Title level={3}>权限不足</Title>
            <Text type="secondary">您没有权限访问用户管理功能</Text>
          </div>
        </Card>
      </div>
    );
  }

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/users/', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else if (response.status === 403) {
        message.error('权限不足：仅管理员可访问');
      } else {
        message.error('获取用户列表失败');
      }
    } catch (error) {
      console.error('获取用户列表失败:', error);
      message.error('网络错误，获取用户列表失败');
    }
    setLoading(false);
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/users/stats', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('获取用户统计失败:', error);
    }
  };

  const handleSyncFromWecom = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/users/sync-from-wecom', {
        method: 'POST',
        credentials: 'include'
      });

      const result = await response.json();

      if (response.ok && result.success) {
        message.success(result.message);
        // 同步成功后刷新用户列表和统计
        fetchUsers();
        fetchStats();
      } else {
        message.error(result.message || '从企业微信同步用户失败');
      }
    } catch (error) {
      console.error('从企业微信同步用户失败:', error);
      message.error('网络错误，同步用户失败');
    }
    setLoading(false);
  };

  const handleRoleChange = (record) => {
    setSelectedUser(record);
    setNewRole(record.role);
    setRoleModalVisible(true);
  };

  const handleUpdateRole = async () => {
    if (!selectedUser || newRole === selectedUser.role) {
      setRoleModalVisible(false);
      return;
    }

    try {
      const response = await fetch(`/api/v1/users/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(newRole)
      });

      const result = await response.json();

      if (response.ok) {
        message.success(result.message);
        fetchUsers();
        fetchStats();
      } else {
        message.error(result.detail || '更新用户角色失败');
      }
    } catch (error) {
      console.error('更新用户角色失败:', error);
      message.error('网络错误，更新用户角色失败');
    }

    setRoleModalVisible(false);
  };

  const handleStatusChange = async (userId, isActive) => {
    try {
      const response = await fetch(`/api/v1/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(isActive)
      });

      const result = await response.json();

      if (response.ok) {
        message.success(result.message);
        fetchUsers();
        fetchStats();
      } else {
        message.error(result.detail || '更新用户状态失败');
      }
    } catch (error) {
      console.error('更新用户状态失败:', error);
      message.error('网络错误，更新用户状态失败');
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <CrownOutlined style={{ color: '#ff4d4f' }} />;
      case 'manager':
        return <TeamOutlined style={{ color: '#1890ff' }} />;
      default:
        return <UserOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'red';
      case 'manager':
        return 'blue';
      default:
        return 'green';
    }
  };

  const columns = [
    {
      title: '用户信息',
      dataIndex: 'name',
      key: 'user_info',
      width: 200,
      render: (name, record) => (
        <div className="user-info-cell">
          <div className="user-name">{name}</div>
          <div className="user-details">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.department} · {record.position}
            </Text>
          </div>
          {record.mobile && (
            <div className="user-contact">
              <Text type="secondary" style={{ fontSize: '11px' }}>
                📱 {record.mobile}
              </Text>
            </div>
          )}
        </div>
      )
    },
    {
      title: '角色权限',
      dataIndex: 'role',
      key: 'role',
      width: 150,
      render: (role, record) => (
        <div className="role-cell">
          <Tag
            icon={getRoleIcon(role)}
            color={getRoleColor(role)}
            className="role-tag"
          >
            {ROLE_LABELS[role]}
          </Tag>
          {record.id !== user?.id && (
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleRoleChange(record)}
              className="role-edit-btn"
            >
              修改
            </Button>
          )}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'status',
      width: 100,
      render: (isActive, record) => (
        <div className="status-cell">
          <Switch
            checked={isActive}
            disabled={record.id === user?.id}
            onChange={(checked) => handleStatusChange(record.id, checked)}
            checkedChildren="启用"
            unCheckedChildren="禁用"
            size="small"
          />
        </div>
      )
    },
    {
      title: '企业微信ID',
      dataIndex: 'userid',
      key: 'userid',
      width: 120,
      render: (userid) => (
        <Text code style={{ fontSize: '11px' }}>
          {userid}
        </Text>
      )
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 130,
      render: (lastLogin) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>
          {lastLogin 
            ? new Date(lastLogin).toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })
            : '未登录'
          }
        </Text>
      )
    }
  ];

  return (
    <div className="user-management-container">
      <div className="page-header">
        <Title level={2}>
          <UserSwitchOutlined /> 用户权限管理
        </Title>
        <Text type="secondary">
          管理系统用户的角色权限和访问状态
        </Text>
      </div>

      {stats && (
        <Row gutter={16} className="stats-row">
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="总用户数"
                value={stats.total_users}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="管理员"
                value={stats.role_distribution.admin}
                prefix={<CrownOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="销售管理"
                value={stats.role_distribution.manager}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="普通用户"
                value={stats.role_distribution.user}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card className="users-table-card">
        <div className="table-header">
          <Space>
            <Button
              onClick={handleSyncFromWecom}
              loading={loading}
              type="primary"
              ghost
            >
              从企业微信同步用户
            </Button>
          </Space>
        </div>
        
        <Divider />
        
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`
          }}
          className="users-table"
        />
      </Card>

      {/* 角色修改弹窗 */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            修改用户角色
          </Space>
        }
        open={roleModalVisible}
        onOk={handleUpdateRole}
        onCancel={() => setRoleModalVisible(false)}
        okText="确认修改"
        cancelText="取消"
      >
        {selectedUser && (
          <div>
            <p>
              <strong>用户：</strong>{selectedUser.name}
              <br />
              <strong>部门：</strong>{selectedUser.department} · {selectedUser.position}
              <br />
              <strong>当前角色：</strong>
              <Tag color={getRoleColor(selectedUser.role)}>
                {ROLE_LABELS[selectedUser.role]}
              </Tag>
            </p>
            
            <div style={{ margin: '20px 0' }}>
              <Text strong>新角色：</Text>
              <Select
                value={newRole}
                onChange={setNewRole}
                style={{ width: '100%', marginTop: '8px' }}
              >
                <Option value="user">
                  <Space>
                    <UserOutlined style={{ color: '#52c41a' }} />
                    {ROLE_LABELS.user}
                  </Space>
                </Option>
                <Option value="manager">
                  <Space>
                    <TeamOutlined style={{ color: '#1890ff' }} />
                    {ROLE_LABELS.manager}
                  </Space>
                </Option>
                <Option value="admin">
                  <Space>
                    <CrownOutlined style={{ color: '#ff4d4f' }} />
                    {ROLE_LABELS.admin}
                  </Space>
                </Option>
              </Select>
            </div>

            <div className="role-description">
              <Tooltip title="查看角色权限说明">
                <InfoCircleOutlined /> 角色权限说明
              </Tooltip>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                <div><strong>普通用户：</strong>所有报价功能 + 查看自己的数据</div>
                <div><strong>销售管理：</strong>所有报价功能 + 查看所有数据 + 订单管理</div>
                <div><strong>管理员：</strong>完全系统访问权限 + 用户管理</div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default UserManagement;