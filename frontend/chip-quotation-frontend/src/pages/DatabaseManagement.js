import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Form, Input, InputNumber, Button, Modal, Popconfirm, message, Card, Tabs, Tree } from 'antd';
import { 
  getMachines, 
  createMachine, 
  updateMachine, 
  deleteMachine 
} from '../services/machines';
import { 
  getConfigurations, 
  createConfiguration, 
  updateConfiguration, 
  deleteConfiguration 
} from '../services/configurations';
import { 
  getCardTypes, 
  createCardType, 
  updateCardType, 
  deleteCardType 
} from '../services/cardTypes';
import { 
  getCards,
  createCard,
  updateCard,
  deleteCard
} from '../services/cards';
import { 
  getAuxiliaryEquipment, 
  createAuxiliaryEquipment, 
  updateAuxiliaryEquipment, 
  deleteAuxiliaryEquipment 
} from '../services/auxiliaryEquipment';
import { formatNumber } from '../utils';
import api from '../services/api';
import '../App.css';

const { TabPane } = Tabs;

const DatabaseManagement = () => {
  const navigate = useNavigate();
  const [hierarchicalData, setHierarchicalData] = useState([]);
  const [machines, setMachines] = useState([]);
  const [configurations, setConfigurations] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);
  const [cards, setCards] = useState([]);
  const [auxEquipments, setAuxEquipments] = useState([]);
  
  const [editingMachine, setEditingMachine] = useState(null);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editingCardType, setEditingCardType] = useState(null);
  const [editingCard, setEditingCard] = useState(null);
  const [editingAuxEquipment, setEditingAuxEquipment] = useState(null);
  
  const [machineModalVisible, setMachineModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [cardTypeModalVisible, setCardTypeModalVisible] = useState(false);
  const [cardModalVisible, setCardModalVisible] = useState(false);
  const [auxEquipmentModalVisible, setAuxEquipmentModalVisible] = useState(false);
  
  const [machineForm] = Form.useForm();
  const [configForm] = Form.useForm();
  const [cardTypeForm] = Form.useForm();
  const [cardForm] = Form.useForm();
  const [auxEquipmentForm] = Form.useForm();

  // 获取所有数据
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 先获取层级数据
      const hierarchicalDataResponse = await api.get('/hierarchical/suppliers');
      
      console.log('Hierarchical data:', hierarchicalDataResponse.data);
      setHierarchicalData(hierarchicalDataResponse.data);
      
      // 然后获取其他数据（忽略错误）
      try {
        const machinesData = await getMachines();
        setMachines(machinesData);
      } catch (error) {
        console.error('获取测试机数据失败:', error);
        setMachines([]);
      }
      
      try {
        const configurationsData = await getConfigurations();
        setConfigurations(configurationsData);
      } catch (error) {
        console.error('获取配置数据失败:', error);
        setConfigurations([]);
      }
      
      try {
        const cardTypesData = await getCardTypes();
        setCardTypes(cardTypesData);
      } catch (error) {
        console.error('获取板卡类型数据失败:', error);
        setCardTypes([]);
      }
      
      try {
        const cardsData = await getCards();
        setCards(cardsData);
      } catch (error) {
        console.error('获取板卡数据失败:', error);
        setCards([]);
      }
      
      try {
        const auxEquipmentsData = await getAuxiliaryEquipment();
        setAuxEquipments(auxEquipmentsData);
      } catch (error) {
        console.error('获取辅助设备数据失败:', error);
        setAuxEquipments([]);
      }
    } catch (error) {
      console.error('获取层级数据失败:', error);
      message.error('获取数据失败: ' + error.message);
    }
  };

  // 将层级数据转换为树形结构
  const convertToTreeData = (data) => {
    if (!data || data.length === 0) {
      return [];
    }
    
    return data.map(supplier => ({
      title: `供应商: ${supplier.name}`,
      key: `supplier-${supplier.id}`,
      children: supplier.machines.map(machine => ({
        title: `测试机: ${machine.name}`,
        key: `machine-${machine.id}`,
        children: [
          ...machine.configurations.map(configuration => ({
            title: `配置: ${configuration.name}`,
            key: `configuration-${configuration.id}`
          })),
          ...machine.cards.map(card => ({
            title: `板卡: ${card.model}`,
            key: `card-${card.id}`
          }))
        ].filter(child => child.title) // 过滤掉无效的子节点
      }))
    }));
  };


  // 机器相关操作
  const handleAddMachine = () => {
    setEditingMachine(null);
    machineForm.resetFields();
    setMachineModalVisible(true);
  };

  const handleEditMachine = (record) => {
    setEditingMachine(record);
    machineForm.setFieldsValue(record);
    setMachineModalVisible(true);
  };

  const handleDeleteMachine = async (id) => {
    try {
      await deleteMachine(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleSaveMachine = async () => {
    try {
      const values = await machineForm.validateFields();
      if (editingMachine) {
        await updateMachine(editingMachine.id, values);
        message.success('更新成功');
      } else {
        await createMachine(values);
        message.success('创建成功');
      }
      setMachineModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('保存失败: ' + error.message);
    }
  };

  // 配置相关操作
  const handleAddConfig = () => {
    setEditingConfig(null);
    configForm.resetFields();
    setConfigModalVisible(true);
  };

  const handleEditConfig = (record) => {
    setEditingConfig(record);
    configForm.setFieldsValue(record);
    setConfigModalVisible(true);
  };

  const handleDeleteConfig = async (id) => {
    try {
      await deleteConfiguration(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleSaveConfig = async () => {
    try {
      const values = await configForm.validateFields();
      if (editingConfig) {
        await updateConfiguration(editingConfig.id, values);
        message.success('更新成功');
      } else {
        await createConfiguration(values);
        message.success('创建成功');
      }
      setConfigModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('保存失败: ' + error.message);
    }
  };

  // 卡类型相关操作
  const handleAddCardType = () => {
    setEditingCardType(null);
    cardTypeForm.resetFields();
    setCardTypeModalVisible(true);
  };

  const handleEditCardType = (record) => {
    setEditingCardType(record);
    cardTypeForm.setFieldsValue(record);
    setCardTypeModalVisible(true);
  };

  const handleDeleteCardType = async (id) => {
    try {
      await deleteCardType(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleSaveCardType = async () => {
    try {
      const values = await cardTypeForm.validateFields();
      if (editingCardType) {
        await updateCardType(editingCardType.id, values);
        message.success('更新成功');
      } else {
        await createCardType(values);
        message.success('创建成功');
      }
      setCardTypeModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('保存失败: ' + error.message);
    }
  };

  // 板卡相关操作
  const handleAddCard = () => {
    setEditingCard(null);
    cardForm.resetFields();
    setCardModalVisible(true);
  };

  const handleEditCard = (record) => {
    setEditingCard(record);
    cardForm.setFieldsValue(record);
    setCardModalVisible(true);
  };

  const handleDeleteCard = async (id) => {
    try {
      await deleteCard(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleSaveCard = async () => {
    try {
      const values = await cardForm.validateFields();
      if (editingCard) {
        await updateCard(editingCard.id, values);
        message.success('更新成功');
      } else {
        await createCard(values);
        message.success('创建成功');
      }
      setCardModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('保存失败: ' + error.message);
    }
  };

  // 辅助设备相关操作
  const handleAddAuxEquipment = () => {
    setEditingAuxEquipment(null);
    auxEquipmentForm.resetFields();
    setAuxEquipmentModalVisible(true);
  };

  const handleEditAuxEquipment = (record) => {
    setEditingAuxEquipment(record);
    auxEquipmentForm.setFieldsValue(record);
    setAuxEquipmentModalVisible(true);
  };

  const handleDeleteAuxEquipment = async (id) => {
    try {
      await deleteAuxiliaryEquipment(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleSaveAuxEquipment = async () => {
    try {
      const values = await auxEquipmentForm.validateFields();
      if (editingAuxEquipment) {
        await updateAuxiliaryEquipment(editingAuxEquipment.id, values);
        message.success('更新成功');
      } else {
        await createAuxiliaryEquipment(values);
        message.success('创建成功');
      }
      setAuxEquipmentModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('保存失败: ' + error.message);
    }
  };

  // 机器表格列定义
  const machineColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '基础小时费率',
      dataIndex: 'base_hourly_rate',
      key: 'base_hourly_rate',
      render: (value) => value ? `¥${formatNumber(value)}` : 'N/A'
    },
    {
      title: '供应商ID',
      dataIndex: 'supplier_id',
      key: 'supplier_id',
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <span>
          <Button type="link" onClick={() => handleEditMachine(record)}>编辑</Button>
          <Popconfirm
            title="确定要删除这个机器吗?"
            onConfirm={() => handleDeleteMachine(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 配置表格列定义
  const configColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '附加费率',
      dataIndex: 'additional_rate',
      key: 'additional_rate',
      render: (value) => value ? `¥${formatNumber(value)}` : 'N/A'
    },
    {
      title: '测试机ID',
      dataIndex: 'machine_id',
      key: 'machine_id',
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <span>
          <Button type="link" onClick={() => handleEditConfig(record)}>编辑</Button>
          <Popconfirm
            title="确定要删除这个配置吗?"
            onConfirm={() => handleDeleteConfig(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 卡类型表格列定义
  const cardTypeColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '小时费率',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      render: (value) => value ? `¥${formatNumber(value)}` : 'N/A'
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <span>
          <Button type="link" onClick={() => handleEditCardType(record)}>编辑</Button>
          <Popconfirm
            title="确定要删除这个卡类型吗?"
            onConfirm={() => handleDeleteCardType(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 板卡表格列定义
  const cardColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '型号',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '测试机ID',
      dataIndex: 'machine_id',
      key: 'machine_id',
    },
    {
      title: '单价',
      dataIndex: 'unit_price',
      key: 'unit_price',
      render: (value) => value ? `¥${formatNumber(value)}` : 'N/A'
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <span>
          <Button type="link" onClick={() => handleEditCard(record)}>编辑</Button>
          <Popconfirm
            title="确定要删除这个板卡吗?"
            onConfirm={() => handleDeleteCard(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  // 辅助设备表格列定义
  const auxEquipmentColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '小时费率',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      render: (value) => value ? `¥${formatNumber(value)}` : 'N/A'
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <span>
          <Button type="link" onClick={() => handleEditAuxEquipment(record)}>编辑</Button>
          <Popconfirm
            title="确定要删除这个辅助设备吗?"
            onConfirm={() => handleDeleteAuxEquipment(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div className="database-management">
      <h1>数据库管理</h1>
      
      <Tabs defaultActiveKey="1">
        <TabPane tab="层级结构" key="1">
          <Card title="供应商 -> 测试机 -> 配置和板卡 层级结构">
            <Tree
              treeData={convertToTreeData(hierarchicalData)}
              defaultExpandAll
            />
          </Card>
        </TabPane>
        
        <TabPane tab="测试机管理" key="2">
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={handleAddMachine}>
              添加测试机
            </Button>
          </div>
          <Table 
            dataSource={machines} 
            columns={machineColumns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </TabPane>
        
        <TabPane tab="配置管理" key="3">
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={handleAddConfig}>
              添加配置
            </Button>
          </div>
          <Table 
            dataSource={configurations} 
            columns={configColumns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </TabPane>
        
        <TabPane tab="板卡类型管理" key="4">
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={handleAddCardType}>
              添加板卡类型
            </Button>
          </div>
          <Table 
            dataSource={cardTypes} 
            columns={cardTypeColumns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </TabPane>
        
        <TabPane tab="板卡管理" key="5">
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={handleAddCard}>
              添加板卡
            </Button>
          </div>
          <Table 
            dataSource={cards} 
            columns={cardColumns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </TabPane>
        
        <TabPane tab="辅助设备管理" key="6">
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={handleAddAuxEquipment}>
              添加辅助设备
            </Button>
          </div>
          <Table 
            dataSource={auxEquipments} 
            columns={auxEquipmentColumns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </TabPane>
      </Tabs>
      
      {/* 机器模态框 */}
      <Modal
        title={editingMachine ? "编辑测试机" : "添加测试机"}
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
            name="base_hourly_rate"
            label="基础小时费率"
            rules={[{ required: true, message: '请输入基础小时费率!' }]}
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="supplier_id"
            label="供应商ID"
            rules={[{ required: true, message: '请输入供应商ID!' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="active"
            label="是否激活"
            valuePropName="checked"
          >
            <input type="checkbox" />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 配置模态框 */}
      <Modal
        title={editingConfig ? "编辑配置" : "添加配置"}
        open={configModalVisible}
        onOk={handleSaveConfig}
        onCancel={() => setConfigModalVisible(false)}
        forceRender
      >
        <Form form={configForm} layout="vertical">
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
            name="additional_rate"
            label="附加费率"
            rules={[{ required: true, message: '请输入附加费率!' }]}
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="machine_id"
            label="测试机ID"
            rules={[{ required: true, message: '请输入测试机ID!' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 卡类型模态框 */}
      <Modal
        title={editingCardType ? "编辑卡类型" : "添加卡类型"}
        open={cardTypeModalVisible}
        onOk={handleSaveCardType}
        onCancel={() => setCardTypeModalVisible(false)}
        forceRender
      >
        <Form form={cardTypeForm} layout="vertical">
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
            name="hourly_rate"
            label="小时费率"
            rules={[{ required: true, message: '请输入小时费率!' }]}
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 板卡模态框 */}
      <Modal
        title={editingCard ? "编辑板卡" : "添加板卡"}
        open={cardModalVisible}
        onOk={handleSaveCard}
        onCancel={() => setCardModalVisible(false)}
        forceRender
      >
        <Form form={cardForm} layout="vertical">
          <Form.Item
            name="model"
            label="型号"
            rules={[{ required: true, message: '请输入型号!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="machine_id"
            label="测试机ID"
            rules={[{ required: true, message: '请输入测试机ID!' }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 辅助设备模态框 */}
      <Modal
        title={editingAuxEquipment ? "编辑辅助设备" : "添加辅助设备"}
        open={auxEquipmentModalVisible}
        onOk={handleSaveAuxEquipment}
        onCancel={() => setAuxEquipmentModalVisible(false)}
        forceRender
      >
        <Form form={auxEquipmentForm} layout="vertical">
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
            name="hourly_rate"
            label="小时费率"
            rules={[{ required: true, message: '请输入小时费率!' }]}
          >
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatabaseManagement;