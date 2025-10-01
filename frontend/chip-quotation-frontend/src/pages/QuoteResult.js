import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button, Card, Divider, message } from 'antd';
import { formatQuotePrice } from '../utils';
import '../App.css';

const QuoteResult = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [quoteData, setQuoteData] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [isQuoteConfirmed, setIsQuoteConfirmed] = useState(false);

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
    console.log(`QuoteResult calculateProcessCardCostForDevice ${deviceName} - quoteCurrency:`, quoteCurrency);
    console.log(`QuoteResult calculateProcessCardCostForDevice ${deviceName} - quoteExchangeRate:`, quoteExchangeRate);
    
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

  // 计算单个工序的双设备板卡总成本（用于工序报价）
  const calculateProcessCardCost = (process, cardTypes) => {
    // 计算测试机成本
    const testMachineCost = calculateProcessCardCostForDevice(process, 'testMachine', cardTypes);
    
    // 根据工序类型计算第二台设备成本
    let secondDeviceCost = 0;
    if (process.name && process.name.includes('CP')) {
      secondDeviceCost = calculateProcessCardCostForDevice(process, 'prober', cardTypes);
    } else if (process.name && process.name.includes('FT')) {
      secondDeviceCost = calculateProcessCardCostForDevice(process, 'handler', cardTypes);
    }
    
    return testMachineCost + secondDeviceCost;
  };

  // 确认报价，创建数据库记录
  const handleConfirmQuote = async () => {
    if (!quoteData || (!quoteData.quoteCreateData && quoteData.type !== '工序报价')) {
      message.error('报价数据不完整，无法创建报价单');
      return;
    }
    
    // 对于工序报价，如果没有quoteCreateData，则构建一个
    let finalQuoteData = quoteData.quoteCreateData;
    if (quoteData.type === '工序报价' && !finalQuoteData) {
      finalQuoteData = {
        title: quoteData.projectInfo?.projectName || '工序报价',
        quote_type: '工序报价',
        customer_name: quoteData.customerInfo?.companyName || '测试客户',
        customer_contact: quoteData.customerInfo?.contactPerson || '',
        customer_phone: quoteData.customerInfo?.phone || '',
        customer_email: quoteData.customerInfo?.email || '',
        quote_unit: quoteData.projectInfo?.quoteUnit || '昆山芯信安',
        currency: quoteData.currency || 'CNY',
        description: `${quoteData.projectInfo?.chipPackage || ''} - ${quoteData.projectInfo?.testType || ''}`,
        items: [],
        subtotal: 0,
        total_amount: 0,
        notes: quoteData.remarks || '',
        valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30天有效期
        payment_terms: '30_days'
      };
      
      // 判断是否为测试工序（需要双设备）
      const isTestProcess = (processName) => {
        if (!processName) return false;
        return (processName.includes('CP') && (processName.includes('1') || processName.includes('2') || processName.includes('3'))) ||
               (processName.includes('FT') && (processName.includes('1') || processName.includes('2') || processName.includes('3')));
      };

      // 添加工序项目到items
      if (quoteData.cpProcesses) {
        quoteData.cpProcesses.forEach((process, index) => {
          const laborCost = process.unitCost || 0;
          const cardCost = calculateProcessCardCost(process, quoteData.cardTypes);
          const totalCost = laborCost + cardCost;
          const isTest = isTestProcess(process.name);
          
          // 根据工序类型设置不同的设备信息
          let machineType, machineModel, configuration;
          
          if (isTest) {
            // 测试工序：双设备
            machineType = '测试机+探针台';
            machineModel = `${process.testMachine || '未选择'}/${process.prober || '未选择'}`;
            configuration = `测试机:${process.testMachine || '未选择'}, 探针台:${process.prober || '未选择'}, UPH:${process.uph || 0}`;
          } else {
            // 非测试工序：单设备（根据工序名称判断设备类型）
            if (process.name.includes('AOI')) {
              machineType = 'AOI';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('烘烤')) {
              machineType = '烘烤设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('编带')) {
              machineType = '编带机';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else {
              machineType = '其他设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            }
            configuration = `设备:${machineModel}, UPH:${process.uph || 0}`;
          }
          
          finalQuoteData.items.push({
            item_name: `CP-${process.name}`,
            item_description: `CP工序 - ${process.name}`,
            quantity: 1,
            unit: '颗',
            unit_price: totalCost, // 保持原始格式，后端会处理转换
            total_price: totalCost,
            supplier: process.testMachineData?.supplier?.name || process.proberData?.supplier?.name || '',
            configuration: configuration,
            machine_model: machineModel,
            machine_type: machineType,
            uph: process.uph || 0,
            hourly_rate: `¥${((process.testMachineData?.price_rate || 0) + (process.proberData?.price_rate || 0)).toFixed(2)}/小时`
          });
        });
      }
      
      if (quoteData.ftProcesses) {
        quoteData.ftProcesses.forEach((process, index) => {
          const laborCost = process.unitCost || 0;
          const cardCost = calculateProcessCardCost(process, quoteData.cardTypes);
          const totalCost = laborCost + cardCost;
          const isTest = isTestProcess(process.name);
          
          // 根据工序类型设置不同的设备信息
          let machineType, machineModel, configuration;
          
          if (isTest) {
            // 测试工序：双设备
            machineType = '测试机+分选机';
            machineModel = `${process.testMachine || '未选择'}/${process.handler || '未选择'}`;
            configuration = `测试机:${process.testMachine || '未选择'}, 分选机:${process.handler || '未选择'}, UPH:${process.uph || 0}`;
          } else {
            // 非测试工序：单设备（根据工序名称判断设备类型）
            if (process.name.includes('AOI')) {
              machineType = 'AOI';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('烘烤')) {
              machineType = '烘烤设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('编带')) {
              machineType = '编带机';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('老化')) {
              machineType = '老化设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else if (process.name.includes('包装')) {
              machineType = '包装设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            } else {
              machineType = '其他设备';
              machineModel = process.testMachine || process.testMachineData?.name || '未选择';
            }
            configuration = `设备:${machineModel}, UPH:${process.uph || 0}`;
          }
          
          finalQuoteData.items.push({
            item_name: `FT-${process.name}`,
            item_description: `FT工序 - ${process.name}`,
            quantity: 1,
            unit: '颗',
            unit_price: totalCost, // 保持原始格式，后端会处理转换
            total_price: totalCost,
            supplier: process.testMachineData?.supplier?.name || process.handlerData?.supplier?.name || '',
            configuration: configuration,
            machine_model: machineModel,
            machine_type: machineType,
            uph: process.uph || 0,
            hourly_rate: `¥${((process.testMachineData?.price_rate || 0) + (process.handlerData?.price_rate || 0)).toFixed(2)}/小时`
          });
        });
      }
      
      finalQuoteData.subtotal = finalQuoteData.items.reduce((sum, item) => sum + (item.total_price || 0), 0);
      finalQuoteData.total_amount = finalQuoteData.subtotal;
    }

    setConfirmLoading(true);
    try {
      // 动态导入API服务
      const QuoteApiService = (await import('../services/quoteApi')).default;
      
      console.log('准备创建报价单，数据:', finalQuoteData);
      console.log('Items字段详情:', JSON.stringify(finalQuoteData.items, null, 2));
      
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
          configuration: item.configuration || '配置',
          item_name: item.item_name.replace('undefined', '配置')
        }))
      };
      
      console.log('修复后的数据:', JSON.stringify(fixedQuoteData, null, 2));

      // 检查是否是编辑模式
      const isEditMode = quoteData.isEditMode && quoteData.editingQuoteId;
      let resultQuote;

      if (isEditMode) {
        // 编辑模式：更新现有报价单
        console.log('更新报价单，ID:', quoteData.editingQuoteId);
        resultQuote = await QuoteApiService.updateQuote(quoteData.editingQuoteId, fixedQuoteData);
        message.success(`报价单更新成功！报价单号：${resultQuote.quote_number}`);
      } else {
        // 新建模式：创建新报价单
        resultQuote = await QuoteApiService.createQuote(fixedQuoteData);
        message.success(`报价单创建成功！报价单号：${resultQuote.quote_number}`);
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

      console.log(`报价单${isEditMode ? '更新' : '创建'}成功:`, resultQuote);
      
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

  // 计算辅助设备费用（不乘以工程系数）
  const calculateAuxDeviceCost = () => {
    if (!quoteData || !quoteData.selectedAuxDevices || !quoteData.cardTypes) return 0;
    
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    return quoteData.selectedAuxDevices.reduce((total, device) => {
      // 如果是机器类型的辅助设备，计算板卡费用
      if (device.supplier || device.machine_type) {
        // 查找该机器的板卡
        const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
        console.log(`报价结果-计算设备 ${device.name} 的费用，板卡数量: ${machineCards.length}`, machineCards);
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
          
          const cardCost = adjustedPrice * device.discount_rate * (card.quantity || 1);
          console.log(`板卡 ${card.board_name} 费用: ${cardCost}`);
          return sum + cardCost;
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
  };

  // 计算单个辅助设备费用
  const calculateSingleAuxDeviceCost = (device) => {
    if (!quoteData || !quoteData.cardTypes) return 0;
    
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    // 如果是机器类型的辅助设备，计算板卡费用
    if (device.supplier || device.machine_type) {
      // 查找该机器的板卡
      const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
      return machineCards.reduce((sum, card) => {
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
        
        return sum + (adjustedPrice * device.discount_rate * (card.quantity || 1));
      }, 0);
    } else {
      // 如果是原来的辅助设备类型，使用小时费率（默认RMB）
      let hourlyRate = device.hourly_rate || 0;
      if (quoteCurrency === 'USD') {
        hourlyRate = hourlyRate / quoteExchangeRate;
      }
      return hourlyRate;
    }
  };


  return (
    <div>
      <Card title={quoteData ? `${quoteData.type}结果` : '报价结果'}>
        <div className="quote-result-content">
          <h3>费用明细</h3>
          {/* 显示各项费用 */}
          {quoteData && quoteData.type === '工程报价' && (
            <>
              {/* 设备费用 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>测试机机时费（含工程系数）:</span>
                <span>{formatHourlyPrice(calculateTestMachineCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>分选机机时费（含工程系数）:</span>
                <span>{formatHourlyPrice(calculateHandlerCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>探针台机时费（含工程系数）:</span>
                <span>{formatHourlyPrice(calculateProberCost())}</span>
              </div>
              
              {/* 辅助设备费用 */}
              {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span>辅助设备:</span>
                    <span></span>
                  </div>
                  <div style={{ paddingLeft: 20 }}>
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
                        <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span>
                            {device.name}
                            {typeName && ` (${typeName})`}
                          </span>
                          <span>{formatPrice(calculateSingleAuxDeviceCost(device))}</span>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
              
              {/* 人员费用 */}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('工程师') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>工程师小时费:</span>
                  <span>{formatHourlyPrice(calculateEngineerCost())}</span>
                </div>
              )}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('技术员') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>技术员小时费:</span>
                  <span>{formatHourlyPrice(calculateTechnicianCost())}</span>
                </div>
              )}
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
          {console.log('DEBUG: Checking tooling quote condition', {
            hasQuoteData: !!quoteData,
            type: quoteData?.type,
            quote_type: quoteData?.quote_type,
            condition1: quoteData?.type === '工装夹具报价',
            condition2: quoteData?.quote_type === 'tooling'
          })}
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
          {quoteData && quoteData.type === '工序报价' && (
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
                
                {/* CP工序费用详情 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('cp') && quoteData.cpProcesses && (
                  <div style={{ marginBottom: 30 }}>
                    <h5 style={{ 
                      color: '#52c41a', 
                      marginBottom: 15,
                      fontSize: '16px',
                      fontWeight: 'bold',
                      borderBottom: '2px solid #52c41a',
                      paddingBottom: '8px'
                    }}>🔬 CP工序</h5>
                    {quoteData.cpProcesses.map((process, index) => (
                      <div key={index} style={{ 
                        marginBottom: 20, 
                        border: '1px solid #d9f7be', 
                        borderRadius: '8px', 
                        padding: '20px',
                        backgroundColor: '#f6ffed'
                      }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          marginBottom: 15, 
                          color: '#52c41a',
                          fontSize: '16px'
                        }}>
                          {process.name}
                        </div>
                        
                        {/* 设备成本 */}
                        <div style={{ marginBottom: 15 }}>
                          <h6 style={{ color: '#389e0d', marginBottom: 8, fontSize: '14px', fontWeight: 'bold' }}>💻 设备成本</h6>
                          <div style={{ paddingLeft: 15, backgroundColor: '#fff', borderRadius: '4px', padding: '12px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '13px', marginBottom: '8px' }}>
                              <div><strong>测试机:</strong> {process.testMachine || process.testMachineData?.name || '未选择'}</div>
                              <div><strong>探针台:</strong> {process.prober || process.proberData?.name || '未选择'}</div>
                              <div><strong>UPH:</strong> {process.uph || 0}</div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
                              <div><strong>设备机时费:</strong> 
                                <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                                  {(() => {
                                    const cardCost = calculateProcessCardCost(process, quoteData.cardTypes);
                                    const hourlyRate = cardCost * (process.uph || 1);
                                    return formatHourlyPrice(hourlyRate);
                                  })()}
                                </span>
                              </div>
                              <div><strong>单颗报价:</strong> 
                                <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                                  {formatUnitPrice(calculateProcessCardCost(process, quoteData.cardTypes))}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* 人工成本 */}
                        {(process.unitCost && process.unitCost > 0) ? (
                          <div style={{ marginBottom: 10 }}>
                            <h6 style={{ color: '#389e0d', marginBottom: 8, fontSize: '14px', fontWeight: 'bold' }}>👥 人工成本</h6>
                            <div style={{ paddingLeft: 15, backgroundColor: '#fff', borderRadius: '4px', padding: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                                <span>人工成本:</span>
                                <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                                  {formatUnitPrice(process.unitCost)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ) : null}
                        
                        {/* 总成本汇总 */}
                        <div style={{ 
                          marginTop: 15,
                          paddingTop: 12,
                          borderTop: '2px solid #52c41a',
                          textAlign: 'right'
                        }}>
                          <div style={{ 
                            fontSize: '16px', 
                            fontWeight: 'bold', 
                            color: '#52c41a'
                          }}>
                            工序总成本: {formatUnitPrice((process.unitCost || 0) + calculateProcessCardCost(process, quoteData.cardTypes))}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div style={{ textAlign: 'center', marginTop: 15, fontSize: '13px', color: '#666', fontStyle: 'italic', backgroundColor: '#f0f0f0', padding: '8px', borderRadius: '4px' }}>
                      💡 注：CP工序各道工序报价不可直接相加，请根据实际工艺流程选择
                    </div>
                  </div>
                )}
                
                {/* FT工序费用详情 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('ft') && quoteData.ftProcesses && (
                  <div style={{ marginBottom: 30 }}>
                    <h5 style={{ 
                      color: '#1890ff', 
                      marginBottom: 15,
                      fontSize: '16px',
                      fontWeight: 'bold',
                      borderBottom: '2px solid #1890ff',
                      paddingBottom: '8px'
                    }}>📱 FT工序</h5>
                    {quoteData.ftProcesses.map((process, index) => (
                      <div key={index} style={{ 
                        marginBottom: 20, 
                        border: '1px solid #91d5ff', 
                        borderRadius: '8px', 
                        padding: '20px',
                        backgroundColor: '#e6f7ff'
                      }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          marginBottom: 15, 
                          color: '#1890ff',
                          fontSize: '16px'
                        }}>
                          {process.name}
                        </div>
                        
                        {/* 设备成本 */}
                        <div style={{ marginBottom: 15 }}>
                          <h6 style={{ color: '#096dd9', marginBottom: 8, fontSize: '14px', fontWeight: 'bold' }}>💻 设备成本</h6>
                          <div style={{ paddingLeft: 15, backgroundColor: '#fff', borderRadius: '4px', padding: '12px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '13px', marginBottom: '8px' }}>
                              <div><strong>测试机:</strong> {process.testMachine || process.testMachineData?.name || '未选择'}</div>
                              <div><strong>分选机:</strong> {process.handler || process.handlerData?.name || '未选择'}</div>
                              <div><strong>UPH:</strong> {process.uph || 0}</div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
                              <div><strong>设备机时费:</strong> 
                                <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                                  {(() => {
                                    const cardCost = calculateProcessCardCost(process, quoteData.cardTypes);
                                    const hourlyRate = cardCost * (process.uph || 1);
                                    return formatHourlyPrice(hourlyRate);
                                  })()}
                                </span>
                              </div>
                              <div><strong>单颗报价:</strong> 
                                <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                                  {formatUnitPrice(calculateProcessCardCost(process, quoteData.cardTypes))}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* 人工成本 */}
                        {(process.unitCost && process.unitCost > 0) ? (
                          <div style={{ marginBottom: 10 }}>
                            <h6 style={{ color: '#096dd9', marginBottom: 8, fontSize: '14px', fontWeight: 'bold' }}>👥 人工成本</h6>
                            <div style={{ paddingLeft: 15, backgroundColor: '#fff', borderRadius: '4px', padding: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                                <span>人工成本:</span>
                                <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                                  {formatUnitPrice(process.unitCost)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ) : null}
                        
                        {/* 总成本汇总 */}
                        <div style={{ 
                          marginTop: 15,
                          paddingTop: 12,
                          borderTop: '2px solid #1890ff',
                          textAlign: 'right'
                        }}>
                          <div style={{ 
                            fontSize: '16px', 
                            fontWeight: 'bold', 
                            color: '#1890ff'
                          }}>
                            工序总成本: {formatUnitPrice((process.unitCost || 0) + calculateProcessCardCost(process, quoteData.cardTypes))}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div style={{ textAlign: 'center', marginTop: 15, fontSize: '13px', color: '#666', fontStyle: 'italic', backgroundColor: '#f0f0f0', padding: '8px', borderRadius: '4px' }}>
                      💡 注：FT工序各道工序报价不可直接相加，请根据实际工艺流程选择
                    </div>
                  </div>
                )}
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>报价说明</h4>
                <div style={{ paddingLeft: 15, border: '1px solid #e8e8e8', borderRadius: '6px', padding: '15px', backgroundColor: '#f0f8ff' }}>
                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#666' }}>
                    <div style={{ marginBottom: '8px', fontWeight: 'bold', color: '#1890ff' }}>
                      ✓ 工序报价说明：
                    </div>
                    <div style={{ marginBottom: '5px' }}>
                      • 以上为各工序独立报价，反映每道工序的实际成本
                    </div>
                    <div style={{ marginBottom: '5px' }}>
                      • 不同工序存在良率差异，实际成本需根据良率计算
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ color: '#666' }}>
                            测试机 - {quoteData.ftData.testMachine.name || 'FT测试机'}
                          </span>
                          <span>
                            {(() => {
                              // 计算FT测试机费用
                              let testMachineFee = 0;
                              if (quoteData.ftData.testMachineCards) {
                                quoteData.ftData.testMachineCards.forEach(card => {
                                  if (card && card.quantity > 0) {
                                    let adjustedPrice = card.unit_price / 10000;
                                    if (quoteData.quoteCurrency === 'USD') {
                                      if (quoteData.ftData.testMachine.currency === 'CNY' || quoteData.ftData.testMachine.currency === 'RMB') {
                                        adjustedPrice = adjustedPrice / quoteData.quoteExchangeRate;
                                      }
                                    } else {
                                      adjustedPrice = adjustedPrice * (quoteData.ftData.testMachine.exchange_rate || 1);
                                    }
                                    testMachineFee += adjustedPrice * (quoteData.ftData.testMachine.discount_rate || 1) * card.quantity;
                                  }
                                });
                              }
                              return formatHourlyPrice(testMachineFee);
                            })()}
                          </span>
                        </div>
                      )}
                      
                      {/* FT分选机 */}
                      {quoteData.ftData?.handler && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ color: '#666' }}>
                            分选机 - {quoteData.ftData.handler.name || 'FT分选机'}
                          </span>
                          <span>
                            {(() => {
                              // 计算FT分选机费用
                              let handlerFee = 0;
                              if (quoteData.ftData.handlerCards) {
                                quoteData.ftData.handlerCards.forEach(card => {
                                  if (card && card.quantity > 0) {
                                    let adjustedPrice = card.unit_price / 10000;
                                    if (quoteData.quoteCurrency === 'USD') {
                                      if (quoteData.ftData.handler.currency === 'CNY' || quoteData.ftData.handler.currency === 'RMB') {
                                        adjustedPrice = adjustedPrice / quoteData.quoteExchangeRate;
                                      }
                                    } else {
                                      adjustedPrice = adjustedPrice * (quoteData.ftData.handler.exchange_rate || 1);
                                    }
                                    handlerFee += adjustedPrice * (quoteData.ftData.handler.discount_rate || 1) * card.quantity;
                                  }
                                });
                              }
                              return formatHourlyPrice(handlerFee);
                            })()}
                          </span>
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
                        <span style={{ color: '#1890ff' }}>{formatHourlyPrice(quoteData.ftHourlyFee || 0)}</span>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ color: '#666' }}>
                            测试机 - {quoteData.cpData.testMachine.name || 'CP测试机'}
                          </span>
                          <span>
                            {(() => {
                              // 计算CP测试机费用
                              let testMachineFee = 0;
                              if (quoteData.cpData.testMachineCards) {
                                quoteData.cpData.testMachineCards.forEach(card => {
                                  if (card && card.quantity > 0) {
                                    let adjustedPrice = card.unit_price / 10000;
                                    if (quoteData.quoteCurrency === 'USD') {
                                      if (quoteData.cpData.testMachine.currency === 'CNY' || quoteData.cpData.testMachine.currency === 'RMB') {
                                        adjustedPrice = adjustedPrice / quoteData.quoteExchangeRate;
                                      }
                                    } else {
                                      adjustedPrice = adjustedPrice * (quoteData.cpData.testMachine.exchange_rate || 1);
                                    }
                                    testMachineFee += adjustedPrice * (quoteData.cpData.testMachine.discount_rate || 1) * card.quantity;
                                  }
                                });
                              }
                              return formatHourlyPrice(testMachineFee);
                            })()}
                          </span>
                        </div>
                      )}
                      
                      {/* CP探针台 */}
                      {quoteData.cpData?.prober && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ color: '#666' }}>
                            探针台 - {quoteData.cpData.prober.name || 'CP探针台'}
                          </span>
                          <span>
                            {(() => {
                              // 计算CP探针台费用
                              let proberFee = 0;
                              if (quoteData.cpData.proberCards) {
                                quoteData.cpData.proberCards.forEach(card => {
                                  if (card && card.quantity > 0) {
                                    let adjustedPrice = card.unit_price / 10000;
                                    if (quoteData.quoteCurrency === 'USD') {
                                      if (quoteData.cpData.prober.currency === 'CNY' || quoteData.cpData.prober.currency === 'RMB') {
                                        adjustedPrice = adjustedPrice / quoteData.quoteExchangeRate;
                                      }
                                    } else {
                                      adjustedPrice = adjustedPrice * (quoteData.cpData.prober.exchange_rate || 1);
                                    }
                                    proberFee += adjustedPrice * (quoteData.cpData.prober.discount_rate || 1) * card.quantity;
                                  }
                                });
                              }
                              return formatHourlyPrice(proberFee);
                            })()}
                          </span>
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
                        <span style={{ color: '#1890ff' }}>{formatHourlyPrice(quoteData.cpHourlyFee || 0)}</span>
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
                        <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingLeft: 20 }}>
                          <span>
                            {device.name}
                            {typeName && ` (${typeName})`}
                          </span>
                          <span>{formatHourlyPrice(calculateSingleAuxDeviceCost(device))}/小时</span>
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
              // 工程报价：真正的上一步，回到步骤1并保留所有数据
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
                fromResultPage: true
              };
              sessionStorage.setItem('quoteData', JSON.stringify(previousStepData));
              navigate('/engineering-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else {
              // 量产报价：真正的上一步，回到步骤1并保留所有数据
              const previousStepData = {
                currentStep: 1, // 返回到步骤1（辅助设备选择）
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
                fromResultPage: true
              };
              sessionStorage.setItem('massProductionQuoteState', JSON.stringify(previousStepData));
              navigate('/mass-production-quote', { 
                state: { 
                  fromResultPage: true
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
              {confirmLoading ? '正在创建报价单...' : '确认报价'}
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