import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Checkbox, Card, Button, Table, InputNumber, message } from 'antd';
import { PrimaryButton, SecondaryButton, PageTitle } from '../components/CommonComponents';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { ceilByCurrency, formatQuotePrice } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import useQuoteEditMode from '../hooks/useQuoteEditMode';
import { QuoteApiService } from '../services/quoteApi';
import '../App.css';

const ProcessQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // 编辑模式相关状态
  const { isEditMode, editingQuote, loading: editLoading, convertQuoteToFormData } = useQuoteEditMode();

  const [machines, setMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const [editMessageShown, setEditMessageShown] = useState(false);

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
      quoteUnit: '昆山芯信安'
    },
    selectedTypes: ['cp'], // 默认选择CP
    cpProcesses: [
      {
        id: 1,
        name: 'CP1测试',
        // CP工序包含两种设备：测试机和探针台
        testMachine: '',
        testMachineData: null,
        testMachineCardQuantities: {},
        prober: '',
        proberData: null,
        proberCardQuantities: {},
        uph: 1000,
        unitCost: 0
      }
    ],
    ftProcesses: [
      {
        id: 1,
        name: 'FT1测试',
        // FT工序包含两种设备：测试机和分选机
        testMachine: '',
        testMachineData: null,
        testMachineCardQuantities: {},
        handler: '',
        handlerData: null,
        handlerCardQuantities: {},
        uph: 1000,
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
        setIsMounted(true);
        
        // 检查是否从结果页返回
        const isFromResultPage = location.state?.fromResultPage;
        
        if (isFromResultPage) {
          // 从结果页返回时，恢复之前保存的状态
          const savedState = sessionStorage.getItem('processQuoteState');
          if (savedState) {
            try {
              const parsedState = JSON.parse(savedState);
              console.log('从 sessionStorage 恢复工序报价状态:', parsedState);
              setFormData(parsedState);
            } catch (error) {
              console.error('恢复状态失败:', error);
            }
          }
        } else {
          // 正常进入页面时清空之前的状态
          sessionStorage.removeItem('processQuoteState');
          console.log('开始全新工序报价流程');
        }
        
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [location.state?.fromResultPage]);


  // 状态保存 - 仅在组件挂载完成后保存
  useEffect(() => {
    if (isMounted && !loading) {
      sessionStorage.setItem('processQuoteState', JSON.stringify(formData));
    }
  }, [formData, isMounted, loading]);

  // 编辑模式：预填充报价数据
  useEffect(() => {
    if (isEditMode && editingQuote && machines.length > 0 && cardTypes.length > 0) {
      console.log('工序报价编辑模式：预填充数据', editingQuote);

      // 使用转换函数将报价数据转换为表单数据
      const convertedFormData = convertQuoteToFormData(
        editingQuote,
        'process',
        cardTypes,
        machines
      );

      if (convertedFormData) {
        console.log('转换后的表单数据:', convertedFormData);
        setFormData(prev => ({
          ...prev,
          ...convertedFormData
        }));
      }
    }
  }, [isEditMode, editingQuote, machines, cardTypes, convertQuoteToFormData]);

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
      // 根据类型设置双设备结构
      ...(type === 'cp' ? {
        testMachine: '',
        testMachineData: null,
        testMachineCardQuantities: {},
        prober: '',
        proberData: null,
        proberCardQuantities: {}
      } : {
        testMachine: '',
        testMachineData: null,
        testMachineCardQuantities: {},
        handler: '',
        handlerData: null,
        handlerCardQuantities: {}
      }),
      uph: 1000,
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

  // 更新工序 - 支持双设备结构
  const updateProcess = (type, processId, field, value) => {
    console.log('updateProcess called:', { type, processId, field, value });
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          let updatedProcess = { ...process, [field]: value };
          
          // 如果改变了工序名称，重置所有设备选择
          if (field === 'name') {
            if (type === 'cp') {
              updatedProcess.testMachine = '';
              updatedProcess.testMachineData = null;
              updatedProcess.testMachineCardQuantities = {};
              updatedProcess.prober = '';
              updatedProcess.proberData = null;
              updatedProcess.proberCardQuantities = {};
            } else {
              updatedProcess.testMachine = '';
              updatedProcess.testMachineData = null;
              updatedProcess.testMachineCardQuantities = {};
              updatedProcess.handler = '';
              updatedProcess.handlerData = null;
              updatedProcess.handlerCardQuantities = {};
            }
          }
          
          // 处理测试机选择
          if (field === 'testMachine') {
            const selectedMachine = machines.find(m => m.name === value);
            updatedProcess.testMachineData = selectedMachine;
            updatedProcess.testMachineCardQuantities = {};
          }
          
          // 处理第二种设备选择 (CP: prober, FT: handler)
          if ((type === 'cp' && field === 'prober') || (type === 'ft' && field === 'handler')) {
            const selectedMachine = machines.find(m => m.name === value);
            const dataField = type === 'cp' ? 'proberData' : 'handlerData';
            const cardField = type === 'cp' ? 'proberCardQuantities' : 'handlerCardQuantities';
            updatedProcess[dataField] = selectedMachine;
            updatedProcess[cardField] = {};
          }
          
          // 人工成本设置为0，不进行自动计算
          if (field === 'uph') {
            updatedProcess.unitCost = 0;
          }
          
          return updatedProcess;
        }
        return process;
      })
    }));
  };

  // 处理板卡选择变化
  const handleCardSelection = (type, processId, selectedRowKeys, selectedRows, deviceName = 'testMachine') => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    const cardQuantitiesKey = `${deviceName}CardQuantities`;
    
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          const newCardQuantities = {};
          selectedRows.forEach(card => {
            // 保持已有的数量，如果没有则设为1
            newCardQuantities[card.id] = process[cardQuantitiesKey]?.[card.id] || 1;
          });
          return {
            ...process,
            [cardQuantitiesKey]: newCardQuantities
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
  const handleCardQuantityChange = (type, processId, cardId, quantity, deviceName = 'testMachine') => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    const cardQuantitiesKey = `${deviceName}CardQuantities`;
    
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          const updatedQuantities = { ...process[cardQuantitiesKey] };
          if (quantity > 0) {
            updatedQuantities[cardId] = quantity;
          } else {
            delete updatedQuantities[cardId];
          }
          return {
            ...process,
            [cardQuantitiesKey]: updatedQuantities
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

  // 计算单个设备的机器费用（包括板卡成本）- 支持双设备
  const calculateProcessMachineCostForDevice = (process, deviceName) => {
    const machineDataKey = `${deviceName}Data`;
    const cardQuantitiesKey = `${deviceName}CardQuantities`;
    
    const machineData = process[machineDataKey];
    const cardQuantities = process[cardQuantitiesKey];
    
    if (!machineData || !cardQuantities) {
      console.log(`calculateProcessMachineCostForDevice: No ${deviceName} data or card quantities`, { 
        machineData: machineData, 
        cardQuantities: cardQuantities 
      });
      return 0;
    }
    
    console.log(`calculateProcessMachineCostForDevice for ${deviceName} in process:`, process.name, 'Machine:', process[deviceName], 'UPH:', process.uph);
    console.log(`${deviceName} Card quantities:`, cardQuantities);
    
    let totalCost = 0;
    Object.entries(cardQuantities).forEach(([cardId, quantity]) => {
      const card = cardTypes.find(c => c.id === parseInt(cardId));
      if (card && quantity > 0) {
        console.log(`Processing ${deviceName} card ${card.part_number}: price=${card.unit_price}, quantity=${quantity}`);
        
        // 计算调整后的板卡价格，参考工程机时的计算逻辑
        let adjustedPrice = (card.unit_price || 0) / 10000;
        console.log(`Adjusted price after /10000: ${adjustedPrice}`);
        
        // 根据报价币种和机器币种进行转换（参考EngineeringQuote.js逻辑）
        if (formData.currency === 'USD') {
          if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
            // RMB机器转USD：除以报价汇率
            adjustedPrice = adjustedPrice / formData.exchangeRate;
            console.log(`Converted CNY to USD: ${adjustedPrice} (rate: ${formData.exchangeRate})`);
          }
          // USD机器：不做汇率转换，直接使用unit_price
        } else {
          // 报价币种是CNY，保持原逻辑
          adjustedPrice = adjustedPrice * (machineData.exchange_rate || 1.0);
          console.log(`Applied exchange rate: ${adjustedPrice} (rate: ${machineData.exchange_rate})`);
        }
        
        // 应用折扣率和数量，然后除以UPH得到单颗成本
        const hourlyCost = adjustedPrice * (machineData.discount_rate || 1.0) * quantity;
        console.log(`${deviceName} Hourly cost: ${adjustedPrice} * ${machineData.discount_rate} * ${quantity} = ${hourlyCost}`);
        
        if (process.uph > 0) {
          const unitCost = hourlyCost / process.uph;
          console.log(`${deviceName} Unit cost: ${hourlyCost} / ${process.uph} = ${unitCost}`);
          totalCost += unitCost;
        } else {
          console.log('UPH is 0 or undefined, unit cost = 0');
        }
      }
    });
    
    console.log(`Total ${deviceName} cost for ${process.name}: ${totalCost}`);
    return totalCost;
  };

  // 计算总成本（人工成本 + 双设备机器成本）
  const calculateTotalUnitCost = () => {
    let total = 0;
    
    if (formData.selectedTypes.includes('cp')) {
      total += formData.cpProcesses.reduce((sum, process) => {
        const laborCost = process.unitCost || 0; // 人工成本
        // 双设备机器成本：测试机 + 探针台
        const testMachineCost = calculateProcessMachineCostForDevice(process, 'testMachine');
        const proberCost = calculateProcessMachineCostForDevice(process, 'prober');
        const totalMachineCost = testMachineCost + proberCost;
        return sum + laborCost + totalMachineCost;
      }, 0);
    }
    
    if (formData.selectedTypes.includes('ft')) {
      total += formData.ftProcesses.reduce((sum, process) => {
        const laborCost = process.unitCost || 0; // 人工成本
        // 双设备机器成本：测试机 + 分选机
        const testMachineCost = calculateProcessMachineCostForDevice(process, 'testMachine');
        const handlerCost = calculateProcessMachineCostForDevice(process, 'handler');
        const totalMachineCost = testMachineCost + handlerCost;
        return sum + laborCost + totalMachineCost;
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

  // 生成临时报价编号
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

  // 生成工序报价项（应用板卡JSON序列化模式）
  const generateProcessQuoteItems = () => {
    const items = [];

    // 辅助函数：获取板卡信息数组
    const getCardsInfo = (cardQuantities) => {
      if (!cardQuantities || Object.keys(cardQuantities).length === 0) return [];
      return Object.entries(cardQuantities).map(([cardId, quantity]) => {
        const card = cardTypes.find(c => c.id === parseInt(cardId));
        return {
          id: parseInt(cardId),
          board_name: card?.board_name || '',
          part_number: card?.part_number || '',
          quantity: quantity || 1
        };
      });
    };

    // 1. 处理CP工序
    if (formData.selectedTypes.includes('cp')) {
      formData.cpProcesses.forEach((process, index) => {
        if (process.testMachine || process.prober) {
          // 计算工序单颗成本（保留4位小数）
          const unitCost = parseFloat(formatUnitPrice(process.unitCost).replace(/[￥$,]/g, ''));

          // 准备工序配置JSON
          const configuration = {
            process_type: process.name,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            prober: process.proberData ? {
              id: process.proberData.id,
              name: process.prober,
              cards: getCardsInfo(process.proberCardQuantities)
            } : null,
            uph: process.uph,
            unit_cost: unitCost
          };

          items.push({
            item_name: `CP工序 - ${process.name}`,
            item_description: `${process.name} (UPH: ${process.uph})`,
            machine_type: 'CP工序',
            supplier: process.testMachineData?.supplier
              ? (typeof process.testMachineData.supplier === 'object'
                  ? process.testMachineData.supplier.name
                  : process.testMachineData.supplier)
              : '',
            machine_model: process.testMachine || '',
            configuration: JSON.stringify(configuration),
            quantity: 1,
            unit: '颗',
            unit_price: unitCost,
            total_price: unitCost, // 工序报价单颗成本即总价
            machine_id: process.testMachineData?.id || null,
            category_type: 'process'
          });
        }
      });
    }

    // 2. 处理FT工序
    if (formData.selectedTypes.includes('ft')) {
      formData.ftProcesses.forEach((process, index) => {
        if (process.testMachine || process.handler) {
          // 计算工序单颗成本（保留4位小数）
          const unitCost = parseFloat(formatUnitPrice(process.unitCost).replace(/[￥$,]/g, ''));

          // 准备工序配置JSON
          const configuration = {
            process_type: process.name,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            handler: process.handlerData ? {
              id: process.handlerData.id,
              name: process.handler,
              cards: getCardsInfo(process.handlerCardQuantities)
            } : null,
            uph: process.uph,
            unit_cost: unitCost
          };

          items.push({
            item_name: `FT工序 - ${process.name}`,
            item_description: `${process.name} (UPH: ${process.uph})`,
            machine_type: 'FT工序',
            supplier: process.testMachineData?.supplier
              ? (typeof process.testMachineData.supplier === 'object'
                  ? process.testMachineData.supplier.name
                  : process.testMachineData.supplier)
              : '',
            machine_model: process.testMachine || '',
            configuration: JSON.stringify(configuration),
            quantity: 1,
            unit: '颗',
            unit_price: unitCost,
            total_price: unitCost, // 工序报价单颗成本即总价
            machine_id: process.testMachineData?.id || null,
            category_type: 'process'
          });
        }
      });
    }

    return items;
  };

  // 提交处理
  const handleSubmit = async () => {
    // 生成报价项（包含JSON序列化的工序配置）
    const quoteItems = generateProcessQuoteItems();

    // 准备数据库创建/更新数据
    const quoteCreateData = {
      quote_type: '工序报价',
      customer_name: formData.customerInfo.companyName,
      contact_person: formData.customerInfo.contactPerson,
      contact_phone: formData.customerInfo.phone || '',
      contact_email: formData.customerInfo.email || '',
      project_name: formData.projectInfo.projectName,
      chip_package: formData.projectInfo.chipPackage || '',
      test_type: formData.projectInfo.testType || '',
      quote_unit: formData.projectInfo.quoteUnit,
      currency: formData.currency,
      exchange_rate: formData.exchangeRate,
      total_amount: calculateTotalUnitCost(),
      remarks: formData.remarks || '',
      items: quoteItems
    };

    // 完成报价，将数据传递到结果页面
    const tempQuoteNumber = generateTempQuoteNumber(formData.projectInfo.quoteUnit);
    const quoteData = {
      type: '工序报价',
      number: tempQuoteNumber,
      date: new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }),
      ...formData,
      cardTypes,
      totalUnitCost: calculateTotalUnitCost(),
      totalProjectCost: calculateTotalProjectCost(),
      generatedAt: new Date().toISOString(),
      quoteCreateData,
      // 编辑模式相关字段
      isEditMode: isEditMode || false,
      editingQuoteId: isEditMode && editingQuote ? editingQuote.id : null,
      quoteNumber: isEditMode && editingQuote ? editingQuote.quote_number : null
    };

    if (isEditMode && editingQuote) {
      // 编辑模式：调用API更新报价
      try {
        const updatedQuote = await QuoteApiService.updateQuote(editingQuote.id, quoteCreateData);
        // 编辑成功后跳转到报价详情页面
        navigate(`/quote-detail/${editingQuote.quote_number}`, {
          state: {
            message: '报价单更新成功',
            updatedQuote: updatedQuote
          }
        });
      } catch (error) {
        console.error('更新工序报价失败:', error);
      }
    } else {
      // 新建模式：通过location.state传递数据到结果页面
      navigate('/quote-result', { state: { ...quoteData, fromQuotePage: true } });
    }
  };

  const handleBack = () => {
    // 保存工序数组到 sessionStorage（用于"上一步"功能）
    const processData = {
      selectedTypes: formData.selectedTypes,
      cpProcesses: formData.cpProcesses,
      ftProcesses: formData.ftProcesses,
      currency: formData.currency,
      exchangeRate: formData.exchangeRate
    };
    sessionStorage.setItem('processQuoteProcessData', JSON.stringify(processData));

    // 保持当前状态并返回报价类型选择页面
    navigate('/quote-type-selection', {
      state: {
        preserveState: true,
        pageType: 'process-quote'
      }
    });
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



  // 判断是否为测试工序（需要双设备）
  const isTestProcess = (processName) => {
    if (!processName) return false;
    return (processName.includes('CP') && (processName.includes('1') || processName.includes('2') || processName.includes('3'))) ||
           (processName.includes('FT') && (processName.includes('1') || processName.includes('2') || processName.includes('3')));
  };

  // 工序表格列定义
  const getProcessColumns = (type) => {
    const baseColumns = [
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
      }
    ];


    // 动态添加设备列的逻辑需要在render时处理，这里先添加一个固定的设备列结构
    baseColumns.push({
      title: '设备选择',
      key: 'equipment',
      render: (_, record) => {
        const isTest = isTestProcess(record.name);
        
        if (isTest) {
          // 测试工序：显示两个设备选择器
          return (
            <div style={{ display: 'flex', gap: '8px', flexDirection: 'column' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>测试机:</label>
                <select
                  value={record.testMachine || ''}
                  onChange={(e) => updateProcess(type, record.id, 'testMachine', e.target.value)}
                  style={{ width: '100%', padding: '4px', marginTop: '2px' }}
                  disabled={!record.name}
                >
                  <option value="">请选择测试机</option>
                  {machines.filter(m => m.supplier?.machine_type?.name?.includes('测试机')).map(machineData => (
                    <option key={machineData.id} value={machineData.name}>
                      {machineData.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>{type === 'cp' ? '探针台:' : '分选机:'}</label>
                <select
                  value={record[type === 'cp' ? 'prober' : 'handler'] || ''}
                  onChange={(e) => updateProcess(type, record.id, type === 'cp' ? 'prober' : 'handler', e.target.value)}
                  style={{ width: '100%', padding: '4px', marginTop: '2px' }}
                  disabled={!record.name}
                >
                  <option value="">{`请选择${type === 'cp' ? '探针台' : '分选机'}`}</option>
                  {machines.filter(m => {
                    const machineTypeName = m.supplier?.machine_type?.name || '';
                    return type === 'cp' ? machineTypeName.includes('探针台') : machineTypeName.includes('分选机');
                  }).map(machineData => (
                    <option key={machineData.id} value={machineData.name}>
                      {machineData.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          );
        } else if (record.name) {
          // 非测试工序：显示单设备选择器
          return (
            <select
              value={record.testMachine || ''}
              onChange={(e) => updateProcess(type, record.id, 'testMachine', e.target.value)}
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
          );
        } else {
          return <span style={{ color: '#ccc' }}>请先选择工序</span>;
        }
      }
    });

    baseColumns.push({
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
    });

    baseColumns.push({
      title: '单颗费用',
      dataIndex: 'unitCost',
      render: (unitCost, record) => {
        const laborCost = unitCost || 0;
        const isTest = isTestProcess(record.name);
        
        if (isTest) {
          // 测试工序：计算双设备成本
          const testMachineCost = calculateProcessMachineCostForDevice(record, 'testMachine');
          const secondDeviceCost = calculateProcessMachineCostForDevice(record, type === 'cp' ? 'prober' : 'handler');
          const totalMachineCost = testMachineCost + secondDeviceCost;
          const totalCost = laborCost + totalMachineCost;
          
          return (
            <div>
              <div>{formatUnitPrice(totalCost)}</div>
              {totalMachineCost > 0 && (
                <div style={{ fontSize: '11px', color: '#666' }}>
                  人工: {formatUnitPrice(laborCost)}<br/>
                  {testMachineCost > 0 && <>测试机: {formatUnitPrice(testMachineCost)}<br/></>}
                  {secondDeviceCost > 0 && <>{type === 'cp' ? '探针台' : '分选机'}: {formatUnitPrice(secondDeviceCost)}</>}
                </div>
              )}
            </div>
          );
        } else {
          // 非测试工序：计算单设备成本
          const machineCost = calculateProcessMachineCostForDevice(record, 'testMachine');
          const totalCost = laborCost + machineCost;
          
          return (
            <div>
              <div>{formatUnitPrice(totalCost)}</div>
              {machineCost > 0 && (
                <div style={{ fontSize: '11px', color: '#666' }}>
                  人工: {formatUnitPrice(laborCost)}<br/>
                  设备: {formatUnitPrice(machineCost)}
                </div>
              )}
            </div>
          );
        }
      }
    });

    baseColumns.push({
      title: '板卡配置',
      dataIndex: 'cardQuantities',
      render: (cardQuantities, record) => {
        // 获取双设备的板卡信息
        const testMachineCards = record.testMachineData ? 
          cardTypes.filter(card => card.machine_id === record.testMachineData.id) : [];
        const secondDeviceCards = record[`${type === 'cp' ? 'prober' : 'handler'}Data`] ? 
          cardTypes.filter(card => card.machine_id === record[`${type === 'cp' ? 'prober' : 'handler'}Data`].id) : [];
        
        const totalAvailableCards = testMachineCards.length + secondDeviceCards.length;
        if (totalAvailableCards === 0) {
          return <span style={{ color: '#999' }}>请先选择设备</span>;
        }
        
        const testMachineSelectedCount = Object.keys(record.testMachineCardQuantities || {}).length;
        const secondDeviceSelectedCount = Object.keys(record[`${type === 'cp' ? 'prober' : 'handler'}CardQuantities`] || {}).length;
        const totalSelectedCount = testMachineSelectedCount + secondDeviceSelectedCount;
        
        return (
          <div>
            <div style={{ color: totalSelectedCount > 0 ? '#1890ff' : '#999', fontSize: '12px' }}>
              已选择 {totalSelectedCount} / {totalAvailableCards} 张板卡
            </div>
            {testMachineCards.length > 0 && (
              <div style={{ fontSize: '11px', color: '#666' }}>
                测试机: {testMachineSelectedCount} / {testMachineCards.length}
              </div>
            )}
            {secondDeviceCards.length > 0 && (
              <div style={{ fontSize: '11px', color: '#666' }}>
                {type === 'cp' ? '探针台' : '分选机'}: {secondDeviceSelectedCount} / {secondDeviceCards.length}
              </div>
            )}
          </div>
        );
      }
    });

    baseColumns.push({
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
    });

    return baseColumns;
  };

  // 渲染单个工序的板卡选择区域（用于展开行）- 支持双设备
  const renderCardSelectionForProcess = (processType, process) => {
    const testMachineCards = process.testMachineData ? 
      cardTypes.filter(card => card.machine_id === process.testMachineData.id) : [];
    const secondDeviceName = processType === 'cp' ? 'prober' : 'handler';
    const secondDeviceCards = process[`${secondDeviceName}Data`] ? 
      cardTypes.filter(card => card.machine_id === process[`${secondDeviceName}Data`].id) : [];
    
    if (testMachineCards.length === 0 && secondDeviceCards.length === 0) return null;
    
    // 渲染单个设备的板卡表格
    const renderDeviceCardTable = (deviceName, deviceDisplayName, cards, cardQuantities) => {
      if (cards.length === 0) return null;
      
      const selectedCardIds = Object.keys(cardQuantities || {}).map(id => parseInt(id));
      
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
              value={cardQuantities?.[cardId] || 1}
              onChange={(value) => handleCardQuantityChange(processType, process.id, cardId, value || 1, deviceName)}
              style={{ width: '80px' }}
              placeholder="数量"
            />
          )
        });
        
        return columns;
      };
      
      return (
        <div style={{ marginBottom: 15 }}>
          <h6 style={{ marginBottom: 10, color: '#1890ff', fontSize: '14px' }}>
            {deviceDisplayName} 板卡配置
          </h6>
          <Table
            dataSource={cards}
            columns={cardColumns()}
            rowKey="id"
            rowSelection={{
              type: 'checkbox',
              selectedRowKeys: selectedCardIds,
              onChange: (selectedRowKeys, selectedRows) => 
                handleCardSelection(processType, process.id, selectedRowKeys, selectedRows, deviceName)
            }}
            pagination={false}
            size="small"
            bordered
          />
        </div>
      );
    };
    
    return (
      <div style={{ padding: '10px 0' }}>
        <h5 style={{ marginBottom: 15, color: '#1890ff' }}>
          {process.name} 板卡配置
        </h5>
        {renderDeviceCardTable('testMachine', '测试机', testMachineCards, process.testMachineCardQuantities)}
        {renderDeviceCardTable(secondDeviceName, processType === 'cp' ? '探针台' : '分选机', secondDeviceCards, process[`${secondDeviceName}CardQuantities`])}
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
        title={isEditMode && editingQuote ? `编辑量产工序报价 - ${editingQuote.quote_number}` : "量产工序报价"}
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
          <div className="form-group">
            <label>报价单位 *</label>
            <select
              value={formData.projectInfo.quoteUnit}
              onChange={(e) => handleInputChange('projectInfo', 'quoteUnit', e.target.value)}
              required
            >
              <option value="昆山芯信安">昆山芯信安</option>
              <option value="苏州芯昱安">苏州芯昱安</option>
              <option value="上海芯睿安">上海芯睿安</option>
              <option value="珠海芯创安">珠海芯创安</option>
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
              rowExpandable: (record) => {
                const testMachineCards = record.testMachineData ? 
                  cardTypes.filter(card => card.machine_id === record.testMachineData.id).length : 0;
                const proberCards = record.proberData ? 
                  cardTypes.filter(card => card.machine_id === record.proberData.id).length : 0;
                return testMachineCards > 0 || proberCards > 0;
              },
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
              rowExpandable: (record) => {
                const testMachineCards = record.testMachineData ? 
                  cardTypes.filter(card => card.machine_id === record.testMachineData.id).length : 0;
                const handlerCards = record.handlerData ? 
                  cardTypes.filter(card => card.machine_id === record.handlerData.id).length : 0;
                return testMachineCards > 0 || handlerCards > 0;
              },
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
          {isEditMode ? "上一步" : "返回"}
        </SecondaryButton>
        <PrimaryButton onClick={handleSubmit}>
          {isEditMode ? "保存修改" : "生成工序报价单"}
        </PrimaryButton>
      </div>
    </div>
  );
};

export default ProcessQuote;