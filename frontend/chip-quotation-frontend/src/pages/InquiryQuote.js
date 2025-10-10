import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Table, InputNumber, message } from 'antd';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { formatHourlyRate, ceilByCurrency, formatQuotePrice } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import useQuoteEditMode from '../hooks/useQuoteEditMode';
import { QuoteApiService } from '../services/quoteApi';
import '../App.css';

const InquiryQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // 编辑模式相关状态
  const { isEditMode, editingQuote, loading: editLoading, convertQuoteToFormData } = useQuoteEditMode();
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
      testType: 'mixed',
      urgency: 'normal',
      quoteUnit: '昆山芯信安'  // 默认选择第一个
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

  const [availableMachines, setAvailableMachines] = useState({});
  const [loading, setLoading] = useState(false);
  const [backendMachines, setBackendMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);
  const [persistedCardQuantities, setPersistedCardQuantities] = useState({});
  const [isMounted, setIsMounted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editMessageShown, setEditMessageShown] = useState(false);
  const [machineTypes, setMachineTypes] = useState([]);

  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' }
  ];

  // 从后端获取机器和板卡数据，然后处理状态恢复
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [machinesData, cardTypesData, hierarchicalData] = await Promise.all([
          getMachines(),
          getCardTypes(),
          fetch('/api/v1/hierarchical/machine-types').then(res => res.json())
        ]);

        setBackendMachines(machinesData);
        setCardTypes(cardTypesData);

        // 从hierarchical API提取设备类型
        const types = hierarchicalData.map(type => ({
          id: type.id,
          name: type.name
        }));
        setMachineTypes(types);

        // 按机器类型ID分类设备
        const categorizedMachines = {};

        machinesData.forEach(machine => {
          // 获取机器的类型ID
          let machineTypeId = null;
          if (machine.supplier && machine.supplier.machine_type) {
            machineTypeId = machine.supplier.machine_type.id;
          } else if (machine.supplier && machine.supplier.machine_type_id) {
            machineTypeId = machine.supplier.machine_type_id;
          }

          if (machineTypeId) {
            if (!categorizedMachines[machineTypeId]) {
              categorizedMachines[machineTypeId] = [];
            }
            categorizedMachines[machineTypeId].push({
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
              setFormData(parsedState.formData);
              setPersistedCardQuantities(parsedState.persistedCardQuantities || {});
            } catch (error) {
              console.error('解析保存状态时出错:', error);
            }
          }
        } else {
          sessionStorage.removeItem('inquiryQuoteState');
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

  // 编辑模式数据预填充
  useEffect(() => {
    if (isEditMode && editingQuote && !editLoading && isMounted) {
      const convertedFormData = convertQuoteToFormData(editingQuote, 'inquiry');
      if (convertedFormData) {
        setFormData(convertedFormData);
        // 只在第一次显示消息
        if (!editMessageShown) {
          message.info(`正在编辑报价单: ${editingQuote.quote_number || editingQuote.id || '未知'}`);
          setEditMessageShown(true);
        }
      }
    }
  }, [isEditMode, editingQuote, editLoading, isMounted, editMessageShown]);

  // 重置编辑消息标志
  useEffect(() => {
    if (!isEditMode) {
      setEditMessageShown(false);
    }
  }, [isEditMode]);

  // 根据类型ID获取类型名称
  const getMachineTypeName = (typeId) => {
    const type = machineTypes.find(t => t.id === typeId);
    return type ? type.name : '';
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

  // 生成临时报价单号（与后端格式保持一致）
  const generateTempQuoteNumber = (quoteUnit) => {
    const unitMapping = {
      "昆山芯信安": "KS",
      "苏州芯昱安": "SZ", 
      "上海芯睿安": "SH",
      "珠海芯创安": "ZH"
    };
    const unitAbbr = unitMapping[quoteUnit] || "KS";
    const dateStr = new Date().toISOString().slice(0,10).replace(/-/g,"");
    const randomSeq = String(Math.floor(Math.random() * 999) + 1).padStart(3, '0');
    return `CIS-${unitAbbr}${dateStr}${randomSeq}`;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    try {
      // 映射测试类型值到显示名称
      const testTypeMap = {
        'CP': 'CP测试',
        'FT': 'FT测试',
        'mixed': '混合测试'
      };
      const testTypeDisplay = testTypeMap[formData.projectInfo.testType] || '混合测试';

      const totalRate = formData.machines.reduce((sum, machine) => sum + machine.hourlyRate, 0);

      // 准备API数据
      const apiData = {
        title: `${formData.customerInfo.companyName} - ${formData.projectInfo.projectName || '询价项目'}`,
        quote_type: 'inquiry',
        customer_name: formData.customerInfo.companyName,
        customer_contact: formData.customerInfo.contactPerson,
        customer_phone: formData.customerInfo.phone || '',
        customer_email: formData.customerInfo.email || '',
        quote_unit: formData.projectInfo.quoteUnit,
        currency: formData.currency,
        subtotal: totalRate,
        discount: 0.0,
        tax_rate: 0.0,
        tax_amount: 0.0,
        total_amount: totalRate,
        description: `芯片封装: ${formData.projectInfo.chipPackage}, 测试类型: ${testTypeDisplay}`,
        notes: formData.remarks || '',
        items: formData.machines.map(machine => {
          const categoryLabel = getMachineTypeName(machine.category) || '未知类型';

          return {
            item_name: testTypeDisplay,
            item_description: `设备: ${machine.model || '未选择'} (${categoryLabel}), 机时费率: ${formatHourlyPrice(machine.hourlyRate)}/小时, 询价系数: ${formData.inquiryFactor}`,
            machine_type: categoryLabel,
            machine_model: machine.model || '未选择',
            configuration: machine.selectedCards.map(card => card.board_name).join(', ') || '无板卡',
            quantity: 1,
            unit: '台·小时',
            unit_price: machine.hourlyRate,
            total_price: machine.hourlyRate,
            machine_id: machine.machineData?.id || null
          };
        })
      };

      let response;

      if (isEditMode && editingQuote) {
        // 编辑模式：更新现有报价
        response = await QuoteApiService.updateQuote(editingQuote.id, apiData);

        // 编辑成功后跳转到报价详情页面
        navigate(`/quote-detail/${editingQuote.quote_number}`, {
          state: {
            message: '报价单更新成功',
            updatedQuote: response
          }
        });
      } else {
        // 新建模式：创建新报价或跳转到结果页面
        // 准备结果页面数据（保持原有逻辑）
        const quoteData = {
          type: '询价报价',
          number: generateTempQuoteNumber(formData.projectInfo.quoteUnit),
          date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          customerInfo: formData.customerInfo,
          projectInfo: formData.projectInfo,
          machines: formData.machines,
          totalHourlyRate: totalRate,
          inquiryFactor: formData.inquiryFactor,
          currency: formData.currency,
          exchangeRate: formData.exchangeRate,
          remarks: formData.remarks,
          generatedAt: new Date().toISOString(),
          items: [
            {
              category: '询价设备配置',
              items: formData.machines.map(machine => ({
                name: `${machine.model || '未选择'} (${getMachineTypeName(machine.category) || '未知类型'})`,
                specification: `机时费率: ${formatHourlyPrice(machine.hourlyRate)}/小时`,
                quantity: 1,
                unit: '台',
                unitPrice: machine.hourlyRate,
                totalPrice: machine.hourlyRate
              }))
            }
          ],
          totalAmount: totalRate,
          quoteCurrency: formData.currency,
          // 添加报价单数据结构，供结果页面确认时使用
          quoteCreateData: apiData
        };

        navigate('/quote-result', { state: quoteData });
      }

    } catch (error) {
      console.error('提交报价失败:', error);
      alert('提交失败，请检查网络连接或稍后重试');
    } finally {
      setIsSubmitting(false);
    }
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
        title={isEditMode ? "编辑询价报价" : "询价报价"}
        subtitle={isEditMode ? `编辑报价单 ${editingQuote?.quote_number || editingQuote?.id || ''}` : "快速获取参考价格，非正式报价"}
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
          <div className="form-group">
            <label>报价单位</label>
            <select
              value={formData.projectInfo.quoteUnit}
              onChange={(e) => handleInputChange('projectInfo', 'quoteUnit', e.target.value)}
            >
              <option value="昆山芯信安">昆山芯信安</option>
              <option value="苏州芯昱安">苏州芯昱安</option>
              <option value="上海芯睿安">上海芯睿安</option>
              <option value="珠海芯创安">珠海芯创安</option>
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
                  {machineTypes.map(type => (
                    <option key={type.id} value={type.id}>
                      {type.name}
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
        <PrimaryButton onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? '提交中...' : (isEditMode ? '更新询价单' : '生成询价单')}
        </PrimaryButton>
      </div>
    </div>
  );
};

export default InquiryQuote;