import React, { useState, useEffect } from 'react';
import { 
  message, 
  Card, 
  Row, 
  Col, 
  Form, 
  Input, 
  InputNumber, 
  Button, 
  Modal, 
  Table,
  Tabs,
  List,
  Dropdown,
  Menu,
  Space,
  Select
} from 'antd';
import ConfirmDialog from '../components/ConfirmDialog';
import { 
  EditOutlined, 
  DeleteOutlined, 
  PlusOutlined,
  MoreOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { formatNumber } from '../utils';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import '../App.css';



const HierarchicalDatabaseManagement = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [hierarchicalData, setHierarchicalData] = useState([]);
  const [activeMachineTypeId, setActiveMachineTypeId] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [dataVersion, setDataVersion] = useState(0); // 用于强制重新渲染的版本号
  
  // Modal states
  const [machineTypeModalVisible, setMachineTypeModalVisible] = useState(false);
  const [supplierModalVisible, setSupplierModalVisible] = useState(false);
  const [machineModalVisible, setMachineModalVisible] = useState(false);
  const [cardConfigModalVisible, setCardConfigModalVisible] = useState(false);
  const [addMachineTypeModalVisible, setAddMachineTypeModalVisible] = useState(false);
  
  // Editing states
  const [editingMachineType, setEditingMachineType] = useState(null);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [editingMachine, setEditingMachine] = useState(null);
  const [editingCardConfig, setEditingCardConfig] = useState(null);
  
  // Forms
  const [machineTypeForm] = Form.useForm();
  const [addMachineTypeForm] = Form.useForm();
  const [supplierForm] = Form.useForm();
  const [machineForm] = Form.useForm();
  const [cardConfigForm] = Form.useForm();
  
  // 获取所有数据
  useEffect(() => {
    fetchData();
  }, [dataVersion]); // 依赖于dataVersion，当它变化时重新获取数据

  const fetchData = async () => {
    try {
      // 获取层级数据
      const hierarchicalDataResponse = await api.get('/hierarchical/machine-types');
      
      // 强制更新状态
      setHierarchicalData(prevData => {
        return [...hierarchicalDataResponse.data]; // 创建新数组确保状态更新
      });
      
      // 保持当前选中状态
      if (activeMachineTypeId && selectedSupplier && selectedMachine) {
        // 等待状态更新完成后重新设置选中项
        setTimeout(() => {
          // 查找并重新设置选中的机器类型、供应商和机器
          let foundMachineType = null;
          let foundSupplier = null;
          let foundMachine = null;
          
          for (const machineType of hierarchicalDataResponse.data) {
            if (machineType.id === activeMachineTypeId) {
              foundMachineType = machineType;
              for (const supplier of machineType.suppliers) {
                if (supplier.id === selectedSupplier.id) {
                  foundSupplier = supplier;
                  for (const machine of supplier.machines) {
                    if (machine.id === selectedMachine.id) {
                      foundMachine = machine;
                      break;
                    }
                  }
                  break;
                }
              }
              break;
            }
          }
          
          // 如果找到了对应的项，则更新选中状态
          if (foundMachineType) {
            setActiveMachineTypeId(foundMachineType.id);
          }
          if (foundSupplier) {
            setSelectedSupplier(foundSupplier);
          }
          if (foundMachine) {
            setSelectedMachine(foundMachine);
          }
        }, 100);
      }
      
    } catch (error) {
      console.error('获取层级数据失败:', error);
      message.error('获取数据失败: ' + error.message);
    }
  };

  // 强制刷新数据的函数
  const forceRefreshData = () => {
    setDataVersion(prev => prev + 1); // 增加版本号以触发重新获取数据
  };

  // 获取当前选中的机器类型数据
  const getCurrentMachineType = () => {
    if (!activeMachineTypeId) return null;
    return hierarchicalData.find(type => type.id === activeMachineTypeId) || null;
  };

  // 处理机器类型切换
  const handleMachineTypeChange = (machineTypeId) => {
    setActiveMachineTypeId(machineTypeId);
    setSelectedSupplier(null);
    setSelectedMachine(null);
  };

  // 处理添加机器类型
  const handleAddMachineType = () => {
    setEditingMachineType(null);
    addMachineTypeForm.resetFields();
    setAddMachineTypeModalVisible(true);
  };

  const handleSaveNewMachineType = async () => {
    try {
      const values = await addMachineTypeForm.validateFields();
      const response = await api.post('/machine-types/', values);
      message.success('创建成功');
      setAddMachineTypeModalVisible(false);
      forceRefreshData(); // 使用新的强制刷新机制
    } catch (error) {
      console.error('创建机器类型失败:', error);
      message.error('保存失败: ' + error.message);
    }
  };

  // 供应商相关操作
  const handleAddSupplier = () => {
    setEditingSupplier(null);
    supplierForm.resetFields();
    setSupplierModalVisible(true);
  };

  const handleEditSupplier = (record) => {
    setEditingSupplier(record);
    supplierForm.setFieldsValue(record);
    setSupplierModalVisible(true);
  };

  const handleSaveSupplier = async () => {
    try {
      const values = await supplierForm.validateFields();
      let response;
      if (editingSupplier) {
        response = await api.put(`/suppliers/${editingSupplier.id}`, values);
        message.success('更新成功');
      } else {
        // 如果是在机器类型下添加供应商，自动设置machine_type_id
        if (activeMachineTypeId) {
          values.machine_type_id = activeMachineTypeId;
        }
        response = await api.post('/suppliers/', values);
        message.success('创建成功');
      }
      setSupplierModalVisible(false);
      forceRefreshData(); // 使用新的强制刷新机制
    } catch (error) {
      console.error('保存供应商失败:', error);
      message.error('保存失败: ' + error.message);
    }
  };

  // 机器相关操作
  const handleAddMachine = () => {
    setEditingMachine(null);
    machineForm.resetFields();
    setMachineModalVisible(true);
  };

  const handleEditMachine = (record) => {
    setEditingMachine(record);
    // 设置表单字段值
    machineForm.setFieldsValue({
      ...record,
      exchange_rate: record.exchange_rate || (record.currency === 'USD' ? 7 : 1)
    });
    setMachineModalVisible(true);
  };

  const handleSaveMachine = async () => {
    try {
      const values = await machineForm.validateFields();
      let response;
      if (editingMachine) {
        // 编辑机器时，确保汇率值正确设置
        if (values.currency === 'RMB') {
          values.exchange_rate = 1; // RMB时汇率固定为1
        } else if (values.currency === 'USD' && (!values.exchange_rate || values.exchange_rate <= 0)) {
          values.exchange_rate = 7; // USD时如果没有有效汇率，则设为默认值7
        }
        
        response = await api.put(`/machines/${editingMachine.id}`, values);
        message.success('更新成功');
      } else {
        // 添加机器时设置默认汇率
        if (values.currency === 'RMB') {
          values.exchange_rate = 1;
        } else if (values.currency === 'USD' && (!values.exchange_rate || values.exchange_rate <= 0)) {
          values.exchange_rate = 7;
        }
        
        // 如果是在供应商下添加机器，自动设置supplier_id
        if (selectedSupplier) {
          values.supplier_id = selectedSupplier.id;
        }
        response = await api.post('/machines/', values);
        message.success('创建成功');
      }
      setMachineModalVisible(false);
      
      // 立即刷新数据
      forceRefreshData();
    } catch (error) {
      console.error('保存机器失败:', error);
      message.error('保存失败: ' + error.message);
    }
  };

  // 板卡配置相关操作
  const handleAddCardConfig = () => {
    setEditingCardConfig(null);
    cardConfigForm.resetFields();
    setCardConfigModalVisible(true);
  };

  const handleEditCardConfig = (record) => {
    setEditingCardConfig(record);
    cardConfigForm.setFieldsValue(record);
    setCardConfigModalVisible(true);
  };

  const handleSaveCardConfig = async () => {
    try {
      const values = await cardConfigForm.validateFields();
      let response;
      if (editingCardConfig) {
        response = await api.put(`/card-configs/${editingCardConfig.id}`, values);
        message.success('更新成功');
      } else {
        // 如果是在机器下添加板卡配置，自动设置machine_id
        if (selectedMachine) {
          values.machine_id = selectedMachine.id;
        }
        response = await api.post('/card-configs/', values);
        message.success('创建成功');
      }
      setCardConfigModalVisible(false);
      forceRefreshData(); // 使用新的强制刷新机制
    } catch (error) {
      console.error('保存板卡配置失败:', error);
      message.error('保存失败: ' + error.message);
    }
  };

  // 删除操作
  const handleDeleteMachineType = async (id) => {
    
    ConfirmDialog.showDeleteConfirm({
      title: '确认删除机器类型',
      content: '您确定要删除这个机器类型吗？删除后将同时删除相关的供应商、测试机和板卡配置数据，此操作不可恢复。',
      onOk: async () => {
        try {
          const response = await api.delete(`/machine-types/${id}`);
          message.success('删除成功');
          
          // 如果删除的是当前选中的机器类型，需要重新设置选中项
          if (id === activeMachineTypeId) {
            // 设置为第一个可用的机器类型，如果没有则清空选中
            setTimeout(() => {
              if (hierarchicalData.length > 1) {
                const firstAvailableMachineType = hierarchicalData.find(type => type.id !== id);
                if (firstAvailableMachineType) {
                  setActiveMachineTypeId(firstAvailableMachineType.id);
                }
              } else {
                setActiveMachineTypeId(null);
                setSelectedSupplier(null);
                setSelectedMachine(null);
              }
            }, 100);
          }
          
          forceRefreshData(); // 使用新的强制刷新机制
        } catch (error) {
          console.error('删除机器类型失败:', error);
          message.error('删除失败: ' + error.message);
        }
      },
      onCancel: () => {
      }
    });
  };

  const handleDeleteSupplier = async (id) => {
    
    ConfirmDialog.showDeleteConfirm({
      title: '确认删除供应商',
      content: '您确定要删除这个供应商吗？删除后将同时删除相关的测试机和板卡配置数据，此操作不可恢复。',
      onOk: async () => {
        try {
          const response = await api.delete(`/suppliers/${id}`);
          message.success('删除成功');
          forceRefreshData(); // 使用新的强制刷新机制
        } catch (error) {
          console.error('删除供应商失败:', error);
          message.error('删除失败: ' + error.message);
        }
      },
      onCancel: () => {
      }
    });
  };

  const handleDeleteMachine = async (id) => {
    
    ConfirmDialog.showDeleteConfirm({
      title: '确认删除测试机',
      content: '您确定要删除这台测试机吗？删除后将同时删除相关的板卡配置数据，此操作不可恢复。',
      onOk: async () => {
        try {
          const response = await api.delete(`/machines/${id}`);
          message.success('删除成功');
          forceRefreshData(); // 使用新的强制刷新机制
        } catch (error) {
          console.error('删除测试机失败:', error);
          message.error('删除失败: ' + error.message);
        }
      },
      onCancel: () => {
      }
    });
  };

  const handleDeleteCardConfig = async (id) => {
    
    ConfirmDialog.showDeleteConfirm({
      title: '确认删除板卡配置',
      content: '您确定要删除这个板卡配置吗？此操作不可恢复。',
      onOk: async () => {
        try {
          const response = await api.delete(`/card-configs/${id}`);
          message.success('删除成功');
          forceRefreshData(); // 使用新的强制刷新机制
        } catch (error) {
          console.error('删除板卡配置失败:', error);
          message.error('删除失败: ' + error.message);
        }
      },
      onCancel: () => {
      }
    });
  };

  // 表格列定义
  const cardConfigColumns = [
    {
      title: 'PartNumber',
      dataIndex: 'part_number',
      key: 'part_number',
    },
    {
      title: 'Board Name',
      dataIndex: 'board_name',
      key: 'board_name',
    },
    {
      title: selectedMachine?.currency ? `Unit Price (${selectedMachine.currency})` : 'Unit Price (RMB)',
      dataIndex: 'unit_price',
      key: 'unit_price',
      render: (text) => formatNumber(parseFloat(text)),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEditCardConfig(record)}
          />
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => handleDeleteCardConfig(record.id)}
          />
        </Space>
      ),
    },
  ];

  // 供应商操作菜单
  const supplierActionMenu = (supplier) => (
    <Menu>
      <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => handleEditSupplier(supplier)}>
        编辑
      </Menu.Item>
      <Menu.Item 
        key="delete" 
        icon={<DeleteOutlined />} 
        danger
        onClick={() => handleDeleteSupplier(supplier.id)}
      >
        删除
      </Menu.Item>
    </Menu>
  );

  // 机器操作菜单
  const machineActionMenu = (machine) => (
    <Menu>
      <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => handleEditMachine(machine)}>
        编辑
      </Menu.Item>
      <Menu.Item 
        key="delete" 
        icon={<DeleteOutlined />} 
        danger
        onClick={() => handleDeleteMachine(machine.id)}
      >
        删除
      </Menu.Item>
    </Menu>
  );

  // 添加千位分隔符格式化函数
  const formatNumber = (num) => {
    return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  };

  const currentMachineType = getCurrentMachineType();

  // 权限检查
  if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h2>权限不足</h2>
        <p>抱歉，您没有访问数据库管理的权限。只有管理员和超级管理员可以访问此功能。</p>
        <p>当前用户角色: {user?.role || '未知'}</p>
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    );
  }

  return (
    <div className="hierarchical-database-management">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1>测试机配置数据管理</h1>
        <Button onClick={() => navigate('/')}>退出数据库管理</Button>
      </div>
      
      {/* 顶部 Tab 导航栏 */}
      <div style={{ marginBottom: '20px' }}>
        <Tabs 
          activeKey={activeMachineTypeId ? activeMachineTypeId.toString() : null}
          onChange={(key) => handleMachineTypeChange(parseInt(key))}
          tabBarExtraContent={
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddMachineType}>
              添加类型
            </Button>
          }
          items={hierarchicalData.map(machineType => ({
            key: machineType.id.toString(),
            label: (
              <span>
                {machineType.name}
                <CloseOutlined 
                  style={{ 
                    marginLeft: 8, 
                    fontSize: 12, 
                    cursor: 'pointer',
                    color: '#ff4d4f'
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteMachineType(machineType.id);
                  }}
                />
              </span>
            ),
            children: <div></div>
          }))}
        />
      </div>
      
      {/* 三栏式内容区 */}
      <Row gutter={16} style={{ height: 'calc(100vh - 250px)' }}>
        {/* 左侧栏：供应商列表 */}
        <Col span={5}>
          <Card 
            title="供应商列表" 
            style={{ height: '100%' }}
            extra={<Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleAddSupplier}>添加</Button>}
          >
            {currentMachineType ? (
              <List
                dataSource={currentMachineType.suppliers}
                renderItem={supplier => (
                  <List.Item 
                    key={supplier.id}
                    onClick={() => {
                      setSelectedSupplier(supplier);
                      setSelectedMachine(null);
                    }}
                    style={{ 
                      cursor: 'pointer', 
                      backgroundColor: selectedSupplier?.id === supplier.id ? '#e6f7ff' : 'white',
                      padding: '8px',
                      marginBottom: '4px',
                      borderRadius: '4px',
                      border: '1px solid #ddd'
                    }}
                    actions={[
                      <Dropdown overlay={supplierActionMenu(supplier)} trigger={['click']}>
                        <Button type="link" icon={<MoreOutlined />} />
                      </Dropdown>
                    ]}
                  >
                    <div>
                      <div>{supplier.name}</div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <div>暂无供应商数据</div>
            )}
          </Card>
        </Col>
        
        {/* 中间栏：设备型号列表 */}
        <Col span={7}>
          <Card 
            title="设备型号列表" 
            style={{ height: '100%' }}
            extra={selectedSupplier && <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleAddMachine}>添加</Button>}
          >
            {selectedSupplier ? (
              <List
                dataSource={selectedSupplier.machines}
                renderItem={machine => (
                  <List.Item 
                    key={machine.id}
                    onClick={() => setSelectedMachine(machine)}
                    style={{ 
                      cursor: 'pointer', 
                      backgroundColor: selectedMachine?.id === machine.id ? '#e6f7ff' : 'white',
                      padding: '12px',
                      marginBottom: '8px',
                      borderRadius: '4px',
                      border: '1px solid #ddd'
                    }}
                    actions={[
                      <Dropdown overlay={machineActionMenu(machine)} trigger={['click']}>
                        <Button type="link" icon={<MoreOutlined />} />
                      </Dropdown>
                    ]}
                  >
                    <div>
                      <h3>{machine.name}</h3>
                      <p>{machine.description || '无描述'}</p>
                      <div>币种: {machine.currency}</div>
                      <div>汇率: {machine.exchange_rate}</div>
                      <div>折扣率: {machine.discount_rate}</div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <div>请在左侧选择一个供应商</div>
            )}
          </Card>
        </Col>
        
        {/* 右侧栏：板卡配置详情 */}
        <Col span={12}>
          <Card 
            title="板卡配置详情" 
            style={{ height: '100%' }}
            extra={selectedMachine && <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleAddCardConfig}>添加</Button>}
          >
            {selectedMachine ? (
              <>
                {selectedMachine.card_configs && selectedMachine.card_configs.length > 0 ? (
                  <Table
                    dataSource={selectedMachine.card_configs}
                    columns={cardConfigColumns}
                    rowKey="id"
                    pagination={false}
                    scroll={{ y: 400 }}
                  />
                ) : (
                  <p>暂无板卡配置</p>
                )}
              </>
            ) : (
              <div>请在中间选择一个设备型号</div>
            )}
          </Card>
        </Col>
      </Row>
      
      {/* 添加机器类型模态框 */}
      <Modal
        title="添加机器类型"
        open={addMachineTypeModalVisible}
        onOk={handleSaveNewMachineType}
        onCancel={() => setAddMachineTypeModalVisible(false)}
        forceRender
      >
        <Form form={addMachineTypeForm} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 供应商模态框 */}
      <Modal
        title={editingSupplier ? "编辑供应商" : "添加供应商"}
        open={supplierModalVisible}
        onOk={handleSaveSupplier}
        onCancel={() => setSupplierModalVisible(false)}
        forceRender
      >
        <Form form={supplierForm} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称!' }]}
          >
            <Input />
          </Form.Item>
          
          {!activeMachineTypeId && (
            <Form.Item
              name="machine_type_id"
              label="机器类型ID"
              rules={[{ required: true, message: '请输入机器类型ID!' }]}
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          )}
        </Form>
      </Modal>
      
      {/* 机器模态框 */}
      <Modal
        title={editingMachine ? "编辑机器" : "添加机器"}
        open={machineModalVisible}
        onOk={handleSaveMachine}
        onCancel={() => setMachineModalVisible(false)}
        forceRender
      >
        <Form form={machineForm} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea />
          </Form.Item>
          
          <Form.Item
            name="currency"
            label="币种"
          >
            <Select 
              placeholder="请选择币种"
              onChange={(value) => {
                // 当币种切换时，自动设置对应的默认汇率
                if (value === 'USD') {
                  machineForm.setFieldsValue({ exchange_rate: 7 });
                } else if (value === 'RMB') {
                  machineForm.setFieldsValue({ exchange_rate: 1 });
                }
              }}
            >
              <Select.Option value="RMB">RMB (¥)</Select.Option>
              <Select.Option value="USD">USD ($)</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.currency !== currentValues.currency}
          >
            {({ getFieldValue }) => {
              const currency = getFieldValue('currency');
              return (
                <Form.Item
                  name="exchange_rate"
                  label="汇率"
                  rules={[{ required: currency === 'USD', message: '请输入汇率!' }]}
                >
                  <InputNumber 
                    min={0} 
                    step={0.01} 
                    style={{ width: '100%' }} 
                    disabled={currency === 'RMB'}
                  />
                </Form.Item>
              );
            }}
          </Form.Item>
          
          <Form.Item
            name="discount_rate"
            label="固定折扣率"
            rules={[{ required: true, message: '请输入固定折扣率!' }]}
          >
            <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="active"
            label="是否激活"
            valuePropName="checked"
          >
            <input type="checkbox" />
          </Form.Item>
          
          { !selectedSupplier && (
            <Form.Item
              name="supplier_id"
              label="供应商ID"
              rules={[{ required: true, message: '请输入供应商ID!' }]}
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          )}
        </Form>
      </Modal>
      
      {/* 板卡配置模态框 */}
      <Modal
        title={editingCardConfig ? "编辑板卡配置" : "添加板卡配置"}
        open={cardConfigModalVisible}
        onOk={handleSaveCardConfig}
        onCancel={() => setCardConfigModalVisible(false)}
        forceRender
      >
        <Form form={cardConfigForm} layout="vertical">
          <Form.Item
            name="part_number"
            label="Part Number"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="board_name"
            label="Board Name"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="unit_price"
            label="Unit Price"
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          
          { !selectedMachine && (
            <Form.Item
              name="machine_id"
              label="机器ID"
              rules={[{ required: true, message: '请输入机器ID!' }]}
            >
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default HierarchicalDatabaseManagement;