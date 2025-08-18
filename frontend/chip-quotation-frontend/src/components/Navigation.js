import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button, Dropdown, Avatar, Space } from 'antd';
import { HomeOutlined, DatabaseOutlined, ApiOutlined, CalculatorOutlined, BarChartOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import HelpModal from './HelpModal';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/engineering-quote',
      icon: <CalculatorOutlined />,
      label: '工程报价',
    },
    {
      key: '/mass-production-quote',
      icon: <BarChartOutlined />,
      label: '量产报价',
    },
    {
      key: '/hierarchical-database-management',
      icon: <DatabaseOutlined />,
      label: '数据库管理',
    },
    {
      key: '/api-test',
      icon: <ApiOutlined />,
      label: 'API测试',
    },
    {
      key: '/api-test-simple',
      icon: <ApiOutlined />,
      label: 'API简单测试',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: `${user?.name || '用户'} (${user?.role === 'admin' ? '管理员' : '普通用户'})`,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      padding: '6px 24px',
      background: '#001529',
      borderBottom: '1px solid #f0f0f0',
      minHeight: '64px'
    }}>
      {/* Logo and Title */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
        {/* 显示企业微信用户信息 */}
        {user && user.name && sessionStorage.getItem('wework_authenticated') === 'true' && (
          <div style={{ 
            color: '#1890ff', 
            fontSize: '0.7rem', 
            marginBottom: '1px',
            fontWeight: 'normal',
            whiteSpace: 'nowrap',
            lineHeight: 1.2
          }}>
            企业微信用户：{user.name} ({user.role === 'admin' ? '管理员' : '普通用户'})
          </div>
        )}
        <div 
          style={{ 
            color: 'white', 
            fontSize: window.innerWidth <= 768 ? '1rem' : '1.5rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            maxWidth: window.innerWidth <= 768 ? '150px' : 'auto'
          }}
          onClick={() => navigate('/')}
        >
芯片测试报价系统
        </div>
      </div>

      {/* Navigation Menu */}
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ 
          flex: 1, 
          justifyContent: 'center',
          borderBottom: 'none'
        }}
      />

      {/* Quick Actions and User Menu */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <HelpModal />
        <Button 
          type="primary" 
          size="small"
          onClick={() => navigate('/engineering-quote')}
        >
          快速报价
        </Button>
        
        {/* User Dropdown */}
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer', color: 'white', whiteSpace: 'nowrap' }}>
            <Avatar 
              size="small" 
              src={user?.avatar} 
              icon={<UserOutlined />}
            />
            <span style={{ whiteSpace: 'nowrap' }}>{user?.name || '用户'}</span>
          </Space>
        </Dropdown>
      </div>
    </div>
  );
};

export default Navigation;