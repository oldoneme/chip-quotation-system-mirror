import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Select, Table, Tabs, Spin, Alert, Checkbox, Button, Card, InputNumber, message, Divider } from 'antd';
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
    // 检查是否从结果页返回
    if (state && state.fromResultPage) {
      // 如果从结果页返回，保持在第二步并恢复之前的选择状态
      setCurrentStep(1);
      
      // 恢复之前的选择状态
      if (state.quoteData) {
        const { selectedTypes, ftData, cpData, selectedAuxDevices } = state.quoteData;
        setSelectedTypes(selectedTypes || ['ft', 'cp']);
        setFtData(ftData || { 
          testMachine: null, 
          handler: null, 
          testMachineCards: [], 
          handlerCards: [] 
        });
        setCpData(cpData || { 
          testMachine: null, 
          prober: null, 
          testMachineCards: [], 
          proberCards: [] 
        });
        setSelectedAuxDevices(selectedAuxDevices || []);
      }
      
      // 确保数据已加载
      if (machines.length === 0) {
        fetchData();
      }
    } else {
      // 检查是否有保存的状态
      const savedState = sessionStorage.getItem('massProductionQuoteState');
      if (savedState) {
        const parsedState = JSON.parse(savedState);
        // 恢复状态
        setCurrentStep(parsedState.currentStep || 0);
        setSelectedTypes(parsedState.selectedTypes || ['ft', 'cp']);
        setFtData(parsedState.ftData || { 
          testMachine: null, 
          handler: null, 
          testMachineCards: [], 
          handlerCards: [] 
        });
        setCpData(parsedState.cpData || { 
          testMachine: null, 
          prober: null, 
          testMachineCards: [], 
          proberCards: [] 
        });
        setSelectedAuxDevices(parsedState.selectedAuxDevices || []);
        setPersistedCardQuantities(parsedState.persistedCardQuantities || {});
      }
      
      // 正常初始化
      fetchData();
    }
  }, [state]);

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
        probers: auxDevicesResponse.filter(device => device.type === 'prober')
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
      }
      
      // 辅助设备应该是除了测试机、分选机、探针台之外的其他机器类型
      const auxMachines = machinesResponse.filter(machine => {
        const machineTypeName = getMachineTypeName(machine);
        const isAuxMachine = machineTypeName !== '测试机' && 
                            machineTypeName !== '分选机' && 
                            machineTypeName !== '探针台';
        return isAuxMachine;
      });
      
      setAuxDevices({
        handlers: auxMachines.filter(machine => getMachineTypeName(machine) === '分选机'),
        probers: auxMachines.filter(machine => getMachineTypeName(machine) === '探针台'),
        others: auxMachines.filter(machine => {
          const machineTypeName = getMachineTypeName(machine);
          return machineTypeName !== '分选机' && machineTypeName !== '探针台';
        })
      });
      
      console.log('数据加载完成');
    } catch (error) {
      console.error('获取数据时出错:', error);
      setError(error.message);
      message.error('获取数据失败: ' + error.message);
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
          return sum + ((card.unit_price / 10000) * data.testMachine.exchange_rate * data.testMachine.discount_rate * card.quantity);
        }, 0);
      }
      
      // 计算分选机板卡费用
      if (data.handler && data.handlerCards.length > 0) {
        total += data.handlerCards.reduce((sum, card) => {
          return sum + ((card.unit_price / 10000) * data.handler.exchange_rate * data.handler.discount_rate * card.quantity);
        }, 0);
      }
    } else if (type === 'cp') {
      // 计算测试机板卡费用
      if (data.testMachine && data.testMachineCards.length > 0) {
        total += data.testMachineCards.reduce((sum, card) => {
          return sum + ((card.unit_price / 10000) * data.testMachine.exchange_rate * data.testMachine.discount_rate * card.quantity);
        }, 0);
      }
      
      // 计算探针台板卡费用
      if (data.prober && data.proberCards.length > 0) {
        total += data.proberCards.reduce((sum, card) => {
          return sum + ((card.unit_price / 10000) * data.prober.exchange_rate * data.prober.discount_rate * card.quantity);
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
      return total + (device.hourly_rate || 0);
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
      persistedCardQuantities
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
        auxDeviceFee
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
      persistedCardQuantities
    };
    sessionStorage.setItem('massProductionQuoteState', JSON.stringify(currentState));
    
    // Navigate to previous step
    setCurrentStep(prevStepValue);
  };
  
  const resetQuote = () => {
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
    setCurrentStep(0);
    
    // 清除sessionStorage中的状态
    sessionStorage.removeItem('massProductionQuoteState');
  };
  
  const handleAuxDeviceSelect = (selectedRowKeys, selectedRows) => {
    setSelectedAuxDevices(selectedRows);
  };

  // 表格列定义
  const cardColumns = (type, machineType) => [
    { title: 'Part Number', dataIndex: 'part_number' },
    { title: 'Board Name', dataIndex: 'board_name' },
    { 
      title: 'Unit Price', 
      dataIndex: 'unit_price',
      render: (value) => formatNumber(value || 0)
    },
    { 
      title: 'Quantity', 
      render: (_, record) => (
        <InputNumber 
          min={1} 
          defaultValue={1} 
          onChange={(value) => handleCardQuantityChange(type, machineType, record.id, value)}
        />
      ) 
    }
  ];
  
  // 辅助设备表格列定义
  const auxDeviceColumns = [
    { title: '设备名称', dataIndex: 'name' },
    { title: '描述', dataIndex: 'description' },
    { 
      title: '小时费率', 
      dataIndex: 'hourly_rate',
      render: (value) => `¥${formatNumber(value || 0)}/小时`
    }
  ];


  if (loading) {
    return <Spin tip="加载数据中..." />;
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
      
      {/* 步骤指示器 */}
      <div style={{ marginBottom: 20 }}>
        <div>步骤 {currentStep + 1} of 2</div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ 
            width: 20, 
            height: 20, 
            borderRadius: '50%', 
            backgroundColor: currentStep >= 0 ? '#1890ff' : '#f0f0f0',
            marginRight: 10
          }}></div>
          <div style={{ 
            width: 60, 
            height: 4, 
            backgroundColor: currentStep >= 1 ? '#1890ff' : '#f0f0f0',
            marginRight: 10
          }}></div>
          <div style={{ 
            width: 20, 
            height: 20, 
            borderRadius: '50%', 
            backgroundColor: currentStep >= 1 ? '#1890ff' : '#f0f0f0'
          }}></div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', width: 120 }}>
          <span>机器选择</span>
          <span>辅助设备</span>
        </div>
      </div>

      {/* 第一步：机器选择 */}
      {currentStep === 0 && (
        <>
          {/* 选择FT或CP */}
          <div style={{ marginBottom: 20 }}>
            <Checkbox.Group value={selectedTypes} onChange={handleProductionTypeChange}>
              <Checkbox value="ft">FT</Checkbox>
              <Checkbox value="cp">CP</Checkbox>
            </Checkbox.Group>
          </div>

          {selectedTypes.includes('ft') && (
            <Card title="FT Configuration" style={{ marginBottom: 20 }}>
              {/* 测试机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择测试机</h4>
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
              </div>

              {/* 测试机板卡选择 */}
              {ftData.testMachine && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择测试机板卡</h4>
                  <Table 
                    dataSource={cardTypes.filter(card => card.machine_id === ftData.testMachine.id)}
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
                </div>
              )}
              
              {/* 分选机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择分选机</h4>
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
              </div>

              {/* 分选机板卡选择 */}
              {ftData.handler && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择分选机板卡</h4>
                  <Table 
                    dataSource={cardTypes.filter(card => card.machine_id === ftData.handler.id)}
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
                </div>
              )}
              
              <p><strong>FT测试机机时费: ¥{formatNumber(ftHourlyFee)}</strong></p>
            </Card>
          )}

          {selectedTypes.includes('cp') && (
            <Card title="CP Configuration" style={{ marginBottom: 20 }}>
              {/* 测试机选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择测试机</h4>
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
              </div>
              
              {/* 测试机板卡选择 */}
              {cpData.testMachine && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择测试机板卡</h4>
                  <Table 
                    dataSource={cardTypes.filter(card => card.machine_id === cpData.testMachine.id)}
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
                </div>
              )}
              
              {/* 探针台选择 */}
              <div style={{ marginBottom: 15 }}>
                <h4>选择探针台</h4>
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
              </div>
              
              {/* 探针台板卡选择 */}
              {cpData.prober && (
                <div style={{ marginBottom: 15 }}>
                  <h4>选择探针台板卡</h4>
                  <Table 
                    dataSource={cardTypes.filter(card => card.machine_id === cpData.prober.id)}
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
                </div>
              )}
              
              <p><strong>CP小时费: ¥{formatNumber(cpHourlyFee)}</strong></p>
            </Card>
          )}
        </>
      )}

      {/* 第二步：辅助设备选择 */}
      {currentStep === 1 && (
        <div>
          <h2 className="section-title">辅助设备选择</h2>
          
          <Card title="辅助设备选择" style={{ marginBottom: 20 }}>
            <Table 
              dataSource={auxDevices.others || []}
              rowKey="id"
              rowSelection={{
                type: 'checkbox',
                onChange: handleAuxDeviceSelect,
                selectedRowKeys: selectedAuxDevices.map(device => device.id)
              }}
              columns={auxDeviceColumns}
              pagination={false}
            />
            <p style={{ marginTop: 10 }}><strong>辅助设备机时费: ¥{formatNumber(calculateAuxDeviceFee())}</strong></p>
          </Card>
          
          <Card title="费用明细" style={{ marginBottom: 20 }}>
            <div style={{ padding: '20px 0' }}>
              {selectedTypes.includes('ft') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span>FT小时费:</span>
                  <span>¥{formatNumber(ftHourlyFee)}</span>
                </div>
              )}
              {selectedTypes.includes('cp') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span>CP小时费:</span>
                  <span>¥{formatNumber(cpHourlyFee)}</span>
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
                      <span>{device.name}</span>
                      <span>¥{formatNumber(device.hourly_rate || 0)}/小时</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* 导航按钮 */}
      <div style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Button 
            onClick={handlePrevStep} 
            disabled={currentStep === 0}
          >
            返回上一步
          </Button>
          <Button 
            onClick={resetQuote}
            style={{ marginLeft: 10 }}
          >
            重置报价
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
            onClick={handleNextStep}
          >
            {currentStep === 1 ? '确认完成' : '继续下一步'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default MassProductionQuote;