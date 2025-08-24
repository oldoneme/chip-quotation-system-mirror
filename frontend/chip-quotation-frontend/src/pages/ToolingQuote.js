import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { formatQuotePrice } from '../utils';
import '../App.css';

const ToolingQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMounted, setIsMounted] = useState(false);
  const [formData, setFormData] = useState({
    customerInfo: {
      companyName: '',
      contactPerson: '',
      phone: '',
      email: ''
    },
    projectInfo: {
      projectName: '',
      chipPackage: '',
      testType: '',
      productStyle: 'new'
    },
    toolingItems: [
      {
        id: 1,
        category: '',
        type: '',
        specification: '',
        quantity: 1,
        unitPrice: 0,
        totalPrice: 0
      }
    ],
    engineeringFees: {
      testProgramDevelopment: 0,
      fixtureDesign: 0,
      testValidation: 0,
      documentation: 0
    },
    productionSetup: {
      setupFee: 0,
      calibrationFee: 0,
      firstArticleInspection: 0
    },
    currency: 'CNY',
    paymentTerms: '30_days',
    deliveryTime: '',
    remarks: ''
  });

  const [toolingCategories] = useState({
    fixture: {
      label: '测试夹具',
      types: [
        { value: 'load_board', label: '负载板', basePrice: 8000 },
        { value: 'dib_board', label: 'DIB板', basePrice: 6000 },
        { value: 'socket', label: '测试座', basePrice: 3000 },
        { value: 'contactor', label: '探针卡', basePrice: 15000 }
      ]
    },
    hardware: {
      label: '硬件设备',
      types: [
        { value: 'handler_kit', label: '分选机套件', basePrice: 12000 },
        { value: 'test_head', label: '测试头', basePrice: 25000 },
        { value: 'interface_board', label: '接口板', basePrice: 4000 },
        { value: 'calibration_kit', label: '校准套件', basePrice: 8000 }
      ]
    },
    consumables: {
      label: '耗材配件',
      types: [
        { value: 'probe_needles', label: '探针', basePrice: 500 },
        { value: 'connector', label: '连接器', basePrice: 200 },
        { value: 'cable', label: '电缆', basePrice: 300 },
        { value: 'spare_parts', label: '备用配件', basePrice: 1000 }
      ]
    }
  });

  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' }
  ];

  const paymentTermOptions = [
    { value: '30_days', label: '30天' },
    { value: '60_days', label: '60天' },
    { value: '90_days', label: '90天' },
    { value: 'prepaid', label: '预付款' },
    { value: 'cod', label: '货到付款' }
  ];

  // 组件挂载和状态管理
  useEffect(() => {
    // 标记组件已挂载
    setIsMounted(true);
    
    // 检查是否从结果页返回
    const isFromResultPage = location.state?.fromResultPage;
    if (isFromResultPage) {
      const savedState = sessionStorage.getItem('toolingQuoteState');
      if (savedState) {
        try {
          const parsedState = JSON.parse(savedState);
          console.log('从 sessionStorage 恢复工装夹具报价状态:', parsedState);
          setFormData(parsedState);
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      sessionStorage.removeItem('toolingQuoteState');
      console.log('开始全新工装夹具报价流程');
    }
  }, [location.state?.fromResultPage]);

  // 保存状态到sessionStorage（只有在已挂载且不是从结果页面返回时才保存）
  useEffect(() => {
    if (isMounted && !location.state?.fromResultPage) {
      sessionStorage.setItem('toolingQuoteState', JSON.stringify(formData));
    }
  }, [formData, isMounted, location.state?.fromResultPage]);

  const addToolingItem = () => {
    const newItem = {
      id: formData.toolingItems.length + 1,
      category: '',
      type: '',
      specification: '',
      quantity: 1,
      unitPrice: 0,
      totalPrice: 0
    };
    setFormData(prev => ({
      ...prev,
      toolingItems: [...prev.toolingItems, newItem]
    }));
  };

  const removeToolingItem = (itemId) => {
    if (formData.toolingItems.length > 1) {
      setFormData(prev => ({
        ...prev,
        toolingItems: prev.toolingItems.filter(item => item.id !== itemId)
      }));
    }
  };

  const updateToolingItem = (itemId, field, value) => {
    setFormData(prev => ({
      ...prev,
      toolingItems: prev.toolingItems.map(item => {
        if (item.id === itemId) {
          let updatedItem = { ...item, [field]: value };
          
          if (field === 'category') {
            updatedItem = {
              ...updatedItem,
              type: '',
              unitPrice: 0,
              totalPrice: 0
            };
          } else if (field === 'type') {
            const selectedType = toolingCategories[item.category]?.types.find(t => t.value === value);
            const newUnitPrice = selectedType ? selectedType.basePrice : 0;
            updatedItem = {
              ...updatedItem,
              unitPrice: newUnitPrice
            };
            // 重新计算小计
            const quantity = parseFloat(updatedItem.quantity) || 0;
            updatedItem.totalPrice = quantity * newUnitPrice;
          } else if (field === 'quantity' || field === 'unitPrice') {
            // 确保数据类型正确并计算小计
            const quantity = parseFloat(updatedItem.quantity) || 0;
            const unitPrice = parseFloat(updatedItem.unitPrice) || 0;
            updatedItem.totalPrice = quantity * unitPrice;
          }
          
          return updatedItem;
        }
        return item;
      })
    }));
  };

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const calculateTotalCost = () => {
    const toolingTotal = formData.toolingItems.reduce((sum, item) => sum + item.totalPrice, 0);
    const engineeringTotal = Object.values(formData.engineeringFees).reduce((sum, fee) => sum + fee, 0);
    const productionTotal = Object.values(formData.productionSetup).reduce((sum, fee) => sum + fee, 0);
    
    return toolingTotal + engineeringTotal + productionTotal;
  };

  const handleSubmit = () => {
    const quoteData = {
      type: '工装夹具报价',
      number: `TL-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-${String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')}`,
      date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...formData,
      totalCost: calculateTotalCost(),
      generatedAt: new Date().toISOString()
    };

    navigate('/quote-result', { state: quoteData });
  };

  const handleBack = () => {
    // 保持当前状态并返回报价类型选择页面
    navigate('/quote-type-selection', { 
      state: { 
        preserveState: true,
        pageType: 'tooling-quote' 
      } 
    });
  };

  return (
    <div className="quote-container">
      <PageTitle 
        title="工装夹具报价" 
        subtitle="专业的测试工装和夹具定制服务" 
      />

      <div className="form-section">
        <h3>客户信息</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>公司名称 *</label>
            <input
              type="text"
              value={formData.customerInfo.companyName}
              onChange={(e) => handleInputChange('customerInfo', 'companyName', e.target.value)}
              placeholder="请输入公司名称"
              required
            />
          </div>
          <div className="form-group">
            <label>联系人 *</label>
            <input
              type="text"
              value={formData.customerInfo.contactPerson}
              onChange={(e) => handleInputChange('customerInfo', 'contactPerson', e.target.value)}
              placeholder="请输入联系人姓名"
              required
            />
          </div>
          <div className="form-group">
            <label>联系电话</label>
            <input
              type="tel"
              value={formData.customerInfo.phone}
              onChange={(e) => handleInputChange('customerInfo', 'phone', e.target.value)}
              placeholder="请输入联系电话"
            />
          </div>
          <div className="form-group">
            <label>邮箱地址</label>
            <input
              type="email"
              value={formData.customerInfo.email}
              onChange={(e) => handleInputChange('customerInfo', 'email', e.target.value)}
              placeholder="请输入邮箱地址"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>项目信息</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>项目名称 *</label>
            <input
              type="text"
              value={formData.projectInfo.projectName}
              onChange={(e) => handleInputChange('projectInfo', 'projectName', e.target.value)}
              placeholder="请输入项目名称"
              required
            />
          </div>
          <div className="form-group">
            <label>芯片封装 *</label>
            <input
              type="text"
              value={formData.projectInfo.chipPackage}
              onChange={(e) => handleInputChange('projectInfo', 'chipPackage', e.target.value)}
              placeholder="如：QFN48, BGA256等"
              required
            />
          </div>
          <div className="form-group">
            <label>测试类型 *</label>
            <select
              value={formData.projectInfo.testType}
              onChange={(e) => handleInputChange('projectInfo', 'testType', e.target.value)}
              required
            >
              <option value="">请选择测试类型</option>
              <option value="CP">CP测试</option>
              <option value="FT">FT测试</option>
              <option value="mixed">混合测试</option>
            </select>
          </div>
          <div className="form-group">
            <label>产品类型</label>
            <select
              value={formData.projectInfo.productStyle}
              onChange={(e) => handleInputChange('projectInfo', 'productStyle', e.target.value)}
            >
              <option value="new">全新产品</option>
              <option value="derivative">衍生产品</option>
              <option value="upgrade">升级改版</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <div className="section-header">
          <h3>工装夹具清单</h3>
          <SecondaryButton onClick={addToolingItem}>
            添加项目
          </SecondaryButton>
        </div>
        
        {formData.toolingItems.map((item, index) => (
          <div key={item.id} className="tooling-item-card">
            <div className="item-header">
              <h4>项目 {index + 1}</h4>
              {formData.toolingItems.length > 1 && (
                <button 
                  type="button"
                  className="remove-item-btn"
                  onClick={() => removeToolingItem(item.id)}
                >
                  删除
                </button>
              )}
            </div>
            
            <div className="form-grid">
              <div className="form-group">
                <label>类别 *</label>
                <select
                  value={item.category}
                  onChange={(e) => updateToolingItem(item.id, 'category', e.target.value)}
                  required
                >
                  <option value="">请选择类别</option>
                  {Object.entries(toolingCategories).map(([key, category]) => (
                    <option key={key} value={key}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>类型 *</label>
                <select
                  value={item.type}
                  onChange={(e) => updateToolingItem(item.id, 'type', e.target.value)}
                  disabled={!item.category}
                  required
                >
                  <option value="">请选择类型</option>
                  {item.category && toolingCategories[item.category]?.types.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>规格说明</label>
                <input
                  type="text"
                  value={item.specification}
                  onChange={(e) => updateToolingItem(item.id, 'specification', e.target.value)}
                  placeholder="请输入详细规格"
                />
              </div>
              
              <div className="form-group">
                <label>数量</label>
                <input
                  type="number"
                  value={item.quantity}
                  onChange={(e) => updateToolingItem(item.id, 'quantity', parseInt(e.target.value) || 1)}
                  min="1"
                />
              </div>
              
              <div className="form-group">
                <label>单价</label>
                <input
                  type="number"
                  value={item.unitPrice}
                  onChange={(e) => updateToolingItem(item.id, 'unitPrice', parseFloat(e.target.value) || 0)}
                  min="0"
                  step="0.01"
                />
              </div>
              
              <div className="form-group">
                <label>小计</label>
                <div className="price-display">
                  {currencies.find(c => c.value === formData.currency)?.symbol} {formatQuotePrice(item.totalPrice, formData.currency)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="form-section">
        <h3>工程费用</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>测试程序开发</label>
            <input
              type="number"
              value={formData.engineeringFees.testProgramDevelopment}
              onChange={(e) => handleInputChange('engineeringFees', 'testProgramDevelopment', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>夹具设计费</label>
            <input
              type="number"
              value={formData.engineeringFees.fixtureDesign}
              onChange={(e) => handleInputChange('engineeringFees', 'fixtureDesign', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>测试验证费</label>
            <input
              type="number"
              value={formData.engineeringFees.testValidation}
              onChange={(e) => handleInputChange('engineeringFees', 'testValidation', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>文档制作费</label>
            <input
              type="number"
              value={formData.engineeringFees.documentation}
              onChange={(e) => handleInputChange('engineeringFees', 'documentation', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>量产准备费用</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>生产准备费</label>
            <input
              type="number"
              value={formData.productionSetup.setupFee}
              onChange={(e) => handleInputChange('productionSetup', 'setupFee', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>设备校准费</label>
            <input
              type="number"
              value={formData.productionSetup.calibrationFee}
              onChange={(e) => handleInputChange('productionSetup', 'calibrationFee', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>首件检验费</label>
            <input
              type="number"
              value={formData.productionSetup.firstArticleInspection}
              onChange={(e) => handleInputChange('productionSetup', 'firstArticleInspection', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>报价条件</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>报价货币 *</label>
            <select
              value={formData.currency}
              onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
              required
            >
              {currencies.map(currency => (
                <option key={currency.value} value={currency.value}>
                  {currency.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>付款条件</label>
            <select
              value={formData.paymentTerms}
              onChange={(e) => setFormData(prev => ({ ...prev, paymentTerms: e.target.value }))}
            >
              {paymentTermOptions.map(term => (
                <option key={term.value} value={term.value}>
                  {term.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>交付周期</label>
            <input
              type="text"
              value={formData.deliveryTime}
              onChange={(e) => setFormData(prev => ({ ...prev, deliveryTime: e.target.value }))}
              placeholder="如：4-6周"
            />
          </div>
          <div className="form-group full-width">
            <label>备注说明</label>
            <textarea
              value={formData.remarks}
              onChange={(e) => setFormData(prev => ({ ...prev, remarks: e.target.value }))}
              placeholder="请输入其他要求或说明..."
              rows="3"
            />
          </div>
        </div>
      </div>

      <div className="quote-summary">
        <h3>报价汇总</h3>
        <div className="summary-breakdown">
          <div className="summary-item">
            <span>工装夹具费用：</span>
            <span>{currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice(formData.toolingItems.reduce((sum, item) => sum + item.totalPrice, 0), formData.currency)}
            </span>
          </div>
          <div className="summary-item">
            <span>工程费用：</span>
            <span>{currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice(Object.values(formData.engineeringFees).reduce((sum, fee) => sum + fee, 0), formData.currency)}
            </span>
          </div>
          <div className="summary-item">
            <span>量产准备费用：</span>
            <span>{currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice(Object.values(formData.productionSetup).reduce((sum, fee) => sum + fee, 0), formData.currency)}
            </span>
          </div>
          <div className="summary-item total">
            <span>总计：</span>
            <span className="summary-value">
              {currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice(calculateTotalCost(), formData.currency)}
            </span>
          </div>
        </div>
      </div>

      <div className="button-group">
        <SecondaryButton onClick={handleBack}>
          返回
        </SecondaryButton>
        <PrimaryButton onClick={handleSubmit}>
          生成报价单
        </PrimaryButton>
      </div>
    </div>
  );
};

export default ToolingQuote;