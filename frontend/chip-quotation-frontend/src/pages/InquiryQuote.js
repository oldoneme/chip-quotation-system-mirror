import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Table, InputNumber } from 'antd';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { formatHourlyRate, ceilByCurrency, formatQuotePrice } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import '../App.css';

const InquiryQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
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
      urgency: 'normal'
    },
    machines: [
      {
        id: 1,
        category: '',
        model: '',
        machineData: null,
        selectedCards: [],
        hourlyRate: 0
      }
    ],
    currency: 'CNY',
    exchangeRate: 7.2,  // 添加汇率字段
    inquiryFactor: 1.5,
    remarks: ''
  });

  const [availableMachines, setAvailableMachines] = useState({
    tester: [],
    handler: [],
    sorter: []
  });
  
  const [loading, setLoading] = useState(false);
  const [backendMachines, setBackendMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);
  const [persistedCardQuantities, setPersistedCardQuantities] = useState({});
  const [isMounted, setIsMounted] = useState(false);

  const machineCategories = [
    { value: 'tester', label: '测试机' },
    { value: 'handler', label: '分选机' },
    { value: 'sorter', label: '编带机' }
  ];

  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' }
  ];

  // 从后端获取机器和板卡数据，然后处理状态恢复
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [machinesData, cardTypesData] = await Promise.all([
          getMachines(),
          getCardTypes()
        ]);
        
        setBackendMachines(machinesData);
        setCardTypes(cardTypesData);
        
        // 按机器类型分类
        const categorizedMachines = {
          tester: [],
          handler: [],
          sorter: []
        };
        
        machinesData.forEach(machine => {
          const machineTypeName = getMachineTypeName(machine);
          
          if (machineTypeName.includes('测试机') || machineTypeName.includes('ATE')) {
            categorizedMachines.tester.push({
              model: machine.name,
              id: machine.id,
              data: machine
            });
          } else if (machineTypeName.includes('分选机') || machineTypeName.includes('Handler')) {
            categorizedMachines.handler.push({
              model: machine.name,
              id: machine.id,
              data: machine
            });
          } else if (machineTypeName.includes('编带') || machineTypeName.includes('Sorter')) {
            categorizedMachines.sorter.push({
              model: machine.name,
              id: machine.id,
              data: machine
            });
          }
        });
        
        setAvailableMachines(categorizedMachines);
        setIsMounted(true);
        
        // 数据加载完成后，检查是否需要恢复状态
        const isFromResultPage = location.state?.fromResultPage;
        if (isFromResultPage) {
          const savedState = sessionStorage.getItem('inquiryQuoteState');
          if (savedState) {
            try {
              const parsedState = JSON.parse(savedState);
              console.log('从 sessionStorage 恢复询价报价状态:', parsedState);
              setFormData(parsedState.formData);
              setPersistedCardQuantities(parsedState.persistedCardQuantities || {});
            } catch (error) {
              console.error('解析保存状态时出错:', error);
            }
          }
        } else {
          sessionStorage.removeItem('inquiryQuoteState');
          console.log('开始全新询价报价流程');
        }
        
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [location.state?.fromResultPage]);

  // 保存状态到sessionStorage（只有在已挂载且不是从结果页面返回时才保存）
  useEffect(() => {
    if (isMounted && !location.state?.fromResultPage) {
      const stateToSave = {
        formData,
        persistedCardQuantities
      };
      sessionStorage.setItem('inquiryQuoteState', JSON.stringify(stateToSave));
    }
  }, [formData, persistedCardQuantities, isMounted, location.state?.fromResultPage]);
  

  // 获取机器类型名称的辅助函数
  const getMachineTypeName = (machine) => {
    try {
      if (machine.supplier && machine.supplier.machine_type) {
        return machine.supplier.machine_type.name || '';
      }
      if (machine.supplier_machine_type_name) {
        return machine.supplier_machine_type_name;
      }
      return '';
    } catch (e) {
      console.error('获取机器类型名称时出错:', e);
      return '';
    }
  };

  const addMachine = () => {
    const newMachine = {
      id: formData.machines.length + 1,
      category: '',
      model: '',
      machineData: null,
      selectedCards: [],
      hourlyRate: 0
    };
    setFormData(prev => ({
      ...prev,
      machines: [...prev.machines, newMachine]
    }));
  };

  const removeMachine = (machineId) => {
    if (formData.machines.length > 1) {
      setFormData(prev => ({
        ...prev,
        machines: prev.machines.filter(machine => machine.id !== machineId)
      }));
    }
  };

  const updateMachine = (machineId, field, value) => {
    setFormData(prev => ({
      ...prev,
      machines: prev.machines.map(machine => {
        if (machine.id === machineId) {
          if (field === 'category') {
            return {
              ...machine,
              [field]: value,
              model: '',
              machineData: null,
              selectedCards: [],
              hourlyRate: 0
            };
          } else if (field === 'model') {
            const selectedMachineOption = availableMachines[machine.category]?.find(m => m.model === value);
            const machineData = selectedMachineOption ? selectedMachineOption.data : null;
            
            return {
              ...machine,
              model: value,
              machineData: machineData,
              selectedCards: [], // 重置板卡选择
              hourlyRate: 0 // 将由板卡选择决定
            };
          }
          return {
            ...machine,
            [field]: value
          };
        }
        return machine;
      })
    }));
  };

  // 处理板卡选择变化
  const handleCardSelection = (machineId, selectedCardIds) => {
    setFormData(prev => ({
      ...prev,
      machines: prev.machines.map(machine => {
        if (machine.id === machineId) {
          const selectedCards = cardTypes.filter(card => selectedCardIds.includes(card.id));
          // 使用当前的formData来计算，确保使用最新的币种和汇率
          const hourlyRate = calculateMachineHourlyRateForMachine(machine.machineData, selectedCards, prev.currency, prev.exchangeRate, prev.inquiryFactor, persistedCardQuantities);
          
          return {
            ...machine,
            selectedCards: selectedCards,
            hourlyRate: hourlyRate
          };
        }
        return machine;
      })
    }));
  };
  
  // 新增：为特定机器计算费率的辅助函数
  const calculateMachineHourlyRateForMachine = (machineData, selectedCards, currency, exchangeRate, inquiryFactor, quantities = null) => {
    if (!machineData || !selectedCards || selectedCards.length === 0) {
      return 0;
    }

    // 使用传入的quantities或全局的persistedCardQuantities
    const cardQuantities = quantities || persistedCardQuantities;

    const totalCardCost = selectedCards.reduce((sum, card) => {
      const quantity = cardQuantities[`${machineData.id}_${card.id}`] || 1;
      let adjustedPrice = card.unit_price / 10000; // 转换为万元
      
      // 根据报价币种和机器币种进行转换
      if (currency === 'USD') {
        if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
          // CNY机器转USD：使用报价汇率
          adjustedPrice = adjustedPrice / exchangeRate;
        }
        // USD机器：价格已经是USD，不需要转换
      } else {
        // 报价币种是CNY
        if (machineData.currency === 'USD') {
          // USD机器转CNY：使用机器的汇率
          adjustedPrice = adjustedPrice * (machineData.exchange_rate || 7.2);
        }
        // CNY机器：价格已经是CNY，不需要转换
      }
      
      // 应用折扣率和数量
      return sum + (adjustedPrice * (machineData.discount_rate || 1.0) * quantity);
    }, 0);

    // 应用询价系数
    const finalCost = totalCardCost * inquiryFactor;
    // 根据货币类型向上取整
    return ceilByCurrency(finalCost, currency);
  };

  // 处理板卡数量变化
  const handleCardQuantityChange = (machineId, cardId, quantity) => {
    // 找到对应的机器数据，使用真实的机器数据库ID
    const machine = formData.machines.find(m => m.id === machineId);
    const realMachineId = machine?.machineData?.id || machineId;
    const key = `${realMachineId}_${cardId}`;
    
    // 创建新的数量状态
    const newPersistedCardQuantities = {
      ...persistedCardQuantities,
      [key]: quantity
    };
    
    setPersistedCardQuantities(newPersistedCardQuantities);

    // 重新计算机器费率 - 使用新的数量状态
    setFormData(prev => ({
      ...prev,
      machines: prev.machines.map(machine => {
        if (machine.id === machineId) {
          const hourlyRate = calculateMachineHourlyRateForMachine(
            machine.machineData, 
            machine.selectedCards, 
            prev.currency, 
            prev.exchangeRate, 
            prev.inquiryFactor, 
            newPersistedCardQuantities
          );
          return {
            ...machine,
            hourlyRate: hourlyRate
          };
        }
        return machine;
      })
    }));
  };

  // 计算机器小时费率（基于选中的板卡）- 使用当前状态的数量
  const calculateMachineHourlyRate = (machineData, selectedCards) => {
    return calculateMachineHourlyRateForMachine(
      machineData, 
      selectedCards, 
      formData.currency, 
      formData.exchangeRate, 
      formData.inquiryFactor, 
      persistedCardQuantities
    );
  };

  // 计算机器小时费率（基于选中的板卡）- 可指定数量状态
  const calculateMachineHourlyRateWithQuantities = (machineData, selectedCards, quantities) => {
    if (!machineData || !selectedCards || selectedCards.length === 0) {
      return 0;
    }

    const totalCardCost = selectedCards.reduce((sum, card) => {
      const quantity = quantities[`${machineData.id}_${card.id}`] || 1;
      let adjustedPrice = card.unit_price / 10000; // 转换为万元
      
      // 根据报价币种和机器币种进行转换
      if (formData.currency === 'USD') {
        if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
          // CNY机器转USD：使用报价汇率
          adjustedPrice = adjustedPrice / formData.exchangeRate;
        }
        // USD机器：价格已经是USD，不需要转换
      } else {
        // 报价币种是CNY
        if (machineData.currency === 'USD') {
          // USD机器转CNY：使用机器的汇率
          adjustedPrice = adjustedPrice * (machineData.exchange_rate || 7.2);
        }
        // CNY机器：价格已经是CNY，不需要转换
      }
      
      // 应用折扣率和数量
      return sum + (adjustedPrice * (machineData.discount_rate || 1.0) * quantity);
    }, 0);

    // 应用询价系数（类似工程系数）
    const finalCost = totalCardCost * formData.inquiryFactor;
    // 根据货币类型向上取整
    return ceilByCurrency(finalCost, formData.currency);
  };

  // 格式化价格显示
  const formatPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, formData.currency);
    const symbol = currencies.find(c => c.value === formData.currency)?.symbol || '￥';
    return `${symbol}${formattedNumber}`;
  };

  // 格式化机时价格显示（包含币种符号，根据币种精度）
  const formatHourlyPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, formData.currency);
    const symbol = currencies.find(c => c.value === formData.currency)?.symbol || '￥';
    return `${symbol}${formattedNumber}`;
  };

  // 板卡表格列定义
  const cardColumns = (machineId) => {
    // 获取真实的机器数据库ID
    const machine = formData.machines.find(m => m.id === machineId);
    const realMachineId = machine?.machineData?.id || machineId;
    
    const columns = [
      { title: 'Part Number', dataIndex: 'part_number' },
      { title: 'Board Name', dataIndex: 'board_name' },
    ];
    
    // 只有管理员以上权限才能看到价格
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      columns.push({ 
        title: 'Unit Price', 
        dataIndex: 'unit_price',
        render: (value) => formatQuotePrice(value || 0, formData.currency)
      });
    }
    
    columns.push({ 
      title: 'Quantity', 
      render: (_, record) => (
        <InputNumber 
          min={1} 
          value={persistedCardQuantities[`${realMachineId}_${record.id}`] || 1}
          onChange={(value) => handleCardQuantityChange(machineId, record.id, value)}
          />
        ) 
      }
    );
    
    return columns;
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

  const handleSubmit = () => {
    const totalRate = formData.machines.reduce((sum, machine) => sum + machine.hourlyRate, 0);
    
    const quoteData = {
      type: '询价报价',
      number: `INQ-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-${String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')}`,
      date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      customerInfo: formData.customerInfo,
      projectInfo: formData.projectInfo,
      machines: formData.machines,
      totalHourlyRate: totalRate,
      inquiryFactor: formData.inquiryFactor,
      currency: formData.currency,
      exchangeRate: formData.exchangeRate,  // 添加汇率
      remarks: formData.remarks,
      generatedAt: new Date().toISOString(),
      items: [
        {
          category: '询价设备配置',
          items: formData.machines.map(machine => ({
            name: `${machine.model || '未选择'} (${machineCategories.find(c => c.value === machine.category)?.label || machine.category})`,
            specification: `机时费率: ${formatHourlyPrice(machine.hourlyRate)}/小时`,
            quantity: 1,
            unit: '台',
            unitPrice: machine.hourlyRate,
            totalPrice: machine.hourlyRate
          }))
        }
      ],
      totalAmount: totalRate,
      quoteCurrency: formData.currency
    };

    navigate('/quote-result', { state: quoteData });
  };

  const handleBack = () => {
    // 保持当前状态并返回报价类型选择页面
    navigate('/quote-type-selection', { 
      state: { 
        preserveState: true,
        pageType: 'inquiry-quote' 
      } 
    });
  };

  return (
    <div className="quote-container">
      <PageTitle 
        title="询价报价" 
        subtitle="快速获取参考价格，非正式报价" 
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
            <label>紧急程度</label>
            <select
              value={formData.projectInfo.urgency}
              onChange={(e) => handleInputChange('projectInfo', 'urgency', e.target.value)}
            >
              <option value="normal">正常</option>
              <option value="urgent">紧急</option>
              <option value="very_urgent">非常紧急</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <div className="section-header">
          <h3>设备选择</h3>
          <SecondaryButton onClick={addMachine}>
            增加机器
          </SecondaryButton>
        </div>
        
        {formData.machines.map((machine, index) => (
          <div key={machine.id} className="machine-selection-card">
            <div className="machine-header">
              <h4>机器 {index + 1}</h4>
              {formData.machines.length > 1 && (
                <button 
                  type="button"
                  className="remove-machine-btn"
                  onClick={() => removeMachine(machine.id)}
                >
                  删除
                </button>
              )}
            </div>
            
            <div className="form-grid">
              <div className="form-group">
                <label>设备类型 *</label>
                <select
                  value={machine.category}
                  onChange={(e) => updateMachine(machine.id, 'category', e.target.value)}
                  required
                >
                  <option value="">请选择设备类型</option>
                  {machineCategories.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>设备型号 *</label>
                <select
                  value={machine.model}
                  onChange={(e) => updateMachine(machine.id, 'model', e.target.value)}
                  disabled={!machine.category}
                  required
                >
                  <option value="">请选择设备型号</option>
                  {machine.category && availableMachines[machine.category]?.map(model => (
                    <option key={model.model} value={model.model}>
                      {model.model}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>机时费率</label>
                <div className="rate-display">
                  {formatHourlyPrice(machine.hourlyRate)}/小时
                </div>
              </div>
            </div>
            
            {/* 板卡选择区域 */}
            {machine.machineData && (
              <div className="card-selection-section">
                <h5>选择板卡配置</h5>
                {(() => {
                  const availableCards = cardTypes.filter(card => card.machine_id === machine.machineData.id);
                  return availableCards.length > 0 ? (
                    <Table 
                      dataSource={availableCards}
                      rowKey="id"
                      rowSelection={{
                        selectedRowKeys: machine.selectedCards.map(card => card.id),
                        onChange: (selectedRowKeys) => handleCardSelection(machine.id, selectedRowKeys)
                      }}
                      columns={cardColumns(machine.id)}
                      pagination={{ pageSize: 3, showSizeChanger: false }}
                      size="small"
                    />
                  ) : (
                    <div className="no-cards-message">
                      该设备暂无可用板卡配置
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="form-section">
        <h3>报价设置</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>报价货币 *</label>
            <select
              value={formData.currency}
              onChange={(e) => {
                const newCurrency = e.target.value;
                setFormData(prev => ({
                  ...prev,
                  currency: newCurrency,
                  machines: prev.machines.map(machine => {
                    if (machine.machineData && machine.selectedCards.length > 0) {
                      const hourlyRate = calculateMachineHourlyRateForMachine(
                        machine.machineData,
                        machine.selectedCards,
                        newCurrency,
                        prev.exchangeRate,
                        prev.inquiryFactor,
                        persistedCardQuantities
                      );
                      return { ...machine, hourlyRate };
                    }
                    return machine;
                  })
                }));
              }}
              required
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
              <label>汇率 (1 USD = ? CNY)</label>
              <input
                type="number"
                value={formData.exchangeRate}
                onChange={(e) => {
                  const newExchangeRate = parseFloat(e.target.value) || 7.2;
                  setFormData(prev => ({
                    ...prev,
                    exchangeRate: newExchangeRate,
                    machines: prev.machines.map(machine => {
                      if (machine.machineData && machine.selectedCards.length > 0) {
                        const hourlyRate = calculateMachineHourlyRateForMachine(
                          machine.machineData,
                          machine.selectedCards,
                          prev.currency,
                          newExchangeRate,
                          prev.inquiryFactor,
                          persistedCardQuantities
                        );
                        return { ...machine, hourlyRate };
                      }
                      return machine;
                    })
                  }));
                }}
                min="6.0"
                max="8.0"
                step="0.01"
                placeholder="7.2"
              />
              <small className="help-text">
                用于将CNY价格转换为USD
              </small>
            </div>
          )}
          <div className="form-group">
            <label>询价系数</label>
            <input
              type="number"
              value={formData.inquiryFactor}
              onChange={(e) => {
                const newInquiryFactor = parseFloat(e.target.value) || 1.5;
                setFormData(prev => ({
                  ...prev,
                  inquiryFactor: newInquiryFactor,
                  machines: prev.machines.map(machine => {
                    if (machine.machineData && machine.selectedCards.length > 0) {
                      const hourlyRate = calculateMachineHourlyRateForMachine(
                        machine.machineData,
                        machine.selectedCards,
                        prev.currency,
                        prev.exchangeRate,
                        newInquiryFactor,
                        persistedCardQuantities
                      );
                      return { ...machine, hourlyRate };
                    }
                    return machine;
                  })
                }));
              }}
              min="1.0"
              max="3.0"
              step="0.1"
              placeholder="1.5"
            />
            <small className="help-text">
              询价系数用于调整基础费率，一般为1.2-2.0倍
            </small>
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
        <div className="summary-item">
          <span>总机时费率：</span>
          <span className="summary-value">
            {formatHourlyPrice(formData.machines.reduce((sum, machine) => sum + machine.hourlyRate, 0))}/小时
          </span>
        </div>
      </div>

      <div className="button-group">
        <SecondaryButton onClick={handleBack}>
          返回
        </SecondaryButton>
        <PrimaryButton onClick={handleSubmit}>
          生成询价单
        </PrimaryButton>
      </div>
    </div>
  );
};

export default InquiryQuote;