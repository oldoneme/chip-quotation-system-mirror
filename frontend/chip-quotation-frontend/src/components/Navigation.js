import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Button } from 'antd';
import { HomeOutlined, DatabaseOutlined, ApiOutlined, CalculatorOutlined, BarChartOutlined } from '@ant-design/icons';
import HelpModal from './HelpModal';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
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

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      padding: '0 24px',
      background: '#001529',
      borderBottom: '1px solid #f0f0f0'
    }}>
      {/* Logo and Title */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div 
          style={{ 
            color: 'white', 
            fontSize: '1.5rem', 
            fontWeight: 'bold',
            cursor: 'pointer'
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

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <HelpModal />
        <Button 
          type="primary" 
          size="small"
          onClick={() => navigate('/engineering-quote')}
        >
          快速报价
        </Button>
      </div>
    </div>
  );
};

export default Navigation;