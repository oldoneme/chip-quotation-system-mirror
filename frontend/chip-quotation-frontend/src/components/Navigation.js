import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button, Dropdown, Avatar, Space, Drawer } from 'antd';
import { HomeOutlined, DatabaseOutlined, ApiOutlined, CalculatorOutlined, BarChartOutlined, UserOutlined, LogoutOutlined, MenuOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import HelpModal from './HelpModal';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [isMobile, setIsMobile] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
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
    setDrawerVisible(false); // 关闭抽屉菜单
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
    <>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: isMobile ? '8px 12px' : '6px 24px',
        background: '#001529',
        borderBottom: '1px solid #f0f0f0',
        minHeight: isMobile ? '50px' : '64px'
      }}>
        {/* Logo and Title */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          {/* 显示企业微信用户信息 - 移动端隐藏 */}
          {!isMobile && user && user.name && sessionStorage.getItem('wework_authenticated') === 'true' && (
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
              fontSize: isMobile ? '1rem' : '1.5rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: isMobile ? '150px' : 'auto'
            }}
            onClick={() => navigate('/')}
          >
            芯片测试报价系统
          </div>
        </div>

        {/* Desktop Navigation Menu */}
        {!isMobile && (
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
        )}

        {/* Desktop Quick Actions and User Menu */}
        {!isMobile && (
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
        )}

        {/* Mobile Menu Button */}
        {isMobile && (
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setDrawerVisible(true)}
            style={{ color: 'white', fontSize: '18px' }}
          />
        )}
      </div>

      {/* Mobile Drawer Menu */}
      <Drawer
        title="菜单"
        placement="right"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={250}
      >
        {/* User Info in Drawer */}
        {user && (
          <div style={{ 
            padding: '16px', 
            borderBottom: '1px solid #f0f0f0',
            marginBottom: '16px'
          }}>
            <Avatar 
              size="large" 
              src={user?.avatar} 
              icon={<UserOutlined />}
              style={{ marginBottom: '8px' }}
            />
            <div style={{ fontWeight: 'bold' }}>{user?.name || '用户'}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {user?.role === 'admin' ? '管理员' : '普通用户'}
            </div>
            {sessionStorage.getItem('wework_authenticated') === 'true' && (
              <div style={{ fontSize: '12px', color: '#1890ff', marginTop: '4px' }}>
                企业微信用户
              </div>
            )}
          </div>
        )}

        {/* Mobile Menu */}
        <Menu
          mode="vertical"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none' }}
        />

        {/* Mobile Quick Actions */}
        <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', marginTop: '16px' }}>
          <Button 
            type="primary" 
            block
            onClick={() => {
              navigate('/engineering-quote');
              setDrawerVisible(false);
            }}
            style={{ marginBottom: '8px' }}
          >
            快速报价
          </Button>
          <HelpModal />
          <Button 
            danger
            block
            onClick={() => {
              logout();
              setDrawerVisible(false);
            }}
            style={{ marginTop: '8px' }}
          >
            退出登录
          </Button>
        </div>
      </Drawer>
    </>
  );
};

export default Navigation;