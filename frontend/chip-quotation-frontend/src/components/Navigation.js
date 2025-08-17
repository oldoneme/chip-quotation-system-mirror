import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button, Dropdown, Avatar, Space, Drawer } from 'antd';
import { HomeOutlined, DatabaseOutlined, CalculatorOutlined, BarChartOutlined, SearchOutlined, SettingOutlined, UnorderedListOutlined, AppstoreOutlined, ToolOutlined, UserOutlined, LogoutOutlined, MenuOutlined } from '@ant-design/icons';
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
      key: '/inquiry-quote',
      icon: <SearchOutlined />,
      label: '询价报价',
    },
    {
      key: '/tooling-quote',
      icon: <ToolOutlined />,
      label: '工装夹具报价',
    },
    {
      key: '/engineering-quote',
      icon: <CalculatorOutlined />,
      label: '工程机时报价',
    },
    {
      key: '/mass-production-quote',
      icon: <BarChartOutlined />,
      label: '量产机时报价',
    },
    {
      key: '/process-quote',
      icon: <UnorderedListOutlined />,
      label: '量产工序报价',
    },
    {
      key: '/comprehensive-quote',
      icon: <SettingOutlined />,
      label: '综合报价',
    },
    {
      key: '/hierarchical-database-management',
      icon: <DatabaseOutlined />,
      label: '数据库管理',
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