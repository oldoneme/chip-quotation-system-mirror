import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Space, Tag, Row, Col, Statistic, message, Modal
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, CopyOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import QuoteApiService from '../services/quoteApi';
import '../styles/QuoteManagement.css';

const { confirm } = Modal;

const QuoteManagement = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [quotes, setQuotes] = useState([]);
  
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
        id: quote.quote_number,
        quoteId: quote.id,  // 保存实际ID用于操作
        title: quote.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quote.quote_type),
        customer: quote.customer_name,
        currency: quote.currency || 'CNY',
        status: QuoteApiService.mapStatusFromBackend(quote.status),
        createdBy: quote.creator_name || `用户${quote.created_by}`,
        createdAt: new Date(quote.created_at).toLocaleString('zh-CN'),
        updatedAt: new Date(quote.updated_at).toLocaleString('zh-CN'),
        validUntil: quote.valid_until ? new Date(quote.valid_until).toLocaleDateString('zh-CN') : '-',
        totalAmount: quote.total_amount,
        quoteDetails: quote.quote_details || []
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

  useEffect(() => {
    fetchQuotes();
    fetchStatistics();
  }, []);

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <EditOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    };
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon}>
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
      dataIndex: 'id',
      key: 'id',
      render: (text) => <a onClick={() => handleView(text)}>{text}</a>
    },
    {
      title: '报价标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: '报价类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => getTypeTag(type)
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status)
    },
    {
      title: '创建人',
      dataIndex: 'createdBy',
      key: 'createdBy'
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '有效期至',
      dataIndex: 'validUntil',
      key: 'validUntil'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          {record.status === 'draft' && (
            <>
              <Button 
                type="link" 
                icon={<EditOutlined />} 
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Button 
                type="link" 
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

  const handleEdit = (record) => {
    message.info(`编辑报价单 ${record.id}`);
    // 根据类型导航到对应的编辑页面
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

  const renderQuoteDetails = (record) => {
    if (!record.quoteDetails || record.quoteDetails.length === 0) {
      return <div style={{ padding: '16px', color: '#666' }}>暂无报价明细</div>;
    }

    // 工装夹具报价使用三大类别显示
    if (record.type === '工装夹具报价') {
      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
          
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

    // 量产工序报价使用分类显示（兼容不同的类型名称）
    if (record.type === '量产工序报价' || record.type === '工序报价' || record.quote_type === 'process') {
      console.log('渲染工序报价明细 - record:', record);
      console.log('渲染工序报价明细 - quoteDetails:', record.quoteDetails);
      
      return (
        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
          <h4 style={{ marginBottom: '16px' }}>费用明细</h4>
          
          {/* CP工序费用详情 */}
          {(() => {
            // 筛选出CP工序（优先使用item_name判断）
            const cpProcesses = record.quoteDetails.filter(item => {
              // 优先检查item_name
              const name = item.item_name || '';
              if (name.startsWith('CP-')) return true;
              
              // 其次检查item_description
              const description = item.item_description || '';
              if (description.includes('CP工序')) return true;
              
              // 最后检查machine_type
              const machineType = item.machine_type || '';
              if (machineType.includes('CP')) return true;
              
              return false;
            });
            
            return cpProcesses && cpProcesses.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h5 style={{ 
                  color: '#52c41a', 
                  marginBottom: 12,
                  fontSize: '14px',
                  fontWeight: 'bold',
                  borderBottom: '2px solid #52c41a',
                  paddingBottom: '6px'
                }}>🔬 CP工序</h5>
                {cpProcesses.map((item, index) => (
                  <div key={index} style={{ 
                    marginBottom: 15, 
                    border: '1px solid #d9f7be', 
                    borderRadius: '6px', 
                    padding: '12px',
                    backgroundColor: '#f6ffed'
                  }}>
                    <div style={{ 
                      fontWeight: 'bold', 
                      marginBottom: 10, 
                      color: '#52c41a',
                      fontSize: '14px'
                    }}>
                      {item.item_name || '-'}
                    </div>
                    
                    {/* 设备成本 */}
                    <div style={{ marginBottom: 10 }}>
                      <h6 style={{ color: '#389e0d', marginBottom: 6, fontSize: '12px', fontWeight: 'bold' }}>💻 设备成本</h6>
                      <div style={{ paddingLeft: 10, backgroundColor: '#fff', borderRadius: '3px', padding: '8px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: '6px', fontSize: '11px' }}>
                          <div><strong>设备类型:</strong> {item.machine_type || 'CP测试机'}</div>
                          <div><strong>设备型号:</strong> {item.machine_model || item.item_name?.split('-')[1] || 'ETS-88'}</div>
                          <div><strong>机时费率:</strong> 
                            <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                              {item.hourly_rate || '¥0.00/小时'}
                            </span>
                          </div>
                          <div><strong>UPH:</strong> {item.uph || '-'}</div>
                          <div><strong>单颗报价:</strong> 
                            <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                              ¥{(item.unit_price || 0).toFixed(4)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* 工序总成本 */}
                    <div style={{ 
                      marginTop: 10,
                      paddingTop: 8,
                      borderTop: '1px solid #52c41a',
                      textAlign: 'right'
                    }}>
                      <div style={{ 
                        fontSize: '12px', 
                        fontWeight: 'bold', 
                        color: '#52c41a'
                      }}>
                        工序总成本: ¥{(item.unit_price || 0).toFixed(4)}
                      </div>
                    </div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', marginTop: 10, fontSize: '11px', color: '#666', fontStyle: 'italic', backgroundColor: '#f0f0f0', padding: '6px', borderRadius: '3px' }}>
                  💡 注：CP工序各道工序报价不可直接相加，请根据实际工艺流程选择
                </div>
              </div>
            );
          })()}
          
          {/* FT工序费用详情 */}
          {(() => {
            // 筛选出FT工序（优先使用item_name判断）
            const ftProcesses = record.quoteDetails.filter(item => {
              // 优先检查item_name
              const name = item.item_name || '';
              if (name.startsWith('FT-')) return true;
              
              // 其次检查item_description
              const description = item.item_description || '';
              if (description.includes('FT工序')) return true;
              
              // 最后检查machine_type
              const machineType = item.machine_type || '';
              if (machineType.includes('FT')) return true;
              
              return false;
            });
            
            return ftProcesses && ftProcesses.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h5 style={{ 
                  color: '#1890ff', 
                  marginBottom: 12,
                  fontSize: '14px',
                  fontWeight: 'bold',
                  borderBottom: '2px solid #1890ff',
                  paddingBottom: '6px'
                }}>📱 FT工序</h5>
                {ftProcesses.map((item, index) => (
                  <div key={index} style={{ 
                    marginBottom: 15, 
                    border: '1px solid #91d5ff', 
                    borderRadius: '6px', 
                    padding: '12px',
                    backgroundColor: '#e6f7ff'
                  }}>
                    <div style={{ 
                      fontWeight: 'bold', 
                      marginBottom: 10, 
                      color: '#1890ff',
                      fontSize: '14px'
                    }}>
                      {item.item_name || '-'}
                    </div>
                    
                    {/* 设备成本 */}
                    <div style={{ marginBottom: 10 }}>
                      <h6 style={{ color: '#096dd9', marginBottom: 6, fontSize: '12px', fontWeight: 'bold' }}>💻 设备成本</h6>
                      <div style={{ paddingLeft: 10, backgroundColor: '#fff', borderRadius: '3px', padding: '8px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: '6px', fontSize: '11px' }}>
                          <div><strong>设备类型:</strong> {item.machine_type || 'FT测试机'}</div>
                          <div><strong>设备型号:</strong> {item.machine_model || item.item_name?.split('-')[1] || 'ETS-88'}</div>
                          <div><strong>机时费率:</strong> 
                            <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                              {item.hourly_rate || '¥0.00/小时'}
                            </span>
                          </div>
                          <div><strong>UPH:</strong> {item.uph || '-'}</div>
                          <div><strong>单颗报价:</strong> 
                            <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                              ¥{(item.unit_price || 0).toFixed(4)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* 工序总成本 */}
                    <div style={{ 
                      marginTop: 10,
                      paddingTop: 8,
                      borderTop: '1px solid #1890ff',
                      textAlign: 'right'
                    }}>
                      <div style={{ 
                        fontSize: '12px', 
                        fontWeight: 'bold', 
                        color: '#1890ff'
                      }}>
                        工序总成本: ¥{(item.unit_price || 0).toFixed(4)}
                      </div>
                    </div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', marginTop: 10, fontSize: '11px', color: '#666', fontStyle: 'italic', backgroundColor: '#f0f0f0', padding: '6px', borderRadius: '3px' }}>
                  💡 注：FT工序各道工序报价不可直接相加，请根据实际工艺流程选择
                </div>
              </div>
            );
          })()}
        </div>
      );
    }

    // 调试信息：打印报价类型
    console.log('QuoteManagement renderQuoteDetails - record.type:', record.type);
    console.log('QuoteManagement renderQuoteDetails - record.quote_type:', record.quote_type);
    console.log('QuoteManagement renderQuoteDetails - record:', record);
    
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
        <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
        <Table
          columns={detailColumns}
          dataSource={record.quoteDetails}
          pagination={false}
          size="small"
          rowKey={(item, index) => `${record.id}_${index}`}
        />
      </div>
    );
  };

  return (
    <div className="quote-management">
      {/* 页面标题 */}
      <div className="page-header">
        <h1>报价单管理</h1>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => navigate('/quote-type-selection')}
          >
            新建报价单
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="statistics-cards">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="总报价单" value={statistics.total} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="待审批" 
              value={statistics.pending} 
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="已批准" 
              value={statistics.approved}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic 
              title="已拒绝" 
              value={statistics.rejected}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={quotes}
          rowKey="id"
          loading={loading}
          expandable={{
            expandedRowRender: (record) => renderQuoteDetails(record),
            rowExpandable: (record) => record.quoteDetails && record.quoteDetails.length > 0,
          }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>
    </div>
  );
};

export default QuoteManagement;