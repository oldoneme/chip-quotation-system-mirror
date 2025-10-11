import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Select, Table, Tabs, Spin, Alert, Checkbox, Button, Card, InputNumber, message, Divider } from 'antd';
// 移除StepIndicator导入，统一为单页面模式
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
import { ceilByCurrency, formatQuotePrice } from '../utils';
import useQuoteEditMode from '../hooks/useQuoteEditMode';
import { QuoteApiService } from '../services/quoteApi';
import '../App.css';

const { Option } = Select;


const MassProductionQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { state } = location;
  const { user } = useAuth();

  // 编辑模式相关状态
  const { isEditMode, editingQuote, loading: editLoading, convertQuoteToFormData } = useQuoteEditMode();

  // 编辑模式数据加载标志（确保只加载一次）
  const [editDataLoaded, setEditDataLoaded] = useState(false);

  // 移除步骤管理，统一为单页面模式
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isMounted, setIsMounted] = useState(false);
  const [editMessageShown, setEditMessageShown] = useState(false);
  
  // 机器数据
  const [machines, setMachines] = useState([]);      // 测试机
  const [handlers, setHandlers] = useState([]);      // 分选机
  const [probers, setProbers] = useState([]);        // 探针台
  const [auxDevices, setAuxDevices] = useState({ handlers: [], probers: [], others: [] }); // 辅助设备
  const [cardTypes, setCardTypes] = useState([]);    // 板卡类型
  const [auxMachinesByType, setAuxMachinesByType] = useState({});  // 辅助设备按类型分组
  const [auxMachineTypes, setAuxMachineTypes] = useState([]);      // 辅助设备类型列表
  
  // 选择状态
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [selectedCards, setSelectedCards] = useState([]);
  const [selectedAuxDevices, setSelectedAuxDevices] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState(['ft', 'cp']);
  const [quoteCurrency, setQuoteCurrency] = useState('CNY'); // 报价币种，默认人民币
  const [quoteExchangeRate, setQuoteExchangeRate] = useState(7.2); // 报价汇率，默认7.2
  
  // 基本信息状态
  const [customerInfo, setCustomerInfo] = useState({
    companyName: '',
    contactPerson: '',
    phone: '',
    email: ''
  });
  const [projectInfo, setProjectInfo] = useState({
    projectName: '',
    chipPackage: '',
    testType: 'mass_production',
    urgency: 'normal',
    quoteUnit: '昆山芯信安'  // 新增报价单位字段
  });
  
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
            // 恢复客户信息和项目信息
            if (parsedState.customerInfo) {
              setCustomerInfo(parsedState.customerInfo);
            }
            if (parsedState.projectInfo) {
              setProjectInfo(parsedState.projectInfo);
            }
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

  // 编辑模式数据预填充
  useEffect(() => {
    // 只在编辑模式下，且数据未加载过时执行，并且需要等待cardTypes和machines数据加载完成
    if (isEditMode && editingQuote && !editLoading && !editDataLoaded && cardTypes.length > 0 && machines.length > 0) {
      console.log('MassProductionQuote 编辑模式：开始预填充数据', editingQuote);

      // 合并所有机器数据供ID匹配使用（包括所有类型的辅助设备）
      const allMachines = [
        ...machines,
        ...handlers,
        ...probers,
        ...auxDevices.handlers,
        ...auxDevices.probers,
        ...auxDevices.others
      ];
      const formData = convertQuoteToFormData(editingQuote, 'mass_production', cardTypes, allMachines);

      if (formData) {
        // 填充基本信息
        setCustomerInfo(formData.customerInfo);
        setProjectInfo(formData.projectInfo);

        // 填充报价参数
        if (formData.quoteCurrency) setQuoteCurrency(formData.quoteCurrency);
        if (formData.quoteExchangeRate) setQuoteExchangeRate(formData.quoteExchangeRate);

        // 填充设备配置（从deviceConfig中获取）
        if (formData.deviceConfig) {
          const { deviceConfig } = formData;

          // 设置测试类型
          if (deviceConfig.selectedTypes) {
            setSelectedTypes(deviceConfig.selectedTypes);
          }

          // 设置FT数据
          if (deviceConfig.ftData) {
            setFtData(deviceConfig.ftData);
          }

          // 设置CP数据
          if (deviceConfig.cpData) {
            setCpData(deviceConfig.cpData);
          }

          // 设置辅助设备
          if (deviceConfig.auxDevices) {
            setSelectedAuxDevices(deviceConfig.auxDevices);
          }

          // 为板卡数量创建持久化数据
          const cardQuantities = {};
          deviceConfig.ftData?.testMachineCards?.forEach(card => {
            cardQuantities[`ft-testMachine-${card.id}`] = card.quantity || 1;
          });
          deviceConfig.ftData?.handlerCards?.forEach(card => {
            cardQuantities[`ft-handler-${card.id}`] = card.quantity || 1;
          });
          deviceConfig.cpData?.testMachineCards?.forEach(card => {
            cardQuantities[`cp-testMachine-${card.id}`] = card.quantity || 1;
          });
          deviceConfig.cpData?.proberCards?.forEach(card => {
            cardQuantities[`cp-prober-${card.id}`] = card.quantity || 1;
          });
          setPersistedCardQuantities(cardQuantities);
        }

        // 标记数据已加载
        setEditDataLoaded(true);

        // 只在第一次显示消息
        if (!editMessageShown) {
          message.info(`正在编辑报价单: ${editingQuote.quote_number || editingQuote.id || '未知'}`);
          setEditMessageShown(true);
        }
      }
    }
  }, [isEditMode, editingQuote, editLoading, editDataLoaded, cardTypes, machines, handlers, probers, auxDevices, editMessageShown]);

  // 重置编辑消息标志
  useEffect(() => {
    if (!isEditMode) {
      setEditMessageShown(false);
    }
  }, [isEditMode]);

  // 格式化价格显示（包含币种符号）
  const formatPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, quoteCurrency);
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

      // 获取层级化的机器类型数据
      const hierarchicalData = await fetch('/api/v1/hierarchical/machine-types').then(res => res.json());
      console.log('获取到的层级化机器类型数据:', hierarchicalData);

      setCardTypes(cardTypesResponse);
      setAuxDevices({
        handlers: auxDevicesResponse.filter(device => device.type === 'handler'),
        probers: auxDevicesResponse.filter(device => device.type === 'prober'),
        others: auxDevicesResponse.filter(device => !device.type || (device.type !== 'handler' && device.type !== 'prober'))
      });

      // 筛选出辅助设备类型(排除测试机、分选机、探针台)
      const auxTypes = hierarchicalData.filter(type =>
        type.name !== '测试机' &&
        type.name !== '分选机' &&
        type.name !== '探针台'
      ).map(type => ({
        id: type.id,
        name: type.name
      }));

      setAuxMachineTypes(auxTypes);

      // 将所有机器按类型分组(只包含辅助设备类型)
      const groupedAuxMachines = {};
      hierarchicalData.forEach(type => {
        if (type.name !== '测试机' && type.name !== '分选机' && type.name !== '探针台') {
          type.suppliers.forEach(supplier => {
            if (supplier.machines && supplier.machines.length > 0) {
              supplier.machines.forEach(machine => {
                if (!groupedAuxMachines[type.id]) {
                  groupedAuxMachines[type.id] = [];
                }
                // 确保包含supplier信息
                groupedAuxMachines[type.id].push({
                  ...machine,
                  supplier: {
                    ...supplier,
                    machine_type: {
                      id: type.id,
                      name: type.name
                    }
                  }
                });
              });
            }
          });
        }
      });

      console.log('辅助设备按类型分组:', groupedAuxMachines);
      setAuxMachinesByType(groupedAuxMachines);
      
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
    
    // 根据货币类型向上取整
    return ceilByCurrency(total, quoteCurrency);
  };

  const ftHourlyFee = calculateHourlyFee(ftData, 'ft');
  const cpHourlyFee = calculateHourlyFee(cpData, 'cp');
  
  // 计算辅助设备费用
  const calculateAuxDeviceFee = () => {
    const totalCost = selectedAuxDevices.reduce((total, device) => {
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
    
    // 根据货币类型向上取整
    return ceilByCurrency(totalCost, quoteCurrency);
  };
  
  const auxDeviceFee = calculateAuxDeviceFee();

  // 生成临时报价单号函数
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

  const handleConfirmQuote = async () => {
    // 保存当前状态到sessionStorage（用于"上一步"功能）
    const currentState = {
      selectedTypes,
      ftData,
      cpData,
      selectedAuxDevices,
      persistedCardQuantities,
      quoteCurrency,
      quoteExchangeRate,
      customerInfo,
      projectInfo
    };
    sessionStorage.setItem('massProductionQuoteState', JSON.stringify(currentState));

    {
      // 生成量产报价项目
      const generateMassProductionQuoteItems = () => {
        const items = [];
        
        // 1. FT测试设备
        if (selectedTypes.includes('ft')) {
          // FT测试机（只有板卡费用）
          if (ftData.testMachine && ftData.testMachine.name && ftData.testMachineCards.length > 0) {
            let testMachineFee = 0;

            // 计算测试机板卡费用
            ftData.testMachineCards.forEach(card => {
              if (card && card.quantity > 0) {
                let adjustedPrice = card.unit_price / 10000;

                // 根据报价币种和机器币种进行转换
                if (quoteCurrency === 'USD') {
                  if (ftData.testMachine.currency === 'CNY' || ftData.testMachine.currency === 'RMB') {
                    adjustedPrice = adjustedPrice / quoteExchangeRate;
                  }
                } else {
                  adjustedPrice = adjustedPrice * (ftData.testMachine.exchange_rate || 1);
                }

                testMachineFee += adjustedPrice * (ftData.testMachine.discount_rate || 1) * card.quantity;
              }
            });

            if (testMachineFee > 0) {
              // 应用价格向上取整
              const ceiledFee = ceilByCurrency(testMachineFee, quoteCurrency);

              // 准备板卡信息JSON
              const cardsInfo = ftData.testMachineCards.map(card => ({
                id: card.id,
                board_name: card.board_name || '',
                part_number: card.part_number || '',
                quantity: card.quantity || 1
              }));

              items.push({
                item_name: ftData.testMachine.name || 'FT测试机',
                item_description: `FT测试机 - ${typeof ftData.testMachine.supplier === 'object'
                  ? ftData.testMachine.supplier.name || ''
                  : ftData.testMachine.supplier || ''}`,
                machine_type: '测试机',
                supplier: typeof ftData.testMachine.supplier === 'object'
                  ? ftData.testMachine.supplier.name || ''
                  : ftData.testMachine.supplier || '',
                machine_model: ftData.testMachine.name || '',
                configuration: JSON.stringify({
                  device_type: '测试机',
                  device_model: ftData.testMachine.name,
                  test_type: 'FT',
                  cards: cardsInfo
                }),
                quantity: 1,
                unit: '小时',
                unit_price: ceiledFee,
                total_price: ceiledFee,
                machine_id: ftData.testMachine.id,
                category_type: 'machine'
              });
            }
          }
          
          // FT分选机（只有板卡费用）
          if (ftData.handler && ftData.handler.name && ftData.handlerCards.length > 0) {
            let handlerFee = 0;

            // 计算分选机板卡费用
            ftData.handlerCards.forEach(card => {
              if (card && card.quantity > 0) {
                let adjustedPrice = card.unit_price / 10000;

                // 根据报价币种和机器币种进行转换
                if (quoteCurrency === 'USD') {
                  if (ftData.handler.currency === 'CNY' || ftData.handler.currency === 'RMB') {
                    adjustedPrice = adjustedPrice / quoteExchangeRate;
                  }
                } else {
                  adjustedPrice = adjustedPrice * (ftData.handler.exchange_rate || 1);
                }

                handlerFee += adjustedPrice * (ftData.handler.discount_rate || 1) * card.quantity;
              }
            });

            if (handlerFee > 0) {
              // 应用价格向上取整
              const ceiledFee = ceilByCurrency(handlerFee, quoteCurrency);

              // 准备板卡信息JSON
              const cardsInfo = ftData.handlerCards.map(card => ({
                id: card.id,
                board_name: card.board_name || '',
                part_number: card.part_number || '',
                quantity: card.quantity || 1
              }));

              items.push({
                item_name: ftData.handler.name || 'FT分选机',
                item_description: `FT分选机 - ${typeof ftData.handler.supplier === 'object'
                  ? ftData.handler.supplier.name || ''
                  : ftData.handler.supplier || ''}`,
                machine_type: '分选机',
                supplier: typeof ftData.handler.supplier === 'object'
                  ? ftData.handler.supplier.name || ''
                  : ftData.handler.supplier || '',
                machine_model: ftData.handler.name || '',
                configuration: JSON.stringify({
                  device_type: '分选机',
                  device_model: ftData.handler.name,
                  test_type: 'FT',
                  cards: cardsInfo
                }),
                quantity: 1,
                unit: '小时',
                unit_price: ceiledFee,
                total_price: ceiledFee,
                machine_id: ftData.handler.id,
                category_type: 'machine'
              });
            }
          }
        }
        
        // 2. CP测试设备
        if (selectedTypes.includes('cp')) {
          // CP测试机（只有板卡费用）
          if (cpData.testMachine && cpData.testMachine.name && cpData.testMachineCards.length > 0) {
            let testMachineFee = 0;

            // 计算测试机板卡费用
            cpData.testMachineCards.forEach(card => {
              if (card && card.quantity > 0) {
                let adjustedPrice = card.unit_price / 10000;

                // 根据报价币种和机器币种进行转换
                if (quoteCurrency === 'USD') {
                  if (cpData.testMachine.currency === 'CNY' || cpData.testMachine.currency === 'RMB') {
                    adjustedPrice = adjustedPrice / quoteExchangeRate;
                  }
                } else {
                  adjustedPrice = adjustedPrice * (cpData.testMachine.exchange_rate || 1);
                }

                testMachineFee += adjustedPrice * (cpData.testMachine.discount_rate || 1) * card.quantity;
              }
            });

            if (testMachineFee > 0) {
              // 应用价格向上取整
              const ceiledFee = ceilByCurrency(testMachineFee, quoteCurrency);

              // 准备板卡信息JSON
              const cardsInfo = cpData.testMachineCards.map(card => ({
                id: card.id,
                board_name: card.board_name || '',
                part_number: card.part_number || '',
                quantity: card.quantity || 1
              }));

              items.push({
                item_name: cpData.testMachine.name || 'CP测试机',
                item_description: `CP测试机 - ${typeof cpData.testMachine.supplier === 'object'
                  ? cpData.testMachine.supplier.name || ''
                  : cpData.testMachine.supplier || ''}`,
                machine_type: '测试机',
                supplier: typeof cpData.testMachine.supplier === 'object'
                  ? cpData.testMachine.supplier.name || ''
                  : cpData.testMachine.supplier || '',
                machine_model: cpData.testMachine.name || '',
                configuration: JSON.stringify({
                  device_type: '测试机',
                  device_model: cpData.testMachine.name,
                  test_type: 'CP',
                  cards: cardsInfo
                }),
                quantity: 1,
                unit: '小时',
                unit_price: ceiledFee,
                total_price: ceiledFee,
                machine_id: cpData.testMachine.id,
                category_type: 'machine'
              });
            }
          }
          
          // CP探针台（只有板卡费用）
          if (cpData.prober && cpData.prober.name && cpData.proberCards.length > 0) {
            let proberFee = 0;

            // 计算探针台板卡费用
            cpData.proberCards.forEach(card => {
              if (card && card.quantity > 0) {
                let adjustedPrice = card.unit_price / 10000;

                // 根据报价币种和机器币种进行转换
                if (quoteCurrency === 'USD') {
                  if (cpData.prober.currency === 'CNY' || cpData.prober.currency === 'RMB') {
                    adjustedPrice = adjustedPrice / quoteExchangeRate;
                  }
                } else {
                  adjustedPrice = adjustedPrice * (cpData.prober.exchange_rate || 1);
                }

                proberFee += adjustedPrice * (cpData.prober.discount_rate || 1) * card.quantity;
              }
            });

            if (proberFee > 0) {
              // 应用价格向上取整
              const ceiledFee = ceilByCurrency(proberFee, quoteCurrency);

              // 准备板卡信息JSON
              const cardsInfo = cpData.proberCards.map(card => ({
                id: card.id,
                board_name: card.board_name || '',
                part_number: card.part_number || '',
                quantity: card.quantity || 1
              }));

              items.push({
                item_name: cpData.prober.name || 'CP探针台',
                item_description: `CP探针台 - ${typeof cpData.prober.supplier === 'object'
                  ? cpData.prober.supplier.name || ''
                  : cpData.prober.supplier || ''}`,
                machine_type: '探针台',
                supplier: typeof cpData.prober.supplier === 'object'
                  ? cpData.prober.supplier.name || ''
                  : cpData.prober.supplier || '',
                machine_model: cpData.prober.name || '',
                configuration: JSON.stringify({
                  device_type: '探针台',
                  device_model: cpData.prober.name,
                  test_type: 'CP',
                  cards: cardsInfo
                }),
                quantity: 1,
                unit: '小时',
                unit_price: ceiledFee,
                total_price: ceiledFee,
                machine_id: cpData.prober.id,
                category_type: 'machine'
              });
            }
          }
        }
        
        // 3. 辅助设备费用
        selectedAuxDevices.forEach(device => {
          if (device) {
            // 计算单个辅助设备的小时费率（参考calculateAuxDeviceHourlyRate函数）
            let deviceHourlyRate = 0;
            if (device.supplier || device.machine_type) {
              // 如果是机器类型的辅助设备，计算板卡费用
              const machineCards = cardTypes.filter(card => card.machine_id === device.id);
              deviceHourlyRate = machineCards.reduce((sum, card) => {
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
            } else {
              // 如果是原来的辅助设备类型，使用小时费率
              deviceHourlyRate = device.hourly_rate || 0;
              if (quoteCurrency === 'USD') {
                deviceHourlyRate = deviceHourlyRate / quoteExchangeRate;
              }
            }

            // 应用价格向上取整
            const ceiledFee = ceilByCurrency(deviceHourlyRate, quoteCurrency);

            if (ceiledFee > 0) {
              items.push({
                item_name: device.name || '辅助设备',
                item_description: `辅助设备 - ${device.description || ''}`,
                machine_type: '辅助设备',
                supplier: typeof device.supplier === 'object'
                  ? device.supplier?.name || ''
                  : device.supplier || '',
                machine_model: device.model || device.name || '',
                configuration: JSON.stringify({
                  device_type: '辅助设备',
                  device_model: device.name,
                  device_category: device.category || device.machine_type || 'other'
                }),
                quantity: 1,
                unit: '小时',
                unit_price: ceiledFee,
                total_price: ceiledFee,
                machine_id: device.id,
                category_type: 'auxiliary_device'
              });
            }
          }
        });
        
        return items;
      };
      
      // 计算总费用
      const totalAmount = ftHourlyFee + cpHourlyFee + auxDeviceFee;
      
      // 准备数据库创建数据
      const quoteCreateData = {
        title: `${projectInfo.projectName || '量产机时报价'} - ${customerInfo.companyName}`,
        quote_type: 'mass_production',
        customer_name: customerInfo.companyName,
        customer_contact: customerInfo.contactPerson,
        customer_phone: customerInfo.phone,
        customer_email: customerInfo.email,
        quote_unit: projectInfo.quoteUnit,
        currency: quoteCurrency,
        subtotal: totalAmount,
        total_amount: totalAmount,
        description: `项目：${projectInfo.projectName}，芯片封装：${projectInfo.chipPackage}，测试类型：${selectedTypes.join('、')}`,
        notes: `汇率：${quoteExchangeRate}，紧急程度：${projectInfo.urgency === 'urgent' ? '紧急' : '正常'}`,
        items: generateMassProductionQuoteItems()
      };
      
      // 完成报价，将数据传递到结果页面
      const quoteData = {
        type: '量产报价',
        number: generateTempQuoteNumber(projectInfo.quoteUnit),  // 使用新的报价单号生成函数
        date: new Date().toLocaleString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }),
        customerInfo,  // 添加客户信息
        projectInfo,   // 添加项目信息
        selectedTypes,
        ftData,
        cpData,
        selectedAuxDevices,
        cardTypes,
        ftHourlyFee,
        cpHourlyFee,
        auxDeviceFee,
        quoteCurrency, // 添加报价币种
        quoteExchangeRate, // 添加报价汇率
        persistedCardQuantities, // 添加板卡数量持久化数据
        generatedAt: new Date().toISOString(),
        quoteCreateData, // 添加数据库创建数据
        // 编辑模式相关字段
        isEditMode: isEditMode || false,
        editingQuoteId: isEditMode && editingQuote ? editingQuote.id : null,
        quoteNumber: isEditMode && editingQuote ? editingQuote.quote_number : null
      };

      if (isEditMode && editingQuote) {
        // 编辑模式：调用API更新报价
        try {
          const updatedQuote = await QuoteApiService.updateQuote(editingQuote.id, quoteCreateData);
          message.success('量产机时报价更新成功！');

          // 编辑成功后跳转到报价详情页面
          navigate(`/quote-detail/${editingQuote.quote_number}`, {
            state: {
              message: '报价单更新成功',
              updatedQuote: updatedQuote
            }
          });
        } catch (error) {
          console.error('更新量产机时报价失败:', error);
          message.error('更新报价单失败，请重试');
        }
      } else {
        // 新建模式：通过location.state传递数据到结果页面
        navigate('/quote-result', { state: { ...quoteData, fromQuotePage: true } });
      }
    }
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
        render: (value) => formatQuotePrice(value || 0, quoteCurrency)
      });
    }
    
    columns.push({
      title: 'Quantity',
      render: (_, record) => {
        const cardKey = `${type}-${machineType}-${record.id}`;
        const currentQuantity = persistedCardQuantities[cardKey] || 1;
        return (
          <InputNumber
            min={1}
            value={currentQuantity}
            onChange={(value) => handleCardQuantityChange(type, machineType, record.id, value)}
          />
        );
      }
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
      // 根据货币类型向上取整
      return ceilByCurrency(totalRate, quoteCurrency);
    } else {
      // 如果是原来的辅助设备类型，使用小时费率
      let hourlyRate = device.hourly_rate || 0;
      if (quoteCurrency === 'USD') {
        hourlyRate = hourlyRate / quoteExchangeRate;
      }
      // 根据货币类型向上取整
      return ceilByCurrency(hourlyRate, quoteCurrency);
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
      <h2>{isEditMode ? `编辑量产机时报价 - ${editingQuote?.quote_number || editingQuote?.id}` : '量产报价'}</h2>
      
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

      {/* 基本信息 - 单页面显示 */}
      <div>
        <h2 className="section-title">基本信息</h2>
          
          {/* 客户信息 */}
          <Card title="客户信息" style={{ marginBottom: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  公司名称 <span style={{ color: 'red' }}>*</span>
                </label>
                <input
                  type="text"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={customerInfo.companyName}
                  onChange={(e) => setCustomerInfo({...customerInfo, companyName: e.target.value})}
                  placeholder="请输入公司名称"
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  联系人 <span style={{ color: 'red' }}>*</span>
                </label>
                <input
                  type="text"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={customerInfo.contactPerson}
                  onChange={(e) => setCustomerInfo({...customerInfo, contactPerson: e.target.value})}
                  placeholder="请输入联系人姓名"
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>联系电话</label>
                <input
                  type="text"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={customerInfo.phone}
                  onChange={(e) => setCustomerInfo({...customerInfo, phone: e.target.value})}
                  placeholder="请输入联系电话"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>邮箱地址</label>
                <input
                  type="email"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={customerInfo.email}
                  onChange={(e) => setCustomerInfo({...customerInfo, email: e.target.value})}
                  placeholder="请输入邮箱地址"
                />
              </div>
            </div>
          </Card>

          {/* 项目信息 */}
          <Card title="项目信息" style={{ marginBottom: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>项目名称</label>
                <input
                  type="text"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={projectInfo.projectName}
                  onChange={(e) => setProjectInfo({...projectInfo, projectName: e.target.value})}
                  placeholder="请输入项目名称"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  芯片封装 <span style={{ color: 'red' }}>*</span>
                </label>
                <input
                  type="text"
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  value={projectInfo.chipPackage}
                  onChange={(e) => setProjectInfo({...projectInfo, chipPackage: e.target.value})}
                  placeholder="如：QFN48, BGA256等"
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>测试类型</label>
                <select
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: '#fff'
                  }}
                  value={projectInfo.testType}
                  onChange={(e) => setProjectInfo({...projectInfo, testType: e.target.value})}
                >
                  <option value="mass_production">量产机时测试</option>
                  <option value="CP">CP测试</option>
                  <option value="FT">FT测试</option>
                  <option value="mixed">混合测试</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>紧急程度</label>
                <select
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: '#fff'
                  }}
                  value={projectInfo.urgency}
                  onChange={(e) => setProjectInfo({...projectInfo, urgency: e.target.value})}
                >
                  <option value="normal">正常</option>
                  <option value="urgent">紧急</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  报价单位 <span style={{ color: 'red' }}>*</span>
                </label>
                <select
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: '#fff'
                  }}
                  value={projectInfo.quoteUnit}
                  onChange={(e) => setProjectInfo({...projectInfo, quoteUnit: e.target.value})}
                >
                  <option value="昆山芯信安">昆山芯信安</option>
                  <option value="苏州芯昱安">苏州芯昱安</option>
                  <option value="上海芯睿安">上海芯睿安</option>
                  <option value="珠海芯创安">珠海芯创安</option>
                </select>
              </div>
            </div>
          </Card>
        </div>

      {/* 机器选择 - 单页面显示 */}
      <div>
        <h2 className="section-title">机器选择</h2>

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
                        pagination={false}
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
                        pagination={false}
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
                        pagination={false}
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
                        pagination={false}
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
      </div>

      {/* 辅助设备选择 - 单页面显示 */}
      <div>
        <h2 className="section-title">辅助设备选择</h2>

          <Card title="辅助设备选择" style={{ marginBottom: 20 }}>
            <div style={{ marginBottom: 15 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                <h4>已选择的辅助设备</h4>
                <Button
                  type="primary"
                  onClick={() => setSelectedAuxDevices([...selectedAuxDevices, { tempId: Date.now(), typeId: null, device: null }])}
                >
                  添加辅助设备
                </Button>
              </div>

              {selectedAuxDevices.length > 0 ? (
                selectedAuxDevices.map((auxDevice, index) => (
                  <div
                    key={auxDevice.tempId || auxDevice.id || index}
                    style={{
                      marginBottom: '15px',
                      padding: '15px',
                      border: '1px solid #d9d9d9',
                      borderRadius: '6px',
                      backgroundColor: '#fafafa'
                    }}
                  >
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '10px', alignItems: 'start' }}>
                      <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>设备类型</label>
                        <Select
                          style={{ width: '100%' }}
                          placeholder="选择设备类型"
                          value={auxDevice.typeId || (auxDevice.supplier?.machine_type?.id)}
                          onChange={(typeId) => {
                            const newAuxDevices = [...selectedAuxDevices];
                            newAuxDevices[index] = { ...auxDevice, typeId, device: null };
                            setSelectedAuxDevices(newAuxDevices);
                          }}
                        >
                          {auxMachineTypes.map(type => (
                            <Option key={type.id} value={type.id}>
                              {type.name}
                            </Option>
                          ))}
                        </Select>
                      </div>

                      <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>设备型号</label>
                        <Select
                          style={{ width: '100%' }}
                          placeholder="选择设备型号"
                          value={auxDevice.id || auxDevice.device?.id}
                          disabled={!auxDevice.typeId && !(auxDevice.supplier?.machine_type?.id)}
                          onChange={(deviceId) => {
                            const currentTypeId = auxDevice.typeId || auxDevice.supplier?.machine_type?.id;
                            const device = auxMachinesByType[currentTypeId]?.find(d => d.id === deviceId);
                            if (device) {
                              const newAuxDevices = [...selectedAuxDevices];
                              newAuxDevices[index] = device;
                              setSelectedAuxDevices(newAuxDevices);
                            }
                          }}
                        >
                          {(auxMachinesByType[auxDevice.typeId || auxDevice.supplier?.machine_type?.id] || []).map(device => (
                            <Option key={device.id} value={device.id}>
                              {device.name} ({device.currency}, 汇率: {device.exchange_rate || 1.0}, 折扣率: {device.discount_rate || 1.0})
                            </Option>
                          ))}
                        </Select>
                      </div>

                      <div style={{ paddingTop: '30px' }}>
                        <Button
                          danger
                          onClick={() => {
                            const newAuxDevices = selectedAuxDevices.filter((_, i) => i !== index);
                            setSelectedAuxDevices(newAuxDevices);
                          }}
                        >
                          删除
                        </Button>
                      </div>
                    </div>

                    {auxDevice.id && (
                      <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#fff', borderRadius: '4px' }}>
                        <strong>设备费率: {formatPrice(calculateAuxDeviceHourlyRate(auxDevice))}/小时</strong>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <EmptyState description="暂无选择的辅助设备，点击上方按钮添加" />
              )}
            </div>
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
              {selectedAuxDevices.length > 0 && selectedAuxDevices.some(d => d.id) && (
                <div style={{ marginTop: 15 }}>
                  <div style={{ fontWeight: 'bold', marginBottom: 10 }}>
                    <span>辅助设备:</span>
                  </div>
                  {selectedAuxDevices.filter(d => d.id).map((device, index) => (
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

      {/* 确认报价按钮 - 单页面模式 */}
      <Card style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <Button
            onClick={() => {
              ConfirmDialog.showCustomConfirm({
                title: '退出报价确认',
                content: '您确定要退出当前报价吗？未保存的配置将会丢失。',
                onOk: () => navigate('/')
              });
            }}
            size="large"
          >
            退出报价
          </Button>
          <Button
            type="primary"
            onClick={handleConfirmQuote}
            size="large"
          >
            {isEditMode ? '保存编辑' : '完成报价'}
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default MassProductionQuote;