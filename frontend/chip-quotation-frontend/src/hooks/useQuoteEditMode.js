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

        // 优先使用已传递的editingQuote数据
        if (location.state?.editingQuote) {
          console.log('编辑模式：使用已传递的报价数据', location.state.editingQuote);
          setEditingQuote(location.state.editingQuote);
          setLoading(false);
        } else if (location.state?.quoteId) {
          // 如果没有完整数据但有ID，则从API获取
          setLoading(true);
          try {
            const quoteData = await QuoteApiService.getQuoteDetailById(location.state.quoteId);
            console.log('编辑模式：从API获取报价数据', quoteData);
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
          console.log('编辑模式：通过URL参数获取报价数据', quoteData);
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
   * @returns {Object} 前端表单数据格式
   */
  const convertQuoteToFormData = (quote, quoteType) => {
    if (!quote) return null;

    console.log('🔄 开始数据转换:', { quoteType, quote });

    // 检测数据格式：后端原始格式 vs 前端展示格式
    const isRawFormat = quote.customer_name !== undefined; // 后端格式有 customer_name
    const isDisplayFormat = quote.customer !== undefined && quote.customer_name === undefined; // 前端格式有 customer 但没有 customer_name

    console.log('🔍 数据格式检测:', { isRawFormat, isDisplayFormat });

    // 统一数据格式 - 将前端展示格式转换为后端原始格式（如果需要）
    let normalizedQuote = quote;
    if (isDisplayFormat) {
      console.log('🔄 转换前端展示格式为后端原始格式');
      normalizedQuote = convertDisplayFormatToRawFormat(quote);
      console.log('✅ 格式转换完成:', normalizedQuote);
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

    console.log('📋 基础表单数据:', baseFormData);

    // 根据报价类型进行特殊转换
    switch (quoteType) {
      case 'tooling':
        return convertToolingQuoteToFormData(normalizedQuote, baseFormData);
      case 'inquiry':
        return convertInquiryQuoteToFormData(normalizedQuote, baseFormData);
      case 'engineering':
        return convertEngineeringQuoteToFormData(normalizedQuote, baseFormData);
      default:
        return baseFormData;
    }
  };

  /**
   * 询价报价数据转换
   */
  const convertInquiryQuoteToFormData = (quote, baseFormData) => {
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
   * 工程机时报价数据转换
   */
  const convertEngineeringQuoteToFormData = (quote, baseFormData) => {
    // 工程机时报价的数据结构较复杂，需要解析多种设备类型和人员配置
    // 这里提供基础转换，具体实现需要根据实际数据结构调整

    return {
      ...baseFormData,
      projectInfo: {
        ...baseFormData.projectInfo,
        chipPackage: extractChipPackageFromDescription(quote.description),
        testType: 'engineering',
        urgency: 'normal'
      },
      // TODO: 根据实际需求实现工程机时报价的详细转换逻辑
      // 包括：设备选择、板卡配置、人员配置、辅助设备等
      remarks: extractRemarksFromNotes(quote.notes)
    };
  };

  /**
   * 工装夹具报价数据转换
   */
  const convertToolingQuoteToFormData = (quote, baseFormData) => {
    console.log('🔧 开始工装夹具报价数据转换');
    console.log('🔧 输入报价数据:', quote);
    console.log('🔧 基础表单数据:', baseFormData);

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

    console.log('🔧 报价项目数组:', quote.items);
    console.log('🔧 项目数量:', quote.items?.length || 0);

    // 解析报价项目
    quote.items?.forEach((item, index) => {
      console.log(`🔧 处理项目 ${index + 1}:`, item);

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
        console.log(`   ✅ 添加到工装项目:`, toolingItems[toolingItems.length - 1]);
      }
      // 工程费用
      else if (itemDesc.includes('工程开发服务费') ||
               ['测试程序开发', '夹具设计', '测试验证', '文档编制'].includes(itemName)) {
        const feeKey = mapEngineeringFeeNameToKey(itemName);
        if (feeKey && engineeringFees.hasOwnProperty(feeKey)) {
          engineeringFees[feeKey] = item.unit_price || 0;
          console.log(`   ✅ 添加到工程费用: ${feeKey} = ${item.unit_price}`);
        }
      }
      // 量产准备费用
      else if (itemDesc.includes('量产准备服务费') ||
               ['设备调试费', '校准费', '首件检验费'].includes(itemName)) {
        const setupKey = mapProductionSetupNameToKey(itemName);
        if (setupKey && productionSetup.hasOwnProperty(setupKey)) {
          productionSetup[setupKey] = item.unit_price || 0;
          console.log(`   ✅ 添加到量产准备: ${setupKey} = ${item.unit_price}`);
        }
      } else {
        console.log(`   ⚠️ 未识别的项目类型: ${itemName} - ${itemDesc}`);
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

    console.log('🔧 工装夹具最终转换结果:', result);
    console.log('🔧 工装项目数量:', result.toolingItems.length);
    console.log('🔧 工程费用:', result.engineeringFees);
    console.log('🔧 量产准备:', result.productionSetup);

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
    const match = description.match(/项目：([^，,]+)/);
    return match ? match[1] : '';
  };

  /**
   * 从描述中提取芯片封装
   */
  const extractChipPackageFromDescription = (description) => {
    if (!description) return '';
    const match = description.match(/芯片封装：([^，,]+)/);
    return match ? match[1] : '';
  };

  /**
   * 从描述中提取测试类型
   */
  const extractTestTypeFromDescription = (description) => {
    if (!description) return '';
    const match = description.match(/测试类型：([^，,]+)/);
    return match ? match[1] : '';
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

    const firstItem = items[0];
    if (firstItem.item_name?.includes('CP')) return 'CP';
    if (firstItem.item_name?.includes('FT')) return 'FT';
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

  return {
    isEditMode,
    editingQuote,
    loading,
    convertQuoteToFormData
  };
};

export default useQuoteEditMode;