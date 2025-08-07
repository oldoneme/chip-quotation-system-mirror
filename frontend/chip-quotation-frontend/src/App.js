import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import QuoteTypeSelection from './pages/QuoteTypeSelection';
import EngineeringQuote from './pages/EngineeringQuote';
import MassProductionQuote from './pages/MassProductionQuote';
import QuoteResult from './pages/QuoteResult';
import DatabaseManagement from './pages/DatabaseManagement';
import HierarchicalDatabaseManagement from './pages/HierarchicalDatabaseManagement';
import ApiTest from './pages/ApiTest';
import './App.css';

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Layout className="site-layout">
          <Header className="site-layout-background" style={{ padding: 0 }} />
          <Content style={{ margin: '0 16px' }}>
            <div className="site-layout-background" style={{ padding: 24, minHeight: 360 }}>
              <Routes>
                <Route path="/" element={<QuoteTypeSelection />} />
                <Route path="/engineering-quote" element={<EngineeringQuote />} />
                <Route path="/mass-production-quote" element={<MassProductionQuote />} />
                <Route path="/quote-result" element={<QuoteResult />} />
                <Route path="/database-management" element={<DatabaseManagement />} />
                <Route path="/hierarchical-database-management" element={<HierarchicalDatabaseManagement />} />
                <Route path="/api-test" element={<ApiTest />} />
              </Routes>
            </div>
          </Content>
          <Footer style={{ textAlign: 'center' }}>芯片测试报价系统 ©2023</Footer>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;