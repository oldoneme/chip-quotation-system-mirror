import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { formatQuotePrice } from '../utils';
import '../App.css';

const ComprehensiveQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMounted, setIsMounted] = useState(false);
  const [formData, setFormData] = useState({
    customerInfo: {
      companyName: '',
      contactPerson: '',
      phone: '',
      email: '',
      customerLevel: 'standard'
    },
    projectInfo: {
      projectName: '',
      projectType: 'new',
      chipPackage: '',
      complexity: 'medium',
      priority: 'normal',
      expectedVolume: 0,
      projectDuration: ''
    },
    quoteType: 'package',
    baseDataSelection: {
      referenceProject: '',
      baseTemplate: '',
      historicalData: ''
    },
    packageQuote: {
      testServices: [],
      engineeringServices: [],
      supportServices: [],
      packageDiscount: 0
    },
    volumeQuote: {
      volumeTiers: [
        { min: 0, max: 10000, unitPrice: 0, discount: 0 },
        { min: 10001, max: 50000, unitPrice: 0, discount: 0.05 },
        { min: 50001, max: 100000, unitPrice: 0, discount: 0.1 },
        { min: 100001, max: 999999999, unitPrice: 0, discount: 0.15 }
      ]
    },
    timeQuote: {
      contractDuration: 12,
      monthlyCommitment: 0,
      timeDiscount: 0,
      escalationRate: 0.03
    },
    customQuote: {
      customItems: [
        {
          id: 1,
          category: '',
          description: '',
          quantity: 1,
          unitPrice: 0,
          discount: 0,
          totalPrice: 0
        }
      ]
    },
    priceAdjustments: {
      urgencyMultiplier: 1.0,
      complexityMultiplier: 1.0,
      customerDiscount: 0,
      seasonalAdjustment: 0
    },
    agreementTerms: {
      validityPeriod: 180,
      paymentTerms: '30_days',
      deliveryTerms: 'standard',
      warrantyPeriod: 90,
      revisionPolicy: 'included',
      cancellationPolicy: 'standard'
    },
    currency: 'CNY',
    remarks: ''
  });

  const [availableServices] = useState({
    testServices: [
      { id: 'cp_test', name: 'CP测试服务', basePrice: 800, unit: '小时' },
      { id: 'ft_test', name: 'FT测试服务', basePrice: 900, unit: '小时' },
      { id: 'burn_in', name: '老化测试', basePrice: 200, unit: '小时' },
      { id: 'parametric', name: '参数测试', basePrice: 600, unit: '小时' }
    ],
    engineeringServices: [
      { id: 'program_dev', name: '程序开发', basePrice: 15000, unit: '项目' },
      { id: 'fixture_design', name: '夹具设计', basePrice: 8000, unit: '套' },
      { id: 'validation', name: '测试验证', basePrice: 5000, unit: '项目' },
      { id: 'documentation', name: '技术文档', basePrice: 3000, unit: '套' }
    ],
    supportServices: [
      { id: 'tech_support', name: '技术支持', basePrice: 500, unit: '小时' },
      { id: 'training', name: '操作培训', basePrice: 800, unit: '天' },
      { id: 'maintenance', name: '设备维护', basePrice: 300, unit: '小时' },
      { id: 'calibration', name: '设备校准', basePrice: 1200, unit: '次' }
    ]
  });

  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' },
    { value: 'EUR', label: '欧元 (EUR)', symbol: '€' }
  ];

  const paymentTermOptions = [
    { value: '15_days', label: '15天' },
    { value: '30_days', label: '30天' },
    { value: '60_days', label: '60天' },
    { value: '90_days', label: '90天' },
    { value: 'prepaid', label: '预付款' }
  ];

  // 组件挂载和状态管理
  useEffect(() => {
    // 标记组件已挂载
    setIsMounted(true);
    
    // 检查是否从结果页返回
    const isFromResultPage = location.state?.fromResultPage;
    if (isFromResultPage) {
      const savedState = sessionStorage.getItem('comprehensiveQuoteState');
      if (savedState) {
        try {
          const parsedState = JSON.parse(savedState);
          console.log('从 sessionStorage 恢复综合报价状态:', parsedState);
          setFormData(parsedState);
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      sessionStorage.removeItem('comprehensiveQuoteState');
      console.log('开始全新综合报价流程');
    }
  }, [location.state?.fromResultPage]);

  // 保存状态到sessionStorage（只有在已挂载且不是从结果页面返回时才保存）
  useEffect(() => {
    if (isMounted && !location.state?.fromResultPage) {
      sessionStorage.setItem('comprehensiveQuoteState', JSON.stringify(formData));
    }
  }, [formData, isMounted, location.state?.fromResultPage]);

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleServiceSelection = (serviceType, serviceId, isSelected) => {
    setFormData(prev => ({
      ...prev,
      packageQuote: {
        ...prev.packageQuote,
        [serviceType]: isSelected 
          ? [...prev.packageQuote[serviceType], serviceId]
          : prev.packageQuote[serviceType].filter(id => id !== serviceId)
      }
    }));
  };

  const updateVolumeTier = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      volumeQuote: {
        ...prev.volumeQuote,
        volumeTiers: prev.volumeQuote.volumeTiers.map((tier, i) => 
          i === index ? { ...tier, [field]: value } : tier
        )
      }
    }));
  };

  const addCustomItem = () => {
    const newItem = {
      id: formData.customQuote.customItems.length + 1,
      category: '',
      description: '',
      quantity: 1,
      unitPrice: 0,
      discount: 0,
      totalPrice: 0
    };
    setFormData(prev => ({
      ...prev,
      customQuote: {
        ...prev.customQuote,
        customItems: [...prev.customQuote.customItems, newItem]
      }
    }));
  };

  const removeCustomItem = (itemId) => {
    if (formData.customQuote.customItems.length > 1) {
      setFormData(prev => ({
        ...prev,
        customQuote: {
          ...prev.customQuote,
          customItems: prev.customQuote.customItems.filter(item => item.id !== itemId)
        }
      }));
    }
  };

  const updateCustomItem = (itemId, field, value) => {
    setFormData(prev => ({
      ...prev,
      customQuote: {
        ...prev.customQuote,
        customItems: prev.customQuote.customItems.map(item => {
          if (item.id === itemId) {
            const updatedItem = { ...item, [field]: value };
            if (field === 'quantity' || field === 'unitPrice' || field === 'discount') {
              const subtotal = updatedItem.quantity * updatedItem.unitPrice;
              updatedItem.totalPrice = subtotal * (1 - updatedItem.discount / 100);
            }
            return updatedItem;
          }
          return item;
        })
      }
    }));
  };

  const calculatePackageTotal = () => {
    let total = 0;
    
    Object.entries(availableServices).forEach(([serviceType, services]) => {
      services.forEach(service => {
        if (formData.packageQuote[serviceType].includes(service.id)) {
          total += service.basePrice;
        }
      });
    });
    
    return total * (1 - formData.packageQuote.packageDiscount / 100);
  };

  const calculateVolumeQuoteTotal = () => {
    const volume = formData.projectInfo.expectedVolume;
    const tier = formData.volumeQuote.volumeTiers.find(
      t => volume >= t.min && volume <= t.max
    );
    
    if (tier && tier.unitPrice > 0) {
      return volume * tier.unitPrice * (1 - tier.discount);
    }
    
    return 0;
  };

  const calculateTimeQuoteTotal = () => {
    const monthlyBase = formData.timeQuote.monthlyCommitment;
    const duration = formData.timeQuote.contractDuration;
    const discount = formData.timeQuote.timeDiscount / 100;
    
    let total = 0;
    for (let month = 1; month <= duration; month++) {
      const escalation = Math.pow(1 + formData.timeQuote.escalationRate, Math.floor((month - 1) / 12));
      total += monthlyBase * escalation;
    }
    
    return total * (1 - discount);
  };

  const calculateCustomQuoteTotal = () => {
    return formData.customQuote.customItems.reduce((sum, item) => sum + item.totalPrice, 0);
  };

  const calculateFinalTotal = () => {
    let baseTotal = 0;
    
    switch (formData.quoteType) {
      case 'package':
        baseTotal = calculatePackageTotal();
        break;
      case 'volume':
        baseTotal = calculateVolumeQuoteTotal();
        break;
      case 'time':
        baseTotal = calculateTimeQuoteTotal();
        break;
      case 'custom':
        baseTotal = calculateCustomQuoteTotal();
        break;
      default:
        baseTotal = 0;
    }
    
    const adjustments = formData.priceAdjustments;
    const multiplier = adjustments.urgencyMultiplier * adjustments.complexityMultiplier;
    const discount = (adjustments.customerDiscount + adjustments.seasonalAdjustment) / 100;
    
    return baseTotal * multiplier * (1 - discount);
  };

  const handleSubmit = () => {
    const quoteData = {
      type: '综合报价',
      number: `CQ-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-${String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')}`,
      date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...formData,
      calculatedTotals: {
        packageTotal: calculatePackageTotal(),
        volumeTotal: calculateVolumeQuoteTotal(),
        timeTotal: calculateTimeQuoteTotal(),
        customTotal: calculateCustomQuoteTotal(),
        finalTotal: calculateFinalTotal()
      },
      generatedAt: new Date().toISOString()
    };

    navigate('/quote-result', { state: quoteData });
  };

  const handleBack = () => {
    // 保持当前状态并返回报价类型选择页面
    navigate('/quote-type-selection', { 
      state: { 
        preserveState: true,
        pageType: 'comprehensive-quote' 
      } 
    });
  };

  return (
    <div className="quote-container">
      <PageTitle 
        title="综合报价方案" 
        subtitle="灵活的协议式报价框架" 
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
          <div className="form-group">
            <label>客户等级</label>
            <select
              value={formData.customerInfo.customerLevel}
              onChange={(e) => handleInputChange('customerInfo', 'customerLevel', e.target.value)}
            >
              <option value="standard">标准客户</option>
              <option value="premium">优质客户</option>
              <option value="strategic">战略客户</option>
              <option value="vip">VIP客户</option>
            </select>
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
            <label>项目类型</label>
            <select
              value={formData.projectInfo.projectType}
              onChange={(e) => handleInputChange('projectInfo', 'projectType', e.target.value)}
            >
              <option value="new">全新项目</option>
              <option value="upgrade">升级项目</option>
              <option value="maintenance">维护项目</option>
              <option value="research">研发项目</option>
            </select>
          </div>
          <div className="form-group">
            <label>芯片封装</label>
            <input
              type="text"
              value={formData.projectInfo.chipPackage}
              onChange={(e) => handleInputChange('projectInfo', 'chipPackage', e.target.value)}
              placeholder="如：QFN48, BGA256等"
            />
          </div>
          <div className="form-group">
            <label>项目复杂度</label>
            <select
              value={formData.projectInfo.complexity}
              onChange={(e) => handleInputChange('projectInfo', 'complexity', e.target.value)}
            >
              <option value="low">低复杂度</option>
              <option value="medium">中复杂度</option>
              <option value="high">高复杂度</option>
              <option value="critical">关键复杂度</option>
            </select>
          </div>
          <div className="form-group">
            <label>优先级</label>
            <select
              value={formData.projectInfo.priority}
              onChange={(e) => handleInputChange('projectInfo', 'priority', e.target.value)}
            >
              <option value="normal">正常</option>
              <option value="high">高优先级</option>
              <option value="urgent">紧急</option>
              <option value="critical">关键</option>
            </select>
          </div>
          <div className="form-group">
            <label>预期数量</label>
            <input
              type="number"
              value={formData.projectInfo.expectedVolume}
              onChange={(e) => handleInputChange('projectInfo', 'expectedVolume', parseInt(e.target.value) || 0)}
              min="0"
            />
          </div>
          <div className="form-group">
            <label>项目周期</label>
            <input
              type="text"
              value={formData.projectInfo.projectDuration}
              onChange={(e) => handleInputChange('projectInfo', 'projectDuration', e.target.value)}
              placeholder="如：6个月"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>报价类型选择</h3>
        <div className="quote-type-selector">
          {[
            { value: 'package', label: '套餐报价', desc: '预定义服务组合' },
            { value: 'volume', label: '数量分级报价', desc: '基于数量的阶梯定价' },
            { value: 'time', label: '时间合约报价', desc: '长期合作协议' },
            { value: 'custom', label: '自定义报价', desc: '完全自定义方案' }
          ].map(type => (
            <label key={type.value} className={`quote-type-option ${formData.quoteType === type.value ? 'selected' : ''}`}>
              <input
                type="radio"
                name="quoteType"
                value={type.value}
                checked={formData.quoteType === type.value}
                onChange={(e) => setFormData(prev => ({ ...prev, quoteType: e.target.value }))}
              />
              <div className="option-content">
                <h4>{type.label}</h4>
                <p>{type.desc}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {formData.quoteType === 'package' && (
        <div className="form-section">
          <h3>套餐服务选择</h3>
          {Object.entries(availableServices).map(([serviceType, services]) => (
            <div key={serviceType} className="service-category">
              <h4>{serviceType === 'testServices' ? '测试服务' : 
                   serviceType === 'engineeringServices' ? '工程服务' : '支持服务'}</h4>
              <div className="service-options">
                {services.map(service => (
                  <label key={service.id} className="service-option">
                    <input
                      type="checkbox"
                      checked={formData.packageQuote[serviceType].includes(service.id)}
                      onChange={(e) => handleServiceSelection(serviceType, service.id, e.target.checked)}
                    />
                    <div className="service-info">
                      <span className="service-name">{service.name}</span>
                      <span className="service-price">
                        {currencies.find(c => c.value === formData.currency)?.symbol}
                        {service.unit === '小时' ? formatQuotePrice(service.basePrice, formData.currency) : formatQuotePrice(service.basePrice, formData.currency)}/{service.unit}
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          ))}
          <div className="form-group">
            <label>套餐折扣 (%)</label>
            <input
              type="number"
              value={formData.packageQuote.packageDiscount}
              onChange={(e) => handleInputChange('packageQuote', 'packageDiscount', parseFloat(e.target.value) || 0)}
              min="0"
              max="50"
              step="0.1"
            />
          </div>
        </div>
      )}

      {formData.quoteType === 'volume' && (
        <div className="form-section">
          <h3>数量分级定价</h3>
          <div className="volume-tiers">
            {formData.volumeQuote.volumeTiers.map((tier, index) => (
              <div key={index} className="tier-row">
                <div className="tier-range">
                  <input
                    type="number"
                    value={tier.min}
                    onChange={(e) => updateVolumeTier(index, 'min', parseInt(e.target.value) || 0)}
                    placeholder="最小值"
                  />
                  <span>-</span>
                  <input
                    type="number"
                    value={tier.max === 999999999 ? '' : tier.max}
                    onChange={(e) => updateVolumeTier(index, 'max', parseInt(e.target.value) || 999999999)}
                    placeholder="最大值"
                  />
                </div>
                <div className="tier-price">
                  <input
                    type="number"
                    value={tier.unitPrice}
                    onChange={(e) => updateVolumeTier(index, 'unitPrice', parseFloat(e.target.value) || 0)}
                    placeholder="单价"
                    step="0.01"
                  />
                </div>
                <div className="tier-discount">
                  <input
                    type="number"
                    value={tier.discount * 100}
                    onChange={(e) => updateVolumeTier(index, 'discount', (parseFloat(e.target.value) || 0) / 100)}
                    placeholder="折扣%"
                    step="0.1"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {formData.quoteType === 'time' && (
        <div className="form-section">
          <h3>时间合约配置</h3>
          <div className="form-grid">
            <div className="form-group">
              <label>合约期限 (月)</label>
              <input
                type="number"
                value={formData.timeQuote.contractDuration}
                onChange={(e) => handleInputChange('timeQuote', 'contractDuration', parseInt(e.target.value) || 12)}
                min="1"
              />
            </div>
            <div className="form-group">
              <label>月度承诺金额</label>
              <input
                type="number"
                value={formData.timeQuote.monthlyCommitment}
                onChange={(e) => handleInputChange('timeQuote', 'monthlyCommitment', parseFloat(e.target.value) || 0)}
                min="0"
                step="0.01"
              />
            </div>
            <div className="form-group">
              <label>合约折扣 (%)</label>
              <input
                type="number"
                value={formData.timeQuote.timeDiscount}
                onChange={(e) => handleInputChange('timeQuote', 'timeDiscount', parseFloat(e.target.value) || 0)}
                min="0"
                max="30"
                step="0.1"
              />
            </div>
            <div className="form-group">
              <label>年度涨幅 (%)</label>
              <input
                type="number"
                value={formData.timeQuote.escalationRate * 100}
                onChange={(e) => handleInputChange('timeQuote', 'escalationRate', (parseFloat(e.target.value) || 0) / 100)}
                min="0"
                max="20"
                step="0.1"
              />
            </div>
          </div>
        </div>
      )}

      {formData.quoteType === 'custom' && (
        <div className="form-section">
          <div className="section-header">
            <h3>自定义项目</h3>
            <SecondaryButton onClick={addCustomItem}>
              添加项目
            </SecondaryButton>
          </div>
          {formData.customQuote.customItems.map((item, index) => (
            <div key={item.id} className="custom-item-card">
              <div className="item-header">
                <h4>项目 {index + 1}</h4>
                {formData.customQuote.customItems.length > 1 && (
                  <button 
                    type="button"
                    className="remove-item-btn"
                    onClick={() => removeCustomItem(item.id)}
                  >
                    删除
                  </button>
                )}
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label>类别</label>
                  <select
                    value={item.category}
                    onChange={(e) => updateCustomItem(item.id, 'category', e.target.value)}
                  >
                    <option value="">请选择类别</option>
                    <option value="testing">测试服务</option>
                    <option value="engineering">工程服务</option>
                    <option value="equipment">设备租赁</option>
                    <option value="consulting">咨询服务</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                <div className="form-group full-width">
                  <label>项目描述</label>
                  <input
                    type="text"
                    value={item.description}
                    onChange={(e) => updateCustomItem(item.id, 'description', e.target.value)}
                    placeholder="请输入详细描述"
                  />
                </div>
                <div className="form-group">
                  <label>数量</label>
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => updateCustomItem(item.id, 'quantity', parseInt(e.target.value) || 1)}
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label>单价</label>
                  <input
                    type="number"
                    value={item.unitPrice}
                    onChange={(e) => updateCustomItem(item.id, 'unitPrice', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="form-group">
                  <label>折扣 (%)</label>
                  <input
                    type="number"
                    value={item.discount}
                    onChange={(e) => updateCustomItem(item.id, 'discount', parseFloat(e.target.value) || 0)}
                    min="0"
                    max="50"
                    step="0.1"
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
      )}

      <div className="form-section">
        <h3>价格调整</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>紧急程度调整</label>
            <select
              value={formData.priceAdjustments.urgencyMultiplier}
              onChange={(e) => handleInputChange('priceAdjustments', 'urgencyMultiplier', parseFloat(e.target.value))}
            >
              <option value={1.0}>正常 (×1.0)</option>
              <option value={1.2}>紧急 (×1.2)</option>
              <option value={1.5}>非常紧急 (×1.5)</option>
              <option value={2.0}>极其紧急 (×2.0)</option>
            </select>
          </div>
          <div className="form-group">
            <label>复杂度调整</label>
            <select
              value={formData.priceAdjustments.complexityMultiplier}
              onChange={(e) => handleInputChange('priceAdjustments', 'complexityMultiplier', parseFloat(e.target.value))}
            >
              <option value={0.8}>简单 (×0.8)</option>
              <option value={1.0}>标准 (×1.0)</option>
              <option value={1.3}>复杂 (×1.3)</option>
              <option value={1.6}>高度复杂 (×1.6)</option>
            </select>
          </div>
          <div className="form-group">
            <label>客户折扣 (%)</label>
            <input
              type="number"
              value={formData.priceAdjustments.customerDiscount}
              onChange={(e) => handleInputChange('priceAdjustments', 'customerDiscount', parseFloat(e.target.value) || 0)}
              min="0"
              max="30"
              step="0.1"
            />
          </div>
          <div className="form-group">
            <label>季节性调整 (%)</label>
            <input
              type="number"
              value={formData.priceAdjustments.seasonalAdjustment}
              onChange={(e) => handleInputChange('priceAdjustments', 'seasonalAdjustment', parseFloat(e.target.value) || 0)}
              min="-20"
              max="20"
              step="0.1"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>协议条款</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>报价有效期 (天)</label>
            <input
              type="number"
              value={formData.agreementTerms.validityPeriod}
              onChange={(e) => handleInputChange('agreementTerms', 'validityPeriod', parseInt(e.target.value) || 180)}
              min="1"
            />
          </div>
          <div className="form-group">
            <label>付款条件</label>
            <select
              value={formData.agreementTerms.paymentTerms}
              onChange={(e) => handleInputChange('agreementTerms', 'paymentTerms', e.target.value)}
            >
              {paymentTermOptions.map(term => (
                <option key={term.value} value={term.value}>
                  {term.label}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>交付条款</label>
            <select
              value={formData.agreementTerms.deliveryTerms}
              onChange={(e) => handleInputChange('agreementTerms', 'deliveryTerms', e.target.value)}
            >
              <option value="standard">标准交付</option>
              <option value="expedited">加急交付</option>
              <option value="scheduled">计划交付</option>
              <option value="flexible">灵活交付</option>
            </select>
          </div>
          <div className="form-group">
            <label>质保期 (天)</label>
            <input
              type="number"
              value={formData.agreementTerms.warrantyPeriod}
              onChange={(e) => handleInputChange('agreementTerms', 'warrantyPeriod', parseInt(e.target.value) || 90)}
              min="0"
            />
          </div>
          <div className="form-group">
            <label>修订政策</label>
            <select
              value={formData.agreementTerms.revisionPolicy}
              onChange={(e) => handleInputChange('agreementTerms', 'revisionPolicy', e.target.value)}
            >
              <option value="included">包含在内</option>
              <option value="limited">有限修订</option>
              <option value="charged">按次收费</option>
            </select>
          </div>
          <div className="form-group">
            <label>取消政策</label>
            <select
              value={formData.agreementTerms.cancellationPolicy}
              onChange={(e) => handleInputChange('agreementTerms', 'cancellationPolicy', e.target.value)}
            >
              <option value="standard">标准政策</option>
              <option value="flexible">灵活政策</option>
              <option value="strict">严格政策</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>其他设置</h3>
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
            <span>{formData.quoteType === 'package' ? '套餐总价' :
                   formData.quoteType === 'volume' ? '数量总价' :
                   formData.quoteType === 'time' ? '合约总价' : '自定义总价'}：</span>
            <span>
              {currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice((formData.quoteType === 'package' ? calculatePackageTotal() :
                formData.quoteType === 'volume' ? calculateVolumeQuoteTotal() :
                formData.quoteType === 'time' ? calculateTimeQuoteTotal() :
                calculateCustomQuoteTotal()), formData.currency)}
            </span>
          </div>
          <div className="summary-item total">
            <span>最终报价：</span>
            <span className="summary-value">
              {currencies.find(c => c.value === formData.currency)?.symbol} 
              {formatQuotePrice(calculateFinalTotal(), formData.currency)}
            </span>
          </div>
        </div>
      </div>

      <div className="button-group">
        <SecondaryButton onClick={handleBack}>
          返回
        </SecondaryButton>
        <PrimaryButton onClick={handleSubmit}>
          生成综合报价单
        </PrimaryButton>
      </div>
    </div>
  );
};

export default ComprehensiveQuote;