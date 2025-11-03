import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button, Dropdown, Avatar, Space, Drawer } from 'antd';
import { HomeOutlined, DatabaseOutlined, CalculatorOutlined, BarChartOutlined, SearchOutlined, SettingOutlined, UnorderedListOutlined, ToolOutlined, UserOutlined, LogoutOutlined, MenuOutlined } from '@ant-design/icons';
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
      // 只根据屏幕宽度判断，不再强制企业微信使用移动端布局
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // 根据用户角色过滤菜单项
  const menuItems = React.useMemo(() => {
    // 基础菜单项
    const baseMenuItems = [
      {
        key: '/',
        icon: <HomeOutlined />,
        label: '首页',
      },
      {
        key: 'quotes',
        icon: <CalculatorOutlined />,
        label: '报价中心',
        children: [
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
        ],
      },
      {
        key: '/quote-management',
        icon: <UnorderedListOutlined />,
        label: '报价单管理',
      },
    ];

    let items = [...baseMenuItems];
    
    // 只有管理员和超级管理员能看到管理功能
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      const managementChildren = [
        {
          key: '/approval-workflow',
          label: '审批工作流',
        },
        {
          key: '/analytics',
          icon: <BarChartOutlined />,
          label: '数据分析',
        },
        {
          key: '/version-control',
          label: '版本管理',
        },
        {
          key: '/hierarchical-database-management',
          icon: <DatabaseOutlined />,
          label: '设备数据库管理',
        },
        {
          key: '/admin/database-quote-management',
          icon: <UnorderedListOutlined />,
          label: '报价单数据库管理',
        },
      ];

      // 只有超级管理员能看到用户管理
      if (user?.role === 'super_admin') {
        managementChildren.push({
          key: '/user-management',
          icon: <UserOutlined />,
          label: '用户管理',
        });
      }

      items.push({
        key: 'management',
        icon: <SettingOutlined />,
        label: '系统管理',
        children: managementChildren,
      });
    }
    
    
    return items;
  }, [user?.role]);

  const handleMenuClick = ({ key }) => {
    navigate(key);
    setDrawerVisible(false); // 关闭抽屉菜单
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: `${user?.name || '用户'} (${
        user?.role === 'super_admin' ? '超级管理员' : 
        user?.role === 'admin' ? '管理员' : 
        user?.role === 'manager' ? '经理' : '普通用户'
      })`,
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

        {/* Mobile Header Content */}
        {isMobile && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            width: '100%'
          }}>
            {/* Mobile User Info */}
            {user && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                color: 'white',
                flex: 1
              }}>
                <Avatar 
                  size="small" 
                  src={user?.avatar} 
                  icon={<UserOutlined />}
                />
                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  lineHeight: 1.2
                }}>
                  <span style={{ 
                    fontSize: '14px', 
                    fontWeight: '500',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: '150px'
                  }}>
                    {user?.name || '用户'}
                  </span>
                  <span style={{ 
                    fontSize: '11px', 
                    opacity: 0.8,
                    whiteSpace: 'nowrap'
                  }}>
                    {user?.role === 'super_admin' ? '超级管理员' : 
                     user?.role === 'admin' ? '管理员' : 
                     user?.role === 'manager' ? '经理' : '普通用户'}
                  </span>
                </div>
              </div>
            )}
            
            {/* Mobile Menu Button */}
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerVisible(true)}
              style={{ 
                color: 'white', 
                fontSize: '18px',
                flexShrink: 0
              }}
            />
          </div>
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
              {user?.role === 'super_admin' ? '超级管理员' : 
               user?.role === 'admin' ? '管理员' : 
               user?.role === 'manager' ? '经理' : '普通用户'}
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