import React from 'react';
import { Breadcrumb as AntBreadcrumb } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { HomeOutlined } from '@ant-design/icons';

const Breadcrumb = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 动态获取报价结果的父级页面
  const getQuoteResultParent = () => {
    // 尝试从location.state获取报价类型
    const quoteData = location.state;
    if (quoteData?.type) {
      switch (quoteData.type) {
        case '询价报价': return '/inquiry-quote';
        case '工程报价': return '/engineering-quote';
        case '量产报价': return '/mass-production-quote';
        case '工艺报价': return '/process-quote';
        case '工装夹具报价': return '/tooling-quote';
        case '综合报价': return '/comprehensive-quote';
        default: return '/quote-type-selection';
      }
    }
    
    // 尝试从sessionStorage获取报价数据
    const storedData = sessionStorage.getItem('quoteData') || 
                      sessionStorage.getItem('inquiryQuoteState') || 
                      sessionStorage.getItem('massProductionQuoteState') || 
                      sessionStorage.getItem('toolingQuoteState');
    
    if (storedData) {
      try {
        const parsedData = JSON.parse(storedData);
        const type = parsedData.type || parsedData.formData?.type;
        if (type) {
          switch (type) {
            case '询价报价': return '/inquiry-quote';
            case '工程报价': return '/engineering-quote';
            case '量产报价': return '/mass-production-quote';
            case '工艺报价': return '/process-quote';
            case '工装夹具报价': return '/tooling-quote';
            case '综合报价': return '/comprehensive-quote';
            default: return '/quote-type-selection';
          }
        }
      } catch (e) {
        console.error('解析sessionStorage数据失败:', e);
      }
    }
    
    // 默认返回报价类型选择页
    return '/quote-type-selection';
  };

  // 定义路由对应的面包屑配置
  const breadcrumbConfig = {
    '/': { title: '首页', icon: <HomeOutlined /> },
    '/quote-type-selection': { title: '报价类型选择', parent: '/' },
    '/inquiry-quote': { title: '询价报价', parent: '/quote-type-selection' },
    '/engineering-quote': { title: '工程报价', parent: '/quote-type-selection' },
    '/mass-production-quote': { title: '量产报价', parent: '/quote-type-selection' },
    '/process-quote': { title: '工艺报价', parent: '/quote-type-selection' },
    '/tooling-quote': { title: '工装夹具报价', parent: '/quote-type-selection' },
    '/comprehensive-quote': { title: '综合报价', parent: '/quote-type-selection' },
    '/quote-result': { title: '报价结果', parent: getQuoteResultParent() },
    '/database-management': { title: '数据库管理', parent: '/' },
    '/hierarchical-database-management': { title: '数据库管理', parent: '/' },
    '/api-test': { title: 'API测试', parent: '/' }
  };

  // 生成面包屑路径
  const generateBreadcrumbItems = (pathname) => {
    const items = [];
    
    // 特殊处理报价结果页面
    if (pathname === '/quote-result') {
      const parentPath = getQuoteResultParent();
      const parentConfig = breadcrumbConfig[parentPath];
      
      // 添加首页
      items.push({
        title: (
          <span 
            style={{ cursor: 'pointer' }}
            onClick={() => navigate('/')}
          >
            <HomeOutlined /> 首页
          </span>
        ),
        key: '/'
      });
      
      // 如果父页面不是首页，添加父页面
      if (parentPath !== '/' && parentConfig) {
        items.push({
          title: (
            <span 
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(parentPath)}
            >
              {parentConfig.title}
            </span>
          ),
          key: parentPath
        });
      }
      
      // 添加当前页面（报价结果）
      items.push({
        title: (
          <span style={{ cursor: 'pointer' }}>
            报价结果
          </span>
        ),
        key: pathname
      });
      
      return items;
    }
    
    // 其他页面使用原来的逻辑
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