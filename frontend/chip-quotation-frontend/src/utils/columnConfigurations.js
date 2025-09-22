/**
 * 报价明细列配置文件
 * 为所有报价类型提供统一的列配置，确保前端显示和PDF生成保持一致
 */

// 获取指定报价类型的列配置
export const getColumnConfigurations = (quoteType, items = []) => {
  const configs = {
    // 1. 询价报价 - 通用机时报价
    '询价报价': {
      default: [
        { title: '测试类型', dataIndex: 'itemName', key: 'itemName' },
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '小时费率', dataIndex: 'unitPrice', key: 'unitPrice', format: 'hourlyRate' }
      ]
    },

    // 2. 工装夹具报价 - 分类显示
    '工装夹具报价': {
      tooling: [  // 工装夹具清单
        { title: '类别', dataIndex: 'category', key: 'category', defaultValue: '工装夹具' },
        { title: '类型', dataIndex: 'itemName', key: 'itemName' },
        { title: '单价', dataIndex: 'unitPrice', key: 'unitPrice', format: 'currency' },
        { title: '数量', dataIndex: 'quantity', key: 'quantity' },
        { title: '小计', dataIndex: 'totalPrice', key: 'totalPrice', format: 'currency' }
      ],
      engineering: [  // 工程费用
        { title: '项目名称', dataIndex: 'itemName', key: 'itemName' },
        { title: '费用', dataIndex: 'totalPrice', key: 'totalPrice', format: 'currency' }
      ],
      production: [  // 量产准备费用
        { title: '项目名称', dataIndex: 'itemName', key: 'itemName' },
        { title: '费用', dataIndex: 'totalPrice', key: 'totalPrice', format: 'currency' }
      ]
    },

    // 3. 工程机时报价 - 分类显示
    '工程机时报价': {
      machine: [  // 机器设备
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '小时费率', dataIndex: 'unitPrice', key: 'unitPrice', format: 'hourlyRate' }
      ],
      personnel: [  // 人员费用
        { title: '人员类别', dataIndex: 'itemName', key: 'itemName' },
        { title: '小时费率', dataIndex: 'unitPrice', key: 'unitPrice', format: 'hourlyRate' }
      ]
    },

    // 4. 量产机时报价 - 分类显示
    '量产机时报价': {
      ft: [  // FT测试设备
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '小时费率', dataIndex: 'unitPrice', key: 'unitPrice', format: 'hourlyRate' }
      ],
      auxiliary: [  // 辅助设备
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '小时费率', dataIndex: 'unitPrice', key: 'unitPrice', format: 'hourlyRate' }
      ]
    },

    // 5. 量产工序报价 - 工序分类
    '量产工序报价': {
      cp: [  // CP工序
        { title: '工序名称', dataIndex: 'itemName', key: 'itemName' },
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '机时费率', dataIndex: 'hourlyRate', key: 'hourlyRate', format: 'hourlyRateText' },
        { title: 'UPH', dataIndex: 'uph', key: 'uph' },
        { title: '单颗报价', dataIndex: 'unitPrice', key: 'unitPrice', format: 'unitPrice4' }
      ],
      ft: [  // FT工序
        { title: '工序名称', dataIndex: 'itemName', key: 'itemName' },
        { title: '设备类型', dataIndex: 'machineType', key: 'machineType' },
        { title: '设备型号', dataIndex: 'machine', key: 'machine' },
        { title: '机时费率', dataIndex: 'hourlyRate', key: 'hourlyRate', format: 'hourlyRateText' },
        { title: 'UPH', dataIndex: 'uph', key: 'uph' },
        { title: '单颗报价', dataIndex: 'unitPrice', key: 'unitPrice', format: 'unitPrice4' }
      ]
    },

    // 6. 综合报价 - 通用显示
    '综合报价': {
      default: [
        { title: '类别', dataIndex: 'category', key: 'category' },
        { title: '型号', dataIndex: 'itemName', key: 'itemName' },
        { title: '描述', dataIndex: 'itemDescription', key: 'itemDescription' },
        { title: '数量', dataIndex: 'quantity', key: 'quantity' },
        { title: '单价', dataIndex: 'unitPrice', key: 'unitPrice', format: 'currency' },
        { title: '小计', dataIndex: 'totalPrice', key: 'totalPrice', format: 'currency' }
      ]
    }
  };

  return configs[quoteType] || configs['综合报价'];
};

// 格式化显示值
export const formatColumnValue = (value, format, item = {}) => {
  if (!value && value !== 0) return '-';

  switch (format) {
    case 'currency':
      return `¥${Number(value).toFixed(2)}`;
    case 'hourlyRate':
      return `¥${Number(value).toLocaleString()}/小时`;
    case 'hourlyRateText':
      return value || '¥0.00/小时';
    case 'unitPrice4':
      return `¥${Number(value).toFixed(4)}`;
    default:
      return value;
  }
};

// 获取列数据值（处理特殊逻辑）
export const getColumnValue = (item, column) => {
  const { dataIndex, key, defaultValue } = column;

  // 处理默认值
  if (defaultValue) {
    return defaultValue;
  }

  // 处理特殊数据索引
  switch (dataIndex) {
    case 'machine':
      return item.machine || item.machineModel || item.itemName?.split('-')[1] || '-';
    case 'category':
      // 根据项目类型自动判断类别
      if (item.unit === '件') return '工装夹具';
      if (item.machineType === '人员') return '人员';
      return item.machineType || '其他';
    default:
      return item[dataIndex] || '-';
  }
};

// 分类数据（与前端显示逻辑保持一致）
export const categorizeItems = (items, quoteType) => {
  if (!items || !Array.isArray(items)) return {};

  switch (quoteType) {
    case '工装夹具报价':
      return {
        tooling: items.filter(item =>
          item.unit === '件' && !item.itemName?.includes('程序') &&
          !item.itemName?.includes('调试') && !item.itemName?.includes('设计')
        ),
        engineering: items.filter(item =>
          item.unit === '项' && (item.itemName?.includes('测试程序') ||
          item.itemName?.includes('程序开发') || item.itemName?.includes('夹具设计') ||
          item.itemName?.includes('测试验证') || item.itemName?.includes('文档') ||
          item.itemName?.includes('设计'))
        ),
        production: items.filter(item =>
          item.unit === '项' && (item.itemName?.includes('调试') ||
          item.itemName?.includes('校准') || item.itemName?.includes('检验') ||
          item.itemName?.includes('设备调试') || item.itemName?.includes('调试费'))
        )
      };

    case '工程机时报价':
      return {
        machine: items.filter(item =>
          item.machineType && item.machineType !== '人员' &&
          (!item.itemName || !['工程师', '技术员'].includes(item.itemName))
        ),
        personnel: items.filter(item =>
          item.machineType === '人员' ||
          (item.itemName && ['工程师', '技术员'].includes(item.itemName))
        )
      };

    case '量产机时报价':
      return {
        ft: items.filter(item => {
          const name = item.itemName || '';
          const description = item.itemDescription || '';
          return name.includes('FT') || description.includes('FT');
        }),
        auxiliary: items.filter(item =>
          item.machineType === '辅助设备' ||
          (!item.itemName?.includes('FT') && !item.itemName?.includes('CP') &&
           item.machineType && item.machineType !== '测试机' &&
           item.machineType !== '分选机' && item.machineType !== '探针台')
        )
      };

    case '量产工序报价':
      return {
        cp: items.filter(item => {
          const name = item.itemName || '';
          const description = item.itemDescription || '';
          const machineType = item.machineType || '';
          return name.includes('CP') || description.includes('CP') || machineType.includes('CP');
        }),
        ft: items.filter(item => {
          const name = item.itemName || '';
          const description = item.itemDescription || '';
          const machineType = item.machineType || '';
          return name.includes('FT') || description.includes('FT') || machineType.includes('FT');
        })
      };

    default:
      return { default: items };
  }
};

// 导出给PDF使用的列配置
export const getColumnsForPDF = (quoteType, items = []) => {
  const columnConfigs = getColumnConfigurations(quoteType, items);
  const categorizedItems = categorizeItems(items, quoteType);

  const result = {};

  // 为每个分类生成列配置
  Object.keys(columnConfigs).forEach(category => {
    if (categorizedItems[category] && categorizedItems[category].length > 0) {
      result[category] = {
        columns: columnConfigs[category].map(col => col.title),
        items: categorizedItems[category]
      };
    }
  });

  return result;
};