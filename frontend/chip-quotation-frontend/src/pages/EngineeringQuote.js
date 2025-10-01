import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Select, Table, Alert, InputNumber, Button, Card, Checkbox, Divider, message } from 'antd';
// 移除StepIndicator导入，统一为单页面模式
import { LoadingSpinner, EmptyState } from '../components/CommonComponents';
import { formatHourlyRate, ceilByCurrency, formatQuotePrice, formatIntermediatePrice } from '../utils';
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
import QuoteApiService from '../services/quoteApi';
import useQuoteEditMode from '../hooks/useQuoteEditMode';
import '../App.css';

const { Option } = Select;


const EngineeringQuote = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // 编辑模式管理
  const { isEditMode, editingQuote, loading: editLoading, convertQuoteToFormData } = useQuoteEditMode();

  // 编辑模式数据加载标志（确保只加载一次）
  const [editDataLoaded, setEditDataLoaded] = useState(false);

  // 移除步骤管理，统一为单页面模式
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
    testType: 'engineering',
    urgency: 'normal',
    quoteUnit: '昆山芯信安'  // 默认选择第一个
  });
  
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
          setMachines(machinesData);
          setHandlers([]);
          setProbers([]);
          setAuxMachines([]);
          
        } else {
          // 筛选测试机（机器类型为"测试机"的机器）
          const testMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isTestMachine = machineTypeName === '测试机';
            return isTestMachine;
          });
          
          // 筛选分选机（机器类型为"分选机"的机器）
          const handlerMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isHandler = machineTypeName === '分选机';
            return isHandler;
          });
          
          // 筛选探针台（机器类型为"探针台"的机器）
          const proberMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isProber = machineTypeName === '探针台';
            return isProber;
          });
          
          // 筛选辅助设备（机器类型不属于测试机、分选机、探针台的机器）
          const auxMachines = machinesData.filter(machine => {
            const machineTypeName = getMachineTypeName(machine);
            const isAuxMachine = machineTypeName !== '测试机' && 
                                machineTypeName !== '分选机' && 
                                machineTypeName !== '探针台';
            return isAuxMachine;
          });
          
          if (isMounted) {
            setMachines(testMachines);      // 测试机
            setHandlers(handlerMachines);   // 分选机
            setProbers(proberMachines);     // 探针台
            setAuxMachines(auxMachines);    // 辅助设备
          }
          
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
          setCustomerInfo(parsedData.customerInfo || { companyName: '', contactPerson: '', phone: '', email: '' });
          setProjectInfo(parsedData.projectInfo || { projectName: '', chipPackage: '', testType: 'engineering', urgency: 'normal', quoteUnit: '昆山芯信安' });
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
        } catch (error) {
          console.error('解析保存状态时出错:', error);
        }
      }
    } else {
      // 正常进入页面时清空所有状态，开始全新流程
      sessionStorage.removeItem('quoteData');
    }

    fetchData();
    
    // 清理函数，防止内存泄漏
    return () => {
      isMounted = false;
    };
  }, []);

  // 编辑模式数据加载（只执行一次）
  useEffect(() => {
    // 如果是从结果页返回，跳过这个数据加载（数据已经在sessionStorage中）
    if (location.state?.fromResultPage) {
      return;
    }

    // 只在编辑模式下，且数据未加载过时执行
    if (isEditMode && editingQuote && !editLoading && !editDataLoaded && cardTypes.length > 0 && machines.length > 0) {
      // 合并所有机器数据供ID匹配使用
      const allMachines = [...machines, ...handlers, ...probers, ...auxMachines];
      const formData = convertQuoteToFormData(editingQuote, 'engineering', cardTypes, allMachines);

      if (formData) {
        // 填充基本信息
        setCustomerInfo(formData.customerInfo);
        setProjectInfo(formData.projectInfo);

        // 填充报价参数
        if (formData.engineeringRate) setEngineeringRate(formData.engineeringRate);
        if (formData.quoteCurrency) setQuoteCurrency(formData.quoteCurrency);
        if (formData.quoteExchangeRate) setQuoteExchangeRate(formData.quoteExchangeRate);

        // 填充设备配置（从deviceConfig中获取）
        if (formData.deviceConfig) {
          const { deviceConfig } = formData;

          // 设置机器选择
          if (deviceConfig.testMachine) setTestMachine(deviceConfig.testMachine);
          if (deviceConfig.handler) setHandler(deviceConfig.handler);
          if (deviceConfig.prober) setProber(deviceConfig.prober);


          // 设置板卡选择
          if (deviceConfig.testMachineCards) setTestMachineCards(deviceConfig.testMachineCards);
          if (deviceConfig.handlerCards) setHandlerCards(deviceConfig.handlerCards);
          if (deviceConfig.proberCards) setProberCards(deviceConfig.proberCards);

          // 设置辅助设备
          if (deviceConfig.auxDevices) setSelectedAuxDevices(deviceConfig.auxDevices);

          // 为板卡数量创建持久化数据
          const cardQuantities = {};
          deviceConfig.testMachineCards?.forEach(card => {
            cardQuantities[`testMachine-${card.id}`] = card.quantity || 1;
          });
          deviceConfig.handlerCards?.forEach(card => {
            cardQuantities[`handler-${card.id}`] = card.quantity || 1;
          });
          deviceConfig.proberCards?.forEach(card => {
            cardQuantities[`prober-${card.id}`] = card.quantity || 1;
          });
          setPersistedCardQuantities(cardQuantities);
        }

        // 填充人员配置（从personnelConfig中获取）
        if (formData.personnelConfig && formData.personnelConfig.personnel) {
          const selectedPersonnelTypes = formData.personnelConfig.personnel
            .filter(person => person.selected)
            .map(person => person.type);
          setSelectedPersonnel(selectedPersonnelTypes);
        }

        // 标记数据已加载
        setEditDataLoaded(true);
      }
    }
  }, [isEditMode, editingQuote, editLoading, editDataLoaded, cardTypes, machines, handlers, probers, auxMachines]);

  // 移除步骤定义，统一为单页面模式

  // 格式化价格显示（包含币种符号）
  // 格式化最终价格（向上取整）
  const formatPrice = (number) => {
    const formattedNumber = formatQuotePrice(number, quoteCurrency);
    if (quoteCurrency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 格式化中间价格（CNY四舍五入显示两位小数，USD向上取整显示两位小数）
  const formatMiddlePrice = (number) => {
    const formattedNumber = formatIntermediatePrice(number, quoteCurrency);
    if (quoteCurrency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 格式化机时价格显示（中间价格，使用formatMiddlePrice）
  const formatHourlyPrice = (number) => {
    return formatMiddlePrice(number);
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

  // nextStep函数已移除 - 使用统一的单页面模式
  
  // 生成工程机时报价项目数据 - 直接使用页面"费用明细"中显示的费率
  const generateEngineeringQuoteItems = () => {
    const items = [];

    // === 机器设备部分：直接使用页面费用明细中的含工程系数费率 ===

    // 测试机机时费（含工程系数）
    if (testMachine && testMachine.name && testMachineCards.length > 0) {
      const testMachineRate = calculateTestMachineFee() * engineeringRate;
      const ceiledRate = ceilByCurrency(testMachineRate, quoteCurrency);

      // 将板卡信息序列化到configuration字段中，用于编辑时恢复
      const cardsInfo = testMachineCards.map(card => ({
        id: card.id,
        board_name: card.board_name || '',
        part_number: card.part_number || '',
        quantity: card.quantity || 1
      }));

      items.push({
        item_name: testMachine.name,
        item_description: `机器 - 测试机`,
        machine_type: '测试机',
        supplier: typeof testMachine.supplier === 'object' ? testMachine.supplier?.name || '' : testMachine.supplier || '',
        machine_model: testMachine.name,
        configuration: JSON.stringify({
          device_type: '测试机',
          device_model: testMachine.name,
          cards: cardsInfo
        }),
        quantity: 1,
        unit: '小时',
        unit_price: ceiledRate,
        total_price: ceiledRate,
        machine_id: testMachine.id
      });
    }
    
    // 分选机机时费（含工程系数）
    if (handler && handler.name && handlerCards.length > 0) {
      const handlerRate = calculateHandlerFee() * engineeringRate;
      const ceiledRate = ceilByCurrency(handlerRate, quoteCurrency);

      // 将板卡信息序列化到configuration字段中，用于编辑时恢复
      const cardsInfo = handlerCards.map(card => ({
        id: card.id,
        board_name: card.board_name || '',
        part_number: card.part_number || '',
        quantity: card.quantity || 1
      }));

      items.push({
        item_name: handler.name,
        item_description: `机器 - 分选机`,
        machine_type: '分选机',
        supplier: typeof handler.supplier === 'object' ? handler.supplier?.name || '' : handler.supplier || '',
        machine_model: handler.name,
        configuration: JSON.stringify({
          device_type: '分选机',
          device_model: handler.name,
          cards: cardsInfo
        }),
        quantity: 1,
        unit: '小时',
        unit_price: ceiledRate,
        total_price: ceiledRate,
        machine_id: handler.id
      });
    }
    
    // 探针台机时费（含工程系数）
    if (prober && prober.name && proberCards.length > 0) {
      const proberRate = calculateProberFee() * engineeringRate;
      const ceiledRate = ceilByCurrency(proberRate, quoteCurrency);

      // 将板卡信息序列化到configuration字段中，用于编辑时恢复
      const cardsInfo = proberCards.map(card => ({
        id: card.id,
        board_name: card.board_name || '',
        part_number: card.part_number || '',
        quantity: card.quantity || 1
      }));

      items.push({
        item_name: prober.name,
        item_description: `机器 - 探针台`,
        machine_type: '探针台',
        supplier: typeof prober.supplier === 'object' ? prober.supplier?.name || '' : prober.supplier || '',
        machine_model: prober.name,
        configuration: JSON.stringify({
          device_type: '探针台',
          device_model: prober.name,
          cards: cardsInfo
        }),
        quantity: 1,
        unit: '小时',
        unit_price: ceiledRate,
        total_price: ceiledRate,
        machine_id: prober.id
      });
    }
    
    // 辅助设备：直接使用页面费用明细中的费率
    if (selectedAuxDevices && selectedAuxDevices.length > 0) {
      selectedAuxDevices.forEach(device => {
        if (!device || !device.name) {
          console.error('无效的辅助设备数据:', device);
          return;
        }
        const deviceRate = calculateAuxDeviceHourlyRate(device);
        const ceiledRate = ceilByCurrency(deviceRate, quoteCurrency);
        items.push({
          item_name: device.name,
          item_description: `机器 - 辅助设备`,
          machine_type: device.supplier?.machine_type?.name || '辅助设备',
          supplier: typeof device.supplier === 'object' ? device.supplier?.name || '' : device.supplier || '',
          machine_model: device.name,
          configuration: `设备类型: 辅助设备, 设备型号: ${device.name}`,
          quantity: 1,
          unit: '小时',
          unit_price: ceiledRate,
          total_price: ceiledRate,
          machine_id: device.id
        });
      });
    }
    
    // === 人员部分：直接使用页面费用明细中的费率 ===

    if (selectedPersonnel && selectedPersonnel.length > 0) {
      selectedPersonnel.forEach(personnelType => {
        // 直接使用页面计算函数得到的费率
        const hourlyRate = calculatePersonnelFeeForQuote(personnelType);
        const ceiledRate = ceilByCurrency(hourlyRate, quoteCurrency);

        items.push({
          item_name: personnelType,
          item_description: `人员 - ${personnelType}`,
          machine_type: '人员',
          supplier: '内部人员',
          machine_model: personnelType,
          configuration: `人员类别: ${personnelType}`,
          quantity: 1,
          unit: '小时',
          unit_price: ceiledRate,
          total_price: ceiledRate
        });
      });
    }
    
    return items;
  };
  
  // 完成报价配置，跳转到最终报价页面
  const handleComplete = () => {
    // 验证必需的字段
    if (!customerInfo.companyName || customerInfo.companyName.trim() === '') {
      message.error('请填写客户公司名称');
      return;
    }
    
    if (!projectInfo.projectName || projectInfo.projectName.trim() === '') {
      message.error('请填写项目名称');
      return;
    }
    
    const quoteItems = generateEngineeringQuoteItems();
    
    const totalAmount = quoteItems.reduce((sum, item) => {
      const itemTotal = isNaN(item.total_price) || item.total_price === null ? 0 : item.total_price;
      return sum + itemTotal;
    }, 0);
    
    const title = `${projectInfo.projectName.trim()} - ${customerInfo.companyName.trim()}`;
    
    // 准备最终报价页面数据
    const quoteData = {
      type: '工程报价',
      quote_type: 'engineering',
      engineeringRate,
      quoteCurrency,
      quoteExchangeRate,
      customerInfo,
      projectInfo,
      testMachine,
      handler,
      prober,
      testMachineCards,
      handlerCards,
      proberCards,
      selectedPersonnel,
      selectedAuxDevices,
      cardTypes,
      totalAmount,
      quoteItems,
      // 编辑模式标识
      isEditMode: isEditMode,
      editingQuoteId: isEditMode && editingQuote ? editingQuote.id : null,
      quoteNumber: isEditMode && editingQuote ? editingQuote.quote_number : null,
      // 添加数据库创建/更新数据，供确认报价按钮使用
      quoteCreateData: {
        title: title,
        quote_type: 'engineering',
        customer_name: customerInfo.companyName.trim(),
        customer_contact: customerInfo.contactPerson?.trim() || '',
        customer_phone: customerInfo.phone?.trim() || '',
        customer_email: customerInfo.email?.trim() || '',
        quote_unit: projectInfo.quoteUnit,
        currency: quoteCurrency,
        subtotal: totalAmount || 0,
        total_amount: totalAmount || 0,
        payment_terms: '30_days',
        description: `项目：${projectInfo.projectName.trim()}，芯片封装：${projectInfo.chipPackage || ''}，测试类型：工程机时测试，工程系数：${engineeringRate}，报价单位：${projectInfo.quoteUnit}`,
        notes: `汇率：${quoteExchangeRate}，紧急程度：${projectInfo.urgency === 'urgent' ? '紧急' : '正常'}`,
        items: quoteItems
      }
    };

    sessionStorage.setItem('quoteData', JSON.stringify(quoteData));
    navigate('/quote-result');
  };
  
  // 提交工程机时报价到数据库
  const handleSubmit = async () => {
    try {
      // 从sessionStorage获取报价数据
      const storedQuoteData = sessionStorage.getItem('quoteData');
      if (!storedQuoteData) {
        message.error('报价数据丢失，请重新生成报价');
        return;
      }
      
      const quoteData = JSON.parse(storedQuoteData);
      const { quoteItems, totalAmount } = quoteData;
      
      const title = `${projectInfo.projectName || '工程机时报价'} - ${customerInfo.companyName}`;
      
      // 构建API数据格式
      const quoteCreateData = {
        title,
        quote_type: 'engineering',
        customer_name: customerInfo.companyName,
        customer_contact: customerInfo.contactPerson,
        customer_phone: customerInfo.phone,
        customer_email: customerInfo.email,
        quote_unit: projectInfo.quoteUnit,
        currency: quoteCurrency,
        subtotal: totalAmount,
        total_amount: totalAmount,
        payment_terms: '30_days',
        description: `项目：${projectInfo.projectName}，芯片封装：${projectInfo.chipPackage}，测试类型：工程机时测试，工程系数：${engineeringRate}，报价单位：${projectInfo.quoteUnit}`,
        notes: `汇率：${quoteExchangeRate}，紧急程度：${projectInfo.urgency === 'urgent' ? '紧急' : '正常'}`,
        items: quoteItems
      };
      
      // 调用API创建报价单
      const createdQuote = await QuoteApiService.createQuote(quoteCreateData);
      
      message.success('工程机时报价创建成功！');
      
      // 更新sessionStorage中的数据，添加数据库返回的信息
      const updatedQuoteData = {
        ...quoteData,
        quoteNumber: createdQuote.quote_number,
        createdAt: createdQuote.created_at,
        isSubmitted: true
      };
      
      sessionStorage.setItem('quoteData', JSON.stringify(updatedQuoteData));
      
      // 刷新当前页面以显示已提交状态
      window.location.reload();
      
    } catch (error) {
      console.error('创建工程机时报价失败:', error);
      message.error('创建报价单失败，请重试');
    }
  };

  // prevStep函数已移除 - 使用统一的单页面模式

  const resetQuote = () => {
    if (window.confirm('确定要重置所有设置吗？这将清除您当前的所有选择。')) {
      setCustomerInfo({ companyName: '', contactPerson: '', phone: '', email: '' });
      setProjectInfo({ projectName: '', chipPackage: '', testType: 'engineering', urgency: 'normal', quoteUnit: '昆山芯信安' });
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

      // 清除sessionStorage中的状态
      sessionStorage.removeItem('quoteData');
    }
  };

  // 计算测试机费用
  const calculateTestMachineFee = () => {
    if (!testMachine || testMachineCards.length === 0) return 0;

    const totalCost = testMachineCards.reduce((total, card) => {
      // 统一的计算逻辑：所有数据都来自同样的API源
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

      const finalPrice = adjustedPrice * testMachine.discount_rate * (card.quantity || 1);
      return total + finalPrice;
    }, 0);

    // 返回原始计算结果，不向上取整
    return totalCost;
  };
  
  // 计算分选机费用
  const calculateHandlerFee = () => {
    if (!handler || handlerCards.length === 0) return 0;

    const totalCost = handlerCards.reduce((total, card) => {
      // 统一的计算逻辑：所有数据都来自同样的API源
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

    // 返回原始计算结果，不向上取整
    return totalCost;
  };
  
  // 计算探针台费用
  const calculateProberFee = () => {
    if (!prober || proberCards.length === 0) return 0;

    const totalCost = proberCards.reduce((total, card) => {
      // 统一的计算逻辑：所有数据都来自同样的API源
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

    // 返回原始计算结果，不向上取整
    return totalCost;
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
      // 统一的计算逻辑：所有数据都来自同样的API源
      // 检查该机器是否有关联的板卡配置
      const machineCards = cardTypes.filter(card => card.machine_id === device.id);

      if (machineCards.length > 0) {
        // 有板卡配置的机器：计算板卡费用
        const cardTotal = machineCards.reduce((sum, card) => {
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
          return sum + cardFee;
        }, 0);
        return total + cardTotal;
      } else {
        // 无板卡配置的简单设备：直接使用小时费率
        let hourlyRate = device.hourly_rate || device.hourlyRate || 0;

        if (quoteCurrency === 'USD') {
          hourlyRate = hourlyRate / quoteExchangeRate;
        }

        return total + hourlyRate;
      }
    }, 0);

    // 返回原始计算结果，不向上取整
    return totalCost;
  };
  
  // 计算应用工程系数的机器总费用
  const calculateMachineTotalWithEngineeringRate = () => {
    let total = 0;
    total += calculateTestMachineFee();
    total += calculateHandlerFee();
    total += calculateProberFee();
    // 应用工程系数
    const totalWithRate = total * engineeringRate;
    // 返回原始计算结果，不向上取整
    return totalWithRate;
  };
  
  // 计算不应用工程系数的其他费用
  const calculateOtherFees = () => {
    let total = 0;
    
    // 人员费用
    selectedPersonnel.forEach(personType => {
      total += calculatePersonnelFeeForQuote(personType);
    });

    total += calculateAuxDeviceFee();

    // 返回原始计算结果，不向上取整
    return total;
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
      render: (_, record) => {
        // 获取对应machineType的已选卡片数组
        let selectedCards = [];
        if (machineType === 'testMachine') {
          selectedCards = testMachineCards;
        } else if (machineType === 'handler') {
          selectedCards = handlerCards;
        } else if (machineType === 'prober') {
          selectedCards = proberCards;
        }

        // 查找当前板卡在已选列表中的数量
        const selectedCard = selectedCards.find(card => card.id === record.id);
        const quantity = selectedCard ? selectedCard.quantity : 1;

        return (
          <InputNumber
            min={1}
            value={quantity}
            onChange={(value) => handleCardQuantityChange(machineType, record.id, value)}
          />
        );
      }
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
      let hourlyRate = device.hourly_rate || device.hourlyRate || 0;
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

  // 步骤0: 基本信息收集
  const renderBasicInfo = () => (
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
              <option value="engineering">工程机时测试</option>
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
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>报价单位</label>
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
  );

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
            <span>{formatMiddlePrice(calculateTestMachineFee())}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>分选机机时费:</span>
            <span>{formatMiddlePrice(calculateHandlerFee())}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span>探针台机时费:</span>
            <span>{formatMiddlePrice(calculateProberFee())}</span>
          </div>
          {selectedPersonnel.includes('工程师') && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span>工程师小时费:</span>
              <span>{formatMiddlePrice(calculatePersonnelFeeForQuote('工程师'))}</span>
            </div>
          )}
          {selectedPersonnel.includes('技术员') && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <span>技术员小时费:</span>
              <span>{formatMiddlePrice(calculatePersonnelFeeForQuote('技术员'))}</span>
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
                  <span>{formatMiddlePrice(quoteCurrency === 'USD' ? (device.hourly_rate || device.hourlyRate || 0) / quoteExchangeRate : (device.hourly_rate || device.hourlyRate || 0))}/小时</span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
                <span>辅助设备费用小计:</span>
                <span>{formatMiddlePrice(calculateAuxDeviceFee())}</span>
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
        <p>应用工程系数的机器总费用: {formatMiddlePrice(calculateMachineTotalWithEngineeringRate())}</p>
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

  if (editLoading) {
    return <LoadingSpinner message="加载报价数据中..." />;
  }

  return (
    <div className="engineering-quote">
      <h1>{isEditMode && editingQuote ? `编辑工程机时报价 - ${editingQuote.quote_number || editingQuote.id}` : '工程报价'}</h1>
      
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
      
      {/* 统一界面：新建和编辑都显示完整表单 */}
      <div>
        {renderBasicInfo()}
        {renderMachineSelection()}
        {renderPersonnelAndAuxSelection()}
      </div>

      {/* 统一按钮区域 */}
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Button
            onClick={resetQuote}
          >
            重置
          </Button>
        </div>
        <div>
          <Button
            onClick={() => navigate('/')}
            style={{ marginRight: 10 }}
          >
            {isEditMode ? '取消编辑' : '退出报价'}
          </Button>
          <Button
            type="primary"
            onClick={isEditMode ? handleComplete : handleComplete}
          >
            {isEditMode ? '保存编辑' : '完成报价'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EngineeringQuote;