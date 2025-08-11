import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Navigation from './Navigation';
import Breadcrumb from './Breadcrumb';
import ErrorBoundary from './ErrorBoundary';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';
import QuoteTypeSelection from '../pages/QuoteTypeSelection';
import EngineeringQuote from '../pages/EngineeringQuote';
import MassProductionQuote from '../pages/MassProductionQuote';
import QuoteResult from '../pages/QuoteResult';
import DatabaseManagement from '../pages/DatabaseManagement';
import HierarchicalDatabaseManagement from '../pages/HierarchicalDatabaseManagement';
import ApiTest from '../pages/ApiTest';
import ApiTestSimple from '../pages/ApiTestSimple';

const { Header, Content, Footer } = Layout;

const AppContent = () => {
  // 现在可以安全地使用键盘快捷键，因为我们在Router内部
  useKeyboardShortcuts();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0 }}>
          <Navigation />
        </Header>
        <Content style={{ margin: '0 16px' }}>
          <div className="site-layout-background" style={{ padding: 24, minHeight: 360 }}>
            <ErrorBoundary>
              <Breadcrumb />
              <Routes>
                <Route path="/" element={<QuoteTypeSelection />} />
                <Route path="/engineering-quote" element={<EngineeringQuote />} />
                <Route path="/mass-production-quote" element={<MassProductionQuote />} />
                <Route path="/quote-result" element={<QuoteResult />} />
                <Route path="/database-management" element={<DatabaseManagement />} />
                <Route path="/hierarchical-database-management" element={<HierarchicalDatabaseManagement />} />
                <Route path="/api-test" element={<ApiTest />} />
                <Route path="/api-test-simple" element={<ApiTestSimple />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>芯片测试报价系统 ©2023</Footer>
      </Layout>
    </Layout>
  );
};

export default AppContent;