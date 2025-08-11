import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import '../App.css';

const QuoteTypeSelection = () => {
  const navigate = useNavigate();

  const handleEngineeringQuote = () => {
    navigate('/engineering-quote');
  };

  const handleMassProductionQuote = () => {
    navigate('/mass-production-quote');
  };

  const handleApiTest = () => {
    navigate('/api-test');
  };

  const handleDatabaseManagement = () => {
    navigate('/hierarchical-database-management');
  };

  return (
    <div className="quote-type-container">
      {/* 页面标题区域 */}
      <div className="page-header">
        <h1 className="main-title">芯片测试小时费率报价系统</h1>
        <p className="sub-title">快速生成专业的芯片测试服务报价</p>
      </div>

      {/* 报价类型选择卡片区域 */}
      <div className="quote-type-cards">
        {/* 工程报价卡片 */}
        <div className="quote-type-card card">
          <h2 className="card-title">工程报价</h2>
          <p className="text">
            包含测试设备的小时费率报价，适用于研发阶段小批量测试
          </p>
          <PrimaryButton onClick={handleEngineeringQuote}>
            开始报价
          </PrimaryButton>
        </div>

        {/* 量产报价卡片 */}
        <div className="quote-type-card card">
          <h2 className="card-title">量产报价</h2>
          <p className="text">
            仅包含测试设备的小时费率报价，适用于量产阶段大批量测试
          </p>
          <PrimaryButton onClick={handleMassProductionQuote}>
            开始报价
          </PrimaryButton>
        </div>
      </div>

      {/* 管理功能按钮区域 */}
      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <SecondaryButton 
          onClick={handleApiTest}
          style={{ marginRight: '10px' }}
        >
          API测试
        </SecondaryButton>
        <SecondaryButton onClick={handleDatabaseManagement}>
          数据库管理
        </SecondaryButton>
      </div>

      {/* 页脚信息区域 */}
      <div className="page-footer">
        <p className="footer-text">© 2023 芯信安电子科技有限公司</p>
        <p className="footer-links">
          <a href="#help">使用帮助</a> | <a href="#contact">联系我们</a>
        </p>
      </div>
    </div>
  );
};

export default QuoteTypeSelection;