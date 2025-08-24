import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import '../App.css';

const QuoteTypeSelection = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // 检查是否需要保持状态并直接返回到对应页面
  useEffect(() => {
    const preserveState = location.state?.preserveState;
    const pageType = location.state?.pageType;
    
    if (preserveState && pageType) {
      // 如果需要保持状态，直接导航到对应页面，传递保持状态标志
      switch (pageType) {
        case 'inquiry-quote':
          navigate('/inquiry-quote', { state: { fromResultPage: true } });
          break;
        case 'tooling-quote':
          navigate('/tooling-quote', { state: { fromResultPage: true } });
          break;
        case 'process-quote':
          navigate('/process-quote', { state: { fromResultPage: true } });
          break;
        case 'comprehensive-quote':
          navigate('/comprehensive-quote', { state: { fromResultPage: true } });
          break;
        default:
          break;
      }
    }
  }, [location.state, navigate]);

  const handleInquiryQuote = () => {
    navigate('/inquiry-quote');
  };

  const handleToolingQuote = () => {
    navigate('/tooling-quote');
  };

  const handleProcessQuote = () => {
    navigate('/process-quote');
  };

  const handleComprehensiveQuote = () => {
    navigate('/comprehensive-quote');
  };

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
        <h1 className="main-title">芯片测试报价系统</h1>
        <p className="sub-title">快速生成专业的芯片测试服务报价</p>
      </div>

      {/* 第一阶段：未合作阶段询价 */}
      <div className="quote-section">
        <h2 className="section-title">📋 初步询价</h2>
        <p className="stage-description">初步接触，快速了解价格范围</p>
        <div className="quote-type-cards">
          {/* 询价报价卡片 */}
          <div className="quote-type-card card inquiry-stage">
            <h2 className="card-title">询价报价</h2>
            <p className="text">
              快速获取参考价格，非正式报价，适用于初步咨询和商务洽谈
            </p>
            <PrimaryButton onClick={handleInquiryQuote}>
              开始询价
            </PrimaryButton>
          </div>
        </div>
      </div>

      {/* 第二阶段：待合作阶段机时报价 */}
      <div className="quote-section">
        <h2 className="section-title">⚡ 机时报价</h2>
        <p className="stage-description">项目确定，详细技术方案和成本评估</p>
        <div className="quote-type-cards">
          {/* 工装夹具报价卡片 */}
          <div className="quote-type-card card cooperation-stage">
            <h2 className="card-title">工装夹具报价</h2>
            <p className="text">
              专业的测试工装和夹具定制服务，包含设计开发和制作费用
            </p>
            <PrimaryButton onClick={handleToolingQuote}>
              工装报价
            </PrimaryButton>
          </div>

          {/* 工程机时报价卡片 */}
          <div className="quote-type-card card cooperation-stage">
            <h2 className="card-title">工程机时报价</h2>
            <p className="text">
              包含测试设备的小时费率报价，适用于研发阶段小批量测试
            </p>
            <PrimaryButton onClick={handleEngineeringQuote}>
              工程机时报价
            </PrimaryButton>
          </div>

          {/* 量产机时报价卡片 */}
          <div className="quote-type-card card cooperation-stage">
            <h2 className="card-title">量产机时报价</h2>
            <p className="text">
              规模化测试服务机时报价，适用于量产阶段大批量测试的机时费率
            </p>
            <PrimaryButton onClick={handleMassProductionQuote}>
              量产机时报价
            </PrimaryButton>
          </div>
        </div>
      </div>

      {/* 第三阶段：合作阶段量产报价 */}
      <div className="quote-section">
        <h2 className="section-title">🏭 量产单颗报价</h2>
        <p className="stage-description">长期合作，规模化生产和协议式定价</p>
        <div className="quote-type-cards">
          {/* 量产工序报价卡片 */}
          <div className="quote-type-card card production-stage">
            <h2 className="card-title">量产工序报价</h2>
            <p className="text">
              基于生产工序的单颗芯片报价，精确的成本分析和量产定价
            </p>
            <PrimaryButton onClick={handleProcessQuote}>
              量产工序报价
            </PrimaryButton>
          </div>

          {/* 综合报价卡片 */}
          <div className="quote-type-card card production-stage">
            <h2 className="card-title">综合报价方案</h2>
            <p className="text">
              灵活的协议式报价框架，支持套餐、分级、合约等多种定价模式
            </p>
            <PrimaryButton onClick={handleComprehensiveQuote}>
              综合报价
            </PrimaryButton>
          </div>
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