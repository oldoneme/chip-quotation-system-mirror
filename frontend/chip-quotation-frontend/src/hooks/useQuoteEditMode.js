import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { QuoteApiService } from '../services/quoteApi';

/**
 * 通用的报价编辑模式Hook
 * 处理新建/编辑模式的状态管理和数据转换
 */
const useQuoteEditMode = () => {
  const location = useLocation();
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingQuote, setEditingQuote] = useState(null);
  const [loading, setLoading] = useState(false);

  // 检测编辑模式
  useEffect(() => {
    const checkEditMode = async () => {
      // 方式1: 通过location.state传递编辑信息
      if (location.state?.isEditing) {
        setIsEditMode(true);

        // 如果是从结果页返回，不重新获取数据，数据已经在sessionStorage中
        if (location.state?.fromResultPage && location.state?.quoteId) {
          // 创建一个基本的editingQuote对象，仅用于标识编辑模式
          setEditingQuote({
            id: location.state.quoteId,
            quote_number: location.state.quoteNumber || location.state.quoteId
          });
          setLoading(false);
        }
        // 优先使用已传递的editingQuote数据
        else if (location.state?.editingQuote) {
          setEditingQuote(location.state.editingQuote);
          setLoading(false);
        } else if (location.state?.quoteId) {
          // 如果没有完整数据但有ID，则从API获取
          setLoading(true);
          try {
            const quoteData = await QuoteApiService.getQuoteDetailById(location.state.quoteId);
            setEditingQuote(quoteData);
          } catch (error) {
            console.error('获取报价数据失败:', error);
            setIsEditMode(false);
          } finally {
            setLoading(false);
          }
        }
      }

      // 方式2: 通过URL参数检测编辑模式
      const urlParams = new URLSearchParams(location.search);
      const editQuoteId = urlParams.get('edit');

      if (editQuoteId && !location.state?.isEditing) {
        setIsEditMode(true);
        setLoading(true);

        try {
          const quoteData = await QuoteApiService.getQuoteDetailById(editQuoteId);
          setEditingQuote(quoteData);
        } catch (error) {
          console.error('获取报价数据失败:', error);
          setIsEditMode(false);
        } finally {
          setLoading(false);
        }
      }
    };

    checkEditMode();
  }, [location]);

  /**
   * 将前端展示格式数据转换为后端原始格式
   * @param {Object} displayQuote - 前端展示格式的报价数据
   * @returns {Object} 后端原始格式的报价数据
   */
  const convertDisplayFormatToRawFormat = (displayQuote) => {
    // 从前端展示格式推断后端原始格式
    return {
      // 客户信息
      customer_name: displayQuote.customer || '',
      customer_contact: displayQuote.contactPerson || '',
      customer_phone: displayQuote.phone || '',
      customer_email: displayQuote.email || '',

      // 基本信息
      id: displayQuote.quoteId || displayQuote.id,
      quote_number: displayQuote.id || displayQuote.quote_number,
      quote_type: mapDisplayTypeToRawType(displayQuote.type),
      currency: displayQuote.currency || 'CNY',
      total_amount: displayQuote.totalAmount,
      status: displayQuote.status,

      // 项目描述和备注（尝试重建）
      description: `项目：${displayQuote.project || ''}，芯片封装：未知，测试类型：${displayQuote.type || ''}`,
      notes: `备注：${displayQuote.remarks || ''}`,

      // 报价项目 - 从 items 数组转换
      items: displayQuote.items || [],

      // 其他字段
      quote_unit: '昆山芯信安',
      payment_terms: '30_days',
      valid_until: displayQuote.validUntil,
      created_at: displayQuote.createdAt,
      updated_at: displayQuote.updatedAt
    };
  };

  /**
   * 将前端展示类型映射到后端原始类型
   */
  const mapDisplayTypeToRawType = (displayType) => {
    const mapping = {
      '询价报价': 'inquiry',
      '工装夹具报价': 'tooling',
      '工程机时报价': 'engineering',
      '量产机时报价': 'mass_production',
      '量产工序报价': 'process',
      '综合报价': 'comprehensive'
    };
    return mapping[displayType] || displayType;
  };

  /**
   * 将后端报价数据转换为前端表单数据格式
   * @param {Object} quote - 后端报价数据或前端展示数据
   * @param {string} quoteType - 报价类型 (tooling, inquiry, engineering, etc.)
   * @param {Array} availableCardTypes - 可用的板卡类型数据（用于ID匹配）
   * @param {Array} availableMachines - 可用的机器数据（用于获取完整机器属性）
   * @returns {Object} 前端表单数据格式
   */
  const convertQuoteToFormData = (quote, quoteType, availableCardTypes = [], availableMachines = []) => {
    if (!quote) return null;


    // 检测数据格式：后端原始格式 vs 前端展示格式
    const isRawFormat = quote.customer_name !== undefined; // 后端格式有 customer_name
    const isDisplayFormat = quote.customer !== undefined && quote.customer_name === undefined; // 前端格式有 customer 但没有 customer_name


    // 统一数据格式 - 将前端展示格式转换为后端原始格式（如果需要）
    let normalizedQuote = quote;
    if (isDisplayFormat) {
      normalizedQuote = convertDisplayFormatToRawFormat(quote);
    }

    // 基础客户信息转换
    const baseFormData = {
      customerInfo: {
        companyName: normalizedQuote.customer_name || '',
        contactPerson: normalizedQuote.customer_contact || '',
        phone: normalizedQuote.customer_phone || '',
        email: normalizedQuote.customer_email || ''
      },
      projectInfo: {
        projectName: extractProjectNameFromDescription(normalizedQuote.description),
        quoteUnit: normalizedQuote.quote_unit || '昆山芯信安'
      },
      currency: normalizedQuote.currency || 'CNY',
      paymentTerms: normalizedQuote.payment_terms || '30_days',
      remarks: extractRemarksFromNotes(normalizedQuote.notes)
    };


    // 根据报价类型进行特殊转换
    switch (quoteType) {
      case 'tooling':
        return convertToolingQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes);
      case 'inquiry':
        return convertInquiryQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes);
      case 'engineering':
        return convertEngineeringQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes, availableMachines);
      case 'mass_production':
        return convertMassProductionQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes, availableMachines);
      case 'process':
        return convertProcessQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes, availableMachines);
      case 'comprehensive':
        return convertComprehensiveQuoteToFormData(normalizedQuote, baseFormData, availableCardTypes);
      default:
        return baseFormData;
    }
  };

  /**
   * 询价报价数据转换
   */
  const convertInquiryQuoteToFormData = (quote, baseFormData, availableCardTypes = []) => {
    const machines = [];

    // 解析询价报价中的机器配置
    quote.items?.forEach(item => {
      if (item.machine_type && item.machine_model) {
        machines.push({
          id: machines.length + 1,
          category: mapMachineTypeToCategory(item.machine_type),
          model: item.machine_model,
          hourlyRate: item.unit_price || 0,
          selectedCards: [], // 询价报价可能不包含详细板卡信息
          machineData: item.machine_id ? { id: item.machine_id } : null
        });
      }
    });

    // 确保至少有一个机器配置
    if (machines.length === 0) {
      machines.push({
        id: 1,
        category: '',
        model: '',
        hourlyRate: 0,
        selectedCards: [],
        machineData: null
      });
    }

    return {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: extractTestTypeFromItems(quote.items),
        urgency: 'normal'
      },
      machines,
      currency: quote.currency || 'CNY',
      exchangeRate: 7.2, // 默认汇率
      inquiryFactor: extractInquiryFactorFromItems(quote.items),
      remarks: extractRemarksFromNotes(quote.notes)
    };
  };

  /**
   * 量产机时报价数据转换
   */
  const convertMassProductionQuoteToFormData = (quote, baseFormData, availableCardTypes = [], availableMachines = []) => {

    // 解析币种和汇率
    const currency = quote.currency || 'CNY';
    const exchangeRate = extractExchangeRateFromNotes(quote.notes);

    // 从items中解析设备配置（FT/CP设备和辅助设备）
    const deviceConfig = parseMassProductionDevicesFromItems(quote.items, availableCardTypes, availableMachines);

    return {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: 'mass_production',
        urgency: extractUrgencyFromNotes(quote.notes)
      },
      quoteCurrency: currency,
      quoteExchangeRate: exchangeRate,
      deviceConfig: deviceConfig,
      remarks: extractRemarksFromNotes(quote.notes)
    };
  };

  /**
   * 量产工序报价数据转换
   */
  const convertProcessQuoteToFormData = (quote, baseFormData, availableCardTypes = [], availableMachines = []) => {
    // 解析币种和汇率
    const currency = quote.currency || 'CNY';
    const exchangeRate = quote.exchange_rate || 7.2;

    // 从items中解析多工序配置
    const processConfig = parseProcessQuoteDevicesFromItems(quote.items, availableCardTypes, availableMachines);

    const result = {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: extractTestTypeFromItems(quote.items) || 'process',
        urgency: extractUrgencyFromNotes(quote.notes)
      },
      // 工序报价特有字段
      selectedTypes: processConfig.selectedTypes,
      cpProcesses: processConfig.cpProcesses.length > 0 ? processConfig.cpProcesses : [
        {
          id: 1,
          name: 'CP1测试',
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
      ftProcesses: processConfig.ftProcesses.length > 0 ? processConfig.ftProcesses : [
        {
          id: 1,
          name: 'FT1测试',
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
      currency: currency,
      exchangeRate: exchangeRate,
      pricing: {
        laborCostPerHour: 0,
        overheadRate: 0,
        profitMargin: 0
      },
      remarks: extractRemarksFromNotes(quote.notes)
    };

    return result;
  };

  /**
   * 综合报价数据转换
   */
  const convertComprehensiveQuoteToFormData = (quote, baseFormData, availableCardTypes = []) => {

    return {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: 'comprehensive',
        urgency: extractUrgencyFromNotes(quote.notes)
      },
      remarks: extractRemarksFromNotes(quote.notes)
    };
  };

  /**
   * 工程机时报价数据转换
   */
  const convertEngineeringQuoteToFormData = (quote, baseFormData, availableCardTypes = [], availableMachines = []) => {

    // 解析工程系数
    const engineeringRate = extractEngineeringRateFromDescription(quote.description);

    // 解析币种和汇率
    const currency = quote.currency || 'CNY';
    const exchangeRate = extractExchangeRateFromNotes(quote.notes);

    // 解析紧急程度
    const urgency = extractUrgencyFromNotes(quote.notes);

    // 从items中解析设备和人员配置
    const deviceConfig = parseEngineeringDevicesFromItems(quote.items, availableCardTypes, availableMachines);
    const personnelConfig = parseEngineeringPersonnelFromItems(quote.items);

    return {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: 'engineering',
        urgency: urgency
      },
      // 工程机时报价特有字段
      engineeringRate: engineeringRate,
      quoteCurrency: currency,
      quoteExchangeRate: exchangeRate,

      // 设备配置（根据解析的数据设置）
      deviceConfig: deviceConfig,
      personnelConfig: personnelConfig,

      // 注意：实际的状态设置需要在EngineeringQuote组件中完成
      // 因为该组件有复杂的状态管理结构

      remarks: extractRemarksFromNotes(quote.notes)
    };
  };

  /**
   * 工装夹具报价数据转换
   */
  const convertToolingQuoteToFormData = (quote, baseFormData, availableCardTypes = []) => {

    const toolingItems = [];
    const engineeringFees = {
      testProgramDevelopment: 0,
      fixtureDesign: 0,
      testValidation: 0,
      documentation: 0
    };
    const productionSetup = {
      setupFee: 0,
      calibrationFee: 0,
      firstArticleInspection: 0
    };


    // 解析报价项目
    quote.items?.forEach((item, index) => {

      // 根据item_description或item_name来判断类型（因为category_type可能为空）
      const itemName = item.item_name || '';
      const itemDesc = item.item_description || '';

      // 工装硬件项目（fixture, consumables等）
      if (itemDesc.includes('fixture') || itemDesc.includes('consumables') ||
          ['load_board', 'contactor', 'socket', 'probe_needles'].includes(itemName)) {
        toolingItems.push({
          id: toolingItems.length + 1,
          category: itemDesc.includes('fixture') ? '夹具' : '耗材',
          type: itemName || '',
          specification: extractSpecFromDescription(itemDesc),
          quantity: item.quantity || 1,
          unitPrice: item.unit_price || 0,
          totalPrice: item.total_price || 0
        });
      }
      // 工程费用
      else if (itemDesc.includes('工程开发服务费') ||
               ['测试程序开发', '夹具设计', '测试验证', '文档编制'].includes(itemName)) {
        const feeKey = mapEngineeringFeeNameToKey(itemName);
        if (feeKey && engineeringFees.hasOwnProperty(feeKey)) {
          engineeringFees[feeKey] = item.unit_price || 0;
        }
      }
      // 量产准备费用
      else if (itemDesc.includes('量产准备服务费') ||
               ['设备调试费', '校准费', '首件检验费'].includes(itemName)) {
        const setupKey = mapProductionSetupNameToKey(itemName);
        if (setupKey && productionSetup.hasOwnProperty(setupKey)) {
          productionSetup[setupKey] = item.unit_price || 0;
        }
      } else {
      }
    });

    // 确保至少有一个工装项目
    if (toolingItems.length === 0) {
      toolingItems.push({
        id: 1,
        category: '',
        type: '',
        specification: '',
        quantity: 1,
        unitPrice: 0,
        totalPrice: 0
      });
    }

    const result = {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: extractTestTypeFromDescription(quote.description),
        productStyle: 'existing'  // 编辑时默认为已有产品
      },
      toolingItems,
      engineeringFees,
      productionSetup,
      deliveryTime: extractDeliveryTimeFromNotes(quote.notes)
    };


    return result;
  };

  /**
   * 工程费用名称到表单字段的映射
   */
  const mapEngineeringFeeNameToKey = (feeName) => {
    const mapping = {
      '测试程序开发': 'testProgramDevelopment',
      '夹具设计': 'fixtureDesign',
      '测试验证': 'testValidation',
      '文档编制': 'documentation'
    };
    return mapping[feeName];
  };

  /**
   * 量产准备费用名称到表单字段的映射
   */
  const mapProductionSetupNameToKey = (setupName) => {
    const mapping = {
      '设备调试费': 'setupFee',
      '校准费': 'calibrationFee',
      '首件检验费': 'firstArticleInspection'
    };
    return mapping[setupName];
  };

  /**
   * 从描述中提取项目名称
   */
  const extractProjectNameFromDescription = (description) => {
    if (!description) return '';
    // 支持多种格式：项目：xxx / 项目名称：xxx / 项目: xxx / 项目名称: xxx
    const match = description.match(/(?:项目名称|项目)[：:]\s*([^;；，,]+)/);
    return match ? match[1].trim() : '';
  };

  /**
   * 从描述中提取芯片封装
   */
  const extractChipPackageFromDescription = (description) => {
    if (!description) return '';
    // 支持中文冒号和英文冒号，支持多种分隔符
    const match = description.match(/芯片封装[：:]\s*([^;；，,]+)/);
    return match ? match[1].trim() : '';
  };

  /**
   * 从描述中提取测试类型
   */
  const extractTestTypeFromDescription = (description) => {
    if (!description) return '';
    // 支持中文冒号和英文冒号，支持多种分隔符
    const match = description.match(/测试类型[：:]\s*([^;；，,]+)/);
    return match ? match[1].trim() : '';
  };

  /**
   * 从备注中提取交期
   */
  const extractDeliveryTimeFromNotes = (notes) => {
    if (!notes) return '';
    const match = notes.match(/交期：([^，,]+)/);
    return match ? match[1] : '';
  };

  /**
   * 从备注中提取实际备注内容
   */
  const extractRemarksFromNotes = (notes) => {
    if (!notes) return '';
    const match = notes.match(/备注：(.+)/);
    return match ? match[1] : '';
  };

  /**
   * 从项目描述中提取规格说明
   */
  const extractSpecFromDescription = (description) => {
    if (!description) return '';
    const parts = description.split(' - ');
    return parts.length > 1 ? parts[1] : '';
  };

  /**
   * 机器类型名称到类别的映射
   */
  const mapMachineTypeToCategory = (machineType) => {
    if (!machineType) return '';
    if (machineType.includes('测试机') || machineType.includes('ATE')) return 'tester';
    if (machineType.includes('分选机') || machineType.includes('Handler')) return 'handler';
    if (machineType.includes('编带') || machineType.includes('Sorter')) return 'sorter';
    return '';
  };

  /**
   * 从报价项目中提取测试类型
   */
  const extractTestTypeFromItems = (items) => {
    if (!items || items.length === 0) return 'mixed';

    // 检查所有items，判断是否同时包含CP和FT工序
    let hasCP = false;
    let hasFT = false;

    for (const item of items) {
      if (item.item_name?.includes('CP')) hasCP = true;
      if (item.item_name?.includes('FT')) hasFT = true;
    }

    // 如果同时有CP和FT，返回mixed
    if (hasCP && hasFT) return 'mixed';
    // 只有CP工序
    if (hasCP) return 'CP';
    // 只有FT工序
    if (hasFT) return 'FT';
    // 都没有，默认mixed
    return 'mixed';
  };

  /**
   * 从报价项目中提取询价系数
   */
  const extractInquiryFactorFromItems = (items) => {
    if (!items || items.length === 0) return 1.5;

    // 尝试从项目描述中提取询价系数
    const firstItem = items[0];
    if (firstItem.item_description) {
      const match = firstItem.item_description.match(/询价系数:\s*([0-9.]+)/);
      if (match) {
        return parseFloat(match[1]) || 1.5;
      }
    }
    return 1.5;
  };

  /**
   * 工程机时报价相关的辅助函数
   */

  /**
   * 从描述中提取工程系数
   */
  const extractEngineeringRateFromDescription = (description) => {
    if (!description) return 1.2;

    const match = description.match(/工程系数[：:]\s*([0-9.]+)/);
    if (match) {
      return parseFloat(match[1]) || 1.2;
    }
    return 1.2;
  };

  /**
   * 从备注中提取汇率
   */
  const extractExchangeRateFromNotes = (notes) => {
    if (!notes) return 7.2;

    const match = notes.match(/汇率[：:]\s*([0-9.]+)/);
    if (match) {
      return parseFloat(match[1]) || 7.2;
    }
    return 7.2;
  };

  /**
   * 从备注中提取紧急程度
   */
  const extractUrgencyFromNotes = (notes) => {
    if (!notes) return 'normal';

    if (notes.includes('紧急')) {
      return 'urgent';
    }
    return 'normal';
  };

  /**
   * 根据设备名称查找设备ID的辅助函数
   * 需要与当前可用的设备列表匹配
   */
  const findMachineIdByName = (machineName, machineType) => {
    // 设备名称到ID的映射（基于当前数据库的实际数据）
    const machineMapping = {
      'ETS-88': 7,
      'JHT6080': 14,
      'AP3000': 15,
      'JS3000': 5,
      'J750': 1,
      'T800': 16,
      'Acco STS8200': 17,
      'QT8100': 18
    };

    return machineMapping[machineName] || null;
  };

  /**
   * 根据板卡名称或Part Number查找真实的cardType ID
   */
  const findCardTypeIdByName = (cardName, partNumber, machineId, availableCardTypes) => {
    if (!availableCardTypes || availableCardTypes.length === 0) {
      return null;
    }

    // 先过滤出该机器的所有板卡
    const machineCards = availableCardTypes.filter(card => card.machine_id === machineId);

    // 尝试精确匹配part_number
    let match = machineCards.find(card =>
      card.part_number === partNumber || card.part_number === cardName
    );

    if (match) {
      return match.id;
    }

    // 尝试匹配board_name
    match = machineCards.find(card =>
      card.board_name === cardName || card.board_name === partNumber
    );

    if (match) {
      return match.id;
    }

    // 模糊匹配（包含关系）
    match = machineCards.find(card =>
      card.part_number?.includes(partNumber) ||
      card.board_name?.includes(cardName) ||
      partNumber?.includes(card.part_number) ||
      cardName?.includes(card.board_name)
    );

    return match ? match.id : null;
  };

  /**
   * 从报价项目中解析工程设备配置
   */
  const parseEngineeringDevicesFromItems = (items, availableCardTypes = [], availableMachines = []) => {
    const config = {
      testMachine: null,
      handler: null,
      prober: null,
      auxDevices: [],
      testMachineCards: [],
      handlerCards: [],
      proberCards: []
    };

    if (!items || items.length === 0) return config;

    // 按设备类型分组items，收集设备信息和板卡信息
    const deviceGroups = {
      testMachine: [],
      handler: [],
      prober: [],
      auxDevices: []
    };

    items.forEach(item => {
      const machineType = item.machine_type || '';
      const itemName = item.item_name || '';
      const itemDesc = item.item_description || '';

      // 按机器类型分类
      if (machineType.includes('测试机') || itemName.includes('测试机') || itemDesc.includes('测试机')) {
        deviceGroups.testMachine.push(item);
      } else if (machineType.includes('分选机') || itemName.includes('分选机') || itemDesc.includes('分选机')) {
        deviceGroups.handler.push(item);
      } else if (machineType.includes('探针台') || itemName.includes('探针台') || itemDesc.includes('探针台')) {
        deviceGroups.prober.push(item);
      } else if (machineType.includes('辅助') || itemDesc.includes('辅助设备') || machineType === 'AOI') {
        deviceGroups.auxDevices.push(item);
      }
    });

    // 解析测试机和板卡信息
    if (deviceGroups.testMachine.length > 0) {
      const firstItem = deviceGroups.testMachine[0];
      const machineName = firstItem.machine_model || firstItem.item_name;
      // 优先使用数据库中的 machine_id，如果没有则尝试通过名称查找
      const machineId = firstItem.machine_id || findMachineIdByName(machineName, '测试机');

      if (machineId) {
        // 查找完整的机器数据
        const fullMachine = availableMachines.find(machine => machine.id === machineId);
        if (fullMachine) {
          config.testMachine = fullMachine;
        } else {
          // 如果找不到完整数据，使用基本结构但添加必要属性
          config.testMachine = {
            id: machineId,
            name: machineName,
            supplier: firstItem.supplier || '',
            exchange_rate: 1.0,
            discount_rate: 1.0,
            currency: 'CNY'
          };
        }
      }

      // 详细板卡格式：item_name格式为"机器名 - 板卡名"（最新格式）
      const detailedFormatCards = deviceGroups.testMachine
        .filter(item => item.item_name && item.item_name.includes(' - '))
        .map(item => {
          const boardName = item.item_name.split(' - ')[1] || item.item_name;

          // 从item_description中提取part_number（format: "测试机板卡 - SYS0088-DUAL-EV"）
          let partNumber = boardName;
          if (item.item_description && item.item_description.includes(' - ')) {
            partNumber = item.item_description.split(' - ')[1] || boardName;
          }

          // 也可以从configuration中提取Part Number
          if (item.configuration && item.configuration.includes('Part Number:')) {
            const configMatch = item.configuration.match(/Part Number:\s*([^,]+)/);
            if (configMatch) {
              partNumber = configMatch[1].trim();
            }
          }

          const realCardId = findCardTypeIdByName(boardName, partNumber, machineId, availableCardTypes);

          // 从availableCardTypes中获取真实的板卡数据，而不是使用报价中的数据
          const realCard = availableCardTypes.find(card => card.id === realCardId);

          const cardData = {
            id: realCardId || `temp_${item.id}`, // 使用真实ID或临时ID
            part_number: partNumber,
            board_name: boardName,
            // 使用API中的真实数据，不是报价中保存的数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: machineId,
            original_item_id: item.id // 保留原始ID用于调试
          };

          return cardData;
        });


      // 新版本：从card_info获取板卡信息，但使用API中的真实数据
      const newFormatCards = deviceGroups.testMachine
        .filter(item => item.card_info)
        .map(item => {
          // 从API中获取真实的板卡数据
          const realCard = availableCardTypes.find(card => card.id === item.card_info.id);
          return {
            id: item.card_info.id,
            part_number: item.card_info.part_number,
            board_name: item.card_info.board_name,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.card_info.quantity || 1,
            machine_id: item.machine_id
          };
        });

      // JSON格式：从configuration的JSON中解析板卡信息
      const jsonFormatCards = deviceGroups.testMachine
        .filter(item => {
          try {
            const config = JSON.parse(item.configuration || '{}');
            return config.cards && Array.isArray(config.cards);
          } catch (e) {
            return false;
          }
        })
        .flatMap(item => {
          try {
            const config = JSON.parse(item.configuration);
            return config.cards.map(cardInfo => {
              // 从API中获取真实的板卡数据
              const realCard = availableCardTypes.find(card => card.id === cardInfo.id);
              return {
                id: cardInfo.id,
                part_number: cardInfo.part_number,
                board_name: cardInfo.board_name,
                // 使用API中的真实数据
                unit_price: realCard ? realCard.unit_price : 0,
                quantity: cardInfo.quantity || 1,
                machine_id: machineId
              };
            });
          } catch (e) {
            return [];
          }
        });

      // 旧版本：从configuration解析板卡信息，但使用API中的真实数据
      const oldFormatCards = deviceGroups.testMachine
        .filter(item => {
          try {
            JSON.parse(item.configuration || '{}');
            return false; // 如果是JSON格式，不用旧格式解析
          } catch (e) {
            return !item.card_info && item.configuration && item.configuration.includes('板卡:');
          }
        })
        .map(item => {
          const config = item.configuration || '';
          const boardNameMatch = config.match(/板卡:\s*([^,]+)/);
          const partNumberMatch = config.match(/Part Number:\s*([^,]+)/);

          const boardName = boardNameMatch ? boardNameMatch[1] : item.item_name;
          const partNumber = partNumberMatch ? partNumberMatch[1] : item.item_name;

          // 查找真实的板卡ID和数据
          const realCardId = findCardTypeIdByName(boardName, partNumber, machineId, availableCardTypes);
          const realCard = availableCardTypes.find(card => card.id === realCardId);

          return {
            id: realCardId || Math.random(), // 使用真实ID或临时ID
            part_number: partNumber,
            board_name: boardName,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: item.machine_id || 1
          };
        });

      // 合并所有格式的板卡信息（优先级：JSON > detailed > new > old）
      if (jsonFormatCards.length > 0) {
        // 使用JSON格式板卡（最新格式，优先级最高）
        config.testMachineCards = jsonFormatCards;
      } else if (detailedFormatCards.length > 0) {
        // 使用详细格式板卡
        config.testMachineCards = detailedFormatCards;
      } else if (newFormatCards.length > 0 || oldFormatCards.length > 0) {
        // 使用card_info或configuration格式
        config.testMachineCards = [...newFormatCards, ...oldFormatCards];
      } else {
        // 如果没有任何板卡信息，创建基本的设备项
        config.testMachineCards = deviceGroups.testMachine.map(item => ({
          id: Math.random(),
          part_number: item.item_name,
          board_name: item.item_name,
          unit_price: item.unit_price || 0,
          quantity: item.quantity || 1,
          machine_id: machineId
        }));
      }

    }

    // 解析分选机和板卡信息（类似逻辑）
    if (deviceGroups.handler.length > 0) {
      const firstItem = deviceGroups.handler[0];
      const machineName = firstItem.machine_model || firstItem.item_name;
      // 优先使用数据库中的 machine_id，如果没有则尝试通过名称查找
      const machineId = firstItem.machine_id || findMachineIdByName(machineName, '分选机');


      if (machineId) {
        // 查找完整的机器数据
        const fullMachine = availableMachines.find(machine => machine.id === machineId);
        if (fullMachine) {
          config.handler = fullMachine;
        } else {
          // 如果找不到完整数据，使用基本结构但添加必要属性
          config.handler = {
            id: machineId,
            name: machineName,
            supplier: firstItem.supplier || '',
            exchange_rate: 1.0,
            discount_rate: 1.0,
            currency: 'CNY'
          };
        }
      }

      // JSON格式：从configuration字段中解析板卡信息
      const jsonFormatCards = deviceGroups.handler
        .filter(item => {
          try {
            const config = JSON.parse(item.configuration || '{}');
            return config.cards && Array.isArray(config.cards);
          } catch (e) {
            return false;
          }
        })
        .flatMap(item => {
          try {
            const config = JSON.parse(item.configuration);
            return config.cards.map(cardInfo => {
              const realCard = availableCardTypes.find(card => card.id === cardInfo.id);
              return {
                id: cardInfo.id,
                part_number: cardInfo.part_number,
                board_name: cardInfo.board_name,
                unit_price: realCard ? realCard.unit_price : 0,
                quantity: cardInfo.quantity || 1,
                machine_id: machineId
              };
            });
          } catch (e) {
            return [];
          }
        });

      // 详细板卡格式：item_name格式为"机器名 - 板卡名"
      const detailedFormatCards = deviceGroups.handler
        .filter(item => item.item_name && item.item_name.includes(' - '))
        .map(item => {
          const boardName = item.item_name.split(' - ')[1] || item.item_name;

          // 从item_description中提取part_number（format: "分选机板卡 - SYS0088-DUAL-EV"）
          let partNumber = boardName;
          if (item.item_description && item.item_description.includes(' - ')) {
            partNumber = item.item_description.split(' - ')[1] || boardName;
          }

          // 也可以从configuration中提取Part Number
          if (item.configuration && item.configuration.includes('Part Number:')) {
            const configMatch = item.configuration.match(/Part Number:\s*([^,]+)/);
            if (configMatch) {
              partNumber = configMatch[1].trim();
            }
          }

          const realCardId = findCardTypeIdByName(boardName, partNumber, machineId, availableCardTypes);
          // 从availableCardTypes中获取真实的板卡数据
          const realCard = availableCardTypes.find(card => card.id === realCardId);

          return {
            id: realCardId || `temp_${item.id}`,
            part_number: partNumber,
            board_name: boardName,
            // 使用API中的真实数据，不是报价中保存的数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: machineId,
            original_item_id: item.id
          };
        });

      const newFormatCards = deviceGroups.handler
        .filter(item => item.card_info)
        .map(item => {
          // 从API中获取真实的板卡数据
          const realCard = availableCardTypes.find(card => card.id === item.card_info.id);
          return {
            id: item.card_info.id,
            part_number: item.card_info.part_number,
            board_name: item.card_info.board_name,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.card_info.quantity || 1,
            machine_id: item.machine_id
          };
        });

      const oldFormatCards = deviceGroups.handler
        .filter(item => !item.item_name?.includes(' - ') && !item.card_info)
        .map(item => {
          // 尝试从API中找到匹配的板卡
          const realCard = availableCardTypes.find(card =>
            card.machine_id === machineId && (
              card.board_name === item.item_name ||
              card.part_number === item.item_name
            )
          );
          return {
            id: realCard ? realCard.id : Math.random(),
            part_number: item.item_name,
            board_name: item.item_name,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: machineId
          };
        });

      // 优先使用JSON格式，其次是详细格式，然后是新格式，最后是旧格式
      if (jsonFormatCards.length > 0) {
        config.handlerCards = jsonFormatCards;
      } else if (detailedFormatCards.length > 0) {
        config.handlerCards = detailedFormatCards;
      } else if (newFormatCards.length > 0) {
        config.handlerCards = newFormatCards;
      } else {
        config.handlerCards = oldFormatCards;
      }

    }

    // 解析探针台和板卡信息（类似逻辑）
    if (deviceGroups.prober.length > 0) {
      const firstItem = deviceGroups.prober[0];
      const machineName = firstItem.machine_model || firstItem.item_name;
      // 优先使用数据库中的 machine_id，如果没有则尝试通过名称查找
      const machineId = firstItem.machine_id || findMachineIdByName(machineName, '探针台');


      if (machineId) {
        // 查找完整的机器数据
        const fullMachine = availableMachines.find(machine => machine.id === machineId);
        if (fullMachine) {
          config.prober = fullMachine;
        } else {
          // 如果找不到完整数据，使用基本结构但添加必要属性
          config.prober = {
            id: machineId,
            name: machineName,
            supplier: firstItem.supplier || '',
            exchange_rate: 1.0,
            discount_rate: 1.0,
            currency: 'CNY'
          };
        }
      }

      // JSON格式：从configuration字段中解析板卡信息
      const jsonFormatCards = deviceGroups.prober
        .filter(item => {
          try {
            const config = JSON.parse(item.configuration || '{}');
            return config.cards && Array.isArray(config.cards);
          } catch (e) {
            return false;
          }
        })
        .flatMap(item => {
          try {
            const config = JSON.parse(item.configuration);
            return config.cards.map(cardInfo => {
              const realCard = availableCardTypes.find(card => card.id === cardInfo.id);
              return {
                id: cardInfo.id,
                part_number: cardInfo.part_number,
                board_name: cardInfo.board_name,
                unit_price: realCard ? realCard.unit_price : 0,
                quantity: cardInfo.quantity || 1,
                machine_id: machineId
              };
            });
          } catch (e) {
            return [];
          }
        });

      // 详细板卡格式：item_name格式为"机器名 - 板卡名"
      const detailedFormatCards = deviceGroups.prober
        .filter(item => item.item_name && item.item_name.includes(' - '))
        .map(item => {
          const boardName = item.item_name.split(' - ')[1] || item.item_name;

          // 从item_description中提取part_number（format: "探针台板卡 - SYS0088-DUAL-EV"）
          let partNumber = boardName;
          if (item.item_description && item.item_description.includes(' - ')) {
            partNumber = item.item_description.split(' - ')[1] || boardName;
          }

          // 也可以从configuration中提取Part Number
          if (item.configuration && item.configuration.includes('Part Number:')) {
            const configMatch = item.configuration.match(/Part Number:\s*([^,]+)/);
            if (configMatch) {
              partNumber = configMatch[1].trim();
            }
          }

          const realCardId = findCardTypeIdByName(boardName, partNumber, machineId, availableCardTypes);
          // 从availableCardTypes中获取真实的板卡数据
          const realCard = availableCardTypes.find(card => card.id === realCardId);

          return {
            id: realCardId || `temp_${item.id}`,
            part_number: partNumber,
            board_name: boardName,
            // 使用API中的真实数据，不是报价中保存的数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: machineId,
            original_item_id: item.id
          };
        });

      const newFormatCards = deviceGroups.prober
        .filter(item => item.card_info)
        .map(item => {
          // 从API中获取真实的板卡数据
          const realCard = availableCardTypes.find(card => card.id === item.card_info.id);
          return {
            id: item.card_info.id,
            part_number: item.card_info.part_number,
            board_name: item.card_info.board_name,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.card_info.quantity || 1,
            machine_id: item.machine_id
          };
        });

      const oldFormatCards = deviceGroups.prober
        .filter(item => !item.item_name?.includes(' - ') && !item.card_info)
        .map(item => {
          // 尝试从API中找到匹配的板卡
          const realCard = availableCardTypes.find(card =>
            card.machine_id === machineId && (
              card.board_name === item.item_name ||
              card.part_number === item.item_name
            )
          );
          return {
            id: realCard ? realCard.id : Math.random(),
            part_number: item.item_name,
            board_name: item.item_name,
            // 使用API中的真实数据
            unit_price: realCard ? realCard.unit_price : 0,
            quantity: item.quantity || 1,
            machine_id: machineId
          };
        });

      // 优先使用JSON格式，其次是详细格式，然后是新格式，最后是旧格式
      if (jsonFormatCards.length > 0) {
        config.proberCards = jsonFormatCards;
      } else if (detailedFormatCards.length > 0) {
        config.proberCards = detailedFormatCards;
      } else if (newFormatCards.length > 0) {
        config.proberCards = newFormatCards;
      } else {
        config.proberCards = oldFormatCards;
      }

    }

    // 解析辅助设备 - 统一使用API数据源
    config.auxDevices = deviceGroups.auxDevices.map(item => {
      const machineName = item.machine_model || item.item_name;
      // 优先使用数据库中的 machine_id，如果没有则尝试通过名称查找
      const machineId = item.machine_id || findMachineIdByName(machineName, item.machine_type);

      // 从availableMachines中获取真实的机器数据
      const realMachine = availableMachines.find(machine => machine.id === machineId);

      // 统一使用API中的数据，尝试多种可能的字段名
      let hourlyRate = 0;
      let exchangeRate = 1.0;
      let discountRate = 1.0;
      let currency = 'CNY';

      if (realMachine) {
        hourlyRate = realMachine.hourly_rate || realMachine.hourlyRate || realMachine.rate || 0;
        exchangeRate = realMachine.exchange_rate || 1.0;
        discountRate = realMachine.discount_rate || 1.0;
        currency = realMachine.currency || 'CNY';
      }

      return {
        id: machineId || Math.random(),
        name: machineName,
        type: item.machine_type,
        // 设置两种字段名格式以确保兼容性
        hourlyRate: hourlyRate,
        hourly_rate: hourlyRate,
        // 计算所需的费率和币种信息
        exchange_rate: exchangeRate,
        discount_rate: discountRate,
        currency: currency,
        // 确保包含EngineeringQuote.js期望的字段
        supplier: item.supplier ? { machine_type: { name: item.machine_type } } : null,
        machine_type: item.machine_type,
        model: machineName
      };
    });

    return config;
  };

  /**
   * 从报价项目中解析量产设备配置（FT/CP设备和辅助设备）
   */
  const parseMassProductionDevicesFromItems = (items, availableCardTypes = [], availableMachines = []) => {
    const config = {
      selectedTypes: [],
      ftData: {
        testMachine: null,
        handler: null,
        testMachineCards: [],
        handlerCards: []
      },
      cpData: {
        testMachine: null,
        prober: null,
        testMachineCards: [],
        proberCards: []
      },
      auxDevices: []
    };

    if (!items || items.length === 0) return config;

    // 解析每个报价项，从configuration JSON中提取设备信息
    items.forEach(item => {
      let configData = null;
      let deviceType = null;
      let testType = null;

      // 尝试解析 configuration（新格式）
      if (item.configuration) {
        try {
          configData = JSON.parse(item.configuration);
          deviceType = configData.device_type;
          testType = configData.test_type;
        } catch (e) {
          console.warn('无法解析configuration JSON:', item.configuration);
        }
      }

      // 如果没有 configuration，尝试从其他字段推断（旧格式）
      if (!deviceType) {
        deviceType = item.machine_type || '';
        // 从 item_description 推断测试类型
        if (item.item_description) {
          if (item.item_description.includes('FT')) testType = 'FT';
          else if (item.item_description.includes('CP')) testType = 'CP';
        }
      }

      // 解析FT测试机
      if (testType === 'FT' && deviceType === '测试机') {
        if (!config.selectedTypes.includes('ft')) {
          config.selectedTypes.push('ft');
        }

        const machineId = item.machine_id;
        const fullMachine = availableMachines.find(m => m.id === machineId);

        if (fullMachine) {
          config.ftData.testMachine = fullMachine;
        }

        // 解析板卡信息
        if (configData.cards && Array.isArray(configData.cards)) {
          config.ftData.testMachineCards = configData.cards.map(cardInfo => {
            const realCard = availableCardTypes.find(c => c.id === cardInfo.id);
            return {
              id: cardInfo.id,
              board_name: cardInfo.board_name || '',
              part_number: cardInfo.part_number || '',
              quantity: cardInfo.quantity || 1,
              unit_price: realCard ? realCard.unit_price : 0,
              machine_id: machineId
            };
          });
        }
      }

      // 解析FT分选机
      if (testType === 'FT' && deviceType === '分选机') {
        const machineId = item.machine_id;
        const fullMachine = availableMachines.find(m => m.id === machineId);

        if (fullMachine) {
          config.ftData.handler = fullMachine;
        }

        // 解析板卡信息
        if (configData.cards && Array.isArray(configData.cards)) {
          config.ftData.handlerCards = configData.cards.map(cardInfo => {
            const realCard = availableCardTypes.find(c => c.id === cardInfo.id);
            return {
              id: cardInfo.id,
              board_name: cardInfo.board_name || '',
              part_number: cardInfo.part_number || '',
              quantity: cardInfo.quantity || 1,
              unit_price: realCard ? realCard.unit_price : 0,
              machine_id: machineId
            };
          });
        }
      }

      // 解析CP测试机
      if (testType === 'CP' && deviceType === '测试机') {
        if (!config.selectedTypes.includes('cp')) {
          config.selectedTypes.push('cp');
        }

        const machineId = item.machine_id;
        const fullMachine = availableMachines.find(m => m.id === machineId);

        if (fullMachine) {
          config.cpData.testMachine = fullMachine;
        }

        // 解析板卡信息
        if (configData.cards && Array.isArray(configData.cards)) {
          config.cpData.testMachineCards = configData.cards.map(cardInfo => {
            const realCard = availableCardTypes.find(c => c.id === cardInfo.id);
            return {
              id: cardInfo.id,
              board_name: cardInfo.board_name || '',
              part_number: cardInfo.part_number || '',
              quantity: cardInfo.quantity || 1,
              unit_price: realCard ? realCard.unit_price : 0,
              machine_id: machineId
            };
          });
        }
      }

      // 解析CP探针台
      if (testType === 'CP' && deviceType === '探针台') {
        const machineId = item.machine_id;
        const fullMachine = availableMachines.find(m => m.id === machineId);

        if (fullMachine) {
          config.cpData.prober = fullMachine;
        }

        // 解析板卡信息
        if (configData.cards && Array.isArray(configData.cards)) {
          config.cpData.proberCards = configData.cards.map(cardInfo => {
            const realCard = availableCardTypes.find(c => c.id === cardInfo.id);
            return {
              id: cardInfo.id,
              board_name: cardInfo.board_name || '',
              part_number: cardInfo.part_number || '',
              quantity: cardInfo.quantity || 1,
              unit_price: realCard ? realCard.unit_price : 0,
              machine_id: machineId
            };
          });
        }
      }

      // 解析辅助设备
      if (deviceType === '辅助设备' || item.category_type === 'auxiliary_device' || item.category_type === 'auxiliary' || item.machine_type === '辅助设备') {
        const machineId = item.machine_id;

        if (machineId) {
          // 有 machine_id 的情况（新格式）
          const fullMachine = availableMachines.find(m => m.id === machineId);
          if (fullMachine && !config.auxDevices.find(d => d.id === machineId)) {
            config.auxDevices.push(fullMachine);
          }
        } else {
          // 旧格式：没有 machine_id，尝试通过名称匹配
          const deviceName = item.item_name || configData?.device_model || item.machine_model;
          if (deviceName) {
            const fullMachine = availableMachines.find(m => m.name === deviceName);
            if (fullMachine && !config.auxDevices.find(d => d.id === fullMachine.id)) {
              config.auxDevices.push(fullMachine);
            }
          }
        }
      }
    });

    return config;
  };

  /**
   * 解析工序报价的多工序配置
   * @param {Array} items - 报价项数组
   * @param {Array} availableCardTypes - 可用板卡类型
   * @param {Array} availableMachines - 可用设备（包含测试机、探针台、分选机）
   * @returns {Object} - 包含cpProcesses和ftProcesses数组的配置对象
   */
  const parseProcessQuoteDevicesFromItems = (items, availableCardTypes = [], availableMachines = []) => {
    const config = {
      selectedTypes: [],
      cpProcesses: [],
      ftProcesses: []
    };

    if (!items || items.length === 0) {
      return config;
    }

    // 解析每个报价项，从configuration JSON中提取工序信息
    items.forEach((item) => {
      let configData = null;
      let processType = null;

      // 尝试解析 configuration（新格式）
      if (item.configuration) {
        try {
          configData = JSON.parse(item.configuration);
          processType = configData.process_type;
        } catch (e) {
          console.warn('无法解析工序configuration JSON:', item.configuration);
        }
      }

      // 如果没有 configuration JSON，尝试从其他字段推断（旧格式）
      if (!processType && item.item_name) {
        // 旧格式1: "CP工序 - CP1测试" -> "CP1测试"
        let match = item.item_name.match(/(?:CP|FT)工序\s*-\s*(.+)/);
        if (match) {
          processType = match[1];
        } else {
          // 旧格式2: "CP-CP1测试" -> "CP1测试"
          match = item.item_name.match(/^(?:CP|FT)-(.+)/);
          if (match) {
            processType = match[1];
          }
        }

        // 如果是旧格式，尝试解析旧的configuration文本字段
        // 格式: "测试机:ETS-88, 探针台:AP3000, UPH:10"
        if (processType && item.configuration && typeof item.configuration === 'string') {
          try {
            const oldConfig = {};
            const parts = item.configuration.split(',').map(p => p.trim());
            parts.forEach(part => {
              const [key, value] = part.split(':').map(s => s.trim());
              if (key === '测试机') oldConfig.testMachine = value;
              else if (key === '探针台') oldConfig.prober = value;
              else if (key === '分选机') oldConfig.handler = value;
              else if (key === 'UPH') oldConfig.uph = parseInt(value) || 1000;
            });

            // 将旧格式转换为新格式结构
            configData = {
              process_type: processType,
              uph: oldConfig.uph || 1000
            };

            // 解析测试机
            if (oldConfig.testMachine) {
              const testMachine = availableMachines.find(m => m.name === oldConfig.testMachine);
              if (testMachine) {
                configData.test_machine = {
                  id: testMachine.id,
                  name: testMachine.name,
                  cards: []
                };
              } else {
                configData.test_machine = { id: null, name: oldConfig.testMachine, cards: [] };
              }
            }

            // 解析探针台/分选机
            if (oldConfig.prober) {
              const prober = availableMachines.find(m => m.name === oldConfig.prober);
              if (prober) {
                configData.prober = {
                  id: prober.id,
                  name: prober.name,
                  cards: []
                };
              } else {
                configData.prober = { id: null, name: oldConfig.prober, cards: [] };
              }
            }
            if (oldConfig.handler) {
              const handler = availableMachines.find(m => m.name === oldConfig.handler);
              if (handler) {
                configData.handler = {
                  id: handler.id,
                  name: handler.name,
                  cards: []
                };
              } else {
                configData.handler = { id: null, name: oldConfig.handler, cards: [] };
              }
            }
          } catch (e) {
            console.warn('无法解析旧格式configuration文本:', item.configuration, e);
          }
        }
      }

      if (!processType) {
        return; // 跳过无法识别的项
      }

      // 判断是CP还是FT工序（根据item_name判断，而不是processType）
      const itemName = item.item_name || '';
      const isCPProcess = itemName.includes('CP工序') || itemName.startsWith('CP-');
      const isFTProcess = itemName.includes('FT工序') || itemName.startsWith('FT-');

      if (isCPProcess) {
        if (!config.selectedTypes.includes('cp')) {
          config.selectedTypes.push('cp');
        }

        // 构建CP工序对象
        const process = {
          id: config.cpProcesses.length + 1,
          name: processType,
          testMachine: '',
          testMachineData: null,
          testMachineCardQuantities: {},
          prober: '',
          proberData: null,
          proberCardQuantities: {},
          uph: configData?.uph || 1000,
          unitCost: 0  // 编辑时人工成本重置为0，让用户重新输入
        };

        // 解析测试机信息
        if (configData?.test_machine) {
          const testMachineId = configData.test_machine.id;
          const fullMachine = availableMachines.find(m => m.id === testMachineId);
          if (fullMachine) {
            process.testMachine = fullMachine.name;
            process.testMachineData = fullMachine;
          } else {
            // 使用 machine_id 查找
            const machineById = availableMachines.find(m => m.id === item.machine_id);
            if (machineById) {
              process.testMachine = machineById.name;
              process.testMachineData = machineById;
            } else {
              // 最后使用名称匹配
              process.testMachine = configData.test_machine.name || item.machine_model || '';
            }
          }

          // 解析测试机板卡
          if (configData.test_machine.cards && Array.isArray(configData.test_machine.cards)) {
            configData.test_machine.cards.forEach(cardInfo => {
              process.testMachineCardQuantities[cardInfo.id] = cardInfo.quantity || 1;
            });
          }
        }

        // 解析探针台信息
        if (configData?.prober) {
          const proberId = configData.prober.id;
          const fullProber = availableMachines.find(m => m.id === proberId);
          if (fullProber) {
            process.prober = fullProber.name;
            process.proberData = fullProber;
          } else {
            process.prober = configData.prober.name || '';
          }

          // 解析探针台板卡
          if (configData.prober.cards && Array.isArray(configData.prober.cards)) {
            configData.prober.cards.forEach(cardInfo => {
              process.proberCardQuantities[cardInfo.id] = cardInfo.quantity || 1;
            });
          }
        }

        config.cpProcesses.push(process);
      } else if (isFTProcess) {
        if (!config.selectedTypes.includes('ft')) {
          config.selectedTypes.push('ft');
        }

        // 构建FT工序对象
        const process = {
          id: config.ftProcesses.length + 1,
          name: processType,
          testMachine: '',
          testMachineData: null,
          testMachineCardQuantities: {},
          handler: '',
          handlerData: null,
          handlerCardQuantities: {},
          uph: configData?.uph || 1000,
          unitCost: 0  // 编辑时人工成本重置为0，让用户重新输入
        };

        // 解析测试机信息
        if (configData?.test_machine) {
          const testMachineId = configData.test_machine.id;
          const fullMachine = availableMachines.find(m => m.id === testMachineId);
          if (fullMachine) {
            process.testMachine = fullMachine.name;
            process.testMachineData = fullMachine;
          } else {
            // 使用 machine_id 查找
            const machineById = availableMachines.find(m => m.id === item.machine_id);
            if (machineById) {
              process.testMachine = machineById.name;
              process.testMachineData = machineById;
            } else {
              // 最后使用名称匹配
              process.testMachine = configData.test_machine.name || item.machine_model || '';
            }
          }

          // 解析测试机板卡
          if (configData.test_machine.cards && Array.isArray(configData.test_machine.cards)) {
            configData.test_machine.cards.forEach(cardInfo => {
              process.testMachineCardQuantities[cardInfo.id] = cardInfo.quantity || 1;
            });
          }
        }

        // 解析分选机信息
        if (configData?.handler) {
          const handlerId = configData.handler.id;
          const fullHandler = availableMachines.find(m => m.id === handlerId);
          if (fullHandler) {
            process.handler = fullHandler.name;
            process.handlerData = fullHandler;
          } else {
            process.handler = configData.handler.name || '';
          }

          // 解析分选机板卡
          if (configData.handler.cards && Array.isArray(configData.handler.cards)) {
            configData.handler.cards.forEach(cardInfo => {
              process.handlerCardQuantities[cardInfo.id] = cardInfo.quantity || 1;
            });
          }
        }

        config.ftProcesses.push(process);
      }
    });

    return config;
  };

  /**
   * 从报价项目中解析工程人员配置
   */
  const parseEngineeringPersonnelFromItems = (items) => {
    const config = {
      personnel: []
    };

    if (!items || items.length === 0) return config;

    items.forEach(item => {
      const itemName = item.item_name || '';
      const itemDesc = item.item_description || '';
      const machineType = item.machine_type || '';

      // 解析人员相关项目
      if (itemName.includes('工程师') || itemName.includes('技术员') || itemName.includes('操作员') ||
          itemDesc.includes('工程师') || itemDesc.includes('技术员') || itemDesc.includes('操作员') ||
          machineType.includes('人员') || machineType.includes('工程师')) {

        let personnelType = '';
        if (itemName.includes('工程师') || itemDesc.includes('工程师')) {
          personnelType = '工程师';
        } else if (itemName.includes('技术员') || itemDesc.includes('技术员')) {
          personnelType = '技术员';
        } else if (itemName.includes('操作员') || itemDesc.includes('操作员')) {
          personnelType = '操作员';
        } else {
          personnelType = '工程师'; // 默认
        }

        config.personnel.push({
          type: personnelType,
          rate: item.unit_price || 0,
          selected: true
        });
      }
    });

    return config;
  };

  return {
    isEditMode,
    editingQuote,
    loading,
    convertQuoteToFormData
  };
};

export default useQuoteEditMode;