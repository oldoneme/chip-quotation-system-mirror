import React, { useState, useEffect } from 'react';
import {
  Table, Card, Button, Space, Tag, Row, Col, Statistic, message, Modal, List, Dropdown
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import QuoteApiService from '../services/quoteApi';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import '../styles/QuoteManagement.css';

const { confirm } = Modal;

const QuoteManagement = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState([]);
  const [isMobile, setIsMobile] = useState(false);
  const [machines, setMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);

  // 统计数据
  const [statistics, setStatistics] = useState({
    total: 0,
    draft: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  const fetchQuotes = async () => {
    setLoading(true);
    try {
      const response = await QuoteApiService.getQuotes();
      const quotesData = response.items || [];
      
      // 格式化数据显示
      const formattedQuotes = quotesData.map(quote => ({
        id: quote.id,  // 使用数字ID作为主键
        quoteId: quote.id,  // 保存实际ID用于操作
        title: quote.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quote.quote_type),
        quote_type: quote.quote_type, // 保留原始类型用于编辑跳转
        quote_number: quote.quote_number, // 保留报价单号
        customer: quote.customer_name,
        currency: quote.currency || 'CNY',
        status: QuoteApiService.mapStatusFromBackend(quote.status),
        approvalStatus: quote.approval_status, // 添加审批状态字段
        createdBy: quote.creator_name || `用户${quote.created_by}`,
        createdAt: new Date(quote.created_at).toLocaleString('zh-CN'),
        updatedAt: new Date(quote.updated_at).toLocaleString('zh-CN'),
        validUntil: quote.valid_until ? new Date(quote.valid_until).toLocaleDateString('zh-CN') : '-',
        totalAmount: quote.total_amount,
        quoteDetails: quote.quote_details || [],
        // 为编辑功能保留完整的原始数据
        ...quote
      }));
      
      setQuotes(formattedQuotes);
    } catch (error) {
      console.error('获取报价单列表失败:', error);
      message.error('获取报价单列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const stats = await QuoteApiService.getStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('获取统计信息失败:', error);
      message.error('获取统计信息失败');
    }
  };

  // 检测移动端
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  useEffect(() => {
    fetchQuotes();
    fetchStatistics();
    // 加载设备和板卡数据（用于工序报价显示机时费率）
    const loadData = async () => {
      try {
        const [machinesData, cardTypesData] = await Promise.all([
          getMachines(),
          getCardTypes()
        ]);
        setMachines(machinesData);
        setCardTypes(cardTypesData);
      } catch (error) {
        console.error('获取设备/板卡数据失败:', error);
      }
    };
    loadData();
  }, []);

  const getStatusTag = (status, approvalStatus) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <EditOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已驳回', icon: <CloseCircleOutlined /> }
    };
    
    // 特殊处理：被驳回后重新提交审批的状态
    if (status === 'rejected' && approvalStatus === 'pending') {
      return (
        <Tag color="processing" icon={<ClockCircleOutlined />} style={{ fontSize: '14px', padding: '4px 12px' }}>
          重新审批中
        </Tag>
      );
    }
    
    // 被驳回但未重新提交
    if (status === 'rejected') {
      return (
        <Tag color="warning" icon={<CloseCircleOutlined />} style={{ fontSize: '14px', padding: '4px 12px' }}>
          已驳回 (可重新提交)
        </Tag>
      );
    }
    
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon} style={{ fontSize: '14px', padding: '4px 12px' }}>
        {config.text}
      </Tag>
    );
  };

  const getTypeTag = (type) => {
    const typeColors = {
      '询价报价': 'blue',
      '工装夹具报价': 'purple',
      '工程机时报价': 'cyan',
      '量产机时报价': 'green',
      '量产工序报价': 'orange',
      '综合报价': 'magenta'
    };
    return <Tag color={typeColors[type]}>{type}</Tag>;
  };

  const columns = [
    {
      title: '报价单号',
      dataIndex: 'quote_number',
      key: 'quote_number',
      width: 160,
      render: (text) => <Button type="link" onClick={() => handleView(text)}>{text}</Button>
    },
    {
      title: '报价标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true
    },
    {
      title: '报价类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => getTypeTag(type)
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      width: 150,
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status, record) => getStatusTag(status, record.approvalStatus)
    },
    {
      title: '创建人',
      dataIndex: 'createdBy',
      key: 'createdBy',
      width: 100,
      ellipsis: true
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      ellipsis: true
    },
    {
      title: '有效期至',
      dataIndex: 'validUntil',
      key: 'validUntil',
      width: 120
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />} 
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          {record.status === 'draft' && (
            <>
              <Button 
                type="link" 
                size="small"
                icon={<EditOutlined />} 
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Button 
                type="link" 
                size="small"
                danger
                icon={<DeleteOutlined />} 
                onClick={() => handleDelete(record)}
              >
                删除
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  const handleView = (id) => {
    navigate(`/quote-detail/${id}`);
  };

  const handleEdit = async (record) => {
    // 根据报价类型跳转到对应的编辑页面（支持中英文类型）
    const quoteTypeToPath = {
      'inquiry': '/inquiry-quote',
      '询价报价': '/inquiry-quote',
      'tooling': '/tooling-quote',
      '工装夹具报价': '/tooling-quote',
      'engineering': '/engineering-quote',
      '工程报价': '/engineering-quote',
      'mass_production': '/mass-production-quote',
      '量产报价': '/mass-production-quote',
      'process': '/process-quote',
      '工序报价': '/process-quote',
      'comprehensive': '/comprehensive-quote',
      '综合报价': '/comprehensive-quote'
    };

    const editPath = quoteTypeToPath[record.quote_type];
    if (editPath) {
      try {
        // 获取完整的报价单详情数据（包含items字段）
        const fullQuoteData = await QuoteApiService.getQuoteDetailById(record.quoteId);

        // 传递完整的报价单数据到编辑页面
        navigate(editPath, {
          state: {
            editingQuote: fullQuoteData, // 使用完整的数据
            isEditing: true,
            quoteId: record.quoteId // 使用实际的数据库ID
          }
        });
      } catch (error) {
        console.error('获取报价单详情失败:', error);
        message.error('获取报价单详情失败，请稍后重试');
      }
    } else {
      message.error(`未知的报价类型：${record.quote_type}，无法编辑`);
    }
  };

  const handleDelete = (record) => {
    confirm({
      title: '确认删除',
      content: `确定要删除报价单 ${record.id} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await QuoteApiService.deleteQuote(record.quoteId);
          message.success('删除成功');
          fetchQuotes();
          fetchStatistics(); // 重新获取统计数据
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  // 移动端操作菜单
  const getMobileActionItems = (record) => {
    const items = [
      {
        key: 'view',
        label: '查看',
        icon: <EyeOutlined />,
        onClick: () => handleView(record.id)
      }
    ];

    if (record.status === 'draft') {
      items.push(
        {
          key: 'edit',
          label: '编辑',
          icon: <EditOutlined />,
          onClick: () => handleEdit(record)
        },
        {
          key: 'delete',
          label: '删除',
          icon: <DeleteOutlined />,
          danger: true,
          onClick: () => handleDelete(record)
        }
      );
    }

    return { items };
  };

  // 移动端列表渲染
  const renderMobileList = () => (
    <List
      loading={loading}
      dataSource={quotes}
      renderItem={(item) => (
        <List.Item
          key={item.id}
          style={{ 
            padding: '12px', 
            marginBottom: '8px', 
            backgroundColor: '#fff', 
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}
        >
          <div style={{ width: '100%' }}>
            {/* 头部信息 */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start',
              marginBottom: '8px'
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontSize: '16px', 
                  fontWeight: 'bold', 
                  color: '#1890ff',
                  marginBottom: '4px'
                }}>
                  {item.id}
                </div>
                <div style={{ 
                  fontSize: '14px', 
                  color: '#333',
                  marginBottom: '4px',
                  wordBreak: 'break-all'
                }}>
                  {item.title}
                </div>
              </div>
              <Dropdown menu={getMobileActionItems(item)} trigger={['click']}>
                <Button type="text" icon={<MoreOutlined />} />
              </Dropdown>
            </div>

            {/* 标签行 */}
            <div style={{ marginBottom: '8px' }}>
              <Space size={[4, 4]} wrap>
                {getTypeTag(item.type)}
                {getStatusTag(item.status, item.approvalStatus)}
              </Space>
            </div>

            {/* 详细信息 */}
            <div style={{ fontSize: '12px', color: '#666' }}>
              <div style={{ marginBottom: '2px' }}>客户：{item.customer}</div>
              <div style={{ marginBottom: '2px' }}>创建人：{item.createdBy}</div>
              <div style={{ marginBottom: '2px' }}>创建时间：{item.createdAt}</div>
              <div>有效期至：{item.validUntil}</div>
            </div>

            {/* 展开明细按钮 */}
            {item.quoteDetails && item.quoteDetails.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <Button 
                  type="link" 
                  size="small" 
                  onClick={() => {
                    // 使用一个简单的方式显示明细
                    Modal.info({
                      title: '报价明细',
                      content: renderQuoteDetailsTable(item),
                      width: '90%',
                      okText: '关闭'
                    });
                  }}
                >
                  查看明细
                </Button>
              </div>
            )}
          </div>
        </List.Item>
      )}
      pagination={{
        current: 1,
        pageSize: 10,
        total: quotes.length,
        showSizeChanger: false,
        showQuickJumper: false,
        showTotal: (total) => `共 ${total} 条`,
        size: 'small'
      }}
    />
  );

  const renderQuoteDetailsTable = (record) => {
    if (!record.quoteDetails || record.quoteDetails.length === 0) {
      return <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>暂无报价明细</div>;
    }

    // 工装夹具报价使用三大类别显示
    if (record.type === '工装夹具报价') {
      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px', color: '#1890ff' }}>报价明细</h4>
          
          {/* 1. 工装夹具清单 */}
          {(() => {
            const toolingItems = record.quoteDetails.filter(item => 
              item.category_type === 'tooling_hardware' || 
              (item.item_description && item.item_description.includes('fixture')) ||
              (item.unit === '件' && !item.item_name?.includes('程序') && !item.item_name?.includes('调试') && !item.item_name?.includes('设计') && 
               !item.item_description?.includes('工程') && !item.item_description?.includes('开发'))
            );
            
            return toolingItems && toolingItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>🔧 1. 工装夹具清单</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '2fr 2fr 1.5fr 1fr 1.5fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>类别</span>
                    <span>类型</span>
                    <span>单价</span>
                    <span>数量</span>
                    <span>小计</span>
                  </div>
                  {toolingItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 1.5fr 1fr 1.5fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < toolingItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.category || item.item_description?.split(' - ')[0] || '工装夹具'}</span>
                      <span>{item.type || item.item_name}</span>
                      <span>¥{item.unit_price?.toFixed(2)}</span>
                      <span>{item.quantity}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{item.total_price?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                  <div style={{ 
                    padding: '8px 12px',
                    backgroundColor: '#f0f9ff',
                    borderTop: '1px solid #d9d9d9',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    fontWeight: 'bold',
                    fontSize: '12px',
                    color: '#1890ff'
                  }}>
                    工装夹具总价: ¥{toolingItems.reduce((sum, item) => sum + (item.total_price || 0), 0).toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })()}
          
          {/* 2. 工程费用 */}
          {(() => {
            const engineeringItems = record.quoteDetails.filter(item => 
              item.category_type === 'engineering_fee' || 
              (item.item_name && (item.item_name.includes('测试程序') || item.item_name.includes('程序开发') || item.item_name.includes('夹具设计') || 
                                 item.item_name.includes('测试验证') || item.item_name.includes('文档') || item.item_name.includes('设计'))) ||
              (item.item_description && (item.item_description.includes('工程') || item.item_description.includes('开发')))
            );
            
            return engineeringItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>⚙️ 2. 工程费用</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  {engineeringItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderBottom: index < engineeringItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.item_name}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{item.total_price?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                  <div style={{ 
                    padding: '8px 12px',
                    backgroundColor: '#f0f9ff',
                    borderTop: '1px solid #d9d9d9',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    fontWeight: 'bold',
                    fontSize: '12px',
                    color: '#1890ff'
                  }}>
                    工程费用总价: ¥{engineeringItems.reduce((sum, item) => sum + (item.total_price || 0), 0).toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })()}
          
          {/* 3. 量产准备费用 */}
          {(() => {
            const productionItems = record.quoteDetails.filter(item => 
              item.category_type === 'production_setup' || 
              (item.item_name && (item.item_name.includes('调试') || item.item_name.includes('校准') || item.item_name.includes('检验') || 
                                 item.item_name.includes('设备调试') || item.item_name.includes('调试费'))) ||
              (item.item_description && (item.item_description.includes('准备') || item.item_description.includes('产线') || item.item_description.includes('设置')))
            );
            
            return productionItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>🏭 3. 量产准备费用</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  {productionItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      borderBottom: index < productionItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.item_name}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{item.total_price?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                  <div style={{ 
                    padding: '8px 12px',
                    backgroundColor: '#f0f9ff',
                    borderTop: '1px solid #d9d9d9',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    fontWeight: 'bold',
                    fontSize: '12px',
                    color: '#1890ff'
                  }}>
                    量产准备费用总价: ¥{productionItems.reduce((sum, item) => sum + (item.total_price || 0), 0).toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      );
    }

    // 工程报价使用分类显示
    if (record.type === '工程机时报价') {
      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
          
          {/* 1. 机器设备 */}
          {(() => {
            const machineItems = record.quoteDetails.filter(item => 
              item.machine_type && item.machine_type !== '人员'
            );
            
            return machineItems && machineItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>🔧 1. 机器设备</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '2fr 2fr 2fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>设备类型</span>
                    <span>设备型号</span>
                    <span>小时费率</span>
                  </div>
                  {machineItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 2fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < machineItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.machine_type}</span>
                      <span>{item.machine_model}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{item.unit_price?.toFixed(2)}/小时
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
          
          {/* 2. 人员费用 */}
          {(() => {
            const personnelItems = record.quoteDetails.filter(item => 
              item.machine_type === '人员' || 
              (item.item_name && (item.item_name === '工程师' || item.item_name === '技术员'))
            );
            
            return personnelItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>👨‍💼 2. 人员费用</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '3fr 3fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>人员类别</span>
                    <span>小时费率</span>
                  </div>
                  {personnelItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '3fr 3fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < personnelItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.item_name || item.machine_model}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{item.unit_price?.toFixed(2)}/小时
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      );
    }

    // 量产机时报价使用分类显示
    if (record.type === '量产机时报价') {
      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
          
          {/* FT测试设备 */}
          {(() => {
            // FT设备：前两个设备（测试机和分选机）
            const ftItems = record.quoteDetails.slice(0, 2);
            
            return ftItems && ftItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>📱 FT测试设备</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '2fr 2fr 2fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>设备类型</span>
                    <span>设备型号</span>
                    <span>小时费率</span>
                  </div>
                  {ftItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 2fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < ftItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.machine_type || '-'}</span>
                      <span>{item.machine_model || item.item_name || '-'}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{(item.unit_price || 0).toFixed(2)}/小时
                      </span>
                    </div>
                  ))}
                  {/* FT小计 */}
                  <div style={{ 
                    padding: '8px 12px',
                    backgroundColor: '#f0f9ff',
                    borderTop: '1px solid #d9d9d9',
                    display: 'grid',
                    gridTemplateColumns: '2fr 2fr 2fr',
                    gap: '10px',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span></span>
                    <span>FT设备小计:</span>
                    <span style={{ color: '#1890ff' }}>
                      ¥{ftItems.reduce((sum, item) => sum + (item.unit_price || 0), 0).toFixed(2)}/小时
                    </span>
                  </div>
                </div>
              </div>
            );
          })()}
          
          {/* CP测试设备 */}
          {(() => {
            // CP设备：后两个设备（测试机和探针台）
            const cpItems = record.quoteDetails.slice(2, 4);
            
            return cpItems && cpItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>🔬 CP测试设备</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '2fr 2fr 2fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>设备类型</span>
                    <span>设备型号</span>
                    <span>小时费率</span>
                  </div>
                  {cpItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 2fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < cpItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.machine_type || '-'}</span>
                      <span>{item.machine_model || item.item_name || '-'}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{(item.unit_price || 0).toFixed(2)}/小时
                      </span>
                    </div>
                  ))}
                  {/* CP小计 */}
                  <div style={{ 
                    padding: '8px 12px',
                    backgroundColor: '#f0f9ff',
                    borderTop: '1px solid #d9d9d9',
                    display: 'grid',
                    gridTemplateColumns: '2fr 2fr 2fr',
                    gap: '10px',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span></span>
                    <span>CP设备小计:</span>
                    <span style={{ color: '#1890ff' }}>
                      ¥{cpItems.reduce((sum, item) => sum + (item.unit_price || 0), 0).toFixed(2)}/小时
                    </span>
                  </div>
                </div>
              </div>
            );
          })()}
          
          {/* 辅助设备 */}
          {(() => {
            const auxItems = record.quoteDetails.filter(item => 
              item.category_type === 'auxiliary' || item.machine_type === '辅助设备'
            );
            
            return auxItems && auxItems.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h5>🔧 辅助设备</h5>
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px', backgroundColor: '#fff' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '2fr 2fr 2fr', 
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    borderBottom: '1px solid #d9d9d9',
                    fontWeight: 'bold',
                    fontSize: '12px'
                  }}>
                    <span>设备类型</span>
                    <span>设备型号</span>
                    <span>小时费率</span>
                  </div>
                  {auxItems.map((item, index) => (
                    <div key={index} style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '2fr 2fr 2fr', 
                      gap: '10px',
                      padding: '8px 12px',
                      borderBottom: index < auxItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      fontSize: '12px'
                    }}>
                      <span>{item.machine_type || '-'}</span>
                      <span>{item.machine_model || item.item_name || '-'}</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        ¥{(item.unit_price || 0).toFixed(2)}/小时
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      );
    }

    // 量产工序报价使用表格显示，分CP和FT两类
    if (record.type === '量产工序报价' || record.type === '工序报价' || record.quote_type === 'process') {
      // 解析工序配置，从configuration JSON中提取UPH和机时费率
      const parseProcessItem = (item) => {
        let uph = null;
        let hourlyRate = null;

        if (item.configuration) {
          try {
            const config = typeof item.configuration === 'string'
              ? JSON.parse(item.configuration)
              : item.configuration;

            // 提取UPH
            uph = config.uph || null;

            // 辅助函数：计算设备的板卡费用
            const calculateDeviceCost = (deviceConfig) => {
              if (!deviceConfig || !deviceConfig.cards || deviceConfig.cards.length === 0) {
                return 0;
              }

              const machine = machines.find(m => m.id === deviceConfig.id);
              if (!machine) {
                return 0;
              }

              let deviceCost = 0;
              deviceConfig.cards.forEach(cardInfo => {
                const card = cardTypes.find(c => c.id === cardInfo.id);
                if (card && cardInfo.quantity > 0) {
                  // 板卡单价 / 10000
                  let adjustedPrice = (card.unit_price || 0) / 10000;

                  // 汇率转换
                  if (record.currency === 'USD') {
                    if (machine.currency === 'CNY' || machine.currency === 'RMB') {
                      adjustedPrice = adjustedPrice / (record.exchange_rate || 7.2);
                    }
                  } else {
                    if (!machine.exchange_rate) {
                      console.error(`设备 ${machine.name} 缺少 exchange_rate`);
                      return;
                    }
                    adjustedPrice = adjustedPrice * machine.exchange_rate;
                  }

                  // 应用折扣率和数量
                  if (!machine.discount_rate) {
                    console.error(`设备 ${machine.name} 缺少 discount_rate`);
                    return;
                  }
                  const hourlyCost = adjustedPrice * machine.discount_rate * (cardInfo.quantity || 1);
                  deviceCost += hourlyCost;
                }
              });

              return deviceCost;
            };

            // 计算机时费率（基于所选板卡）
            if (machines.length > 0 && cardTypes.length > 0) {
              let totalHourlyCost = 0;

              // 计算测试机费用
              if (config.test_machine) {
                totalHourlyCost += calculateDeviceCost(config.test_machine);
              }

              // 计算探针台费用（CP工序）
              if (config.prober) {
                totalHourlyCost += calculateDeviceCost(config.prober);
              }

              // 计算分选机费用（FT工序）
              if (config.handler) {
                totalHourlyCost += calculateDeviceCost(config.handler);
              }

              if (totalHourlyCost > 0) {
                const currencySymbol = record.currency === 'USD' ? '$' : '¥';
                hourlyRate = `${currencySymbol}${totalHourlyCost.toFixed(2)}/小时`;
              }
            }
          } catch (e) {
            console.warn('无法解析工序配置:', e);
          }
        }

        return {
          ...item,
          uph: uph,
          hourly_rate: hourlyRate || '-'
        };
      };

      const processDetailColumns = [
        {
          title: '工序名称',
          dataIndex: 'item_name',
          key: 'item_name',
          render: (text) => text || '-'
        },
        {
          title: '设备类型',
          dataIndex: 'machine_type',
          key: 'machine_type',
          render: (text) => text || '-'
        },
        {
          title: '设备型号',
          dataIndex: 'machine_model',
          key: 'machine_model',
          render: (text) => text || '-'
        },
        {
          title: '机时费率',
          dataIndex: 'hourly_rate',
          key: 'hourly_rate',
          render: (rate) => rate || '-'
        },
        {
          title: 'UPH',
          dataIndex: 'uph',
          key: 'uph',
          render: (text) => text || '-'
        },
        {
          title: '单颗报价',
          dataIndex: 'unit_price',
          key: 'unit_price',
          render: (price) => price ? `¥${price.toFixed(4)}` : '¥0.0000'
        }
      ];

      // 分离CP和FT工序，并解析配置
      const cpProcesses = record.quoteDetails
        .filter(item => {
          const name = item.item_name || '';
          const description = item.item_description || '';
          const machineType = item.machine_type || '';
          return name.includes('CP') || description.includes('CP') || machineType.includes('CP');
        })
        .map(parseProcessItem);

      const ftProcesses = record.quoteDetails
        .filter(item => {
          const name = item.item_name || '';
          const description = item.item_description || '';
          const machineType = item.machine_type || '';
          return name.includes('FT') || description.includes('FT') || machineType.includes('FT');
        })
        .map(parseProcessItem);

      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px', color: '#1890ff' }}>报价明细</h4>
          
          {/* CP工序表格 */}
          {cpProcesses.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h5 style={{ marginBottom: '8px', color: '#52c41a' }}>🔬 CP工序</h5>
              <Table
                columns={processDetailColumns}
                dataSource={cpProcesses}
                pagination={false}
                size="small"
                rowKey={(item, index) => `${record.id}_cp_${index}`}
                style={{ backgroundColor: 'white', marginBottom: '8px' }}
              />
              <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                💡 注：CP工序各道工序报价不可直接相加，请根据实际工艺流程选择
              </div>
            </div>
          )}
          
          {/* FT工序表格 */}
          {ftProcesses.length > 0 && (
            <div>
              <h5 style={{ marginBottom: '8px', color: '#1890ff' }}>📱 FT工序</h5>
              <Table
                columns={processDetailColumns}
                dataSource={ftProcesses}
                pagination={false}
                size="small"
                rowKey={(item, index) => `${record.id}_ft_${index}`}
                style={{ backgroundColor: 'white', marginBottom: '8px' }}
              />
              <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                💡 注：FT工序各道工序报价不可直接相加，请根据实际工艺流程选择
              </div>
            </div>
          )}
        </div>
      );
    }

    // 其他报价类型使用原有的表格显示
    const detailColumns = [
      {
        title: '测试类型',
        dataIndex: 'item_name',
        key: 'item_name',
        render: (text) => text || '-'
      },
      {
        title: '设备类型',
        dataIndex: 'machine_type', 
        key: 'machine_type',
        render: (text) => text || '-'
      },
      {
        title: '设备型号',
        dataIndex: 'machine_model',
        key: 'machine_model', 
        render: (text) => text || '-'
      },
      {
        title: '小时费率',
        dataIndex: 'unit_price',
        key: 'unit_price',
        render: (price) => price ? `¥${price.toLocaleString()}/小时` : '-'
      }
    ];

    return (
      <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
        <h4 style={{ marginBottom: '16px', color: '#1890ff' }}>报价明细</h4>
        <Table
          columns={detailColumns}
          dataSource={record.quoteDetails}
          pagination={false}
          size="small"
          rowKey={(item, index) => `${record.id}_${index}`}
          style={{ backgroundColor: 'white' }}
        />
      </div>
    );
  };

  return (
    <div className="quote-management" style={{ 
      padding: isMobile ? '8px' : '24px',
      backgroundColor: isMobile ? '#f5f5f5' : 'inherit'
    }}>
      {/* 页面标题 */}
      <div className="page-header" style={{ 
        marginBottom: isMobile ? '12px' : '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: isMobile ? 'flex-start' : 'center',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? '12px' : '0'
      }}>
        <h1 style={{ 
          fontSize: isMobile ? '20px' : '28px',
          margin: '0'
        }}>
          报价单管理
        </h1>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            size={isMobile ? "middle" : "default"}
            onClick={() => navigate('/quote-type-selection')}
            style={{ width: isMobile ? '100%' : 'auto' }}
          >
            新建报价单
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={isMobile ? [8, 8] : [16, 16]} className="statistics-cards">
        <Col xs={12} sm={12} md={6}>
          <Card size={isMobile ? "small" : "default"}>
            <Statistic 
              title="总报价单" 
              value={statistics.total}
              valueStyle={{ fontSize: isMobile ? '20px' : '24px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card size={isMobile ? "small" : "default"}>
            <Statistic 
              title="待审批" 
              value={statistics.pending} 
              valueStyle={{ 
                color: '#1890ff',
                fontSize: isMobile ? '20px' : '24px'
              }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card size={isMobile ? "small" : "default"}>
            <Statistic 
              title="已批准" 
              value={statistics.approved}
              valueStyle={{ 
                color: '#52c41a',
                fontSize: isMobile ? '20px' : '24px'
              }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card size={isMobile ? "small" : "default"}>
            <Statistic 
              title="已拒绝" 
              value={statistics.rejected}
              valueStyle={{ 
                color: '#f5222d',
                fontSize: isMobile ? '20px' : '24px'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 报价单列表 */}
      {isMobile ? (
        <Card 
          title="报价单列表" 
          style={{ marginBottom: 16 }}
          size="small"
          bodyStyle={{ padding: '8px' }}
        >
          {renderMobileList()}
        </Card>
      ) : (
        <Card title="报价单列表" style={{ marginBottom: 16 }}>
          <Table
            columns={columns}
            dataSource={quotes}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1200, y: 600 }}
            expandable={{
              expandedRowRender: (record) => renderQuoteDetailsTable(record),
              rowExpandable: (record) => record.quoteDetails && record.quoteDetails.length > 0,
              expandRowByClick: false
            }}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
              pageSize: 10
            }}
            size="middle"
          />
        </Card>
      )}
    </div>
  );
};

export default QuoteManagement;