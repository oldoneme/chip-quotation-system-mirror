from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from .admin_auth import require_admin_auth
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin-management"])

@router.get("/user-management", response_class=HTMLResponse)
async def user_management_page(request: Request):
    """独立的用户管理页面 - 支持管理员认证"""
    
    # 检查是否已认证
    try:
        admin_token = request.cookies.get("admin_token")
        if admin_token:
            from .admin_auth import verify_admin_token
            admin_info = verify_admin_token(admin_token)
            if admin_info:
                # 已认证，显示用户管理页面
                return HTMLResponse(content=get_user_management_html())
    except:
        pass
    
    # 未认证，重定向到登录页面
    return RedirectResponse(url="/admin/login", status_code=302)

def get_user_management_html():
    """返回用户管理页面的HTML"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户权限管理 - 芯片测试报价系统</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://unpkg.com/antd@5.12.8/dist/antd.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/antd@5.12.8/dist/reset.css" />
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; }
        .admin-header {
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 16px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .admin-title { margin: 0; color: #333; }
        .logout-btn { background: #ff4d4f; border: none; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
        .content { padding: 0 24px; max-width: 1400px; margin: 0 auto; }
        .loading { text-align: center; padding: 40px; }
        .error { background: #fff2f0; border: 1px solid #ffccc7; border-radius: 6px; padding: 16px; margin: 20px 0; color: #cf1322; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h1 class="admin-title">🛡️ 用户权限管理系统</h1>
        <button class="logout-btn" onclick="logout()">退出登录</button>
    </div>
    <div class="content">
        <div id="app">
            <div class="loading">正在加载用户管理界面...</div>
        </div>
    </div>

    <script type="text/babel">
        const { useState, useEffect } = React;
        const { Table, Card, Button, Select, Switch, Tag, Space, Modal, message, Statistic, Row, Col, Typography } = antd;
        const { Title, Text } = Typography;
        const { Option } = Select;

        // 角色映射
        const ROLE_LABELS = {
            admin: '管理员',
            manager: '销售管理',
            user: '普通用户'
        };

        function UserManagement() {
            const [users, setUsers] = useState([]);
            const [stats, setStats] = useState(null);
            const [loading, setLoading] = useState(false);
            const [roleModalVisible, setRoleModalVisible] = useState(false);
            const [selectedUser, setSelectedUser] = useState(null);
            const [newRole, setNewRole] = useState('');

            useEffect(() => {
                fetchUsers();
                fetchStats();
            }, []);

            const fetchUsers = async () => {
                setLoading(true);
                try {
                    const response = await fetch('/api/users/', { credentials: 'include' });
                    if (response.ok) {
                        const data = await response.json();
                        setUsers(data);
                    } else {
                        message.error('获取用户列表失败');
                    }
                } catch (error) {
                    message.error('网络错误');
                }
                setLoading(false);
            };

            const fetchStats = async () => {
                try {
                    const response = await fetch('/api/users/stats', { credentials: 'include' });
                    if (response.ok) {
                        const data = await response.json();
                        setStats(data);
                    }
                } catch (error) {
                    console.error('获取统计失败:', error);
                }
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
                    const response = await fetch(`/api/users/\${selectedUser.id}/role`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify(newRole)
                    });

                    const result = await response.json();
                    if (response.ok) {
                        message.success(result.message);
                        fetchUsers();
                        fetchStats();
                    } else {
                        message.error(result.detail || '更新失败');
                    }
                } catch (error) {
                    message.error('网络错误');
                }

                setRoleModalVisible(false);
            };

            const handleStatusChange = async (userId, isActive) => {
                try {
                    const response = await fetch(`/api/users/\${userId}/status`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify(isActive)
                    });

                    const result = await response.json();
                    if (response.ok) {
                        message.success(result.message);
                        fetchUsers();
                        fetchStats();
                    } else {
                        message.error(result.detail || '更新失败');
                    }
                } catch (error) {
                    message.error('网络错误');
                }
            };

            const columns = [
                {
                    title: '用户信息',
                    dataIndex: 'name',
                    key: 'user_info',
                    render: (name, record) => (
                        <div>
                            <div style={{ fontWeight: 500 }}>{name}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                                {record.department} · {record.position}
                            </div>
                            {record.mobile && (
                                <div style={{ fontSize: '11px', color: '#999' }}>
                                    📱 {record.mobile}
                                </div>
                            )}
                        </div>
                    )
                },
                {
                    title: '角色',
                    dataIndex: 'role',
                    key: 'role',
                    render: (role, record) => (
                        <div>
                            <Tag color={role === 'admin' ? 'red' : role === 'manager' ? 'blue' : 'green'}>
                                {ROLE_LABELS[role]}
                            </Tag>
                            <Button type="link" size="small" onClick={() => handleRoleChange(record)}>
                                修改
                            </Button>
                        </div>
                    )
                },
                {
                    title: '状态',
                    dataIndex: 'is_active',
                    key: 'status',
                    render: (isActive, record) => (
                        <Switch
                            checked={isActive}
                            onChange={(checked) => handleStatusChange(record.id, checked)}
                            checkedChildren="启用"
                            unCheckedChildren="禁用"
                            size="small"
                        />
                    )
                },
                {
                    title: '企业微信ID',
                    dataIndex: 'userid',
                    key: 'userid',
                    render: (userid) => <code style={{ fontSize: '11px' }}>{userid}</code>
                }
            ];

            return (
                <div>
                    {stats && (
                        <Row gutter={16} style={{ marginBottom: '24px' }}>
                            <Col span={6}>
                                <Card size="small">
                                    <Statistic title="总用户数" value={stats.total_users} />
                                </Card>
                            </Col>
                            <Col span={6}>
                                <Card size="small">
                                    <Statistic 
                                        title="管理员" 
                                        value={stats.role_distribution.admin} 
                                        valueStyle={{ color: '#ff4d4f' }}
                                    />
                                </Card>
                            </Col>
                            <Col span={6}>
                                <Card size="small">
                                    <Statistic 
                                        title="销售管理" 
                                        value={stats.role_distribution.manager} 
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col span={6}>
                                <Card size="small">
                                    <Statistic 
                                        title="普通用户" 
                                        value={stats.role_distribution.user} 
                                        valueStyle={{ color: '#52c41a' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    )}

                    <Card>
                        <div style={{ marginBottom: '16px' }}>
                            <Button onClick={fetchUsers} loading={loading}>刷新列表</Button>
                        </div>
                        
                        <Table
                            columns={columns}
                            dataSource={users}
                            rowKey="id"
                            loading={loading}
                            pagination={{
                                showSizeChanger: true,
                                showQuickJumper: true,
                                showTotal: (total, range) => 
                                    `第 \${range[0]}-\${range[1]} 条，共 \${total} 条记录`
                            }}
                        />
                    </Card>

                    <Modal
                        title="修改用户角色"
                        open={roleModalVisible}
                        onOk={handleUpdateRole}
                        onCancel={() => setRoleModalVisible(false)}
                        okText="确认修改"
                        cancelText="取消"
                    >
                        {selectedUser && (
                            <div>
                                <p><strong>用户：</strong>{selectedUser.name}</p>
                                <p><strong>当前角色：</strong>{ROLE_LABELS[selectedUser.role]}</p>
                                <div style={{ margin: '20px 0' }}>
                                    <label><strong>新角色：</strong></label>
                                    <Select
                                        value={newRole}
                                        onChange={setNewRole}
                                        style={{ width: '100%', marginTop: '8px' }}
                                    >
                                        <Option value="user">{ROLE_LABELS.user}</Option>
                                        <Option value="manager">{ROLE_LABELS.manager}</Option>
                                        <Option value="admin">{ROLE_LABELS.admin}</Option>
                                    </Select>
                                </div>
                            </div>
                        )}
                    </Modal>
                </div>
            );
        }

        // 渲染应用
        ReactDOM.render(<UserManagement />, document.getElementById('app'));

        // 退出登录
        async function logout() {
            try {
                await fetch('/admin/logout', { method: 'POST', credentials: 'include' });
                window.location.href = '/admin/login';
            } catch (error) {
                window.location.href = '/admin/login';
            }
        }
    </script>
</body>
</html>
    """