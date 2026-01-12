import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Checkbox, Card, Button, Table, InputNumber } from 'antd';
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
  const { isEditMode, editingQuote, convertQuoteToFormData } = useQuoteEditMode();

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
              setFormData(parsedState);
            } catch (error) {
              console.error('恢复状态失败:', error);
            }
          }
        } else {
          // 正常进入页面时清空之前的状态
          sessionStorage.removeItem('processQuoteState');
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
    if (isEditMode && editingQuote && machines.length > 0 && cardTypes.length > 0 && !editMessageShown) {
      // 使用转换函数将报价数据转换为表单数据
      const convertedFormData = convertQuoteToFormData(
        editingQuote,
        'process',
        cardTypes,
        machines
      );

      if (convertedFormData) {
        setFormData(prev => {
          // Merge existing processes with converted ones, ensuring new fields are preserved
          const updatedCpProcesses = convertedFormData.cpProcesses ? prev.cpProcesses.map(prevProcess => {
            const convertedProcess = convertedFormData.cpProcesses.find(cp => cp.id === prevProcess.id);
            return convertedProcess ? { ...prevProcess, ...convertedProcess } : prevProcess;
          }).concat(convertedFormData.cpProcesses.filter(cp => !prev.cpProcesses.some(prevP => prevP.id === cp.id))) : prev.cpProcesses;

          const updatedFtProcesses = convertedFormData.ftProcesses ? prev.ftProcesses.map(prevProcess => {
            const convertedProcess = convertedFormData.ftProcesses.find(ft => ft.id === prevProcess.id);
            return convertedProcess ? { ...prevProcess, ...convertedProcess } : prevProcess;
          }).concat(convertedFormData.ftProcesses.filter(ft => !prev.ftProcesses.some(prevP => prevP.id === ft.id))) : prev.ftProcesses;


          return {
            ...prev,
            ...convertedFormData,
            // 确保嵌套对象正确合并
            customerInfo: {
              ...prev.customerInfo,
              ...convertedFormData.customerInfo
            },
            projectInfo: {
              ...prev.projectInfo,
              ...convertedFormData.projectInfo
            },
            cpProcesses: updatedCpProcesses,
            ftProcesses: updatedFtProcesses
          };
        });
        setEditMessageShown(true); // 标记已加载，防止重复
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditMode, editingQuote, machines, cardTypes, editMessageShown]);

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
    const defaultProcessName = type === 'cp' ? 'CP1测试' : 'FT1测试';
    const newProcessId = formData[processKey].length > 0 ? Math.max(...formData[processKey].map(p => p.id)) + 1 : 1;
    
    let baseProcess = {
      id: newProcessId,
      name: defaultProcessName,
      testMachine: '',
      testMachineData: null,
      testMachineCardQuantities: {},
      uph: 1000,
      unitCost: 0, // Calculated unit cost
      adjustedUnitPrice: 0 // User adjusted unit cost
    };

    if (type === 'cp') {
      baseProcess = {
        ...baseProcess,
        prober: '',
        proberData: null,
        proberCardQuantities: {},
      };
    } else { // ft
      baseProcess = {
        ...baseProcess,
        handler: '',
        handlerData: null,
        handlerCardQuantities: {},
      };
    }

    // Initialize specific fields based on default process name
    if (isTestProcess(defaultProcessName)) {
      baseProcess.adjustedMachineRate = 0; // for test processes
    } else if (isBakingProcess(defaultProcessName) || isBurnInProcess(defaultProcessName)) {
      baseProcess.quantityPerOven = 1000;
      baseProcess.bakingTime = 60; // minutes
    } else if (isTapingProcess(defaultProcessName)) {
      baseProcess.packageType = '';
      baseProcess.quantityPerReel = 3000;
    } else if (isAOIProcess(defaultProcessName)) {
      baseProcess.packageType = '';
    }
    // For other processes, uph and unitCost are sufficient initially.

    setFormData(prev => ({
      ...prev,
      [processKey]: [...prev[processKey], baseProcess]
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

  // 更新工序 - 支持双设备结构和不同工序类型
  const updateProcess = (type, processId, field, value) => {
    const processKey = type === 'cp' ? 'cpProcesses' : 'ftProcesses';
    setFormData(prev => ({
      ...prev,
      [processKey]: prev[processKey].map(process => {
        if (process.id === processId) {
          let updatedProcess = { ...process, [field]: value };
          
          // 如果改变了工序名称，重置所有设备选择和相关参数
          if (field === 'name') {
            updatedProcess = {
              ...updatedProcess,
              testMachine: '',
              testMachineData: null,
              testMachineCardQuantities: {},
              prober: type === 'cp' ? '' : undefined,
              proberData: type === 'cp' ? null : undefined,
              proberCardQuantities: type === 'cp' ? {} : undefined,
              handler: type === 'ft' ? '' : undefined,
              handlerData: type === 'ft' ? null : undefined,
              handlerCardQuantities: type === 'ft' ? {} : undefined,
              uph: 1000,
              adjustedMachineRate: 0,
              quantityPerOven: 1000,
              bakingTime: 60,
              packageType: '',
              quantityPerReel: 3000,
              adjustedUnitPrice: 0 // Reset adjusted unit price
            };
            // Re-initialize based on new name if it's a known type
            if (isTestProcess(value)) {
              updatedProcess.adjustedMachineRate = 0;
            } else if (isBakingProcess(value) || isBurnInProcess(value)) {
              updatedProcess.quantityPerOven = 1000;
              updatedProcess.bakingTime = 60;
            } else if (isTapingProcess(value)) {
              updatedProcess.packageType = '';
              updatedProcess.quantityPerReel = 3000;
            } else if (isAOIProcess(value)) {
              updatedProcess.packageType = '';
              updatedProcess.uph = 1000;
            }
          }
          
          // 处理测试机选择
          if (field === 'testMachine') {
            const selectedMachine = machines.find(m => m.name === value);
            updatedProcess.testMachineData = selectedMachine;
            updatedProcess.testMachineCardQuantities = {};
            if (isTestProcess(updatedProcess.name)) {
              updatedProcess.adjustedMachineRate = 0; // Reset adjusted machine rate when machine changes
            }
          }
          
          // 处理第二种设备选择 (CP: prober, FT: handler)
          if ((type === 'cp' && field === 'prober') || (type === 'ft' && field === 'handler')) {
            const selectedMachine = machines.find(m => m.name === value);
            const dataField = type === 'cp' ? 'proberData' : 'handlerData';
            const cardField = type === 'cp' ? 'proberCardQuantities' : 'handlerCardQuantities';
            updatedProcess[dataField] = selectedMachine;
            updatedProcess[cardField] = {};
            if (isTestProcess(updatedProcess.name)) {
              updatedProcess.adjustedMachineRate = 0; // Reset adjusted machine rate when machine changes
            }
          }
          
          // UPH改变时，如果不是测试工序，unitCost可以重新计算（人工成本设置为0，不进行自动计算）
          // if (field === 'uph' && !isTestProcess(updatedProcess.name)) {
          //   updatedProcess.unitCost = 0; // 这里的0应该被计算函数覆盖
          // }

          // 如果是测试工序，并且改变的是 adjustedMachineRate 或者 uph，需要更新 unitCost
          // if (isTestProcess(updatedProcess.name) && (field === 'adjustedMachineRate' || field === 'uph')) {
          //   // 重新计算 unitCost
          //   // This will be handled by the cost calculation functions directly in render or handleSubmit
          // }
          
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
  const calculateSystemMachineRate = (machineData, cardQuantities) => {
    if (!machineData) {
      return 0;
    }

    let machineBaseRate = (machineData.unit_price || 0) / 10000; // 假设设备单价也是万分位
    // 根据报价币种和机器币种进行转换
    if (formData.currency === 'USD') {
      if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
        machineBaseRate = machineBaseRate / formData.exchangeRate;
      }
    } else { // 报价币种是CNY
      if (machineData.currency === 'USD') {
        machineBaseRate = machineBaseRate * formData.exchangeRate;
      }
    }
    
    // 应用折扣率
    const discountedMachineRate = machineBaseRate * (machineData.discount_rate || 1.0);

    let totalCardCost = 0;
    Object.entries(cardQuantities || {}).forEach(([cardId, quantity]) => {
      const card = cardTypes.find(c => c.id === parseInt(cardId));
      if (card && quantity > 0) {
        let adjustedCardPrice = (card.unit_price || 0) / 10000;

        // 根据报价币种和机器币种进行转换（假设板卡价格币种与机器币种相同）
        if (formData.currency === 'USD') {
          if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
            adjustedCardPrice = adjustedCardPrice / formData.exchangeRate;
          }
        } else {
          if (machineData.currency === 'USD') {
            adjustedCardPrice = adjustedCardPrice * formData.exchangeRate;
          }
        }
        totalCardCost += adjustedCardPrice * quantity;
      }
    });

    return discountedMachineRate + totalCardCost;
  };

  // 计算单个工序的单颗费用
  const calculateProcessUnitCost = (process, processType, type) => {
    // 如果用户输入了调整后的单颗费用，则直接使用该值
    if (process.adjustedUnitPrice > 0) {
      return process.adjustedUnitPrice;
    }

    let totalCost = 0;

    if (isTestProcess(process.name)) {
      // 测试工序: (adjustedMachineRate / UPH)
      const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
      const secondDeviceSystemRate = calculateSystemMachineRate(process[type === 'cp' ? 'proberData' : 'handlerData'], process[type === 'cp' ? 'proberCardQuantities' : 'handlerCardQuantities']);
      
      const totalSystemRate = testMachineSystemRate + secondDeviceSystemRate;
      
      // 如果用户没有输入 adjustedMachineRate，则使用系统机时
      // Logic fix: Ensure adjustedMachineRate is used if present, otherwise default to totalSystemRate
      // Note: In the UI, adjustedMachineRate defaults to 0 initially.
      // If it's 0, we effectively use the system rate. But the UI input displays the system rate as default value visually.
      // However, for calculation, we should strictly use the value that represents the final hourly rate.
      
      const effectiveMachineRate = process.adjustedMachineRate > 0 ? process.adjustedMachineRate : totalSystemRate;
      
      if (effectiveMachineRate > 0 && process.uph > 0) {
        totalCost = effectiveMachineRate / process.uph;
      }
    } else if (isBakingProcess(process.name) || isBurnInProcess(process.name)) {
      // 烘烤/老化工序: (设备机时 * 烘烤时间 / 60) / 每炉数量
      const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
      if (testMachineSystemRate > 0 && process.bakingTime > 0 && process.quantityPerOven > 0) {
        totalCost = (testMachineSystemRate * (process.bakingTime / 60)) / process.quantityPerOven;
      }
    } else if (isTapingProcess(process.name)) {
      // 编带工序: (设备机时 / UPH) 或 (设备机时 * 时间 / 每卷数量)
      // 暂时假设编带工序的单颗费用也与设备机时和UPH相关
      const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
      if (testMachineSystemRate > 0 && process.uph > 0) { // Assume UPH for now as it's a common metric
        totalCost = testMachineSystemRate / process.uph;
      }
    } else if (isAOIProcess(process.name)) {
      // AOI工序: (设备机时 / UPH)
      const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
      if (testMachineSystemRate > 0 && process.uph > 0) {
        totalCost = testMachineSystemRate / process.uph;
      }
    }
    // 其他工序暂时返回0，或可在此处添加默认计算逻辑

    // 移除 ceilByCurrency，直接返回原始计算值，避免单颗成本被错误取整
    return totalCost;
  };

  // 计算总成本（设备成本）
  const calculateTotalUnitCost = () => {
    let total = 0;

    if (formData.selectedTypes.includes('cp')) {
      total += formData.cpProcesses.reduce((sum, process) => {
        return sum + calculateProcessUnitCost(process, 'cp', 'cp');
      }, 0);
    }

    if (formData.selectedTypes.includes('ft')) {
      total += formData.ftProcesses.reduce((sum, process) => {
        return sum + calculateProcessUnitCost(process, 'ft', 'ft');
      }, 0);
    }

    // 保留4位小数，与单颗费用显示保持一致，避免不必要的取整
    return parseFloat(total.toFixed(4));
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
      formData.cpProcesses.forEach((process) => {
        if (!process.name || (!process.testMachineData && !process.proberData && !process.testMachine)) {
          return; // Skip if no name or device selected
        }
        
        // 计算工序单颗成本
        const unitCost = calculateProcessUnitCost(process, 'cp', 'cp');

        // 准备工序配置JSON
        let configuration = {
          process_type: process.name,
          uph: process.uph,
          adjusted_unit_price: process.adjustedUnitPrice // Always include adjustedUnitPrice
        };

        let itemDescription = `${process.name}`;
        let deviceType = '-';
        let deviceModel = '-';

        if (isTestProcess(process.name)) {
          const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
          const proberSystemRate = calculateSystemMachineRate(process.proberData, process.proberCardQuantities);
          const totalSystemRate = testMachineSystemRate + proberSystemRate;

          configuration = {
            ...configuration,
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
            system_machine_rate: parseFloat(totalSystemRate.toFixed(4)),
            // 保存 effective machine rate: 如果用户显式调整了 adjustedMachineRate (且不为0),则用调整后的值, 否则用系统机时
            adjusted_machine_rate: parseFloat((process.adjustedMachineRate !== 0 ? process.adjustedMachineRate : totalSystemRate).toFixed(4))
          };
          itemDescription += ` (UPH: ${process.uph})`;
          deviceType = (process.testMachine && process.prober)
            ? '测试机/探针台'
            : (process.testMachine ? '测试机' : (process.prober ? '探针台' : '-'));
          deviceModel = (process.testMachine && process.prober)
            ? `${process.testMachine}/${process.prober}`
            : (process.testMachine || process.prober || '-');
        } else if (isBakingProcess(process.name) || isBurnInProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            quantity_per_oven: process.quantityPerOven,
            baking_time: process.bakingTime,
          };
          itemDescription += ` (每炉数量: ${process.quantityPerOven}, 时间: ${process.bakingTime}分钟)`;
          deviceType = process.testMachine ? '烘烤炉' : '-';
          deviceModel = process.testMachine || '-';
        } else if (isTapingProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            package_type: process.packageType,
            quantity_per_reel: process.quantityPerReel,
          };
          itemDescription += ` (封装: ${process.packageType}, 每卷数量: ${process.quantityPerReel})`;
          deviceType = process.testMachine ? '编带机' : '-';
          deviceModel = process.testMachine || '-';
        } else if (isAOIProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            package_type: process.packageType,
            uph: process.uph,
          };
          itemDescription += ` (封装: ${process.packageType}, UPH: ${process.uph})`;
          deviceType = process.testMachine ? 'AOI设备' : '-';
          deviceModel = process.testMachine || '-';
        } else {
           // For other processes, still include test_machine if selected
           configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
          };
          deviceType = process.testMachine ? '设备' : '-';
          deviceModel = process.testMachine || '-';
        }
        
        items.push({
          item_name: `CP工序 - ${process.name}`,
          item_description: itemDescription,
          machine_type: deviceType,
          supplier: process.testMachineData?.supplier
            ? (typeof process.testMachineData.supplier === 'object'
                ? process.testMachineData.supplier.name
                : process.testMachineData.supplier)
            : '',
          machine_model: deviceModel,
          configuration: JSON.stringify(configuration),
          quantity: 1,
          unit: '颗',
          unit_price: unitCost,
          total_price: unitCost,
          machine_id: process.testMachineData?.id || null,
          category_type: 'process'
        });
      });
    }

    // 2. 处理FT工序
    if (formData.selectedTypes.includes('ft')) {
      formData.ftProcesses.forEach((process) => {
        if (!process.name || (!process.testMachineData && !process.handlerData && !process.testMachine)) {
          return; // Skip if no name or device selected
        }

        // 计算工序单颗成本
        const unitCost = calculateProcessUnitCost(process, 'ft', 'ft');

        // 准备工序配置JSON
        let configuration = {
          process_type: process.name,
          uph: process.uph,
          adjusted_unit_price: process.adjustedUnitPrice // Always include adjustedUnitPrice
        };

        let itemDescription = `${process.name}`;
        let deviceType = '-';
        let deviceModel = '-';

        if (isTestProcess(process.name)) {
          const testMachineSystemRate = calculateSystemMachineRate(process.testMachineData, process.testMachineCardQuantities);
          const handlerSystemRate = calculateSystemMachineRate(process.handlerData, process.handlerCardQuantities);
          const totalSystemRate = testMachineSystemRate + handlerSystemRate;

          configuration = {
            ...configuration,
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
            system_machine_rate: parseFloat(totalSystemRate.toFixed(4)),
            // 保存 effective machine rate: 如果用户显式调整了 adjustedMachineRate (且不为0),则用调整后的值, 否则用系统机时
            adjusted_machine_rate: parseFloat((process.adjustedMachineRate !== 0 ? process.adjustedMachineRate : totalSystemRate).toFixed(4))
          };
          itemDescription += ` (UPH: ${process.uph})`;
          deviceType = (process.testMachine && process.handler)
            ? '测试机/分选机'
            : (process.testMachine ? '测试机' : (process.handler ? '分选机' : '-'));
          deviceModel = (process.testMachine && process.handler)
            ? `${process.testMachine}/${process.handler}`
            : (process.testMachine || process.handler || '-');
        } else if (isBakingProcess(process.name) || isBurnInProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            quantity_per_oven: process.quantityPerOven,
            baking_time: process.bakingTime,
          };
          itemDescription += ` (每炉数量: ${process.quantityPerOven}, 时间: ${process.bakingTime}分钟)`;
          deviceType = process.testMachine ? '烘烤炉' : '-';
          deviceModel = process.testMachine || '-';
        } else if (isTapingProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            package_type: process.packageType,
            quantity_per_reel: process.quantityPerReel,
          };
          itemDescription += ` (封装: ${process.packageType}, 每卷数量: ${process.quantityPerReel})`;
          deviceType = process.testMachine ? '编带机' : '-';
          deviceModel = process.testMachine || '-';
        } else if (isAOIProcess(process.name)) {
          configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
            package_type: process.packageType,
            uph: process.uph,
          };
          itemDescription += ` (封装: ${process.packageType}, UPH: ${process.uph})`;
          deviceType = process.testMachine ? 'AOI设备' : '-';
          deviceModel = process.testMachine || '-';
        } else {
           // For other processes, still include test_machine if selected
           configuration = {
            ...configuration,
            test_machine: process.testMachineData ? {
              id: process.testMachineData.id,
              name: process.testMachine,
              cards: getCardsInfo(process.testMachineCardQuantities)
            } : null,
          };
          deviceType = process.testMachine ? '设备' : '-';
          deviceModel = process.testMachine || '-';
        }

        items.push({
          item_name: `FT工序 - ${process.name}`,
          item_description: itemDescription,
          machine_type: deviceType,
          supplier: process.testMachineData?.supplier
            ? (typeof process.testMachineData.supplier === 'object'
                ? process.testMachineData.supplier.name
                : process.testMachineData.supplier)
            : '',
          machine_model: deviceModel,
          configuration: JSON.stringify(configuration),
          quantity: 1,
          unit: '颗',
          unit_price: unitCost,
          total_price: unitCost,
          machine_id: process.testMachineData?.id || null,
          category_type: 'process'
        });
      });
    }

    return items;
  };

  // 提交处理
  const handleSubmit = async () => {
    // 生成报价项（包含JSON序列化的工序配置）
    const quoteItems = generateProcessQuoteItems();

    // 构建报价标题
    const title = `${formData.projectInfo.projectName || '工序报价'} - ${formData.customerInfo.companyName}`;

    // 准备数据库创建/更新数据
    // 构建项目描述信息（用于存储在description字段，使用中文标点符号以匹配解析逻辑）
    const projectDescription = [
      formData.projectInfo.projectName && `项目：${formData.projectInfo.projectName}`,
      formData.projectInfo.chipPackage && `芯片封装：${formData.projectInfo.chipPackage}`,
      `测试类型：工序报价`
    ].filter(Boolean).join('，');

    const quoteCreateData = {
      title,
      quote_type: '工序报价',
      customer_name: formData.customerInfo.companyName,
      customer_contact: formData.customerInfo.contactPerson,
      customer_phone: formData.customerInfo.phone || '',
      customer_email: formData.customerInfo.email || '',
      quote_unit: formData.projectInfo.quoteUnit,
      currency: formData.currency,
      exchange_rate: formData.exchangeRate,
      total_amount: calculateTotalUnitCost(), // 使用新的总成本计算
      description: projectDescription || '',
      notes: formData.remarks || '',
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



  const isTestProcess = (processName) => {
    if (!processName) return false;
    return (processName.includes('CP') && (processName.includes('1') || processName.includes('2') || processName.includes('3'))) ||
           (processName.includes('FT') && (processName.includes('1') || processName.includes('2') || processName.includes('3')));
  };

  const isBakingProcess = (processName) => processName === '烘烤';
  const isTapingProcess = (processName) => processName === '编带';
  const isAOIProcess = (processName) => processName === 'AOI检测';
  const isBurnInProcess = (processName) => processName === '老化测试';
  const isXRayProcess = (processName) => processName === 'X-Ray检测';
  const isAppearanceProcess = (processName) => processName === '外观检查' || processName === '包装';

  const packageTypeOptions = [
    'QFN', 'BGA', 'SOP', 'SSOP', 'TSSOP', 'MSOP', 'DFN', 'TO', 'SOT', 'FC', 'WLCSP', 'Others'
  ];

  const getFilteredMachinesForProcess = (processName, allMachines) => {
    if (!processName) return [];
    let requiredMachineTypes = [];

    if (isTestProcess(processName)) {
      // For test processes, the specific device selection handlers already filter by '测试机', '探针台', '分选机'.
      // This helper is mainly for the single device selector below.
      // So for simplicity, we return all machines for 'Test Process' if it's not handled specifically
      // by the dedicated test machine/prober/handler selectors.
      // However, if the general selector is used, it should filter relevant test machines.
      // For this context, it will likely be covered by the specific selectors.
      // If a generic "test machine" needs to be selected, it's usually '测试机'.
      return allMachines.filter(m => m.supplier?.machine_type?.name?.includes('测试机'));
    } else if (isBakingProcess(processName)) {
      requiredMachineTypes = ['烘烤设备', '烤箱']; // Add any other relevant types
    } else if (isAOIProcess(processName)) {
      requiredMachineTypes = ['AOI', 'AOI设备'];
    } else if (isTapingProcess(processName)) {
      requiredMachineTypes = ['编带机'];
    } else if (isBurnInProcess(processName)) {
      requiredMachineTypes = ['老化设备'];
    } else if (isXRayProcess(processName)) {
      requiredMachineTypes = ['X-Ray', 'X-Ray检测设备'];
    } else if (isAppearanceProcess(processName)) {
      requiredMachineTypes = ['外观检查设备', 'AOI', 'AOI设备']; // Appearance check might use AOI or dedicated equipment
    } else {
      // Default for other non-test processes, e.g., general auxiliary equipment
      return allMachines; // Or a more specific default if available
    }

    return allMachines.filter(machine => 
      requiredMachineTypes.some(type => machine.supplier?.machine_type?.name?.includes(type))
    );
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
      },
      {
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
            const filteredMachines = getFilteredMachinesForProcess(record.name, machines);
            return (
              <select
                value={record.testMachine || ''}
                onChange={(e) => updateProcess(type, record.id, 'testMachine', e.target.value)}
                style={{ width: '100%', padding: '4px' }}
                disabled={!record.name}
              >
                <option value="">请选择设备</option>
                {filteredMachines.map(machineData => (
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
      }
    ];

    // 新增“规格参数”列
    baseColumns.push({
      title: '规格参数',
      key: 'specs',
      render: (_, record) => {
        if (isTestProcess(record.name)) {
          const testMachineSystemRate = calculateSystemMachineRate(record.testMachineData, record.testMachineCardQuantities);
          const secondDeviceSystemRate = calculateSystemMachineRate(record[type === 'cp' ? 'proberData' : 'handlerData'], record[type === 'cp' ? 'proberCardQuantities' : 'handlerCardQuantities']);
          const totalSystemRate = testMachineSystemRate + secondDeviceSystemRate;
          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>系统机时:</label>
                <InputNumber
                  value={parseFloat(totalSystemRate.toFixed(4))}
                  formatter={(value) => `${formData.currency === 'USD' ? '$' : '￥'}${value}`}
                  parser={(value) => value.replace(/[^0-9.]/g, '')}
                  disabled
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>调整机时:</label>
                <InputNumber
                  value={record.adjustedMachineRate > 0 ? record.adjustedMachineRate : parseFloat(totalSystemRate.toFixed(4))}
                  onChange={(value) => updateProcess(type, record.id, 'adjustedMachineRate', value || 0)}
                  min={0}
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>UPH ({type === 'cp' ? '片' : '颗'}/小时):</label>
                <InputNumber
                  value={record.uph}
                  onChange={(value) => updateProcess(type, record.id, 'uph', value || 0)}
                  min={0}
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
            </div>
          );
        } else if (isBakingProcess(record.name) || isBurnInProcess(record.name)) {
          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>每炉数量:</label>
                <InputNumber
                  value={record.quantityPerOven}
                  onChange={(value) => updateProcess(type, record.id, 'quantityPerOven', value || 0)}
                  min={0}
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>烘烤时间 (分钟):</label>
                <InputNumber
                  value={record.bakingTime}
                  onChange={(value) => updateProcess(type, record.id, 'bakingTime', value || 0)}
                  min={0}
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
            </div>
          );
        } else if (isTapingProcess(record.name) || isAOIProcess(record.name)) {
          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>封装形式:</label>
                <select
                  value={record.packageType || ''}
                  onChange={(e) => updateProcess(type, record.id, 'packageType', e.target.value)}
                  style={{ width: '100%', padding: '4px', marginTop: '2px' }}
                >
                  <option value="">请选择封装形式</option>
                  {packageTypeOptions.map(pkgType => (
                    <option key={pkgType} value={pkgType}>
                      {pkgType}
                    </option>
                  ))}
                </select>
              </div>
              {isTapingProcess(record.name) && (
                <div>
                  <label style={{ fontSize: '12px', color: '#666' }}>每卷数量:</label>
                  <InputNumber
                    value={record.quantityPerReel}
                    onChange={(value) => updateProcess(type, record.id, 'quantityPerReel', value || 0)}
                    min={0}
                    style={{ width: '100%' }}
                    size="small"
                  />
                </div>
              )}
              {isAOIProcess(record.name) && (
                <div>
                  <label style={{ fontSize: '12px', color: '#666' }}>UPH (颗/小时):</label>
                  <InputNumber
                    value={record.uph}
                    onChange={(value) => updateProcess(type, record.id, 'uph', value || 0)}
                    min={0}
                    style={{ width: '100%' }}
                    size="small"
                  />
                </div>
              )}
            </div>
          );
        } else {
          return <span style={{ color: '#ccc' }}>无特定参数</span>;
        }
      }
    });

    baseColumns.push({
      title: type === 'cp' ? '单片费用' : '单颗费用',
      key: 'unit_cost_display',
      render: (_, record) => {
        const calculatedCost = calculateProcessUnitCost(record, type, type);
        
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div>
              <label style={{ fontSize: '12px', color: '#666' }}>计算费用:</label>
              <InputNumber
                value={parseFloat(calculatedCost.toFixed(4))}
                formatter={(value) => `${formData.currency === 'USD' ? '$' : '￥'}${value}`}
                parser={(value) => value.replace(/[^0-9.]/g, '')}
                disabled
                style={{ width: '100%' }}
                size="small"
              />
            </div>
            {!isTestProcess(record.name) && ( // 只有非测试工序才有调整单颗费用
              <div>
                <label style={{ fontSize: '12px', color: '#666' }}>调整费用:</label>
                <InputNumber
                  value={record.adjustedUnitPrice > 0 ? record.adjustedUnitPrice : parseFloat(calculatedCost.toFixed(4))}
                  onChange={(value) => updateProcess(type, record.id, 'adjustedUnitPrice', value || 0)}
                  min={0}
                  style={{ width: '100%' }}
                  size="small"
                />
              </div>
            )}
            {isTestProcess(record.name) && (
              <div style={{ fontSize: '11px', color: '#666', marginTop: '5px' }}>
                <span style={{ fontWeight: 'bold' }}>{type === 'cp' ? '最终单片价' : '最终单价'}: </span>
                {formatUnitPrice(calculatedCost)}
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
              disabled={isEditMode}
              style={isEditMode ? { backgroundColor: '#f5f5f5', cursor: 'not-allowed' } : {}}
              title={isEditMode ? '编辑模式下不允许修改报价单位' : ''}
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
          {isEditMode ? "保存修改" : "完成报价"}
        </PrimaryButton>
      </div>
    </div>
  );
};

export default ProcessQuote;