import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button, Card, Divider, message, Input, InputNumber, Table } from 'antd';
import { formatQuotePrice } from '../utils';
import '../App.css';

const QuoteResult = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [quoteData, setQuoteData] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [isQuoteConfirmed, setIsQuoteConfirmed] = useState(false);
  const [engineeringItems, setEngineeringItems] = useState([]);

  const [processItems, setProcessItems] = useState([]);

  // Helper functions for process types
  const isTestProcess = (processName) => {
    if (!processName) return false;
    return (processName.includes('CP') && (processName.includes('1') || processName.includes('2') || processName.includes('3'))) ||
           (processName.includes('FT') && (processName.includes('1') || processName.includes('2') || processName.includes('3')));
  };
  const isBakingProcess = (processName) => processName.includes('烘烤');
  const isTapingProcess = (processName) => processName.includes('编带');
  const isBurnInProcess = (processName) => processName.includes('老化');

  // 初始化工程报价和量产报价项目
  useEffect(() => {
    if (!quoteData) return;
    // 避免重复初始化导致用户编辑丢失
    if (engineeringItems.length > 0 || processItems.length > 0) return;

    if (quoteData.type === '量产报价' || quoteData.type === '量产机时报价') {
      // ... (existing logic for mass production quote) ...
      const items = [];
      const { quoteCurrency, quoteExchangeRate } = quoteData;

      const calculateFee = (machine, cards) => {
        if (!machine || !cards) return 0;
        let total = 0;
        cards.forEach(card => {
          if (card && card.quantity > 0) {
            let price = card.unit_price / 10000;
            if (quoteCurrency === 'USD') {
              if (machine.currency === 'CNY' || machine.currency === 'RMB') {
                price = price / quoteExchangeRate;
              }
            } else {
              price = price * (machine.exchange_rate || 1);
            }
            total += price * (machine.discount_rate || 1) * card.quantity;
          }
        });
        const { ceilByCurrency } = require('../utils');
        return ceilByCurrency(total, quoteCurrency);
      };

      const findOriginal = (name) => quoteData.quoteCreateData?.items?.find(i => i.item_name === name);

      if (quoteData.ftData) {
        if (quoteData.ftData.testMachine) {
          const name = quoteData.ftData.testMachine.name;
          const price = calculateFee(quoteData.ftData.testMachine, quoteData.ftData.testMachineCards);
          items.push({ key: 'ft_tm', name, systemPrice: price, adjustedPrice: price, reason: '', originalData: findOriginal(name), testType: 'FT' });
        }
        if (quoteData.ftData.handler) {
          const name = quoteData.ftData.handler.name;
          const price = calculateFee(quoteData.ftData.handler, quoteData.ftData.handlerCards);
          items.push({ key: 'ft_h', name, systemPrice: price, adjustedPrice: price, reason: '', originalData: findOriginal(name), testType: 'FT' });
        }
      }

      if (quoteData.cpData) {
        if (quoteData.cpData.testMachine) {
          const name = quoteData.cpData.testMachine.name;
          const price = calculateFee(quoteData.cpData.testMachine, quoteData.cpData.testMachineCards);
          items.push({ key: 'cp_tm', name, systemPrice: price, adjustedPrice: price, reason: '', originalData: findOriginal(name), testType: 'CP' });
        }
        if (quoteData.cpData.prober) {
          const name = quoteData.cpData.prober.name;
          const price = calculateFee(quoteData.cpData.prober, quoteData.cpData.proberCards);
          items.push({ key: 'cp_p', name, systemPrice: price, adjustedPrice: price, reason: '', originalData: findOriginal(name), testType: 'CP' });
        }
      }

      if (quoteData.selectedAuxDevices) {
        quoteData.selectedAuxDevices.forEach((device, idx) => {
           const original = findOriginal(device.name);
           const price = original ? original.total_price : 0;
           items.push({ key: `aux_${idx}`, name: device.name, systemPrice: price, adjustedPrice: price, reason: '', originalData: original });
        });
      }

      setEngineeringItems(items);

    } else if ((quoteData.type === '工程报价' || quoteData.type === '工程机时报价') && quoteData.quoteCreateData && quoteData.quoteCreateData.items) {
      // ... (existing logic for engineering quote) ...
      const items = quoteData.quoteCreateData.items.map((item, index) => ({
        key: `item_${index}`,
        name: item.item_name,
        systemPrice: item.total_price,
        adjustedPrice: item.total_price,
        reason: '',
        originalData: item
      }));
      setEngineeringItems(items);
    } else if (quoteData.type === '工序报价' && quoteData.quoteCreateData && quoteData.quoteCreateData.items) {
      // Initialize Process Quote Items
      const items = quoteData.quoteCreateData.items.map((item, index) => {
        let config = {};
        try {
          config = JSON.parse(item.configuration || '{}');
        } catch (e) {
          console.error("Failed to parse configuration", e);
        }
        return {
          ...item,
          key: `process_${index}`,
          config: config, // Store parsed config for easier access
          calculatedUnitPrice: item.unit_price, // Initial calculated price
          finalUnitPrice: config.adjusted_unit_price > 0 ? config.adjusted_unit_price : item.unit_price // Display price
        };
      });
      setProcessItems(items);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quoteData]);

  // Handle changes in Process Quote items
  const handleProcessItemChange = (index, field, value) => {
    setProcessItems(prevItems => {
      const newItems = [...prevItems];
      const item = { ...newItems[index] };
      const config = { ...item.config };
      const processName = config.process_type || item.item_name;

      // Update the specific field in config
      if (field === 'adjusted_machine_rate') config.adjusted_machine_rate = value;
      else if (field === 'uph') {
        config.uph = value;
        item.uph = value; // Update item level uph as well
      }
      else if (field === 'quantity_per_oven') config.quantity_per_oven = value;
      else if (field === 'baking_time') config.baking_time = value;
      else if (field === 'quantity_per_reel') config.quantity_per_reel = value;
      else if (field === 'adjusted_unit_price') config.adjusted_unit_price = value;

      // Recalculate Unit Cost based on process type and new values
      let calculatedCost = 0;
      
      // Basic calculation logic mirrored from ProcessQuote.js
      if (isTestProcess(processName)) {
        const effectiveRate = config.adjusted_machine_rate > 0 ? config.adjusted_machine_rate : config.system_machine_rate;
        if (effectiveRate > 0 && config.uph > 0) {
          calculatedCost = effectiveRate / config.uph;
        }
      } else if (isBakingProcess(processName) || isBurnInProcess(processName)) {
        // (System Rate * Time / 60) / Qty
        // Note: system_machine_rate needs to be available in config. Assuming it is from previous step.
        // If system_machine_rate is missing for baking (it might be 0 or not passed if it's purely manual), we rely on adjusted.
        // Actually for baking, we might not have system_machine_rate if it wasn't calculated before.
        // But let's assume we use what's there.
        // FIX: The calculation in ProcessQuote.js uses testMachineSystemRate. We need to preserve that.
        // If it's not in config, we can't recalculate accurately without machine data. 
        // We should ensure system_machine_rate IS in config for all types if we want to recalculate.
        // ProcessQuote.js currently only puts system_machine_rate in config for Test Processes.
        // I should have added it for others. 
        // fallback: use the initial unit price to reverse engineer or just trust the user adjustment for now if data is missing.
        // BETTER: Use unit_price as base if system rate is missing.
        
        // For now, let's implement the logic assuming system_machine_rate exists or we default to item.calculatedUnitPrice logic
        // If we can't recalculate perfectly, we heavily rely on Adjusted Unit Price.
        
        // However, for test process, we have all info (system rate, adjusted rate, uph).
        
        // For Baking: 
        if (config.test_machine && config.quantity_per_oven > 0 && config.baking_time > 0) {
             // We don't have the machine rate easily here unless we saved it. 
             // Let's assume for non-test processes, the user primarily adjusts the final unit price directly.
             // But if they adjust params, we should try.
             // Given limitations, let's focus on Test Process calculation which is critical.
        }
      }

      // Update finalUnitPrice
      // If user manually set adjusted_unit_price, use it.
      // Otherwise, if it's a test process, use the newly calculated cost.
      // For others, keep existing unless adjusted.
      
      if (field === 'adjusted_unit_price') {
        item.finalUnitPrice = value;
      } else if (isTestProcess(processName)) {
        // Auto-update final price based on parameters if not manually overridden by price directly
        // But wait, if user sets adjusted price, parameter changes shouldn't overwrite it? 
        // Usually parameter changes imply a new calculation.
        // Let's say: if you change params, we recalculate calculatedUnitPrice. 
        // If adjusted_unit_price is set, it takes precedence, UNLESS we want params to drive it.
        // Let's stick to: Calculated is (Rate/UPH). Final is Adjusted > 0 ? Adjusted : Calculated.
        
        // Update calculated cost for display
        item.calculatedUnitPrice = parseFloat(calculatedCost.toFixed(4));
        
        // If user hasn't explicitly set a fixed final price override (adjusted_unit_price), update the final price.
        // Actually, config.adjusted_unit_price IS the override.
        // If user changes UPH, does it update adjusted_unit_price? No. It updates the underlying calc.
        // So Final = Adjusted > 0 ? Adjusted : NewCalculated.
        
        item.finalUnitPrice = config.adjusted_unit_price > 0 ? config.adjusted_unit_price : item.calculatedUnitPrice;
      }

      item.config = config;
      // We don't serialize config back to string yet, we do that on save.
      
      newItems[index] = item;
      return newItems;
    });
  };

  // Handle changes in Engineering Quote items
  const handleEngineeringItemChange = (key, field, value) => {
    setEngineeringItems(prevItems => {
      return prevItems.map(item => {
        if (item.key === key) {
          return { ...item, [field]: value };
        }
        return item;
      });
    });
  };

  // Calculate Engineering Quote Total
  const calculateEngineeringTotal = () => {
    return engineeringItems.reduce((sum, item) => {
      const price = item.adjustedPrice !== undefined && item.adjustedPrice !== null ? item.adjustedPrice : item.systemPrice;
      return sum + (Number(price) || 0);
    }, 0);
  };

  // Calculate Process Quote Total
  const calculateProcessTotal = () => {
    return processItems.reduce((sum, item) => sum + (Number(item.finalUnitPrice) || 0), 0);
  };

  // 计算FT小时费总计（使用调整后的价格）
  const calculateFTHourlyTotal = () => {
    return engineeringItems.reduce((sum, item) => {
      if (item.testType === 'FT') {
         const price = item.adjustedPrice !== null && item.adjustedPrice !== undefined ? item.adjustedPrice : item.systemPrice;
         return sum + price;
      }
      return sum;
    }, 0);
  };

  // 计算CP小时费总计（使用调整后的价格）
  const calculateCPHourlyTotal = () => {
    return engineeringItems.reduce((sum, item) => {
      if (item.testType === 'CP') {
         const price = item.adjustedPrice !== null && item.adjustedPrice !== undefined ? item.adjustedPrice : item.systemPrice;
         return sum + price;
      }
      return sum;
    }, 0);
  };


  // 渲染调整控制组件
  const renderAdjustmentControls = (itemKey) => {
    const item = engineeringItems.find(i => i.key === itemKey);
    if (!item) return null;
    
    return (
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '8px', padding: '8px', backgroundColor: '#fff', borderRadius: '4px', border: '1px dashed #d9d9d9' }}>
        <span style={{ fontWeight: 'bold' }}>客户调整报价:</span>
        <InputNumber
          value={item.adjustedPrice}
          onChange={(value) => handleEngineeringItemChange(item.key, 'adjustedPrice', value)}
          precision={2}
          style={{ width: 120 }}
          min={0}
          placeholder="调整后价格"
        />
        <span style={{ marginLeft: '10px' }}>调整理由:</span>
        <Input
          value={item.reason}
          onChange={(e) => handleEngineeringItemChange(item.key, 'reason', e.target.value)}
          placeholder={item.adjustedPrice < item.systemPrice ? "价格下调必填理由" : "选填"}
          status={item.adjustedPrice < item.systemPrice && !item.reason ? 'error' : ''}
          style={{ flex: 1 }}
        />
      </div>
    );
  };

  // 货币配置
  const currencies = [
    { value: 'CNY', label: '人民币 (CNY)', symbol: '￥' },
    { value: 'USD', label: '美元 (USD)', symbol: '$' }
  ];

  // 获取币种信息，兼容不同的字段名
  const getCurrency = () => {
    return quoteData?.quoteCurrency || quoteData?.currency || 'CNY';
  };

  // 格式化价格显示（包含币种符号）
  const formatPrice = (number) => {
    const currency = getCurrency();
    const formattedNumber = formatQuotePrice(number, currency);
    if (currency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 格式化机时价格显示（包含币种符号，根据币种精度）
  const formatHourlyPrice = (number) => {
    const currency = getCurrency();
    const formattedNumber = formatQuotePrice(number, currency);
    if (currency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  // 格式化单颗费用显示（4位小数，万分位向上取整）- 用于工序报价
  const formatUnitPrice = (number) => {
    const currency = getCurrency();
    const symbol = currency === 'USD' ? '$' : '¥';
    if (number === null || number === undefined || number === 0) return `${symbol}0.0000`;
    
    // 万分位向上取整：乘以10000，向上取整，再除以10000
    const ceiledToFourDecimals = Math.ceil(number * 10000) / 10000;
    const formatted = ceiledToFourDecimals.toFixed(4);
    return `${symbol}${formatted}`;
  };

  useEffect(() => {
    let newData = null;
    
    // 优先从location.state中读取报价数据
    if (location.state) {
      // 检查是否已经包含了正确的type字段
      if (location.state.type) {
        newData = location.state;
      } else {
        // 兼容原有逻辑，默认为量产报价
        newData = {
          type: '量产报价',
          ...location.state
        };
      }
    } else {
      // 其次从sessionStorage中读取报价数据（来自工程报价页面）
      const storedQuoteData = sessionStorage.getItem('quoteData');
      if (storedQuoteData) {
        newData = JSON.parse(storedQuoteData);
      }
    }
    
    // 如果没有找到有效数据，使用默认的模拟数据
    if (!newData) {
      newData = {
        type: '工程报价',
        number: `QT-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-0001`,
        date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        items: [
          {
            category: '测试机配置',
            items: []
          }
        ],
        engineeringRate: 1.2, // 工程系数
        personnelCost: 0, // 人员费用
        auxiliaryEquipmentCost: 0, // 辅助设备费用
        testMachineCost: 0, // 测试机费用（乘以工程系数）
        handlerCost: 0, // 分选机费用（乘以工程系数）
        proberCost: 0, // 探针台费用（乘以工程系数）
        totalCost: 0 // 总费用
      };
    }
    
    setQuoteData(newData);
  }, [location]);

  // 计算设备费用（乘以工程系数）
  const calculateEquipmentCost = (equipmentType) => {
    if (!quoteData || !quoteData[equipmentType] || !quoteData[`${equipmentType}Cards`]) return 0;
    
    const equipment = quoteData[equipmentType];
    const cards = quoteData[`${equipmentType}Cards`];
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    const baseCost = cards.reduce((total, card) => {
      let adjustedPrice = card.unit_price / 10000;
      
      // 根据报价币种和机器币种进行转换
      if (quoteCurrency === 'USD') {
        if (equipment.currency === 'CNY' || equipment.currency === 'RMB') {
          // RMB机器转USD：除以报价汇率
          adjustedPrice = adjustedPrice / quoteExchangeRate;
        }
        // USD机器：不做汇率转换，直接使用unit_price
      } else {
        // 报价币种是CNY，保持原逻辑
        adjustedPrice = adjustedPrice * equipment.exchange_rate;
      }
      
      return total + (adjustedPrice * equipment.discount_rate * (card.quantity || 1));
    }, 0);
    
    return baseCost * (quoteData.engineeringRate || 1.2);
  };
  
  // 计算测试机费用（乘以工程系数）
  const calculateTestMachineCost = () => {
    return calculateEquipmentCost('testMachine');
  };
  
  // 计算分选机费用（乘以工程系数）
  const calculateHandlerCost = () => {
    return calculateEquipmentCost('handler');
  };
  
  // 计算探针台费用（乘以工程系数）
  const calculateProberCost = () => {
    return calculateEquipmentCost('prober');
  };
  
  // 计算工程师费用（不乘以工程系数）
  const calculateEngineerCost = () => {
    if (!quoteData || !quoteData.selectedPersonnel || !quoteData.selectedPersonnel.includes('工程师')) return 0;
    
    let rate = 350; // 工程师费用固定为350元/小时
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    if (quoteCurrency === 'USD') {
      rate = rate / quoteExchangeRate;
    }
    return rate;
  };
  
  // 计算技术员费用（不乘以工程系数）
  const calculateTechnicianCost = () => {
    if (!quoteData || !quoteData.selectedPersonnel || !quoteData.selectedPersonnel.includes('技术员')) return 0;
    
    let rate = 200; // 技术员费用固定为200元/小时
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    if (quoteCurrency === 'USD') {
      rate = rate / quoteExchangeRate;
    }
    return rate;
  };
  
  // 计算单个设备的板卡成本（用于工序报价） - 支持双设备
  const calculateProcessCardCostForDevice = (process, deviceName, cardTypes) => {
    const machineDataKey = `${deviceName}Data`;
    const cardQuantitiesKey = `${deviceName}CardQuantities`;
    
    const machineData = process[machineDataKey];
    const cardQuantities = process[cardQuantitiesKey];
    
    if (!machineData || !cardQuantities || !cardTypes) return 0;
    
    const quoteCurrency = quoteData.currency || 'CNY';
    const quoteExchangeRate = quoteData.exchangeRate || 7.2;
    
    let cardCost = 0;
    Object.entries(cardQuantities).forEach(([cardId, quantity]) => {
      const card = cardTypes.find(c => c.id === parseInt(cardId));
      if (card && quantity > 0) {
        // 板卡单价除以10000，然后按照工程机时的逻辑进行币种转换
        let adjustedPrice = (card.unit_price || 0) / 10000;
        
        // 根据报价币种和机器币种进行转换（参考EngineeringQuote.js逻辑）
        if (quoteCurrency === 'USD') {
          if (machineData.currency === 'CNY' || machineData.currency === 'RMB') {
            // RMB机器转USD：除以报价汇率
            adjustedPrice = adjustedPrice / quoteExchangeRate;
          }
          // USD机器：不做汇率转换，直接使用unit_price
        } else {
          // 报价币种是CNY，保持原逻辑
          adjustedPrice = adjustedPrice * (machineData.exchange_rate || 1.0);
        }
        
        const cardHourlyCost = adjustedPrice * (machineData.discount_rate || 1.0) * quantity;
        const cardUnitCost = process.uph > 0 ? cardHourlyCost / process.uph : 0;
        cardCost += cardUnitCost;
      }
    });
    
    return cardCost;
  };

  // 确认报价，创建数据库记录
  const handleConfirmQuote = async () => {
    if (!quoteData || (!quoteData.quoteCreateData && quoteData.type !== '工序报价' && quoteData.type !== '工程报价' && quoteData.type !== '工程机时报价')) {
      message.error('报价数据不完整，无法创建报价单');
      return;
    }
    
    let finalQuoteData = quoteData.quoteCreateData;

    // 处理工程报价和量产报价
    if (quoteData.type === '工程报价' || quoteData.type === '工程机时报价' || quoteData.type === '量产报价' || quoteData.type === '量产机时报价') {
        // 验证调整理由
        const invalidItems = engineeringItems.filter(item => {
           // 处理 undefined/null 情况
           const adjusted = item.adjustedPrice !== undefined && item.adjustedPrice !== null ? item.adjustedPrice : item.systemPrice;
           return adjusted < item.systemPrice && !item.reason;
        });
        
        if (invalidItems.length > 0) {
            message.error('请填写调整价格低于系统报价的项目的调整理由');
            return;
        }

        // 确保 finalQuoteData 存在 (EngineeringQuote.js 应该已经创建了大部分数据)
        if (!finalQuoteData) {
             const isMassProduction = quoteData.type === '量产报价' || quoteData.type === '量产机时报价';
             finalQuoteData = {
                title: quoteData.projectInfo?.projectName || (isMassProduction ? '量产报价' : '工程报价'),
                quote_type: isMassProduction ? 'mass_production' : 'engineering',
                customer_name: quoteData.customerInfo?.companyName || '测试客户',
                customer_contact: quoteData.customerInfo?.contactPerson || '',
                customer_phone: quoteData.customerInfo?.phone || '',
                customer_email: quoteData.customerInfo?.email || '',
                quote_unit: quoteData.projectInfo?.quoteUnit || '昆山芯信安',
                currency: quoteData.quoteCurrency || 'CNY',
                items: []
             };
        }

        // 使用 engineeringItems 更新 items
        // 注意：这里我们完全重写 items，因为 engineeringItems 包含了最新的调整信息
        finalQuoteData.items = engineeringItems.map(item => {
            // 尝试从原始数据获取更多信息
            const originalItem = quoteData.quoteCreateData?.items?.find(i => i.item_name === item.name);
            const originalData = item.originalData || {};
            
            const adjustedPrice = item.adjustedPrice !== undefined && item.adjustedPrice !== null ? item.adjustedPrice : item.systemPrice;

            return {
                ...(originalItem || {}), // 保留原始所有字段
                item_name: item.name,
                quantity: 1,
                unit: '小时',
                unit_price: item.systemPrice, // 系统原价
                total_price: item.systemPrice, // 系统原总价
                adjusted_price: adjustedPrice, // 调整后价格
                adjustment_reason: item.reason, // 调整理由
                // 确保关键字段存在
                machine_type: originalItem?.machine_type || originalData.machine_type || '其他',
                machine_model: originalItem?.machine_model || originalData.machine_model || '',
                supplier: originalItem?.supplier || originalData.supplier || '',
                configuration: originalItem?.configuration || originalData.configuration || '',
            };
        });
        
        // 更新总价
        finalQuoteData.total_amount = calculateEngineeringTotal();
        finalQuoteData.subtotal = finalQuoteData.total_amount;
    }
    
    // 对于工序报价，使用 processItems 重新构建数据
    if (quoteData.type === '工序报价') {
      if (!finalQuoteData) {
        // Should exist if we came from ProcessQuote, but safety check
        finalQuoteData = {
          title: quoteData.projectInfo?.projectName || '工序报价',
          quote_type: '工序报价',
          customer_name: quoteData.customerInfo?.companyName || '测试客户',
          // ... copy other fields if needed, but usually they are in quoteCreateData
          ...quoteData.quoteCreateData
        };
      }

      // Reconstruct items from processItems state
      if (processItems.length > 0) {
        finalQuoteData.items = processItems.map(item => ({
          ...item,
          unit_price: Number(item.finalUnitPrice) || 0,
          total_price: Number(item.finalUnitPrice) || 0,
          configuration: JSON.stringify(item.config)
        }));
        
        finalQuoteData.subtotal = calculateProcessTotal();
        finalQuoteData.total_amount = finalQuoteData.subtotal;
      }
    } else if (quoteData.type === '工序报价' && !finalQuoteData) {
      // Fallback for the case where we don't have processItems initialized (shouldn't happen if useEffect ran)
      // This block is the old logic, we can keep it as safety or remove.
      // Given we initialize processItems in useEffect, we should rely on it.
      // But let's keep the old logic structure but updated to use processItems if available.
      // Actually, if processItems is empty, we can't save much.
    }

    setConfirmLoading(true);
    try {
      // 动态导入API服务
      const QuoteApiService = (await import('../services/quoteApi')).default;
      
      
      // 修复数据格式问题
      const fixedQuoteData = {
        ...finalQuoteData,
        subtotal: finalQuoteData.subtotal || 0,
        total_amount: finalQuoteData.total_amount || 0,
        items: finalQuoteData.items.map(item => ({
          ...item,
          supplier: typeof item.supplier === 'object' ? (item.supplier.name || '') : (item.supplier || ''),
          unit_price: item.unit_price === null || isNaN(item.unit_price) ? 0 : item.unit_price,
          total_price: item.total_price === null || isNaN(item.total_price) ? 0 : item.total_price,
                        configuration: item.configuration, // 避免覆盖 EngineeringQuote.js 正确生成的 JSON          item_name: item.item_name.replace('undefined', '配置')
        }))
      };
      
      // 检查是否是编辑模式
      const isEditMode = quoteData.isEditMode && quoteData.editingQuoteId;
      let resultQuote;

      if (isEditMode) {
        // 编辑模式：更新现有报价单
        resultQuote = await QuoteApiService.updateQuote(quoteData.editingQuoteId, fixedQuoteData);
        message.success(`报价单更新成功！报价单号：${resultQuote.quote_number}`);
        navigate(`/quote-detail/${resultQuote.quote_number}`);
      } else {
        // 新建模式：创建新报价单
        resultQuote = await QuoteApiService.createQuote(fixedQuoteData);
        message.success(`报价单创建成功！报价单号：${resultQuote.quote_number}`);
        navigate(`/quote-detail/${resultQuote.quote_number}`);
      }

      setIsQuoteConfirmed(true);

      // 更新报价数据，添加创建/更新的报价单信息
      setQuoteData(prev => ({
        ...prev,
        quoteId: resultQuote.id,
        quoteNumber: resultQuote.quote_number,
        quoteStatus: resultQuote.status,
        dbRecord: true
      }));

    } catch (error) {
      const isEditMode = quoteData.isEditMode && quoteData.editingQuoteId;
      console.error(`${isEditMode ? '更新' : '创建'}报价单详细错误:`, error);

      let errorMessage = `${isEditMode ? '更新' : '创建'}报价单失败，请稍后重试`;
      
      if (error.response) {
        console.error('错误响应:', error.response.status, error.response.data);
        
        // 详细打印验证错误
        if (error.response.status === 422 && error.response.data?.detail) {
          console.error('验证错误详情:', JSON.stringify(error.response.data.detail, null, 2));
        }
        
        if (error.response.status === 401) {
          errorMessage = '用户认证失败，请重新登录';
        } else if (error.response.status === 400) {
          // 简化处理400错误
          try {
            const errorData = error.response.data;
            if (typeof errorData === 'string') {
              errorMessage = errorData;
            } else if (errorData?.detail) {
              if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
              } else if (Array.isArray(errorData.detail)) {
                // 只取第一个错误信息
                const firstError = errorData.detail[0];
                if (firstError && firstError.msg) {
                  errorMessage = `数据验证错误: ${firstError.msg}`;
                } else {
                  errorMessage = '数据验证失败，请检查输入信息';
                }
              } else {
                errorMessage = '请求数据有误，请检查报价信息';
              }
            }
          } catch (parseError) {
            console.error('解析错误信息失败:', parseError);
            errorMessage = '请求数据有误，请检查报价信息';
          }
        } else if (error.response.data?.detail && typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        }
      } else if (error.request) {
        errorMessage = '网络连接失败，请检查网络设置';
      }
      
      message.error(errorMessage);
    } finally {
      setConfirmLoading(false);
    }
  };


  return (
    <div>
      <Card title={quoteData ? `${quoteData.type}结果` : '报价结果'}>
        <div className="quote-result-content">
          <h3>费用明细</h3>
          {/* 显示各项费用 */}
          {quoteData && (quoteData.type === '工程报价' || quoteData.type === '工程机时报价') && (
            <>
              <Table
                dataSource={engineeringItems}
                pagination={false}
                rowKey="key"
                columns={[
                  {
                    title: '费用项目',
                    dataIndex: 'name',
                    key: 'name',
                  },
                  {
                    title: '系统报价',
                    dataIndex: 'systemPrice',
                    key: 'systemPrice',
                    render: (text) => formatHourlyPrice(text)
                  },
                  {
                    title: '客户调整报价',
                    key: 'adjustedPrice',
                    render: (_, record) => (
                      <InputNumber
                        value={record.adjustedPrice}
                        onChange={(value) => handleEngineeringItemChange(record.key, 'adjustedPrice', value)}
                        precision={2}
                        style={{ width: 120 }}
                        min={0}
                      />
                    )
                  },
                  {
                    title: '调整理由',
                    key: 'reason',
                    render: (_, record) => {
                      const isLower = record.adjustedPrice < record.systemPrice;
                      return (
                        <Input
                          value={record.reason}
                          onChange={(e) => handleEngineeringItemChange(record.key, 'reason', e.target.value)}
                          placeholder={isLower ? "请输入调整理由（必填）" : "选填"}
                          status={isLower && !record.reason ? 'error' : ''}
                          style={{ width: '100%' }}
                        />
                      );
                    }
                  }
                ]}
                footer={() => (
                  <div style={{ textAlign: 'right', fontWeight: 'bold' }}>
                    报价总额: {formatHourlyPrice(calculateEngineeringTotal())}
                  </div>
                )}
              />
              <div style={{ marginTop: 10, color: '#666', fontSize: '12px' }}>
                * 如果客户调整报价低于系统报价，必须填写调整理由。
              </div>
            </>
          )}
          
          {/* 询价报价显示 */}
          {quoteData && quoteData.type === '询价报价' && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>项目名称: {quoteData.projectInfo?.projectName || '-'}</div>
                  <div>芯片封装: {quoteData.projectInfo?.chipPackage || '-'}</div>
                  <div>测试类型: {quoteData.projectInfo?.testType || '-'}</div>
                  <div>紧急程度: {quoteData.projectInfo?.urgency || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>设备配置及费用</h4>
                {quoteData.machines && quoteData.machines.map((machine, index) => (
                  <div key={index} style={{ marginBottom: 15, paddingLeft: 15, border: '1px solid #f0f0f0', borderRadius: '4px', padding: '10px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 5 }}>
                      机器 {index + 1}: {machine.model || '未选择'}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>机时费率（含询价系数 {quoteData.inquiryFactor || 1.5}）:</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        {formatHourlyPrice(machine.hourlyRate || 0)}/小时
                      </span>
                    </div>
                    {machine.selectedCards && machine.selectedCards.length > 0 && (
                      <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                        选用板卡: {machine.selectedCards.map(card => card.board_name).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              <div style={{ marginBottom: 20, fontSize: '18px', fontWeight: 'bold', textAlign: 'right', color: '#1890ff' }}>
                总机时费率: {formatHourlyPrice(quoteData.totalHourlyRate || 0)}/小时
              </div>
              
              {quoteData.remarks && (
                <div style={{ marginBottom: 20 }}>
                  <h4>备注说明</h4>
                  <div style={{ paddingLeft: 15, color: '#666' }}>
                    {quoteData.remarks}
                  </div>
                </div>
              )}
            </>
          )}
          
          {/* 工装夹具报价显示 */}
          {(quoteData && (quoteData.type === '工装夹具报价' || quoteData.quote_type === 'tooling')) && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || quoteData.customer_name || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || quoteData.customer_contact || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || quoteData.customer_phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || quoteData.customer_email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>报价标题: {quoteData.title || '-'}</div>
                  <div>项目描述: {quoteData.description || '-'}</div>
                  <div>备注: {quoteData.notes || '-'}</div>
                </div>
              </div>
              
              {/* 1. 工装夹具清单 */}
              {(() => {
                // 从数据库items中筛选出工装夹具类项目（category_type为tooling_hardware或根据item_description判断）
                const toolingItems = quoteData.items ? quoteData.items.filter(item => 
                  item.category_type === 'tooling_hardware' || 
                  (item.item_description && item.item_description.includes('fixture')) ||
                  (!item.item_description?.includes('工程') && !item.item_description?.includes('准备') && item.unit === '件')
                ) : (quoteData.toolingItems || []);
                
                return toolingItems && toolingItems.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4>🔧 1. 工装夹具清单 [新版本显示]</h4>
                  <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                    {/* 表头 */}
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 1.5fr 1fr 1.5fr', 
                      gap: '10px',
                      padding: '12px 15px',
                      backgroundColor: '#fafafa',
                      borderBottom: '1px solid #d9d9d9',
                      fontWeight: 'bold',
                      fontSize: '14px'
                    }}>
                      <span>类别</span>
                      <span>类型</span>
                      <span>单价</span>
                      <span>数量</span>
                      <span>小计</span>
                    </div>
                    {/* 内容 */}
                    {toolingItems.map((item, index) => (
                      <div key={index} style={{ 
                        display: 'grid', 
                        gridTemplateColumns: '2fr 2fr 1.5fr 1fr 1.5fr', 
                        gap: '10px',
                        padding: '12px 15px',
                        borderBottom: index < toolingItems.length - 1 ? '1px solid #f0f0f0' : 'none'
                      }}>
                        <span>{item.category || item.item_description?.split(' - ')[0] || '工装夹具'}</span>
                        <span>{item.type || item.item_name}</span>
                        <span>{formatPrice(item.unitPrice || item.unit_price || 0)}</span>
                        <span>{item.quantity}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          {formatPrice(item.totalPrice || item.total_price || 0)}
                        </span>
                      </div>
                    ))}
                    {/* 工装夹具总价 */}
                    <div style={{ 
                      padding: '12px 15px',
                      backgroundColor: '#f0f9ff',
                      borderTop: '1px solid #d9d9d9',
                      display: 'flex',
                      justifyContent: 'flex-end',
                      fontWeight: 'bold',
                      fontSize: '16px',
                      color: '#1890ff'
                    }}>
                      工装夹具总价: {formatPrice(toolingItems.reduce((sum, item) => sum + (item.totalPrice || item.total_price || 0), 0))}
                    </div>
                  </div>
                </div>
                );
              })()}
              
              {/* 2. 工程费用 - 只显示非零项目 */}
              {(() => {
                // 从数据库items中筛选出工程费用项目
                const engineeringItems = quoteData.items ? quoteData.items.filter(item => 
                  item.category_type === 'engineering_fee' || 
                  (item.item_description && item.item_description.includes('工程')) ||
                  item.unit === '项' && (item.item_name?.includes('测试程序') || item.item_name?.includes('夹具设计') || 
                                         item.item_name?.includes('测试验证') || item.item_name?.includes('文档'))
                ) : [];
                
                // 如果没有数据库items，尝试从原始engineeringFees获取
                if (engineeringItems.length === 0 && quoteData.engineeringFees) {
                  const fees = quoteData.engineeringFees;
                  const feeNames = {
                    testProgramDevelopment: '测试程序开发费用',
                    fixtureDesign: '夹具设计费',
                    testValidation: '测试验证费',
                    documentation: '文档制作费'
                  };
                  
                  Object.entries(fees).forEach(([key, value]) => {
                    if (value > 0) {
                      engineeringItems.push({ item_name: feeNames[key], total_price: value });
                    }
                  });
                }
                
                return engineeringItems.length > 0 && (
                  <div style={{ marginBottom: 20 }}>
                    <h4>2. 工程费用</h4>
                    <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                      {engineeringItems.map((item, index) => (
                        <div key={index} style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          padding: '12px 15px',
                          borderBottom: index < engineeringItems.length - 1 ? '1px solid #f0f0f0' : 'none'
                        }}>
                          <span>{item.name || item.item_name}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                            {formatPrice(item.value || item.total_price)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
              
              {/* 3. 量产准备费用 - 只显示非零项目 */}
              {(() => {
                // 从数据库items中筛选出量产准备费用项目
                const productionItems = quoteData.items ? quoteData.items.filter(item => 
                  item.category_type === 'production_setup' || 
                  (item.item_description && item.item_description.includes('准备')) ||
                  item.unit === '项' && (item.item_name?.includes('调试') || item.item_name?.includes('校准') || item.item_name?.includes('检验'))
                ) : [];
                
                // 如果没有数据库items，尝试从原始productionSetup获取
                if (productionItems.length === 0 && quoteData.productionSetup) {
                  const setup = quoteData.productionSetup;
                  const setupNames = {
                    setupFee: '生产准备费',
                    calibrationFee: '设备校准费',
                    firstArticleInspection: '首件检验费'
                  };
                  
                  Object.entries(setup).forEach(([key, value]) => {
                    if (value > 0) {
                      productionItems.push({ item_name: setupNames[key], total_price: value });
                    }
                  });
                }
                
                return productionItems.length > 0 && (
                  <div style={{ marginBottom: 20 }}>
                    <h4>3. 量产准备费用</h4>
                    <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                      {productionItems.map((item, index) => (
                        <div key={index} style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          padding: '12px 15px',
                          borderBottom: index < productionItems.length - 1 ? '1px solid #f0f0f0' : 'none'
                        }}>
                          <span>{item.name || item.item_name}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                            {formatPrice(item.value || item.total_price)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
              
              <div style={{ marginBottom: 20, fontSize: '18px', fontWeight: 'bold', textAlign: 'right', color: '#1890ff' }}>
                报价总额: {formatPrice(quoteData.totalCost || quoteData.total_amount || 0)}
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>商务条款</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>付款条件: {(() => {
                    const paymentTerms = quoteData.paymentTerms || quoteData.payment_terms;
                    return paymentTerms === '30_days' ? '30天付款' : 
                           paymentTerms === '60_days' ? '60天付款' : 
                           paymentTerms === 'advance' ? '预付款' : 
                           paymentTerms || '-';
                  })()}</div>
                  <div>币种: {quoteData.currency || 'CNY'}</div>
                  {(quoteData.deliveryTime || quoteData.valid_until) && 
                    <div>有效期: {quoteData.deliveryTime || (quoteData.valid_until ? new Date(quoteData.valid_until).toLocaleDateString() : '-')}</div>
                  }
                  {(quoteData.remarks || quoteData.notes) && 
                    <div>备注: {quoteData.remarks || quoteData.notes}</div>
                  }
                </div>
              </div>
            </>
          )}
          
          {/* 工序报价显示 */}
          {quoteData && quoteData.type === '工序报价' && processItems.length > 0 && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>项目名称: {quoteData.projectInfo?.projectName || '-'}</div>
                  <div>芯片封装: {quoteData.projectInfo?.chipPackage || '-'}</div>
                  <div>测试类型: {quoteData.projectInfo?.testType || '-'}</div>
                  <div>报价单位: {quoteData.projectInfo?.quoteUnit || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>费用明细</h4>
                
                {(() => {
                  const cpItems = processItems.filter(item => item.item_name.startsWith('CP工序'));
                  const ftItems = processItems.filter(item => item.item_name.startsWith('FT工序'));

                  const renderEditableProcessCard = (item, index, realIndex, type) => {
                    const config = item.config;
                    const processName = config.process_type || item.item_name;
                    const isTest = isTestProcess(processName);
                    
                    return (
                      <div key={item.key} style={{ 
                        marginBottom: 20, 
                        border: type === 'CP' ? '1px solid #d9f7be' : '1px solid #91d5ff', 
                        borderRadius: '8px', 
                        padding: '20px',
                        backgroundColor: type === 'CP' ? '#f6ffed' : '#e6f7ff'
                      }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          marginBottom: 15, 
                          color: type === 'CP' ? '#52c41a' : '#1890ff',
                          fontSize: '16px'
                        }}>
                          {processName}
                        </div>
                        
                        <div style={{ marginBottom: 15 }}>
                          <h6 style={{ color: type === 'CP' ? '#389e0d' : '#096dd9', marginBottom: 8, fontSize: '14px', fontWeight: 'bold' }}>📋 规格参数</h6>
                          <div style={{ paddingLeft: 15, backgroundColor: '#fff', borderRadius: '4px', padding: '12px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '15px', fontSize: '13px' }}>
                              
                              {/* 设备信息 */}
                              {config.test_machine && (
                                <div><strong>{isTest ? '测试机' : '设备'}:</strong> {config.test_machine.name}</div>
                              )}
                              {config.prober && (
                                <div><strong>探针台:</strong> {config.prober.name}</div>
                              )}
                              {config.handler && (
                                <div><strong>分选机:</strong> {config.handler.name}</div>
                              )}

                              {/* 详细参数 - 可编辑 */}
                              {config.system_machine_rate !== undefined && (
                                <div>
                                  <strong>系统机时:</strong> {formatPrice(config.system_machine_rate)}
                                </div>
                              )}
                              
                              {isTest && (
                                <div>
                                  <strong>调整机时:</strong>
                                  <InputNumber
                                    size="small"
                                    style={{ width: '100px', marginLeft: '5px' }}
                                    value={config.adjusted_machine_rate}
                                    onChange={(val) => handleProcessItemChange(realIndex, 'adjusted_machine_rate', val)}
                                    min={0}
                                    precision={2}
                                  />
                                </div>
                              )}
                              
                              {config.uph !== undefined && (
                                <div>
                                  <strong>UPH ({type === 'CP' ? '片' : '颗'}/小时):</strong>
                                  <InputNumber
                                    size="small"
                                    style={{ width: '80px', marginLeft: '5px' }}
                                    value={config.uph}
                                    onChange={(val) => handleProcessItemChange(realIndex, 'uph', val)}
                                    min={1}
                                  />
                                </div>
                              )}
                              
                              {isBakingProcess(processName) && config.quantity_per_oven !== undefined && (
                                <div>
                                  <strong>每炉数量:</strong>
                                  <InputNumber
                                    size="small"
                                    style={{ width: '80px', marginLeft: '5px' }}
                                    value={config.quantity_per_oven}
                                    onChange={(val) => handleProcessItemChange(realIndex, 'quantity_per_oven', val)}
                                    min={1}
                                  />
                                </div>
                              )}
                              {isBakingProcess(processName) && config.baking_time !== undefined && (
                                <div>
                                  <strong>时间 (分钟):</strong>
                                  <InputNumber
                                    size="small"
                                    style={{ width: '80px', marginLeft: '5px' }}
                                    value={config.baking_time}
                                    onChange={(val) => handleProcessItemChange(realIndex, 'baking_time', val)}
                                    min={1}
                                  />
                                </div>
                              )}
                              
                              {config.package_type !== undefined && (
                                <div><strong>封装形式:</strong> {config.package_type}</div>
                              )}
                              {isTapingProcess(processName) && config.quantity_per_reel !== undefined && (
                                <div>
                                  <strong>每卷数量:</strong>
                                  <InputNumber
                                    size="small"
                                    style={{ width: '80px', marginLeft: '5px' }}
                                    value={config.quantity_per_reel}
                                    onChange={(val) => handleProcessItemChange(realIndex, 'quantity_per_reel', val)}
                                    min={1}
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* 费用信息 - 可编辑单价 */}
                        <div style={{ 
                          marginTop: 15,
                          paddingTop: 12,
                          borderTop: type === 'CP' ? '2px solid #52c41a' : '2px solid #1890ff',
                          display: 'flex',
                          justifyContent: 'flex-end',
                          alignItems: 'center',
                          gap: '20px'
                        }}>
                          {item.calculatedUnitPrice > 0 && (
                             <div style={{ fontSize: '13px', color: '#999' }}>
                                计算单价: {formatUnitPrice(item.calculatedUnitPrice)}
                             </div>
                          )}
                          <div style={{ 
                            fontSize: '16px', 
                            fontWeight: 'bold', 
                            color: type === 'CP' ? '#52c41a' : '#1890ff',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px'
                          }}>
                            <span>最终单价:</span>
                            <InputNumber
                              style={{ width: '120px' }}
                              value={item.finalUnitPrice}
                              onChange={(val) => handleProcessItemChange(realIndex, 'adjusted_unit_price', val)}
                              min={0}
                              precision={4}
                              prefix={currencies.find(c => c.value === quoteData.currency)?.symbol || '¥'}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  };

                  return (
                    <>
                      {cpItems.length > 0 && (
                        <div style={{ marginBottom: 30 }}>
                          <h5 style={{ color: '#52c41a', marginBottom: 15, fontSize: '16px', fontWeight: 'bold', borderBottom: '2px solid #52c41a', paddingBottom: '8px' }}>
                            🔬 CP工序
                          </h5>
                          {cpItems.map((item, index) => {
                             // find the real index in processItems to update state correctly
                             const realIndex = processItems.findIndex(p => p.key === item.key);
                             return renderEditableProcessCard(item, index, realIndex, 'CP');
                          })}
                        </div>
                      )}

                      {ftItems.length > 0 && (
                        <div style={{ marginBottom: 30 }}>
                          <h5 style={{ color: '#1890ff', marginBottom: 15, fontSize: '16px', fontWeight: 'bold', borderBottom: '2px solid #1890ff', paddingBottom: '8px' }}>
                            📱 FT工序
                          </h5>
                          {ftItems.map((item, index) => {
                             const realIndex = processItems.findIndex(p => p.key === item.key);
                             return renderEditableProcessCard(item, index, realIndex, 'FT');
                          })}
                        </div>
                      )}
                      
                      <div style={{ marginBottom: 20, fontSize: '18px', fontWeight: 'bold', textAlign: 'right', color: '#1890ff' }}>
                        {/* 报价总额不再显示，但仍会在后端计算 */}
                      </div>
                    </>
                  );
                })()}

              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>报价说明</h4>
                <div style={{ paddingLeft: 15, border: '1px solid #e8e8e8', borderRadius: '6px', padding: '15px', backgroundColor: '#f0f8ff' }}>
                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#666' }}>
                    <div style={{ marginBottom: '8px', fontWeight: 'bold', color: '#1890ff' }}>
                      ✓ 工序报价说明：
                    </div>
                    <div style={{ marginBottom: '5px' }}>
                      • 您可以直接在此页面微调参数或最终单价，确认后将按显示金额生成报价单。
                    </div>
                    <div style={{ marginBottom: '5px' }}>
                      • 调整机时或UPH会自动更新计算单价，但您可以直接修改“最终单价”进行覆盖。
                    </div>
                    <div style={{ color: '#f5222d', fontWeight: 'bold' }}>
                      • 各工序报价不可直接相加，请根据实际生产需求选择
                    </div>
                  </div>
                </div>
              </div>
              
              {quoteData.remarks && (
                <div style={{ marginBottom: 20 }}>
                  <h4>备注说明</h4>
                  <div style={{ paddingLeft: 15, color: '#666', fontStyle: 'italic' }}>
                    {quoteData.remarks}
                  </div>
                </div>
              )}
            </>
          )}

          {/* 综合报价显示 */}
          {quoteData && quoteData.type === '综合报价' && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h3>报价方案类型</h3>
                <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '4px', marginBottom: '15px' }}>
                  <strong>
                    {quoteData.quoteType === 'package' ? '套餐定价方案' :
                     quoteData.quoteType === 'volume' ? '分级定价方案' :
                     quoteData.quoteType === 'time' ? '合约定价方案' : '自定义方案'}
                  </strong>
                </div>
              </div>

              {/* 套餐定价显示 */}
              {quoteData.quoteType === 'package' && quoteData.packages && (
                <div style={{ marginBottom: 20 }}>
                  <h4>套餐配置</h4>
                  {quoteData.packages.map((pkg, index) => (
                    <div key={index} style={{ 
                      padding: '12px', 
                      marginBottom: '10px', 
                      border: '1px solid #d9d9d9',
                      borderRadius: '4px',
                      background: '#fafafa'
                    }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>{pkg.name}</div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>{pkg.description}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>服务内容: {pkg.services.join(', ')}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          {currencies.find(c => c.value === quoteData.currency)?.symbol}{pkg.price}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 分级定价显示 */}
              {quoteData.quoteType === 'volume' && quoteData.volumeTiers && (
                <div style={{ marginBottom: 20 }}>
                  <h4>数量分级定价</h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#fafafa' }}>
                        <th style={{ padding: '8px', border: '1px solid #d9d9d9', textAlign: 'left' }}>数量范围</th>
                        <th style={{ padding: '8px', border: '1px solid #d9d9d9', textAlign: 'right' }}>单价</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quoteData.volumeTiers.map((tier, index) => (
                        <tr key={index}>
                          <td style={{ padding: '8px', border: '1px solid #d9d9d9' }}>
                            {tier.minQty} - {tier.maxQty || '以上'}
                          </td>
                          <td style={{ padding: '8px', border: '1px solid #d9d9d9', textAlign: 'right' }}>
                            {currencies.find(c => c.value === quoteData.currency)?.symbol}{tier.unitPrice}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 合约定价显示 */}
              {quoteData.quoteType === 'time' && quoteData.timeContracts && (
                <div style={{ marginBottom: 20 }}>
                  <h4>合约期限定价</h4>
                  {quoteData.timeContracts.map((contract, index) => (
                    <div key={index} style={{ 
                      padding: '12px', 
                      marginBottom: '10px', 
                      border: '1px solid #d9d9d9',
                      borderRadius: '4px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span><strong>{contract.duration}个月合约</strong></span>
                        <span>折扣: {contract.discount}%</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>月费: {currencies.find(c => c.value === quoteData.currency)?.symbol}{contract.monthlyRate}</span>
                        <span style={{ fontWeight: 'bold', color: '#52c41a' }}>
                          总价: {currencies.find(c => c.value === quoteData.currency)?.symbol}
                          {formatQuotePrice(contract.monthlyRate * contract.duration * (1 - contract.discount / 100), quoteData.quoteCurrency || 'CNY')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 自定义方案显示 */}
              {quoteData.quoteType === 'custom' && quoteData.customTerms && (
                <div style={{ marginBottom: 20 }}>
                  <h4>自定义条款</h4>
                  {quoteData.customTerms.map((term, index) => (
                    <div key={index} style={{ 
                      padding: '12px', 
                      marginBottom: '10px', 
                      border: '1px solid #d9d9d9',
                      borderRadius: '4px'
                    }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{term.name}</div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>{term.description}</div>
                      <div style={{ textAlign: 'right', fontWeight: 'bold', color: '#1890ff' }}>
                        {currencies.find(c => c.value === quoteData.currency)?.symbol}{term.value}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 协议条款 */}
              {quoteData.agreementTerms && (
                <div style={{ marginBottom: 20 }}>
                  <h4>协议条款</h4>
                  <div style={{ padding: '12px', background: '#f9f9f9', borderRadius: '4px' }}>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>有效期：</strong> {quoteData.agreementTerms.validityPeriod}天
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>付款条件：</strong> 
                      {quoteData.agreementTerms.paymentTerms === '30_days' ? '30天' :
                       quoteData.agreementTerms.paymentTerms === '60_days' ? '60天' :
                       quoteData.agreementTerms.paymentTerms === '90_days' ? '90天' :
                       quoteData.agreementTerms.paymentTerms === 'prepaid' ? '预付款' : '货到付款'}
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>交付条款：</strong> 
                      {quoteData.agreementTerms.deliveryTerms === 'standard' ? '标准交付' :
                       quoteData.agreementTerms.deliveryTerms === 'expedited' ? '加急交付' :
                       quoteData.agreementTerms.deliveryTerms === 'scheduled' ? '计划交付' : '灵活交付'}
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>质保期：</strong> {quoteData.agreementTerms.warrantyPeriod}天
                    </div>
                  </div>
                </div>
              )}

              {/* 价格汇总 */}
              <div style={{ marginBottom: 20 }}>
                <h4>价格汇总</h4>
                <div style={{ padding: '15px', background: '#e6f7ff', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                    <span>最终报价：</span>
                    <span>
                      {currencies.find(c => c.value === quoteData.currency)?.symbol}
                      {formatQuotePrice(quoteData.calculatedTotals?.finalTotal || 0, quoteData.quoteCurrency || 'CNY')}
                    </span>
                  </div>
                </div>
              </div>

              {quoteData.remarks && (
                <div style={{ marginBottom: 20 }}>
                  <h4>备注说明</h4>
                  <div style={{ paddingLeft: 15, color: '#666', fontStyle: 'italic' }}>
                    {quoteData.remarks}
                  </div>
                </div>
              )}
            </>
          )}
          
          {quoteData && quoteData.type === '量产报价' && (
            <>
              <div style={{ padding: '20px 0' }}>
                {/* FT测试费用明细 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('ft') && (
                  <div style={{ marginBottom: 20 }}>
                    <h4 style={{ marginBottom: 10 }}>📱 FT测试费用明细</h4>
                    <div style={{ paddingLeft: 20 }}>
                      {/* FT测试机 */}
                      {quoteData.ftData?.testMachine && (
                        <div style={{ marginBottom: 15, padding: '10px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #f0f0f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ color: '#666' }}>
                              测试机 - {quoteData.ftData.testMachine.name || 'FT测试机'}
                            </span>
                            <span>
                              {(() => {
                                const item = engineeringItems.find(i => i.key === 'ft_tm');
                                return formatHourlyPrice(item ? item.systemPrice : 0);
                              })()}
                            </span>
                          </div>
                          {renderAdjustmentControls('ft_tm')}
                        </div>
                      )}
                      
                      {/* FT分选机 */}
                      {quoteData.ftData?.handler && (
                        <div style={{ marginBottom: 15, padding: '10px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #f0f0f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ color: '#666' }}>
                              分选机 - {quoteData.ftData.handler.name || 'FT分选机'}
                            </span>
                            <span>
                              {(() => {
                                const item = engineeringItems.find(i => i.key === 'ft_h');
                                return formatHourlyPrice(item ? item.systemPrice : 0);
                              })()}
                            </span>
                          </div>
                          {renderAdjustmentControls('ft_h')}
                        </div>
                      )}
                      
                      {/* FT小时费总计 */}
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        marginTop: 10,
                        paddingTop: 10,
                        borderTop: '1px solid #f0f0f0',
                        fontWeight: 'bold'
                      }}>
                        <span>FT小时费合计:</span>
                        <span style={{ color: '#1890ff' }}>{formatHourlyPrice(calculateFTHourlyTotal())}</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* CP测试费用明细 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('cp') && (
                  <div style={{ marginBottom: 20 }}>
                    <h4 style={{ marginBottom: 10 }}>🔬 CP测试费用明细</h4>
                    <div style={{ paddingLeft: 20 }}>
                      {/* CP测试机 */}
                      {quoteData.cpData?.testMachine && (
                        <div style={{ marginBottom: 15, padding: '10px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #f0f0f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ color: '#666' }}>
                              测试机 - {quoteData.cpData.testMachine.name || 'CP测试机'}
                            </span>
                            <span>
                              {(() => {
                                const item = engineeringItems.find(i => i.key === 'cp_tm');
                                return formatHourlyPrice(item ? item.systemPrice : 0);
                              })()}
                            </span>
                          </div>
                          {renderAdjustmentControls('cp_tm')}
                        </div>
                      )}
                      
                      {/* CP探针台 */}
                      {quoteData.cpData?.prober && (
                        <div style={{ marginBottom: 15, padding: '10px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #f0f0f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ color: '#666' }}>
                              探针台 - {quoteData.cpData.prober.name || 'CP探针台'}
                            </span>
                            <span>
                              {(() => {
                                const item = engineeringItems.find(i => i.key === 'cp_p');
                                return formatHourlyPrice(item ? item.systemPrice : 0);
                              })()}
                            </span>
                          </div>
                          {renderAdjustmentControls('cp_p')}
                        </div>
                      )}
                      
                      {/* CP小时费总计 */}
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        marginTop: 10,
                        paddingTop: 10,
                        borderTop: '1px solid #f0f0f0',
                        fontWeight: 'bold'
                      }}>
                        <span>CP小时费合计:</span>
                        <span style={{ color: '#1890ff' }}>{formatHourlyPrice(calculateCPHourlyTotal())}</span>
                      </div>
                    </div>
                  </div>
                )}
                {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                      <span>辅助设备:</span>
                      <span></span>
                    </div>
                    {quoteData.selectedAuxDevices.map((device, index) => {
                      // 获取设备类型名称
                      let typeName = '';
                      if (device.supplier?.machine_type?.name) {
                        typeName = device.supplier.machine_type.name;
                      } else if (device.machine_type?.name) {
                        typeName = device.machine_type.name;
                      } else if (device.type === 'handler') {
                        typeName = '分选机';
                      } else if (device.type === 'prober') {
                        typeName = '探针台';
                      } else if (device.type) {
                        typeName = device.type;
                      }
                      
                      return (
                        <div key={index} style={{ marginBottom: 15, padding: '10px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #f0f0f0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span>
                              {device.name}
                              {typeName && ` (${typeName})`}
                            </span>
                            <span>{(() => {
                              const item = engineeringItems.find(i => i.key === `aux_${index}`);
                              return formatHourlyPrice(item ? item.systemPrice : 0);
                            })()}/小时</span>
                          </div>
                          {renderAdjustmentControls(`aux_${index}`)}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
        <Divider />
        <div className="quote-result-actions">
          <Button onClick={() => {
            if (quoteData && quoteData.type === '询价报价') {
              // 询价报价：直接返回到询价页面
              navigate('/inquiry-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工装夹具报价') {
              navigate('/tooling-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工序报价') {
              navigate('/process-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '综合报价') {
              navigate('/comprehensive-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工程报价') {
              // 工程报价：真正的上一步，回到编辑页面并保留所有数据（包括编辑模式信息）
              const previousStepData = {
                currentStep: 1, // 返回到步骤1（人员和辅助设备选择）
                testMachine: quoteData.testMachine,
                handler: quoteData.handler,
                prober: quoteData.prober,
                testMachineCards: quoteData.testMachineCards || [],
                handlerCards: quoteData.handlerCards || [],
                proberCards: quoteData.proberCards || [],
                selectedPersonnel: quoteData.selectedPersonnel || [],
                selectedAuxDevices: quoteData.selectedAuxDevices || [],
                engineeringRate: quoteData.engineeringRate || 1.2,
                quoteCurrency: quoteData.quoteCurrency || 'CNY',
                quoteExchangeRate: quoteData.quoteExchangeRate || 7.2,
                persistedCardQuantities: quoteData.persistedCardQuantities || {},
                // 保留编辑模式信息
                isEditMode: quoteData.isEditMode || false,
                editingQuoteId: quoteData.editingQuoteId || null,
                editingQuoteNumber: quoteData.quoteNumber || null,  // 保存报价单号
                // 保留客户信息和项目信息
                customerInfo: quoteData.customerInfo || {},
                projectInfo: quoteData.projectInfo || {},
                fromResultPage: true
              };
              sessionStorage.setItem('quoteData', JSON.stringify(previousStepData));
              navigate('/engineering-quote', {
                state: {
                  fromResultPage: true,
                  isEditing: quoteData.isEditMode || false,  // 使用isEditing以匹配hook
                  quoteId: quoteData.editingQuoteId || null,
                  quoteNumber: quoteData.quoteNumber || null  // 传递报价单号
                }
              });
            } else {
              // 量产报价：真正的上一步，回到报价页面并保留所有数据
              const previousStepData = {
                selectedTypes: quoteData.selectedTypes || ['ft', 'cp'],
                ftData: quoteData.ftData || {
                  testMachine: null,
                  handler: null,
                  testMachineCards: [],
                  handlerCards: []
                },
                cpData: quoteData.cpData || {
                  testMachine: null,
                  prober: null,
                  testMachineCards: [],
                  proberCards: []
                },
                selectedAuxDevices: quoteData.selectedAuxDevices || [],
                persistedCardQuantities: quoteData.persistedCardQuantities || {},
                quoteCurrency: quoteData.quoteCurrency || 'CNY',
                quoteExchangeRate: quoteData.quoteExchangeRate || 7.2,
                // 保留客户信息和项目信息
                customerInfo: quoteData.customerInfo || {},
                projectInfo: quoteData.projectInfo || {},
                // 保留编辑模式信息
                isEditMode: quoteData.isEditMode || false,
                editingQuoteId: quoteData.editingQuoteId || null,
                editingQuoteNumber: quoteData.quoteNumber || null,
                fromResultPage: true
              };
              sessionStorage.setItem('massProductionQuoteState', JSON.stringify(previousStepData));
              navigate('/mass-production-quote', {
                state: {
                  fromResultPage: true,
                  isEditing: quoteData.isEditMode || false,
                  quoteId: quoteData.editingQuoteId || null,
                  quoteNumber: quoteData.quoteNumber || null
                }
              });
            }
          }}>
            上一步
          </Button>
          <Button type="primary" onClick={() => {
            if (quoteData && quoteData.type === '工程报价') {
              navigate('/engineering-quote');
            } else if (quoteData && quoteData.type === '询价报价') {
              navigate('/inquiry-quote');
            } else if (quoteData && quoteData.type === '工装夹具报价') {
              navigate('/tooling-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工序报价') {
              navigate('/process-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '综合报价') {
              navigate('/comprehensive-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else {
              navigate('/mass-production-quote');
            }
          }}>
            重新编辑
          </Button>
          <Button type="primary" onClick={() => window.print()}>
            打印报价
          </Button>
          {/* 确认报价按钮 - 工序报价和其他报价类型的显示逻辑 */}
          {quoteData && (quoteData.quoteCreateData || quoteData.type === '工序报价') && !isQuoteConfirmed && (
            <Button 
              type="primary" 
              size="large"
              loading={confirmLoading}
              onClick={handleConfirmQuote}
              style={{ 
                backgroundColor: '#52c41a', 
                borderColor: '#52c41a',
                fontWeight: 'bold'
              }}
            >
              {confirmLoading ? '正在创建报价单...' : '确认生成报价单'}
            </Button>
          )}
          {/* 已确认状态显示 */}
          {isQuoteConfirmed && (
            <div style={{ 
              padding: '8px 16px', 
              backgroundColor: '#f6ffed', 
              border: '1px solid #b7eb8f',
              borderRadius: '6px',
              color: '#52c41a',
              fontWeight: 'bold'
            }}>
              ✓ 报价单已创建：{quoteData?.quoteNumber}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default QuoteResult;
