import React, { useState, useEffect } from 'react';
import { Modal, Button, Space, Card, Descriptions, Tag } from 'antd';
import { BugOutlined, UserOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const DebugPanel = () => {
  const { user, setUser } = useAuth();
  const [visible, setVisible] = useState(false);
  const [debugMode, setDebugMode] = useState(false);

  useEffect(() => {
    try {
      // 检查URL参数是否包含debug=true
      const urlParams = new URLSearchParams(window.location.search);
      const isDebugMode = urlParams.get('debug') === 'true';
      setDebugMode(isDebugMode);
      
      // 如果是调试模式，在控制台输出提示
      if (isDebugMode) {
        console.log('%c🐛 调试模式已启用', 'color: #52c41a; font-size: 14px; font-weight: bold;');
        console.log('可用功能：权限切换、用户信息修改');
      }
    } catch (error) {
      console.warn('Debug panel URL parameter parsing failed:', error);
      setDebugMode(false);
    }
  }, []);

  // 模拟不同的用户数据
  const mockUsers = {
    'super_admin': {
      name: '超级管理员',
      role: 'super_admin',
      avatar: null,
      permissions: ['all']
    },
    'admin': {
      name: '系统管理员', 
      role: 'admin',
      avatar: null,
      permissions: ['quote_manage', 'user_manage', 'analytics']
    },
    'manager': {
      name: '项目经理',
      role: 'manager', 
      avatar: null,
      permissions: ['quote_manage', 'analytics']
    },
    'user': {
      name: '普通用户',
      role: 'user',
      avatar: null, 
      permissions: ['quote_view']
    }
  };

  const handleUserSwitch = (userType) => {
    const mockUser = mockUsers[userType];
    setUser(mockUser);
    console.log(`👤 用户已切换为: ${mockUser.name}`, mockUser);
  };

  if (!debugMode) {
    return null;
  }

  return (
    <>
      {/* 调试按钮 - 悬浮在右下角 */}
      <div style={{
        position: 'fixed',
        right: '20px',
        bottom: '20px',
        zIndex: 1000
      }}>
        <Button 
          type="primary" 
          shape="circle" 
          icon={<BugOutlined />}
          size="large"
          onClick={() => setVisible(true)}
          style={{
            backgroundColor: '#722ed1',
            borderColor: '#722ed1',
            boxShadow: '0 4px 12px rgba(114, 46, 209, 0.4)'
          }}
        />
      </div>

      {/* 调试面板模态框 */}
      <Modal
        title={
          <Space>
            <BugOutlined style={{ color: '#722ed1' }} />
            <span>开发者调试面板</span>
          </Space>
        }
        open={visible}
        onCancel={() => setVisible(false)}
        footer={[
          <Button key="close" onClick={() => setVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          
          {/* 当前用户信息 */}
          <Card title="当前用户信息" size="small">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="用户名">{user?.name || '未登录'}</Descriptions.Item>
              <Descriptions.Item label="角色">
                <Tag color={
                  user?.role === 'super_admin' ? 'red' :
                  user?.role === 'admin' ? 'orange' :
                  user?.role === 'manager' ? 'blue' : 'default'
                }>
                  {user?.role === 'super_admin' ? '超级管理员' :
                   user?.role === 'admin' ? '管理员' :
                   user?.role === 'manager' ? '经理' : '普通用户'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 快速切换用户 */}
          <Card title="快速切换用户" size="small">
            <Space wrap>
              <Button 
                type={user?.role === 'super_admin' ? 'primary' : 'default'}
                onClick={() => handleUserSwitch('super_admin')}
                icon={<UserOutlined />}
              >
                超级管理员
              </Button>
              <Button 
                type={user?.role === 'admin' ? 'primary' : 'default'}
                onClick={() => handleUserSwitch('admin')}
                icon={<UserOutlined />}
              >
                管理员
              </Button>
              <Button 
                type={user?.role === 'manager' ? 'primary' : 'default'}
                onClick={() => handleUserSwitch('manager')}
                icon={<UserOutlined />}
              >
                经理
              </Button>
              <Button 
                type={user?.role === 'user' ? 'primary' : 'default'}
                onClick={() => handleUserSwitch('user')}
                icon={<UserOutlined />}
              >
                普通用户
              </Button>
            </Space>
          </Card>

          {/* 权限测试说明 */}
          <Card title="权限说明" size="small">
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              <li><strong>超级管理员</strong>：所有功能权限</li>
              <li><strong>管理员</strong>：报价管理、审批工作流、数据分析、版本管理、数据库管理</li>  
              <li><strong>经理</strong>：报价管理、报价模板</li>
              <li><strong>普通用户</strong>：报价管理、报价模板</li>
            </ul>
          </Card>

          {/* 调试信息 */}
          <Card title="调试信息" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="调试模式">
                <Tag color="green">已启用 (?debug=true)</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="控制台日志">
                打开浏览器开发者工具查看详细日志
              </Descriptions.Item>
            </Descriptions>
          </Card>

        </Space>
      </Modal>
    </>
  );
};

export default DebugPanel;
