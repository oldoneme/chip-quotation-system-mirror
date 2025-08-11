import React from 'react';
import { Breadcrumb as AntBreadcrumb } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

const Breadcrumb = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 定义路由对应的面包屑配置
  const breadcrumbConfig = {
    '/': { title: '首页', icon: <HomeOutlined /> },
    '/engineering-quote': { title: '工程报价', parent: '/' },
    '/mass-production-quote': { title: '量产报价', parent: '/' },
    '/quote-result': { title: '报价结果', parent: '/engineering-quote' },
    '/database-management': { title: '数据库管理', parent: '/' },
    '/hierarchical-database-management': { title: '数据库管理', parent: '/' },
    '/api-test': { title: 'API测试', parent: '/' }
  };

  // 生成面包屑路径
  const generateBreadcrumbItems = (pathname) => {
    const items = [];
    const config = breadcrumbConfig[pathname];
    
    if (!config) return items;
    
    // 递归添加父级路径
    const addParentItems = (path) => {
      const pathConfig = breadcrumbConfig[path];
      if (pathConfig && pathConfig.parent) {
        addParentItems(pathConfig.parent);
      }
      
      if (pathConfig) {
        items.push({
          title: (
            <span 
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(path)}
            >
              {pathConfig.icon && pathConfig.icon} {pathConfig.title}
            </span>
          ),
          key: path
        });
      }
    };
    
    addParentItems(pathname);
    return items;
  };

  const breadcrumbItems = generateBreadcrumbItems(location.pathname);
  
  // 如果只有首页，不显示面包屑
  if (breadcrumbItems.length <= 1) {
    return null;
  }

  return (
    <div style={{ 
      marginBottom: 16,
      padding: '8px 0',
      background: 'rgba(255, 255, 255, 0.8)',
      borderRadius: 6
    }}>
      <AntBreadcrumb items={breadcrumbItems} />
    </div>
  );
};

export default Breadcrumb;