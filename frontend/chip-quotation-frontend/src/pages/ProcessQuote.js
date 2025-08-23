import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Checkbox, Card, Button, Table, InputNumber } from 'antd';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { formatHourlyRate, ceilByCurrency, formatQuotePrice } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import '../App.css';

const ProcessQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  const [machines, setMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);
  const [loading, setLoading] = useState(true);

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
      testType: ''
    },
    selectedTypes: ['cp'], // 默认选择CP
    cpProcesses: [
      {
        id: 1,
        name: 'CP1测试',
        machine: '',
        machineData: null,
        cardQuantities: {},
        uph: 0,
        unitCost: 0
      }
    ],
    ftProcesses: [
      {
        id: 1,
        name: 'FT1测试',
        machine: '',
        machineData: null,
        cardQuantities: {},
        uph: 0,
        unitCost: 0
      }
    ],
    pricing: {
      laborCostPerHour: 0,
      overheadRate: 0,
      profitMargin: 0
    },
    currency: 'CNY',
    exchangeRate: 7.2,
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
    { value: 'USD', label: '美元 (USD)', symbol: '$' }
  ];

  // 获取机器和板卡数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [machinesData, cardTypesData] = await Promise.all([
          getMachines(),
          getCardTypes()
        ]);
        setMachines(machinesData);
        setCardTypes(cardTypesData);
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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
      machineData: null,
      cardQuantities: {},
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
            updatedProcess.machineData = null;
            updatedProcess.cardQuantities = {};
          }
          
          // 如果改变了机器选择，更新机器数据并重置板卡选择
          if (field === 'machine') {
            const selectedMachine = machines.find(m => m.name === value);
            updatedProcess.machineData = selectedMachine;
            updatedProcess.cardQuantities = {};
          }
          
          // 人工成本设置为0，不进行自动计算
          if (field === 'uph') {
            updatedProcess.unitCost = 0; // 人工成本设为0
          }
          
          return updatedProcess;
        }
        return process;
      })
    }));
  };

  // 处理板卡选择变化
  const handleCardSelection = (type, processId, selectedRowKeys, selectedRows) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          const newCardQuantities = {};
          selectedRows.forEach(card => {
            // 保持已有的数量，如果没有则设为1
            newCardQuantities[card.id] = process.cardQuantities[card.id] || 1;
          });
          return {
            ...process,
            cardQuantities: newCardQuantities
          };
        }
        return process;
      })
    }));
    
    // 强制组件重新渲染以更新成本计算
    setTimeout(() => {
      setFormData(prev => ({ ...prev }));
    }, 0);
  };

  // 处理板卡数量变化
  const handleCardQuantityChange = (type, processId, cardId, quantity) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          const updatedQuantities = { ...process.cardQuantities };
          if (quantity > 0) {
            updatedQuantities[cardId] = quantity;
          } else {
            delete updatedQuantities[cardId];
          }
          return {
            ...process,
            cardQuantities: updatedQuantities
          };
        }
        return process;
      })
    }));
    
    // 强制组件重新渲染以更新成本计算
    setTimeout(() => {
      setFormData(prev => ({ ...prev }));
    }, 0);
  };

  // 计算单个工序的机器费用（包括板卡成本）
  const calculateProcessMachineCost = (process) => {
    if (!process.machineData || !process.cardQuantities) return 0;
    
    let totalCost = 0;
    Object.entries(process.cardQuantities).forEach(([cardId, quantity]) => {
      const card = cardTypes.find(c => c.id === parseInt(cardId));
      if (card && quantity > 0) {
        // 计算调整后的板卡价格（注意：板卡有自己的币种）
        let adjustedPrice = (card.unit_price || 0) / 10000;
        
        // 根据报价币种和机器币种进行转换
        if (formData.currency === 'USD') {
          if (process.machineData.currency === 'CNY' || process.machineData.currency === 'RMB') {
            // CNY机器转USD：使用报价汇率
            adjustedPrice = adjustedPrice / formData.exchangeRate;
          }
          // USD机器：价格已经是USD，不需要转换
        } else {
          // 报价币种是CNY
          if (process.machineData.currency === 'USD') {
            // USD机器转CNY：使用机器的汇率
            adjustedPrice = adjustedPrice * (process.machineData.exchange_rate || 7.2);
          }
          // CNY机器：价格已经是CNY，不需要转换
        }
        
        // 应用折扣率和数量，然后除以UPH得到单颗成本
        const hourlyCost = adjustedPrice * (process.machineData.discount_rate || 1.0) * quantity;
        const unitCost = process.uph > 0 ? hourlyCost / process.uph : 0;
        totalCost += unitCost;
      }
    });
    
    // 不使用向上取整，保持精确计算
    return totalCost;
  };

  // 计算总成本（人工成本 + 机器成本）
  const calculateTotalUnitCost = () => {
    let total = 0;
    
    if (formData.selectedTypes.includes('cp')) {
      total += formData.cpProcesses.reduce((sum, process) => {
        const laborCost = process.unitCost || 0; // 人工成本（现在为0）
        const machineCost = calculateProcessMachineCost(process); // 机器成本
        return sum + laborCost + machineCost;
      }, 0);
    }
    
    if (formData.selectedTypes.includes('ft')) {
      total += formData.ftProcesses.reduce((sum, process) => {
        const laborCost = process.unitCost || 0; // 人工成本（现在为0）
        const machineCost = calculateProcessMachineCost(process); // 机器成本
        return sum + laborCost + machineCost;
      }, 0);
    }
    
    // 根据货币类型向上取整
    return ceilByCurrency(total, formData.currency);
  };

  const calculateTotalProjectCost = () => {
    return calculateTotalUnitCost();
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
      cardTypes, // 传递板卡类型数据
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
    const formattedNumber = formatQuotePrice(number, formData.currency);
    return `${symbol}${formattedNumber}`;
  };

  // 格式化单颗费用显示（4位小数，万分位向上取整）- v2.0
  const formatUnitPrice = (number) => {
    const symbol = currencies.find(c => c.value === formData.currency)?.symbol || '￥';
    if (number === null || number === undefined || number === 0) return `${symbol}0.0000`;
    
    // 万分位向上取整：乘以10000，向上取整，再除以10000
    const ceiledToFourDecimals = Math.ceil(number * 10000) / 10000;
    const formatted = ceiledToFourDecimals.toFixed(4);
    return `${symbol}${formatted}`;
  };

  // 格式化机时价格显示（包含币种符号，根据币种精度）
  const formatHourlyPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, formData.currency);
    const symbol = currencies.find(c => c.value === formData.currency)?.symbol || '￥';
    return `${symbol}${formattedNumber}`;
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
          {machines.map(machineData => (
            <option key={machineData.id} value={machineData.name}>
              {machineData.name}
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
      title: '单颗费用',
      dataIndex: 'unitCost',
      render: (unitCost, record) => {
        const laborCost = unitCost || 0;
        const machineCost = calculateProcessMachineCost(record);
        const totalCost = laborCost + machineCost;
        return (
          <div>
            <div>{formatUnitPrice(totalCost)}</div>
            {machineCost > 0 && (
              <div style={{ fontSize: '11px', color: '#666' }}>
                人工: {formatUnitPrice(laborCost)}<br/>
                机器: {formatUnitPrice(machineCost)}
              </div>
            )}
          </div>
        );
      }
    },
    {
      title: '板卡配置',
      dataIndex: 'cardQuantities',
      render: (cardQuantities, record) => {
        if (!record.machineData) {
          return <span style={{ color: '#999' }}>请先选择设备</span>;
        }
        
        const availableCards = cardTypes.filter(card => card.machine_id === record.machineData.id);
        if (availableCards.length === 0) {
          return <span style={{ color: '#999' }}>无可用板卡</span>;
        }
        
        const selectedCount = Object.keys(cardQuantities).length;
        const totalCards = availableCards.length;
        
        return (
          <span style={{ color: selectedCount > 0 ? '#1890ff' : '#999' }}>
            已选择 {selectedCount} / {totalCards} 张板卡
          </span>
        );
      }
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

  // 渲染单个工序的板卡选择区域（用于展开行）
  const renderCardSelectionForProcess = (processType, process) => {
    if (!process.machineData) return null;
    
    const availableCards = cardTypes.filter(card => card.machine_id === process.machineData.id);
    if (availableCards.length === 0) return null;
    
    // 获取已选择的板卡ID列表
    const selectedCardIds = Object.keys(process.cardQuantities).map(id => parseInt(id));
    
    // 板卡表格列定义
    const cardColumns = () => {
      const columns = [
        { 
          title: 'Part Number', 
          dataIndex: 'part_number',
          width: '25%'
        },
        { 
          title: 'Board Name', 
          dataIndex: 'board_name',
          width: user?.role === 'admin' || user?.role === 'super_admin' ? '35%' : '55%',
          render: (text) => (
            <span style={{ fontWeight: '500', color: '#333' }}>
              {text}
            </span>
          )
        }
      ];
      
      // 只有管理员以上权限才能看到价格
      if (user?.role === 'admin' || user?.role === 'super_admin') {
        columns.push({ 
          title: 'Unit Price', 
          dataIndex: 'unit_price',
          width: '20%',
          render: (value) => formatQuotePrice(value || 0, formData.currency)
        });
      }
      
      columns.push({ 
        title: 'Quantity', 
        dataIndex: 'id',
        width: '20%',
        render: (cardId, record) => (
          <InputNumber
            size="small"
            min={1}
            value={process.cardQuantities[cardId] || 1}
            onChange={(value) => handleCardQuantityChange(processType, process.id, cardId, value || 1)}
            style={{ width: '80px' }}
            placeholder="数量"
          />
        )
      });
      
      return columns;
    };
    
    return (
      <div style={{ padding: '10px 0' }}>
        <h5 style={{ marginBottom: 10, color: '#1890ff' }}>
          {process.name} - {process.machine} 板卡配置
        </h5>
        <Table
          dataSource={availableCards}
          columns={cardColumns()}
          rowKey="id"
          rowSelection={{
            type: 'checkbox',
            selectedRowKeys: selectedCardIds,
            onChange: (selectedRowKeys, selectedRows) => 
              handleCardSelection(processType, process.id, selectedRowKeys, selectedRows)
          }}
          pagination={false}
          size="small"
          bordered
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="quote-container" style={{ textAlign: 'center', paddingTop: '50px' }}>
        <div>加载中...</div>
      </div>
    );
  }

  return (
    <div className="quote-container">
      <PageTitle 
        title="量产工序报价" 
        subtitle="基于生产工序的单颗芯片成本分析 (v2.0)" 
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
            expandable={{
              expandedRowRender: (record) => renderCardSelectionForProcess('cp', record),
              rowExpandable: (record) => record.machineData && cardTypes.filter(card => card.machine_id === record.machineData.id).length > 0,
              expandRowByClick: false
            }}
          />
          <div style={{ marginTop: 15, textAlign: 'right', fontSize: '14px', color: '#666' }}>
            <em>注：各工序报价不可直接相加，需考虑良率差异</em>
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
            expandable={{
              expandedRowRender: (record) => renderCardSelectionForProcess('ft', record),
              rowExpandable: (record) => record.machineData && cardTypes.filter(card => card.machine_id === record.machineData.id).length > 0,
              expandRowByClick: false
            }}
          />
          <div style={{ marginTop: 15, textAlign: 'right', fontSize: '14px', color: '#666' }}>
            <em>注：各工序报价不可直接相加，需考虑良率差异</em>
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
          {formData.currency === 'USD' && (
            <div className="form-group">
              <label>USD 汇率 (1 USD = ? CNY)</label>
              <input
                type="number"
                step="0.01"
                value={formData.exchangeRate}
                onChange={(e) => setFormData(prev => ({ ...prev, exchangeRate: parseFloat(e.target.value) || 7.2 }))}
                placeholder="7.2"
              />
            </div>
          )}
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

      {/* 报价说明 */}
      <div className="quote-summary">
        <h3>报价说明</h3>
        <div style={{ padding: '15px', backgroundColor: '#f6f8fa', border: '1px solid #d0d7de', borderRadius: '6px' }}>
          <div style={{ marginBottom: '10px', fontWeight: 'bold', color: '#0969da' }}>
            工序报价明细
          </div>
          <div style={{ fontSize: '14px', color: '#656d76', lineHeight: '1.5' }}>
            • 各工序单独报价，反映每道工序的实际成本<br/>
            • 不同工序存在良率差异，总成本需根据实际良率计算<br/>
            • 最终报价请参考各工序明细，不可简单相加
          </div>
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