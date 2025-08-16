import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Checkbox, Card, Button, Table, InputNumber } from 'antd';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import '../App.css';

const ProcessQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
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
      volume: 0,
      deliverySchedule: ''
    },
    selectedTypes: ['cp'], // 默认选择CP
    cpProcesses: [
      {
        id: 1,
        name: 'CP1测试',
        machine: '',
        uph: 0,
        unitCost: 0
      }
    ],
    ftProcesses: [
      {
        id: 1,
        name: 'FT1测试',
        machine: '',
        uph: 0,
        unitCost: 0
      }
    ],
    pricing: {
      laborCostPerHour: 50,
      overheadRate: 0.3,
      profitMargin: 0.15
    },
    currency: 'CNY',
    remarks: ''
  });

  // 可选工序类型
  const cpProcessTypes = [
    'CP1测试', 'CP2测试', 'CP3测试', '烘烤', 'AOI检测', 'X-Ray检测', '外观检查'
  ];
  
  const ftProcessTypes = [
    'FT1测试', 'FT2测试', 'FT3测试', '烘烤', '编带', 'AOI检测', '包装', '老化测试'
  ];

  // 设备选项
  const machineOptions = {
    'CP1测试': ['Advantest V93K', 'Teradyne UltraFlex', 'Cohu Delta'],
    'CP2测试': ['Advantest V93K', 'Teradyne UltraFlex', 'Cohu Delta'],
    'CP3测试': ['Advantest V93K', 'Teradyne UltraFlex', 'Cohu Delta'],
    'FT1测试': ['Advantest T2000', 'Teradyne Magnum', 'Cohu Eagle'],
    'FT2测试': ['Advantest T2000', 'Teradyne Magnum', 'Cohu Eagle'],
    'FT3测试': ['Advantest T2000', 'Teradyne Magnum', 'Cohu Eagle'],
    '烘烤': ['Blue M Oven', 'Despatch Oven', 'Heraeus Oven'],
    '编带': ['Multitest MT8590', 'Advantest M6541', 'Delta S3000'],
    'AOI检测': ['Orbotech VT-9300', 'Koh Young Zenith', 'Mirtec MV-7'],
    'X-Ray检测': ['Dage XD7600NT', 'Nordson DAGE 4000', 'Yxlon Y.Cougar'],
    '外观检查': ['人工检测', 'Cognex VisionPro', 'Keyence CV-X'],
    '包装': ['ASM SIPLACE', 'Universal GSM2', 'Assembleon Topaz'],
    '老化测试': ['Delta Design 9023', 'Thermonics T-2420', 'Temptronic ThermoStream']
  };

  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' },
    { value: 'EUR', label: '欧元 (EUR)', symbol: '€' }
  ];

  // 状态保存和恢复
  useEffect(() => {
    const isFromResultPage = location.state?.fromResultPage;
    
    if (isFromResultPage) {
      const savedState = sessionStorage.getItem('processQuoteState');
      if (savedState) {
        try {
          const parsedState = JSON.parse(savedState);
          console.log('从 sessionStorage 恢复工序报价状态:', parsedState);
          setFormData(parsedState);
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      sessionStorage.removeItem('processQuoteState');
      console.log('开始全新工序报价流程');
    }
  }, [location.state?.fromResultPage]);

  useEffect(() => {
    sessionStorage.setItem('processQuoteState', JSON.stringify(formData));
  }, [formData]);

  // 处理测试类型变化
  const handleProductionTypeChange = (checkedValues) => {
    setFormData(prev => ({
      ...prev,
      selectedTypes: checkedValues
    }));
  };

  // 添加工序
  const addProcess = (type) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    const newProcess = {
      id: formData[processKey].length + 1,
      name: type === 'cp' ? 'CP1测试' : 'FT1测试',
      machine: '',
      uph: 0,
      unitCost: 0
    };
    
    setFormData(prev => ({
      ...prev,
      [processKey]: [...prev[processKey], newProcess]
    }));
  };

  // 删除工序
  const removeProcess = (type, processId) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    if (formData[processKey].length > 1) {
      setFormData(prev => ({
        ...prev,
        [processKey]: prev[processKey].filter(process => process.id !== processId)
      }));
    }
  };

  // 更新工序
  const updateProcess = (type, processId, field, value) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          let updatedProcess = { ...process, [field]: value };
          
          // 如果改变了工序名称，重置机器选择
          if (field === 'name') {
            updatedProcess.machine = '';
          }
          
          // 自动计算单位成本
          if (field === 'uph' && updatedProcess.uph > 0) {
            const hourlyRate = prev.pricing.laborCostPerHour;
            const overhead = hourlyRate * prev.pricing.overheadRate;
            const totalHourlyRate = hourlyRate + overhead;
            const profit = totalHourlyRate * prev.pricing.profitMargin;
            const unitCost = (totalHourlyRate + profit) / updatedProcess.uph;
            updatedProcess.unitCost = Math.round(unitCost * 10000) / 10000; // 保留4位小数
          }
          
          return updatedProcess;
        }
        return process;
      })
    }));
  };

  // 计算总成本
  const calculateTotalUnitCost = () => {
    let total = 0;
    
    if (formData.selectedTypes.includes('cp')) {
      total += formData.cpProcesses.reduce((sum, process) => sum + (process.unitCost || 0), 0);
    }
    
    if (formData.selectedTypes.includes('ft')) {
      total += formData.ftProcesses.reduce((sum, process) => sum + (process.unitCost || 0), 0);
    }
    
    return total;
  };

  const calculateTotalProjectCost = () => {
    return calculateTotalUnitCost() * (formData.projectInfo.volume || 0);
  };

  // 表单输入处理
  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  // 提交处理
  const handleSubmit = () => {
    const quoteData = {
      type: '工序报价',
      number: `PR-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-${String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')}`,
      date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...formData,
      totalUnitCost: calculateTotalUnitCost(),
      totalProjectCost: calculateTotalProjectCost(),
      generatedAt: new Date().toISOString()
    };

    navigate('/quote-result', { state: quoteData });
  };

  const handleBack = () => {
    navigate('/quote-type-selection');
  };

  // 格式化价格显示
  const formatPrice = (number) => {
    const symbol = currencies.find(c => c.value === formData.currency)?.symbol || '￥';
    return `${symbol}${number.toFixed(4)}`;
  };

  // 工序表格列定义
  const getProcessColumns = (type) => [
    {
      title: '工序名称',
      dataIndex: 'name',
      render: (name, record) => (
        <select
          value={name}
          onChange={(e) => updateProcess(type, record.id, 'name', e.target.value)}
          style={{ width: '100%', padding: '4px' }}
        >
          {(type === 'cp' ? cpProcessTypes : ftProcessTypes).map(processType => (
            <option key={processType} value={processType}>
              {processType}
            </option>
          ))}
        </select>
      )
    },
    {
      title: '设备型号',
      dataIndex: 'machine',
      render: (machine, record) => (
        <select
          value={machine}
          onChange={(e) => updateProcess(type, record.id, 'machine', e.target.value)}
          style={{ width: '100%', padding: '4px' }}
          disabled={!record.name}
        >
          <option value="">请选择设备</option>
          {(machineOptions[record.name] || []).map(option => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      )
    },
    {
      title: 'UPH',
      dataIndex: 'uph',
      render: (uph, record) => (
        <InputNumber
          value={uph}
          onChange={(value) => updateProcess(type, record.id, 'uph', value || 0)}
          min={0}
          style={{ width: '100%' }}
        />
      )
    },
    {
      title: '单位成本',
      dataIndex: 'unitCost',
      render: (unitCost) => formatPrice(unitCost || 0)
    },
    {
      title: '操作',
      render: (_, record) => (
        <Button
          type="link"
          danger
          onClick={() => removeProcess(type, record.id)}
          disabled={formData[type === 'cp' ? 'cpProcesses' : 'ftProcesses'].length <= 1}
        >
          删除
        </Button>
      )
    }
  ];

  return (
    <div className="quote-container">
      <PageTitle 
        title="量产工序报价" 
        subtitle="基于生产工序的单颗芯片成本分析" 
      />

      {/* 客户信息 */}
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

      {/* 项目信息 */}
      <div className="form-section">
        <h3>项目信息</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>项目名称</label>
            <input
              type="text"
              value={formData.projectInfo.projectName}
              onChange={(e) => handleInputChange('projectInfo', 'projectName', e.target.value)}
              placeholder="请输入项目名称"
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
            <label>年产量 *</label>
            <input
              type="number"
              value={formData.projectInfo.volume}
              onChange={(e) => handleInputChange('projectInfo', 'volume', parseInt(e.target.value) || 0)}
              placeholder="请输入年产量"
              required
            />
          </div>
          <div className="form-group full-width">
            <label>交期计划</label>
            <textarea
              value={formData.projectInfo.deliverySchedule}
              onChange={(e) => handleInputChange('projectInfo', 'deliverySchedule', e.target.value)}
              placeholder="请输入交期要求..."
              rows="2"
            />
          </div>
        </div>
      </div>

      {/* 工序类型选择 */}
      <Card title="工序类型选择" style={{ marginBottom: 20 }}>
        <Checkbox.Group value={formData.selectedTypes} onChange={handleProductionTypeChange}>
          <Checkbox value="cp" style={{ marginRight: 20 }}>CP工序报价</Checkbox>
          <Checkbox value="ft">FT工序报价</Checkbox>
        </Checkbox.Group>
        <div style={{ marginTop: 10, color: '#666', fontSize: '12px' }}>
          可同时选择CP和FT工序进行综合报价
        </div>
      </Card>

      {/* CP工序配置 */}
      {formData.selectedTypes.includes('cp') && (
        <Card title="CP工序配置" style={{ marginBottom: 20 }}>
          <div style={{ marginBottom: 15 }}>
            <Button type="dashed" onClick={() => addProcess('cp')}>
              + 添加CP工序
            </Button>
          </div>
          <Table
            dataSource={formData.cpProcesses}
            columns={getProcessColumns('cp')}
            rowKey="id"
            pagination={false}
            size="small"
          />
          <div style={{ marginTop: 15, textAlign: 'right' }}>
            <strong>CP工序总成本: {formatPrice(formData.cpProcesses.reduce((sum, p) => sum + (p.unitCost || 0), 0))}</strong>
          </div>
        </Card>
      )}

      {/* FT工序配置 */}
      {formData.selectedTypes.includes('ft') && (
        <Card title="FT工序配置" style={{ marginBottom: 20 }}>
          <div style={{ marginBottom: 15 }}>
            <Button type="dashed" onClick={() => addProcess('ft')}>
              + 添加FT工序
            </Button>
          </div>
          <Table
            dataSource={formData.ftProcesses}
            columns={getProcessColumns('ft')}
            rowKey="id"
            pagination={false}
            size="small"
          />
          <div style={{ marginTop: 15, textAlign: 'right' }}>
            <strong>FT工序总成本: {formatPrice(formData.ftProcesses.reduce((sum, p) => sum + (p.unitCost || 0), 0))}</strong>
          </div>
        </Card>
      )}

      {/* 成本参数设置 */}
      <div className="form-section">
        <h3>成本参数设置</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>人工成本(/小时)</label>
            <input
              type="number"
              value={formData.pricing.laborCostPerHour}
              onChange={(e) => handleInputChange('pricing', 'laborCostPerHour', parseFloat(e.target.value) || 0)}
              placeholder="50"
            />
          </div>
          <div className="form-group">
            <label>费用率</label>
            <input
              type="number"
              step="0.01"
              value={formData.pricing.overheadRate}
              onChange={(e) => handleInputChange('pricing', 'overheadRate', parseFloat(e.target.value) || 0)}
              placeholder="0.3"
            />
          </div>
          <div className="form-group">
            <label>利润率</label>
            <input
              type="number"
              step="0.01"
              value={formData.pricing.profitMargin}
              onChange={(e) => handleInputChange('pricing', 'profitMargin', parseFloat(e.target.value) || 0)}
              placeholder="0.15"
            />
          </div>
          <div className="form-group">
            <label>报价货币</label>
            <select
              value={formData.currency}
              onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
            >
              {currencies.map(currency => (
                <option key={currency.value} value={currency.value}>
                  {currency.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 备注 */}
      <div className="form-section">
        <h3>备注说明</h3>
        <div className="form-group full-width">
          <textarea
            value={formData.remarks}
            onChange={(e) => setFormData(prev => ({ ...prev, remarks: e.target.value }))}
            placeholder="请输入其他要求或说明..."
            rows="3"
          />
        </div>
      </div>

      {/* 报价汇总 */}
      <div className="quote-summary">
        <h3>成本汇总</h3>
        <div className="summary-item">
          <span>单颗总成本：</span>
          <span className="summary-value">
            {formatPrice(calculateTotalUnitCost())}
          </span>
        </div>
        <div className="summary-item total">
          <span>项目总成本：</span>
          <span className="summary-value">
            {formatPrice(calculateTotalProjectCost())}
          </span>
        </div>
      </div>

      <div className="button-group">
        <SecondaryButton onClick={handleBack}>
          返回
        </SecondaryButton>
        <PrimaryButton onClick={handleSubmit}>
          生成工序报价单
        </PrimaryButton>
      </div>
    </div>
  );
};

export default ProcessQuote;