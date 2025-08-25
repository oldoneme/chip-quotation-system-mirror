import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Select, Table, Tabs, Spin, Alert, InputNumber, Form, Button, Card, Checkbox, Divider, message } from 'antd';
import StepIndicator from '../components/StepIndicator';
import ConfirmDialog from '../components/ConfirmDialog';
import { LoadingSpinner, EmptyState } from '../components/CommonComponents';
import { formatHourlyRate, ceilByCurrency, formatQuotePrice } from '../utils';
import { useAuth } from '../contexts/AuthContext';
import {
  getMachines
} from '../services/machines';
import {
  getConfigurations
} from '../services/configurations';
import {
  getCardTypes
} from '../services/cardTypes';
import {
  getAuxiliaryEquipment
} from '../services/auxiliaryEquipment';
import '../App.css';

const { Option } = Select;


const EngineeringQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [testMachine, setTestMachine] = useState(null);
  const [handler, setHandler] = useState(null);
  const [prober, setProber] = useState(null);
  const [testMachineCards, setTestMachineCards] = useState([]); // 选中的测试机板卡
  const [handlerCards, setHandlerCards] = useState([]); // 选中的分选机板卡
  const [proberCards, setProberCards] = useState([]); // 选中的探针台板卡
  const [selectedPersonnel, setSelectedPersonnel] = useState([]); // 选中的人员类型
  const [selectedAuxDevices, setSelectedAuxDevices] = useState([]); // 选中的辅助设备
  const [engineeringRate, setEngineeringRate] = useState(1.2); // 工程系数，默认1.2
  const [quoteCurrency, setQuoteCurrency] = useState('CNY'); // 报价币种，默认人民币
  const [quoteExchangeRate, setQuoteExchangeRate] = useState(7.2); // 报价汇率，默认7.2
  
  // 持久化存储所有板卡的数量状态，避免取消选中后再选中时丢失数量
  const [persistedCardQuantities, setPersistedCardQuantities] = useState({});
  
  // 数据状态
  const [machines, setMachines] = useState([]);        // 测试机
  const [handlers, setHandlers] = useState([]);        // 分选机
  const [probers, setProbers] = useState([]);          // 探针台
  const [auxMachines, setAuxMachines] = useState([]);  // 辅助设备（机器类型不属于测试机、分选机、探针台的机器）
  const [cardTypes, setCardTypes] = useState([]);
  const [auxDevices, setAuxDevices] = useState({ handlers: [], probers: [] });
  const [personnelOptions] = useState([
    { type: '工程师', rate: 350 },
    { type: '技术员', rate: 200 }
  ]);
  
  // 加载状态
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 获取所有数据
  useEffect(() => {
    let isMounted = true; // 防止组件卸载后设置状态
    
    const fetchData = async () => {
      if (!isMounted) return;
      
      setLoading(true);
      setError(null);
      try {
        // 并行获取所有数据
        const [
          machinesData,
          configurationsData,
          cardTypesData,
          auxEquipmentData
        ] = await Promise.all([
          getMachines(),
          getConfigurations(),
          getCardTypes(),
          getAuxiliaryEquipment()
        ]);

        if (isMounted) {
          setCardTypes(cardTypesData);
        }

        // 从机器中筛选出不同类型的机器
        console.log('开始筛选不同类型机器...');
        
        // 安全获取机器类型名称的函数
        const getMachineTypeName = (machine) => {
          try {
            // 处理不同的数据结构可能性
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
        
        // 如果没有供应商信息，我们尝试使用所有机器并添加警告
        if (machinesData.length > 0 && !machinesData[0].supplier) {
          console.log('警告：机器数据中没有供应商信息，将使用所有机器作为测试机');
          setMachines(machinesData);
          setHandlers([]);
          setProbers([]);
          setAuxMachines([]);
          
          console.log('所有机器将被视为测试机');
          console.log('机器列表:', machinesData.map(m => `${m.name} (ID: ${m.id})`));
        } else {
          // 筛选测试机（机器类型为"测试机"的机器）
          const testMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isTestMachine = machineTypeName === '测试机';
            console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为测试机: ${isTestMachine}`);
            return isTestMachine;
          });
          
          // 筛选分选机（机器类型为"分选机"的机器）
          const handlerMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isHandler = machineTypeName === '分选机';
            console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为分选机: ${isHandler}`);
            return isHandler;
          });
          
          // 筛选探针台（机器类型为"探针台"的机器）
          const proberMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isProber = machineTypeName === '探针台';
            console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为探针台: ${isProber}`);
            return isProber;
          });
          
          // 筛选辅助设备（机器类型不属于测试机、分选机、探针台的机器）
          const auxMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isAuxMachine = machineTypeName !== '测试机' && 
                                machineTypeName !== '分选机' && 
                                machineTypeName !== '探针台';
            console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为辅助设备: ${isAuxMachine}`);
            return isAuxMachine;
          });
          
          if (isMounted) {
            setMachines(testMachines);      // 测试机
            setHandlers(handlerMachines);   // 分选机
            setProbers(proberMachines);     // 探针台
            setAuxMachines(auxMachines);    // 辅助设备
          }
          
          console.log('筛选结果:');
          console.log('- 测试机:', testMachines.map(m => `${m.name} (ID: ${m.id})`));
          console.log('- 分选机:', handlerMachines.map(m => `${m.name} (ID: ${m.id})`));
          console.log('- 探针台:', proberMachines.map(m => `${m.name} (ID: ${m.id})`));
          console.log('- 辅助设备:', auxMachines.map(m => `${m.name} (ID: ${m.id})`));
        }

        // 处理辅助设备数据，分为handlers和probers
        const handlers = auxEquipmentData.filter(item => item.name.includes('分选机') || item.name.includes('Handler'));
        const probers = auxEquipmentData.filter(item => item.name.includes('探针台') || item.name.includes('Prober'));
        if (isMounted) {
          setAuxDevices({ handlers, probers });
        }
      } catch (err) {
        console.error('详细错误信息:', err);
        console.error('错误响应:', err.response);
        console.error('错误请求:', err.request);
        console.error('错误消息:', err.message);
        
        let errorMessage = '获取数据失败，请检查后端服务是否正常运行';
        if (err.response) {
          errorMessage = `服务器错误 (${err.response.status}): ${err.response.data?.detail || err.response.statusText}`;
        } else if (err.request) {
          errorMessage = '网络连接失败，无法连接到服务器。请检查：\n1. 后端服务是否运行在 http://localhost:8000\n2. 网络连接是否正常\n3. 防火墙设置是否允许连接';
        }
        
        if (isMounted) {
          setError(errorMessage);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // 检查是否从结果页或其他页面返回
    const isFromResultPage = location.state?.fromResultPage;
    
    if (isFromResultPage && isMounted) {
      // 只有从结果页返回时才恢复状态
      const storedQuoteData = sessionStorage.getItem('quoteData');
      if (storedQuoteData) {
        try {
          const parsedData = JSON.parse(storedQuoteData);
          // 恢复状态
          setTestMachine(parsedData.testMachine);
          setHandler(parsedData.handler);
          setProber(parsedData.prober);
          setTestMachineCards(parsedData.testMachineCards || []);
          setHandlerCards(parsedData.handlerCards || []);
          setProberCards(parsedData.proberCards || []);
          setSelectedPersonnel(parsedData.selectedPersonnel || []);
          setSelectedAuxDevices(parsedData.selectedAuxDevices || []);
          setEngineeringRate(parsedData.engineeringRate || 1.2);
          setQuoteCurrency(parsedData.quoteCurrency || 'CNY');
          setQuoteExchangeRate(parsedData.quoteExchangeRate || 7.2);
          setPersistedCardQuantities(parsedData.persistedCardQuantities || {});
          // 设置当前步骤
          setCurrentStep(parsedData.currentStep || 0);
          console.log('从 sessionStorage 恢复状态:', parsedData);
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      // 正常进入页面时清空所有状态，开始全新流程
      sessionStorage.removeItem('quoteData');
      console.log('开始全新报价流程，已清空之前的状态');
    }

    fetchData();
    
    // 清理函数，防止内存泄漏
    return () => {
      isMounted = false;
    };
  }, []);

  const steps = [
    '设备选择',
    '人员和辅助设备选择'
  ];

  // 格式化价格显示（包含币种符号）
  const formatPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, quoteCurrency);
    if (quoteCurrency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 格式化机时价格显示（包含币种符号，根据币种精度）
  const formatHourlyPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, quoteCurrency);
    if (quoteCurrency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 统一的价格转换函数
  const convertPrice = (price, deviceCurrency, deviceExchangeRate = 1) => {
    let adjustedPrice = price;
    
    if (quoteCurrency === 'USD') {
      if (deviceCurrency === 'CNY' || deviceCurrency === 'RMB') {
        // RMB设备转USD：除以报价汇率
        adjustedPrice = adjustedPrice / quoteExchangeRate;
      }
      // USD设备：不做汇率转换，直接使用原价格
    } else {
      // 报价币种是CNY，保持原逻辑
      adjustedPrice = adjustedPrice * deviceExchangeRate;
    }
    
    return adjustedPrice;
  };

  const nextStep = () => {
    const nextStepValue = currentStep + 1;
    
    // 保存当前状态到sessionStorage
    const currentState = {
      currentStep: nextStepValue,
      testMachine,
      handler,
      prober,
      testMachineCards,
      handlerCards,
      proberCards,
      selectedPersonnel,
      selectedAuxDevices,
      engineeringRate,
      quoteCurrency,
      quoteExchangeRate,
      persistedCardQuantities
    };
    sessionStorage.setItem('quoteData', JSON.stringify(currentState));
    
    if (nextStepValue < steps.length) {
      setCurrentStep(nextStepValue);
    } else {
      // 在完成时将数据存储到sessionStorage
      const quoteData = {
        type: '工程报价',
        engineeringRate, // 添加工程系数
        quoteCurrency, // 添加报价币种
        quoteExchangeRate, // 添加报价汇率
        testMachine,
        handler,
        prober,
        testMachineCards,
        handlerCards,
        proberCards,
        selectedPersonnel,
        selectedAuxDevices,
        cardTypes // 传递板卡类型数据用于计算
      };
      sessionStorage.setItem('quoteData', JSON.stringify(quoteData));
      navigate('/quote-result');
    }
  };
  
  const prevStep = () => {
    if (currentStep > 0) {
      const prevStepValue = currentStep - 1;
      
      // 保存当前状态到sessionStorage
      const currentState = {
        currentStep: prevStepValue,
        testMachine,
        handler,
        prober,
        testMachineCards,
        handlerCards,
        proberCards,
        selectedPersonnel,
        selectedAuxDevices,
        engineeringRate,
        persistedCardQuantities
      };
      sessionStorage.setItem('quoteData', JSON.stringify(currentState));
      
      setCurrentStep(prevStepValue);
    }
  };

  const resetQuote = () => {
    ConfirmDialog.showResetConfirm({
      onOk: () => {
        setTestMachine(null);
        setHandler(null);
        setProber(null);
        setTestMachineCards([]);
        setHandlerCards([]);
        setProberCards([]);
        setSelectedPersonnel([]);
        setSelectedAuxDevices([]);
        setEngineeringRate(1.2);
        setQuoteCurrency('CNY');
        setQuoteExchangeRate(7.2);
        setPersistedCardQuantities({});
        setCurrentStep(0);
        
        // 清除sessionStorage中的状态
        sessionStorage.removeItem('quoteData');
      }
    });
  };

  // 计算测试机费用
  const calculateTestMachineFee = () => {
    if (!testMachine || testMachineCards.length === 0) return 0;
    
    const totalCost = testMachineCards.reduce((total, card) => {
      let adjustedPrice = card.unit_price / 10000;
      
      // 根据报价币种和机器币种进行转换
      if (quoteCurrency === 'USD') {
        if (testMachine.currency === 'CNY' || testMachine.currency === 'RMB') {
          // RMB机器转USD：除以报价汇率
          adjustedPrice = adjustedPrice / quoteExchangeRate;
        }
        // USD机器：不做汇率转换，直接使用unit_price
      } else {
        // 报价币种是CNY，保持原逻辑
        adjustedPrice = adjustedPrice * testMachine.exchange_rate;
      }
      
      return total + (adjustedPrice * testMachine.discount_rate * (card.quantity || 1));
    }, 0);
    
    // 根据货币类型向上取整
    return ceilByCurrency(totalCost, quoteCurrency);
  };
  
  // 计算分选机费用
  const calculateHandlerFee = () => {
    if (!handler || handlerCards.length === 0) return 0;
    
    const totalCost = handlerCards.reduce((total, card) => {
      let adjustedPrice = card.unit_price / 10000;
      
      // 根据报价币种和机器币种进行转换
      if (quoteCurrency === 'USD') {
        if (handler.currency === 'CNY' || handler.currency === 'RMB') {
          // RMB机器转USD：除以报价汇率
          adjustedPrice = adjustedPrice / quoteExchangeRate;
        }
        // USD机器：不做汇率转换，直接使用unit_price
      } else {
        // 报价币种是CNY，保持原逻辑
        adjustedPrice = adjustedPrice * handler.exchange_rate;
      }
      
      return total + (adjustedPrice * handler.discount_rate * (card.quantity || 1));
    }, 0);
    
    // 根据货币类型向上取整
    return ceilByCurrency(totalCost, quoteCurrency);
  };
  
  // 计算探针台费用
  const calculateProberFee = () => {
    if (!prober || proberCards.length === 0) return 0;
    
    const totalCost = proberCards.reduce((total, card) => {
      let adjustedPrice = card.unit_price / 10000;
      
      // 根据报价币种和机器币种进行转换
      if (quoteCurrency === 'USD') {
        if (prober.currency === 'CNY' || prober.currency === 'RMB') {
          // RMB机器转USD：除以报价汇率
          adjustedPrice = adjustedPrice / quoteExchangeRate;
        }
        // USD机器：不做汇率转换，直接使用unit_price
      } else {
        // 报价币种是CNY，保持原逻辑
        adjustedPrice = adjustedPrice * prober.exchange_rate;
      }
      
      return total + (adjustedPrice * prober.discount_rate * (card.quantity || 1));
    }, 0);
    
    // 根据货币类型向上取整
    return ceilByCurrency(totalCost, quoteCurrency);
  };
  
  // 计算人员费用（用于明细显示，固定RMB）
  const calculatePersonnelFee = (personType) => {
    const person = personnelOptions.find(p => p.type === personType);
    return person ? person.rate : 0;
  };

  // 计算人员费用（用于最终报价，根据币种转换）
  const calculatePersonnelFeeForQuote = (personType) => {
    const person = personnelOptions.find(p => p.type === personType);
    if (!person) return 0;
    
    let rate = person.rate;
    if (quoteCurrency === 'USD') {
      rate = rate / quoteExchangeRate;
    }
    return rate;
  };
  
  
  // 计算辅助设备费用
  const calculateAuxDeviceFee = () => {
    const totalCost = selectedAuxDevices.reduce((total, device) => {
      // 如果是机器类型的辅助设备（有supplier信息），计算板卡费用
      if (device.supplier || device.machine_type) {
        // 查找该机器的板卡
        const machineCards = cardTypes.filter(card => card.machine_id === device.id);
        console.log(`计算设备 ${device.name} 的费用，板卡数量: ${machineCards.length}`, machineCards);
        return total + machineCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (device.currency === 'CNY' || device.currency === 'RMB') {
              // RMB机器转USD：除以报价汇率
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
            // USD机器：不做汇率转换，直接使用unit_price
          } else {
            // 报价币种是CNY，保持原逻辑
            adjustedPrice = adjustedPrice * device.exchange_rate;
          }
          
          const cardFee = adjustedPrice * device.discount_rate * (card.quantity || 1);
          console.log(`板卡 ${card.board_name} 费用: ${cardFee}`);
          return sum + cardFee;
        }, 0);
      } else {
        // 如果是原来的辅助设备类型，使用小时费率（默认RMB）
        let hourlyRate = device.hourly_rate || 0;
        if (quoteCurrency === 'USD') {
          hourlyRate = hourlyRate / quoteExchangeRate;
        }
        return total + hourlyRate;
      }
    }, 0);
    
    // 根据货币类型向上取整
    return ceilByCurrency(totalCost, quoteCurrency);
  };
  
  // 计算应用工程系数的机器总费用
  const calculateMachineTotalWithEngineeringRate = () => {
    let total = 0;
    total += calculateTestMachineFee();
    total += calculateHandlerFee();
    total += calculateProberFee();
    
    // 应用工程系数
    const totalWithRate = total * engineeringRate;
    // 根据货币类型向上取整
    return ceilByCurrency(totalWithRate, quoteCurrency);
  };
  
  // 计算不应用工程系数的其他费用
  const calculateOtherFees = () => {
    let total = 0;
    
    // 人员费用
    selectedPersonnel.forEach(personType => {
      total += calculatePersonnelFeeForQuote(personType);
    });
    
    total += calculateAuxDeviceFee();
    
    // 根据货币类型向上取整
    return ceilByCurrency(total, quoteCurrency);
  };
  
  // 计算总费用
  const calculateTotal = () => {
    const machineTotal = calculateMachineTotalWithEngineeringRate();
    const otherTotal = calculateOtherFees();
    const grandTotal = machineTotal + otherTotal;
    // 根据货币类型向上取整
    return ceilByCurrency(grandTotal, quoteCurrency);
  };

  const handleCardSelection = (machineType, selectedRowKeys, selectedRows) => {
    console.log(`选择${machineType}板卡:`, selectedRowKeys, selectedRows);
    
    // 为新选择的行添加数量属性，优先使用持久化存储的数量
    const rowsWithQuantity = selectedRows.map(row => {
      const cardKey = `${machineType}-${row.id}`;
      return {
        ...row,
        quantity: persistedCardQuantities[cardKey] || 1  // 使用持久化存储的数量，否则设为1
      };
    });

    if (machineType === 'testMachine') {
      setTestMachineCards(rowsWithQuantity);
    } else if (machineType === 'handler') {
      setHandlerCards(rowsWithQuantity);
    } else if (machineType === 'prober') {
      setProberCards(rowsWithQuantity);
    }
  };

  const handleCardQuantityChange = (machineType, cardId, quantity) => {
    console.log(`更改${machineType}板卡数量:`, cardId, quantity);
    
    // 更新持久化存储的数量状态
    setPersistedCardQuantities(prev => ({
      ...prev,
      [`${machineType}-${cardId}`]: quantity
    }));
    
    if (machineType === 'testMachine') {
      setTestMachineCards(prevCards => 
        prevCards.map(card => 
          card.id === cardId ? { ...card, quantity } : card
        )
      );
    } else if (machineType === 'handler') {
      setHandlerCards(prevCards => 
        prevCards.map(card => 
          card.id === cardId ? { ...card, quantity } : card
        )
      );
    } else if (machineType === 'prober') {
      setProberCards(prevCards => 
        prevCards.map(card => 
          card.id === cardId ? { ...card, quantity } : card
        )
      );
    }
  };

  // 表格列定义
  const cardColumns = (machineType) => {
    const columns = [
      { title: 'Part Number', dataIndex: 'part_number' },
      { title: 'Board Name', dataIndex: 'board_name' },
    ];
    
    // 只有管理员以上权限才能看到价格
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      columns.push({ 
        title: 'Unit Price', 
        dataIndex: 'unit_price',
        render: (value) => formatQuotePrice(value || 0, quoteCurrency)
      });
    }
    
    columns.push({ 
      title: 'Quantity', 
      render: (_, record) => (
        <InputNumber 
          min={1} 
          defaultValue={1} 
          onChange={(value) => handleCardQuantityChange(machineType, record.id, value)}
        />
      ) 
    });
    
    return columns;
  };
  
  // 计算单个辅助设备的小时费率
  const calculateAuxDeviceHourlyRate = (device) => {
    if (device.machine_type || device.supplier) {
      // 如果是机器类型的辅助设备，计算板卡费用
      const machineCards = cardTypes.filter(card => card.machine_id === device.id);
      const totalRate = machineCards.reduce((sum, card) => {
        let adjustedPrice = card.unit_price / 10000;
        
        // 根据报价币种和机器币种进行转换
        if (quoteCurrency === 'USD') {
          if (device.currency === 'CNY' || device.currency === 'RMB') {
            // RMB机器转USD：除以报价汇率
            adjustedPrice = adjustedPrice / quoteExchangeRate;
          }
          // USD机器：不做汇率转换，直接使用unit_price
        } else {
          // 报价币种是CNY，保持原逻辑
          adjustedPrice = adjustedPrice * device.exchange_rate;
        }
        
        return sum + (adjustedPrice * device.discount_rate);
      }, 0);
      return totalRate;
    } else {
      // 如果是原来的辅助设备类型，使用小时费率（默认RMB）
      let hourlyRate = device.hourly_rate || 0;
      if (quoteCurrency === 'USD') {
        hourlyRate = hourlyRate / quoteExchangeRate;
      }
      return hourlyRate;
    }
  };

  // 辅助设备表格列定义
  const auxMachineColumns = [
    { 
      title: '设备名称', 
      dataIndex: 'name',
      render: (name, device) => (
        <span>
          {name} ({device.currency || 'CNY'}, 汇率: {device.exchange_rate || 1.0}, 折扣率: {device.discount_rate || 1.0})
        </span>
      )
    },
    { 
      title: '类型', 
      dataIndex: 'supplier',
      render: (supplier) => supplier?.machine_type?.name || '辅助设备'
    },
    {
      title: '小时费率',
      render: (_, record) => {
        const rate = calculateAuxDeviceHourlyRate(record);
        return rate > 0 ? `${formatHourlyPrice(rate)}/小时` : 'N/A';
      }
    }
  ];

  // 人员选择变化处理
  const handlePersonnelChange = (checkedValues) => {
    setSelectedPersonnel(checkedValues);
  };

  // 辅助设备选择处理
  const handleAuxDeviceSelect = (selectedRowKeys, selectedRows) => {
    setSelectedAuxDevices(selectedRows);
  };

  // 步骤1: 设备选择内容
  const renderMachineSelection = () => (
    <div>
      <h2 className="section-title">设备选择</h2>
      

      {/* 测试机选择 */}
      <Card title="测试机选择" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 15 }}>
          <h4>选择测试机</h4>
          <Select 
            style={{ width: '100%' }}
            placeholder="选择测试机" 
            onChange={(value) => setTestMachine(machines.find(m => m.id === value))}
            value={testMachine ? testMachine.id : undefined}
            showSearch
            optionFilterProp="children"
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {machines.map(machine => (
              <Option key={machine.id} value={machine.id}>
                {machine.name} ({machine.currency}, 汇率: {machine.exchange_rate}, 折扣率: {machine.discount_rate})
              </Option>
            ))}
          </Select>
        </div>

        {/* 测试机板卡选择 */}
        {testMachine && (
          <div style={{ marginBottom: 15 }}>
            <h4>选择测试机板卡</h4>
            {cardTypes.filter(card => card.machine_id === testMachine.id).length > 0 ? (
              <Table 
                dataSource={cardTypes.filter(card => card.machine_id === testMachine.id)}
                rowKey="id"
                rowSelection={{
                  type: 'checkbox',
                  onChange: (selectedRowKeys, selectedRows) => 
                    handleCardSelection('testMachine', selectedRowKeys, selectedRows),
                  selectedRowKeys: testMachineCards.map(card => card.id)
                }}
                columns={cardColumns('testMachine')}
                pagination={false}
              />
            ) : (
              <EmptyState 
                description="该测试机暂无板卡配置"
                imageStyle={{ height: 40 }}
              />
            )}
          </div>
        )}

        <p><strong>测试机机时费: {formatHourlyPrice(calculateTestMachineFee())}</strong></p>
      </Card>

      {/* 分选机选择 */}
      <Card title="分选机选择" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 15 }}>
          <h4>选择分选机</h4>
          <Select 
            style={{ width: '100%' }}
            placeholder="选择分选机" 
            onChange={(value) => setHandler(handlers.find(h => h.id === value))}
            value={handler ? handler.id : undefined}
            showSearch
            optionFilterProp="children"
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {handlers.map(handler => (
              <Option key={handler.id} value={handler.id}>
                {handler.name} ({handler.currency}, 汇率: {handler.exchange_rate}, 折扣率: {handler.discount_rate})
              </Option>
            ))}
          </Select>
        </div>

        {/* 分选机板卡选择 */}
        {handler && (
          <div style={{ marginBottom: 15 }}>
            <h4>选择分选机板卡</h4>
            <Table 
              dataSource={cardTypes.filter(card => card.machine_id === handler.id)}
              rowKey="id"
              rowSelection={{
                type: 'checkbox',
                onChange: (selectedRowKeys, selectedRows) => 
                  handleCardSelection('handler', selectedRowKeys, selectedRows),
                selectedRowKeys: handlerCards.map(card => card.id)
              }}
              columns={cardColumns('handler')}
              pagination={false}
            />
          </div>
        )}

        <p><strong>分选机机时费: {formatHourlyPrice(calculateHandlerFee())}</strong></p>
      </Card>

      {/* 探针台选择 */}
      <Card title="探针台选择" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 15 }}>
          <h4>选择探针台</h4>
          <Select 
            style={{ width: '100%' }}
            placeholder="选择探针台" 
            onChange={(value) => setProber(probers.find(p => p.id === value))}
            value={prober ? prober.id : undefined}
            showSearch
            optionFilterProp="children"
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {probers.map(prober => (
              <Option key={prober.id} value={prober.id}>
                {prober.name} ({prober.currency}, 汇率: {prober.exchange_rate}, 折扣率: {prober.discount_rate})
              </Option>
            ))}
          </Select>
        </div>

        {/* 探针台板卡选择 */}
        {prober && (
          <div style={{ marginBottom: 15 }}>
            <h4>选择探针台板卡</h4>
            <Table 
              dataSource={cardTypes.filter(card => card.machine_id === prober.id)}
              rowKey="id"
              rowSelection={{
                type: 'checkbox',
                onChange: (selectedRowKeys, selectedRows) => 
                  handleCardSelection('prober', selectedRowKeys, selectedRows),
                selectedRowKeys: proberCards.map(card => card.id)
              }}
              columns={cardColumns('prober')}
              pagination={false}
            />
          </div>
        )}

        <p><strong>探针台机时费: {formatHourlyPrice(calculateProberFee())}</strong></p>
      </Card>
    </div>
  );

  // 步骤2: 人员和辅助设备选择
  const renderPersonnelAndAuxSelection = () => (
    <div>
      <h2 className="section-title">人员和辅助设备选择</h2>
      
      <Card title="人员选择" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 15 }}>
          <h4>选择需要的人员类型</h4>
          <Checkbox.Group 
            value={selectedPersonnel} 
            onChange={handlePersonnelChange}
            style={{ width: '100%' }}
          >
            {personnelOptions.map((person, index) => (
              <div key={index} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '10px 0',
                borderBottom: index < personnelOptions.length - 1 ? '1px solid #f0f0f0' : 'none'
              }}>
                <Checkbox value={person.type}>{person.type}</Checkbox>
                <span>{formatHourlyPrice(quoteCurrency === 'USD' ? person.rate / quoteExchangeRate : person.rate)}/小时</span>
              </div>
            ))}
          </Checkbox.Group>
        </div>
        
        {selectedPersonnel.includes('工程师') && (
          <p><strong>工程师小时费: {formatHourlyPrice(calculatePersonnelFeeForQuote('工程师'))}</strong></p>
        )}
        
        {selectedPersonnel.includes('技术员') && (
          <p><strong>技术员小时费: {formatHourlyPrice(calculatePersonnelFeeForQuote('技术员'))}</strong></p>
        )}
      </Card>
      
      <Card title="辅助设备选择" style={{ marginBottom: 20 }}>
        {auxMachines.length > 0 ? (
          <>
            <Table 
              dataSource={auxMachines}
              rowKey="id"
              rowSelection={{
                type: 'checkbox',
                onChange: handleAuxDeviceSelect,
                selectedRowKeys: selectedAuxDevices.map(device => device.id)
              }}
              columns={auxMachineColumns}
              pagination={false}
            />
            <p style={{ marginTop: 10 }}><strong>辅助设备机时费: {formatHourlyPrice(calculateAuxDeviceFee())}</strong></p>
          </>
        ) : (
          <EmptyState 
            description="暂无可选择的辅助设备"
            imageStyle={{ height: 40 }}
          />
        )}
      </Card>
      
      <Card title="费用明细" style={{ marginBottom: 20 }}>
        <div style={{ padding: '20px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>测试机机时费:</span>
            <span>{formatPrice(calculateTestMachineFee())}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>分选机机时费:</span>
            <span>{formatPrice(calculateHandlerFee())}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>探针台机时费:</span>
            <span>{formatPrice(calculateProberFee())}</span>
          </div>
          {selectedPersonnel.includes('工程师') && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span>工程师小时费:</span>
              <span>{formatHourlyPrice(calculatePersonnelFeeForQuote('工程师'))}</span>
            </div>
          )}
          {selectedPersonnel.includes('技术员') && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span>技术员小时费:</span>
              <span>{formatHourlyPrice(calculatePersonnelFeeForQuote('技术员'))}</span>
            </div>
          )}
          {selectedAuxDevices.length > 0 && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>辅助设备:</span>
                <span></span>
              </div>
              {selectedAuxDevices.map((device, index) => (
                <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingLeft: 20 }}>
                  <span>{device.name} ({device.supplier?.machine_type?.name || '辅助设备'})</span>
                  <span>{formatHourlyPrice(quoteCurrency === 'USD' ? (device.hourly_rate || 0) / quoteExchangeRate : (device.hourly_rate || 0))}/小时</span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
                <span>辅助设备费用小计:</span>
                <span>{formatPrice(calculateAuxDeviceFee())}</span>
              </div>
            </div>
          )}
          <Divider />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>工程系数:</span>
            <span>{engineeringRate}</span>
          </div>
        </div>
      </Card>
      
      <div style={{ marginBottom: 20 }}>
        <h4>工程系数设置</h4>
        <InputNumber 
          min={1.0}
          max={3.0}
          step={0.1}
          value={engineeringRate}
          onChange={setEngineeringRate}
        />
        <p>当前工程系数: {engineeringRate}</p>
        <p>应用工程系数的机器总费用: {formatPrice(calculateMachineTotalWithEngineeringRate())}</p>
      </div>
    </div>
  );

  if (loading) {
    return <LoadingSpinner tip="正在加载设备数据..." />;
  }

  if (error) {
    return (
      <Alert 
        message="数据加载失败" 
        description={error}
        type="error" 
        showIcon
      />
    );
  }

  return (
    <div className="engineering-quote">
      <h1>工程报价</h1>
      
      {/* 币种选择 */}
      <Card title="币种设置" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>选择报价币种:</label>
            <Select 
              style={{ width: 150 }}
              value={quoteCurrency}
              onChange={setQuoteCurrency}
            >
              <Option value="CNY">人民币 (¥)</Option>
              <Option value="USD">美元 ($)</Option>
            </Select>
          </div>
          {quoteCurrency === 'USD' && (
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>设置汇率:</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>1 USD =</span>
                <InputNumber 
                  style={{ width: 100 }}
                  min={1}
                  max={20}
                  step={0.1}
                  precision={1}
                  value={quoteExchangeRate}
                  onChange={(value) => {
                    if (value && value >= 1 && value <= 20) {
                      setQuoteExchangeRate(value);
                    }
                  }}
                  onBlur={(e) => {
                    const value = parseFloat(e.target.value);
                    if (isNaN(value) || value < 1 || value > 20) {
                      message.error('汇率必须在1-20之间');
                      setQuoteExchangeRate(7.2); // 重置为默认值
                    }
                  }}
                />
                <span>CNY</span>
              </div>
            </div>
          )}
          <div style={{ color: '#666', fontSize: '14px' }}>
            <div><strong>说明：</strong></div>
            <div>• 选择币种后，所有价格将以该币种显示</div>
            <div>• 系统会根据设备数据库币种自动进行转换计算</div>
          </div>
        </div>
      </Card>
      
      {/* 步骤指示器 */}
      <StepIndicator currentStep={currentStep} steps={steps} />

      {/* 渲染当前步骤的内容 */}
      {currentStep === 0 && renderMachineSelection()}
      {currentStep === 1 && renderPersonnelAndAuxSelection()}

      {/* 导航按钮 */}
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Button 
            onClick={prevStep} 
            disabled={currentStep === 0}
          >
            上一步
          </Button>
          <Button 
            onClick={resetQuote}
            style={{ marginLeft: 10 }}
          >
            重置
          </Button>
        </div>
        <div>
          <Button 
            onClick={() => navigate('/')}
            style={{ marginRight: 10 }}
          >
            退出报价
          </Button>
          <Button 
            type="primary" 
            onClick={nextStep}
          >
            {currentStep === steps.length - 1 ? '完成报价' : '下一步'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EngineeringQuote;