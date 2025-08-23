import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Select, Table, Tabs, Spin, Alert, Checkbox, Button, Card, InputNumber, message, Divider } from 'antd';
import StepIndicator from '../components/StepIndicator';
import ConfirmDialog from '../components/ConfirmDialog';
import { LoadingSpinner, EmptyState } from '../components/CommonComponents';
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
import { formatNumber } from '../utils';
import '../App.css';

const { Option } = Select;
const { TabPane } = Tabs;

const MassProductionQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { state } = location;
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 机器数据
  const [machines, setMachines] = useState([]);      // 测试机
  const [handlers, setHandlers] = useState([]);      // 分选机
  const [probers, setProbers] = useState([]);        // 探针台
  const [auxDevices, setAuxDevices] = useState({ handlers: [], probers: [], others: [] }); // 辅助设备
  const [cardTypes, setCardTypes] = useState([]);    // 板卡类型
  
  // 选择状态
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [selectedCards, setSelectedCards] = useState([]);
  const [selectedAuxDevices, setSelectedAuxDevices] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState(['ft', 'cp']);
  const [quoteCurrency, setQuoteCurrency] = useState('CNY'); // 报价币种，默认人民币
  const [quoteExchangeRate, setQuoteExchangeRate] = useState(7.2); // 报价汇率，默认7.2
  
  // FT数据状态
  const [ftData, setFtData] = useState({
    testMachine: null,
    handler: null,
    testMachineCards: [],
    handlerCards: [],
    proberCards: []
  });
  
  // CP数据状态
  const [cpData, setCpData] = useState({
    testMachine: null,
    prober: null,
    testMachineCards: [],
    handlerCards: [],
    proberCards: []
  });
  
  // 持久化存储所有板卡的数量状态，避免取消选中后再选中时丢失数量
  const [persistedCardQuantities, setPersistedCardQuantities] = useState({});
  
  useEffect(() => {
    let isMounted = true; // 防止组件卸载后设置状态
    
    // 检查是否从结果页返回
    const isFromResultPage = location.state?.fromResultPage;
    
    if (isFromResultPage && isMounted) {
      // 从结果页返回时，恢复之前保存的状态
      const savedState = sessionStorage.getItem('massProductionQuoteState');
      if (savedState) {
        try {
          const parsedState = JSON.parse(savedState);
          console.log('从 sessionStorage 恢复状态:', parsedState);
          
          if (isMounted) {
            // 恢复所有状态
            setCurrentStep(parsedState.currentStep || 0);
            setSelectedTypes(parsedState.selectedTypes || ['ft', 'cp']);
            setFtData(parsedState.ftData || { 
              testMachine: null, 
              handler: null, 
              testMachineCards: [], 
              handlerCards: [],
              proberCards: []
            });
            setCpData(parsedState.cpData || { 
              testMachine: null, 
              prober: null, 
              testMachineCards: [], 
              handlerCards: [],
              proberCards: [] 
            });
            setSelectedAuxDevices(parsedState.selectedAuxDevices || []);
            setPersistedCardQuantities(parsedState.persistedCardQuantities || {});
            setQuoteCurrency(parsedState.quoteCurrency || 'CNY');
            setQuoteExchangeRate(parsedState.quoteExchangeRate || 7.2);
          }
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      // 正常进入页面时清空所有状态，开始全新流程
      sessionStorage.removeItem('massProductionQuoteState');
      console.log('开始全新报价流程，已清空之前的状态');
    }
    
    // 加载数据
    fetchData();
    
    // 清理函数，防止内存泄漏
    return () => {
      isMounted = false;
    };
  }, []);

  // 格式化价格显示（包含币种符号）
  const formatPrice = (number) => {
    const formattedNumber = formatNumber(number);
    if (quoteCurrency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('开始获取数据...');
      const machinesResponse = await getMachines();
      console.log('获取到的机器数据:', machinesResponse);
      const cardTypesResponse = await getCardTypes();
      console.log('获取到的板卡类型数据:', cardTypesResponse);
      const auxDevicesResponse = await getAuxiliaryEquipment();
      console.log('获取到的辅助设备数据:', auxDevicesResponse);

      setCardTypes(cardTypesResponse);
      setAuxDevices({
        handlers: auxDevicesResponse.filter(device => device.type === 'handler'),
        probers: auxDevicesResponse.filter(device => device.type === 'prober'),
        others: auxDevicesResponse.filter(device => !device.type || (device.type !== 'handler' && device.type !== 'prober'))
      });
      
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
      if (machinesResponse.length > 0 && !machinesResponse[0].supplier) {
        console.log('警告：机器数据中没有供应商信息，将使用所有机器作为测试机');
        setMachines(machinesResponse);
        setHandlers([]);
        setProbers([]);
        
        console.log('所有机器将被视为测试机');
        console.log('机器列表:', machinesResponse.map(m => `${m.name} (ID: ${m.id})`));
      } else {
        // 筛选测试机（机器类型为"测试机"的机器）
        const testMachines = machinesResponse.filter(machine => {
          const machineTypeName = getMachineTypeName(machine);
          const isTestMachine = machineTypeName === '测试机';
          console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为测试机: ${isTestMachine}`);
          return isTestMachine;
        });
        
        // 筛选分选机（机器类型为"分选机"的机器）
        const handlerMachines = machinesResponse.filter(machine => {
          const machineTypeName = getMachineTypeName(machine);
          const isHandler = machineTypeName === '分选机';
          console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为分选机: ${isHandler}`);
          return isHandler;
        });
        
        // 筛选探针台（机器类型为"探针台"的机器）
        const proberMachines = machinesResponse.filter(machine => {
          const machineTypeName = getMachineTypeName(machine);
          const isProber = machineTypeName === '探针台';
          console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为探针台: ${isProber}`);
          return isProber;
        });
        
        console.log('筛选结果:');
        console.log('- 测试机:', testMachines.map(m => `${m.name} (ID: ${m.id})`));
        console.log('- 分选机:', handlerMachines.map(m => `${m.name} (ID: ${m.id})`));
        console.log('- 探针台:', proberMachines.map(m => `${m.name} (ID: ${m.id})`));
        
        // 设置筛选后的机器数据
        setMachines(testMachines);      // 测试机
        setHandlers(handlerMachines);   // 分选机
        setProbers(proberMachines);     // 探针台
        
        // 筛选辅助设备（机器类型不属于测试机、分选机、探针台的机器）
        const auxMachines = machinesResponse.filter(machine => {
          const machineTypeName = getMachineTypeName(machine);
          const isAuxMachine = machineTypeName !== '测试机' && 
                              machineTypeName !== '分选机' && 
                              machineTypeName !== '探针台';
          console.log(`机器 ${machine.name} (ID: ${machine.id}) 类型: "${machineTypeName}", 是否为辅助设备: ${isAuxMachine}`);
          return isAuxMachine;
        });
        
        console.log('筛选出的机器类型辅助设备:', auxMachines.map(m => `${m.name} (类型: ${getMachineTypeName(m)})`));
        
        // 更新辅助设备，包含机器类型的辅助设备
        setAuxDevices(prevState => {
          const newOthers = [...prevState.others, ...auxMachines];
          console.log('更新后的others辅助设备:', newOthers.map(d => d.name));
          return {
            ...prevState,
            others: newOthers
          };
        });
      }
      
      
      console.log('数据加载完成');
    } catch (error) {
      console.error('获取数据时出错:', error);
      const errorMessage = error.response?.data?.detail || error.message || '获取数据失败';
      setError(errorMessage);
      message.error('获取数据失败: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleProductionTypeChange = (checkedValues) => {
    setSelectedTypes(checkedValues);
  };

  const handleTestMachineSelect = (type, machineId) => {
    console.log(`选择${type}测试机:`, machineId);
    const selectedMachine = machines.find(m => m.id === machineId);
    console.log('选中的测试机:', selectedMachine);
    if (type === 'ft') {
      setFtData(prevData => ({
        ...prevData,
        testMachine: selectedMachine
      }));
    } else if (type === 'cp') {
      setCpData(prevData => ({
        ...prevData,
        testMachine: selectedMachine
      }));
    }
  };

  const handleHandlerSelect = (type, handlerId) => {
    console.log(`选择${type}分选机:`, handlerId);
    const selectedHandler = handlers.find(h => h.id === handlerId);
    console.log('选中的分选机:', selectedHandler);
    if (type === 'ft') {
      setFtData(prevData => ({
        ...prevData,
        handler: selectedHandler
      }));
    } else if (type === 'cp') {
      setCpData(prevData => ({
        ...prevData,
        handler: selectedHandler
      }));
    }
  };

  const handleProberSelect = (type, proberId) => {
    console.log(`选择${type}探针台:`, proberId);
    const selectedProber = probers.find(p => p.id === proberId);
    console.log('选中的探针台:', selectedProber);
    if (type === 'ft') {
      setFtData(prevData => ({
        ...prevData,
        prober: selectedProber
      }));
    } else if (type === 'cp') {
      setCpData(prevData => ({
        ...prevData,
        prober: selectedProber
      }));
    }
  };

  const handleCardSelection = (type, machineType, selectedRowKeys, selectedRows) => {
    console.log(`选择${type}的${machineType}板卡:`, selectedRowKeys, selectedRows);
    
    // 为新选择的行添加数量属性，优先使用持久化存储的数量
    const rowsWithQuantity = selectedRows.map(row => {
      const cardKey = `${type}-${machineType}-${row.id}`;
      return {
        ...row,
        quantity: persistedCardQuantities[cardKey] || 1  // 使用持久化存储的数量，否则设为1
      };
    });

    if (type === 'ft') {
      if (machineType === 'testMachine') {
        setFtData(prevData => ({
          ...prevData,
          testMachineCards: rowsWithQuantity
        }));
      } else if (machineType === 'handler') {
        setFtData(prevData => ({
          ...prevData,
          handlerCards: rowsWithQuantity
        }));
      } else if (machineType === 'prober') {
        setFtData(prevData => ({
          ...prevData,
          proberCards: rowsWithQuantity
        }));
      }
    } else if (type === 'cp') {
      if (machineType === 'testMachine') {
        setCpData(prevData => ({
          ...prevData,
          testMachineCards: rowsWithQuantity
        }));
      } else if (machineType === 'handler') {
        setCpData(prevData => ({
          ...prevData,
          handlerCards: rowsWithQuantity
        }));
      } else if (machineType === 'prober') {
        setCpData(prevData => ({
          ...prevData,
          proberCards: rowsWithQuantity
        }));
      }
    }
  };

  const handleCardQuantityChange = (type, machineType, cardId, quantity) => {
    console.log(`更改${type}的${machineType}板卡数量:`, cardId, quantity);
    
    // 更新持久化存储的数量状态
    setPersistedCardQuantities(prev => ({
      ...prev,
      [`${type}-${machineType}-${cardId}`]: quantity
    }));
    
    if (type === 'ft') {
      if (machineType === 'testMachine') {
        setFtData(prevData => ({
          ...prevData,
          testMachineCards: prevData.testMachineCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      } else if (machineType === 'handler') {
        setFtData(prevData => ({
          ...prevData,
          handlerCards: prevData.handlerCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      } else if (machineType === 'prober') {
        setFtData(prevData => ({
          ...prevData,
          proberCards: prevData.proberCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      }
    } else if (type === 'cp') {
      if (machineType === 'testMachine') {
        setCpData(prevData => ({
          ...prevData,
          testMachineCards: prevData.testMachineCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      } else if (machineType === 'handler') {
        setCpData(prevData => ({
          ...prevData,
          handlerCards: prevData.handlerCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      } else if (machineType === 'prober') {
        setCpData(prevData => ({
          ...prevData,
          proberCards: prevData.proberCards.map(card => 
            card.id === cardId ? { ...card, quantity } : card
          )
        }));
      }
    }
  };

  const calculateHourlyFee = (data, type) => {
    let total = 0;
    
    if (type === 'ft') {
      // 计算测试机板卡费用
      if (data.testMachine && data.testMachineCards.length > 0) {
        total += data.testMachineCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (data.testMachine.currency === 'CNY' || data.testMachine.currency === 'RMB') {
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
          } else {
            adjustedPrice = adjustedPrice * data.testMachine.exchange_rate;
          }
          
          return sum + (adjustedPrice * data.testMachine.discount_rate * card.quantity);
        }, 0);
      }
      
      // 计算分选机板卡费用
      if (data.handler && data.handlerCards.length > 0) {
        total += data.handlerCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (data.handler.currency === 'CNY' || data.handler.currency === 'RMB') {
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
          } else {
            adjustedPrice = adjustedPrice * data.handler.exchange_rate;
          }
          
          return sum + (adjustedPrice * data.handler.discount_rate * card.quantity);
        }, 0);
      }
    } else if (type === 'cp') {
      // 计算测试机板卡费用
      if (data.testMachine && data.testMachineCards.length > 0) {
        total += data.testMachineCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (data.testMachine.currency === 'CNY' || data.testMachine.currency === 'RMB') {
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
          } else {
            adjustedPrice = adjustedPrice * data.testMachine.exchange_rate;
          }
          
          return sum + (adjustedPrice * data.testMachine.discount_rate * card.quantity);
        }, 0);
      }
      
      // 计算探针台板卡费用
      if (data.prober && data.proberCards.length > 0) {
        total += data.proberCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (data.prober.currency === 'CNY' || data.prober.currency === 'RMB') {
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
          } else {
            adjustedPrice = adjustedPrice * data.prober.exchange_rate;
          }
          
          return sum + (adjustedPrice * data.prober.discount_rate * card.quantity);
        }, 0);
      }
    }
    
    return total;
  };

  const ftHourlyFee = calculateHourlyFee(ftData, 'ft');
  const cpHourlyFee = calculateHourlyFee(cpData, 'cp');
  
  // 计算辅助设备费用
  const calculateAuxDeviceFee = () => {
    return selectedAuxDevices.reduce((total, device) => {
      // 如果是机器类型的辅助设备（有supplier信息），计算板卡费用
      if (device.supplier || device.machine_type) {
        const machineCards = cardTypes.filter(card => card.machine_id === device.id);
        console.log(`量产报价-计算设备 ${device.name} 的总费用，板卡数量: ${machineCards.length}`, machineCards);
        return total + machineCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (device.currency === 'CNY' || device.currency === 'RMB') {
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
          } else {
            adjustedPrice = adjustedPrice * (device.exchange_rate || 1);
          }
          
          const cardFee = adjustedPrice * (device.discount_rate || 1);
          console.log(`板卡 ${card.board_name} 费用: ${cardFee}`);
          return sum + cardFee;
        }, 0);
      } else {
        // 如果是原来的辅助设备类型，使用小时费率
        let hourlyRate = device.hourly_rate || 0;
        if (quoteCurrency === 'USD') {
          hourlyRate = hourlyRate / quoteExchangeRate;
        }
        return total + hourlyRate;
      }
    }, 0);
  };
  
  const auxDeviceFee = calculateAuxDeviceFee();

  const handleNextStep = () => {
    const nextStepValue = currentStep + 1;
    
    // 保存当前状态到sessionStorage
    const currentState = {
      currentStep: nextStepValue,
      selectedTypes,
      ftData,
      cpData,
      selectedAuxDevices,
      persistedCardQuantities,
      quoteCurrency,
      quoteExchangeRate
    };
    sessionStorage.setItem('massProductionQuoteState', JSON.stringify(currentState));
    
    if (nextStepValue < 2) {
      // Save current step data and navigate to next step
      setCurrentStep(nextStepValue);
    } else {
      // 完成报价，将数据传递到结果页面
      const quoteData = {
        type: '量产报价',
        selectedTypes,
        ftData,
        cpData,
        selectedAuxDevices,
        cardTypes,
        ftHourlyFee,
        cpHourlyFee,
        auxDeviceFee,
        quoteCurrency, // 添加报价币种
        quoteExchangeRate // 添加报价汇率
      };
      
      // 通过location.state传递数据到结果页面
      navigate('/quote-result', { state: { ...quoteData, fromQuotePage: true } });
    }
  };
  
  const handlePrevStep = () => {
    const prevStepValue = currentStep - 1;
    
    // 保存当前状态到sessionStorage
    const currentState = {
      currentStep: prevStepValue,
      selectedTypes,
      ftData,
      cpData,
      selectedAuxDevices,
      persistedCardQuantities,
      quoteCurrency,
      quoteExchangeRate
    };
    sessionStorage.setItem('massProductionQuoteState', JSON.stringify(currentState));
    
    // Navigate to previous step
    setCurrentStep(prevStepValue);
  };
  
  const resetQuote = () => {
    ConfirmDialog.showResetConfirm({
      title: '确认重置报价',
      content: '您确定要重置所有选择吗？这将清除您当前的所有配置和选择。',
      onOk: () => {
        setSelectedMachine(null);
        setSelectedConfig(null);
        setSelectedCards([]);
        setSelectedAuxDevices([]);
        setSelectedTypes(['ft', 'cp']);
        setFtData({ 
          testMachine: null, 
          handler: null, 
          testMachineCards: [], 
          handlerCards: [] 
        });
        setCpData({ 
          testMachine: null, 
          prober: null, 
          testMachineCards: [], 
          proberCards: [] 
        });
        setPersistedCardQuantities({});
        setQuoteCurrency('CNY');
        setQuoteExchangeRate(7.2);
        setCurrentStep(0);
        
        // 清除sessionStorage中的状态
        sessionStorage.removeItem('massProductionQuoteState');
        message.success('报价已重置');
      }
    });
  };
  
  const handleAuxDeviceSelect = (selectedRowKeys, selectedRows) => {
    setSelectedAuxDevices(selectedRows);
  };

  // 表格列定义
  const cardColumns = (type, machineType) => {
    const columns = [
      { title: 'Part Number', dataIndex: 'part_number' },
      { title: 'Board Name', dataIndex: 'board_name' },
    ];
    
    // 只有管理员以上权限才能看到价格
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      columns.push({ 
        title: 'Unit Price', 
        dataIndex: 'unit_price',
        render: (value) => formatNumber(value || 0)
      });
    }
    
    columns.push({ 
      title: 'Quantity', 
      render: (_, record) => (
        <InputNumber 
          min={1} 
          defaultValue={1} 
          onChange={(value) => handleCardQuantityChange(type, machineType, record.id, value)}
        />
      ) 
    });
    
    return columns;
  };
  
  // 计算单个辅助设备的小时费率
  const calculateAuxDeviceHourlyRate = (device) => {
    if (device.supplier || device.machine_type) {
      // 如果是机器类型的辅助设备，计算板卡费用
      const machineCards = cardTypes.filter(card => card.machine_id === device.id);
      const totalRate = machineCards.reduce((sum, card) => {
        let adjustedPrice = card.unit_price / 10000;
        
        // 根据报价币种和机器币种进行转换
        if (quoteCurrency === 'USD') {
          if (device.currency === 'CNY' || device.currency === 'RMB') {
            adjustedPrice = adjustedPrice / quoteExchangeRate;
          }
        } else {
          adjustedPrice = adjustedPrice * (device.exchange_rate || 1);
        }
        
        const cardRate = adjustedPrice * (device.discount_rate || 1);
        return sum + cardRate;
      }, 0);
      return totalRate;
    } else {
      // 如果是原来的辅助设备类型，使用小时费率
      let hourlyRate = device.hourly_rate || 0;
      if (quoteCurrency === 'USD') {
        hourlyRate = hourlyRate / quoteExchangeRate;
      }
      return hourlyRate;
    }
  };

  // 辅助设备表格列定义
  const auxDeviceColumns = [
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
      render: (supplier, device) => {
        if (supplier?.machine_type?.name) {
          return supplier.machine_type.name;
        }
        if (device.machine_type?.name) {
          return device.machine_type.name;
        }
        if (device.type === 'handler') {
          return '分选机';
        }
        if (device.type === 'prober') {
          return '探针台';
        }
        return '辅助设备';
      }
    },
    { 
      title: '小时费率',
      render: (_, record) => {
        const rate = calculateAuxDeviceHourlyRate(record);
        return `${formatPrice(rate)}/小时`;
      }
    }
  ];


  if (loading) {
    return <LoadingSpinner tip="正在加载量产报价数据..." />;
  }

  if (error) {
    return (
      <Alert 
        message="数据加载失败" 
        description={error}
        type="error" 
        showIcon
        action={
          <Button size="small" danger onClick={fetchData}>
            重新加载
          </Button>
        }
      />
    );
  }

  return (
    <div className="mass-production-quote">
      <h2>量产报价</h2>
      
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
      <StepIndicator 
        currentStep={currentStep}
        steps={[
          '机器选择',
          '辅助设备'
        ]}
      />

      {/* 第一步：机器选择 */}
      {currentStep === 0 && (
        <>
          {/* 选择FT或CP */}
          <Card title="测试类型选择" style={{ marginBottom: 20 }}>
            <Checkbox.Group value={selectedTypes} onChange={handleProductionTypeChange}>
              <Checkbox value="ft" style={{ marginRight: 20 }}>FT</Checkbox>
              <Checkbox value="cp">CP</Checkbox>
            </Checkbox.Group>
            <div style={{ marginTop: 10, color: '#666', fontSize: '12px' }}>
              可同时选择多种测试类型进行综合报价
            </div>
          </Card>

          {selectedTypes.includes('ft') && (
            <Card title="FT" style={{ marginBottom: 20 }}>
              {/* 测试机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择测试机</h4>
                {machines && machines.length > 0 ? (
                  <Select 
                    style={{ width: '100%' }}
                    placeholder="选择测试机" 
                    onChange={(value) => handleTestMachineSelect('ft', value)}
                    value={ftData.testMachine ? ftData.testMachine.id : undefined}
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
                ) : (
                  <EmptyState 
                    description="暂无可用的测试机"
                    action={<Button onClick={fetchData}>刷新数据</Button>}
                  />
                )}
              </div>

              {/* 测试机板卡选择 */}
              {ftData.testMachine && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择测试机板卡</h4>
                  {(() => {
                    const availableCards = cardTypes.filter(card => card.machine_id === ftData.testMachine.id);
                    return availableCards.length > 0 ? (
                      <Table 
                        dataSource={availableCards}
                        rowKey="id"
                        rowSelection={{
                          type: 'checkbox',
                          onChange: (selectedRowKeys, selectedRows) => 
                            handleCardSelection('ft', 'testMachine', selectedRowKeys, selectedRows),
                          selectedRowKeys: (ftData.testMachineCards || []).map(card => card.id)
                        }}
                        columns={cardColumns('ft', 'testMachine')}
                        pagination={{ pageSize: 5, showSizeChanger: false }}
                      />
                    ) : (
                      <EmptyState 
                        description={`该测试机暂无可用板卡`}
                        size="small"
                      />
                    );
                  })()} 
                </div>
              )}
              
              {/* 分选机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择分选机</h4>
                {handlers && handlers.length > 0 ? (
                  <Select 
                    style={{ width: '100%' }}
                    placeholder="选择分选机" 
                    onChange={(value) => handleHandlerSelect('ft', value)}
                    value={ftData.handler ? ftData.handler.id : undefined}
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
                ) : (
                  <EmptyState 
                    description="暂无可用的分选机"
                    action={<Button onClick={fetchData}>刷新数据</Button>}
                  />
                )}
              </div>

              {/* 分选机板卡选择 */}
              {ftData.handler && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择分选机板卡</h4>
                  {(() => {
                    const availableCards = cardTypes.filter(card => card.machine_id === ftData.handler.id);
                    return availableCards.length > 0 ? (
                      <Table 
                        dataSource={availableCards}
                        rowKey="id"
                        rowSelection={{
                          type: 'checkbox',
                          onChange: (selectedRowKeys, selectedRows) => 
                            handleCardSelection('ft', 'handler', selectedRowKeys, selectedRows),
                          selectedRowKeys: (ftData.handlerCards || []).map(card => card.id)
                        }}
                        columns={cardColumns('ft', 'handler')}
                        pagination={{ pageSize: 5, showSizeChanger: false }}
                      />
                    ) : (
                      <EmptyState 
                        description={`该分选机暂无可用板卡`}
                        size="small"
                      />
                    );
                  })()} 
                </div>
              )}
              
              <p><strong>FT测试机机时费: {formatPrice(ftHourlyFee)}</strong></p>
            </Card>
          )}

          {selectedTypes.includes('cp') && (
            <Card title="CP" style={{ marginBottom: 20 }}>
              {/* 测试机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择测试机</h4>
                {machines && machines.length > 0 ? (
                  <Select 
                    style={{ width: '100%' }}
                    placeholder="选择测试机" 
                    onChange={(value) => handleTestMachineSelect('cp', value)}
                    value={cpData.testMachine ? cpData.testMachine.id : undefined}
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
                ) : (
                  <EmptyState 
                    description="暂无可用的测试机"
                    action={<Button onClick={fetchData}>刷新数据</Button>}
                  />
                )}
              </div>
              
              {/* 测试机板卡选择 */}
              {cpData.testMachine && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择测试机板卡</h4>
                  {(() => {
                    const availableCards = cardTypes.filter(card => card.machine_id === cpData.testMachine.id);
                    return availableCards.length > 0 ? (
                      <Table 
                        dataSource={availableCards}
                        rowKey="id"
                        rowSelection={{
                          type: 'checkbox',
                          onChange: (selectedRowKeys, selectedRows) => 
                            handleCardSelection('cp', 'testMachine', selectedRowKeys, selectedRows),
                          selectedRowKeys: (cpData.testMachineCards || []).map(card => card.id)
                        }}
                        columns={cardColumns('cp', 'testMachine')}
                        pagination={{ pageSize: 5, showSizeChanger: false }}
                      />
                    ) : (
                      <EmptyState 
                        description={`该测试机暂无可用板卡`}
                        size="small"
                      />
                    );
                  })()} 
                </div>
              )}
              
              {/* 探针台选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择探针台</h4>
                {probers && probers.length > 0 ? (
                  <Select 
                    style={{ width: '100%' }}
                    placeholder="选择探针台" 
                    onChange={(value) => handleProberSelect('cp', value)}
                    value={cpData.prober ? cpData.prober.id : undefined}
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
                ) : (
                  <EmptyState 
                    description="暂无可用的探针台"
                    action={<Button onClick={fetchData}>刷新数据</Button>}
                  />
                )}
              </div>
              
              {/* 探针台板卡选择 */}
              {cpData.prober && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择探针台板卡</h4>
                  {(() => {
                    const availableCards = cardTypes.filter(card => card.machine_id === cpData.prober.id);
                    return availableCards.length > 0 ? (
                      <Table 
                        dataSource={availableCards}
                        rowKey="id"
                        rowSelection={{
                          type: 'checkbox',
                          onChange: (selectedRowKeys, selectedRows) => 
                            handleCardSelection('cp', 'prober', selectedRowKeys, selectedRows),
                          selectedRowKeys: (cpData.proberCards || []).map(card => card.id)
                        }}
                        columns={cardColumns('cp', 'prober')}
                        pagination={{ pageSize: 5, showSizeChanger: false }}
                      />
                    ) : (
                      <EmptyState 
                        description={`该探针台暂无可用板卡`}
                        size="small"
                      />
                    );
                  })()} 
                </div>
              )}
              
              <p><strong>CP小时费: {formatPrice(cpHourlyFee)}</strong></p>
            </Card>
          )}
        </>
      )}

      {/* 第二步：辅助设备选择 */}
      {currentStep === 1 && (
        <div>
          <h2 className="section-title">辅助设备选择</h2>
          
          <Card title="辅助设备选择" style={{ marginBottom: 20 }}>
            <Tabs defaultActiveKey="others">
              {/* 分选机类辅助设备 */}
              {auxDevices.handlers && auxDevices.handlers.length > 0 && (
                <TabPane tab="分选机类" key="handlers">
                  <Table 
                    dataSource={auxDevices.handlers}
                    rowKey="id"
                    rowSelection={{
                      type: 'checkbox',
                      onChange: handleAuxDeviceSelect,
                      selectedRowKeys: selectedAuxDevices.map(device => device.id)
                    }}
                    columns={auxDeviceColumns}
                    pagination={{ pageSize: 5, showSizeChanger: false }}
                  />
                </TabPane>
              )}
              
              {/* 探针台类辅助设备 */}
              {auxDevices.probers && auxDevices.probers.length > 0 && (
                <TabPane tab="探针台类" key="probers">
                  <Table 
                    dataSource={auxDevices.probers}
                    rowKey="id"
                    rowSelection={{
                      type: 'checkbox',
                      onChange: handleAuxDeviceSelect,
                      selectedRowKeys: selectedAuxDevices.map(device => device.id)
                    }}
                    columns={auxDeviceColumns}
                    pagination={{ pageSize: 5, showSizeChanger: false }}
                  />
                </TabPane>
              )}
              
              {/* 其他类辅助设备 */}
              <TabPane tab="其他设备" key="others">
                {auxDevices.others && auxDevices.others.length > 0 ? (
                  <Table 
                    dataSource={auxDevices.others}
                    rowKey="id"
                    rowSelection={{
                      type: 'checkbox',
                      onChange: handleAuxDeviceSelect,
                      selectedRowKeys: selectedAuxDevices.map(device => device.id)
                    }}
                    columns={auxDeviceColumns}
                    pagination={{ pageSize: 5, showSizeChanger: false }}
                  />
                ) : (
                  <EmptyState 
                    description="暂无可用的其他设备"
                    size="small"
                  />
                )}
              </TabPane>
            </Tabs>
            
            {selectedAuxDevices.length > 0 && (
              <p style={{ marginTop: 10 }}><strong>辅助设备机时费: {formatPrice(calculateAuxDeviceFee())}</strong></p>
            )}
          </Card>
          
          <Card title="费用明细" style={{ marginBottom: 20 }}>
            <div style={{ padding: '20px 0' }}>
              {selectedTypes.includes('ft') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 15, padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <span style={{ fontWeight: 'bold', color: '#1890ff' }}>FT小时费:</span>
                  <span style={{ fontWeight: 'bold', fontSize: '16px', color: '#1890ff' }}>{formatPrice(ftHourlyFee)}</span>
                </div>
              )}
              {selectedTypes.includes('cp') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 15, padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                  <span style={{ fontWeight: 'bold', color: '#52c41a' }}>CP小时费:</span>
                  <span style={{ fontWeight: 'bold', fontSize: '16px', color: '#52c41a' }}>{formatPrice(cpHourlyFee)}</span>
                </div>
              )}
              {selectedAuxDevices.length > 0 && (
                <div style={{ marginTop: 15 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10, fontWeight: 'bold', borderBottom: '1px solid #d9d9d9', paddingBottom: '5px' }}>
                    <span>辅助设备费用:</span>
                    <span>{formatPrice(auxDeviceFee)}/小时</span>
                  </div>
                  {selectedAuxDevices.map((device, index) => (
                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, paddingLeft: 20, color: '#666' }}>
                      <span>• {device.name}</span>
                      <span>{formatPrice(calculateAuxDeviceHourlyRate(device))}/小时</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* 导航按钮 */}
      <Card style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Button 
              onClick={handlePrevStep} 
              disabled={currentStep === 0}
              size="large"
            >
              返回上一步
            </Button>
            <Button 
              onClick={resetQuote}
              style={{ marginLeft: 10 }}
              size="large"
              danger
            >
              重置报价
            </Button>
          </div>
          
          {/* 进度提示 */}
          <div style={{ textAlign: 'center', color: '#666' }}>
            <div>步骤 {currentStep + 1} / 2</div>
            <div style={{ fontSize: '12px', marginTop: '4px' }}>
              {currentStep === 0 ? '配置测试机器和板卡' : '选择辅助设备并确认费用'}
            </div>
          </div>
          
          <div>
            <Button 
              onClick={() => {
                ConfirmDialog.showCustomConfirm({
                  title: '退出报价确认',
                  content: '您确定要退出当前报价吗？未保存的配置将会丢失。',
                  onOk: () => navigate('/')
                });
              }}
              style={{ marginRight: 10 }}
              size="large"
            >
              退出报价
            </Button>
            <Button 
              type="primary" 
              onClick={handleNextStep}
              size="large"
              disabled={currentStep === 0 && !selectedTypes.length}
            >
              {currentStep === 1 ? '生成报价结果' : '继续下一步'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default MassProductionQuote;