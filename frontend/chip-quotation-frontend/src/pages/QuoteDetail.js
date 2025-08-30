import React, { useState, useEffect } from 'react';
import { 
  Card, Descriptions, Table, Button, Space, Tag, 
  Divider, Row, Col, Modal, message, 
  Spin, Empty
} from 'antd';
import { 
  ArrowLeftOutlined, DownloadOutlined, 
  EditOutlined, DeleteOutlined, SendOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import QuoteApiService from '../services/quoteApi';
import '../styles/QuoteDetail.css';

const { confirm } = Modal;

const QuoteDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [quote, setQuote] = useState(null);

  useEffect(() => {
    fetchQuoteDetail();
  }, [id]);

  const fetchQuoteDetail = async () => {
    setLoading(true);
    try {
      const quoteData = await QuoteApiService.getQuoteDetailTest(id);
      
      if (quoteData.error) {
        throw new Error(quoteData.error);
      }
      
      // 格式化数据显示
      const formattedQuote = {
        id: quoteData.quote_number,
        quoteId: quoteData.id,  // 保存实际ID用于操作
        title: quoteData.title,
        type: QuoteApiService.mapQuoteTypeFromBackend(quoteData.quote_type),
        customer: quoteData.customer_name,
        currency: quoteData.currency || 'CNY',
        status: QuoteApiService.mapStatusFromBackend(quoteData.status),
        createdBy: quoteData.creator_name || `用户${quoteData.created_by}`,
        createdAt: new Date(quoteData.created_at).toLocaleString('zh-CN'),
        updatedAt: new Date(quoteData.updated_at).toLocaleString('zh-CN'),
        validUntil: quoteData.valid_until ? new Date(quoteData.valid_until).toLocaleDateString('zh-CN') : '-',
        approvedBy: quoteData.approved_by_name,
        approvedAt: quoteData.approved_at ? new Date(quoteData.approved_at).toLocaleString('zh-CN') : null,
        totalAmount: quoteData.total_amount || 0,
        discount: quoteData.discount || 0,
        description: quoteData.description,
        items: quoteData.items?.map(item => ({
          key: item.id?.toString(),
          itemName: item.item_name,
          itemDescription: item.item_description,
          machineType: item.machine_type,
          supplier: item.supplier,
          machine: item.machine_model,
          quantity: item.quantity,
          unit: item.unit,
          unitPrice: item.unit_price,
          totalPrice: item.total_price,
          configuration: item.configuration,
          uph: item.uph,
          hourlyRate: item.hourly_rate
        })) || []
      };
      
      setQuote(formattedQuote);
    } catch (error) {
      console.error('获取报价单详情失败:', error);
      message.error('获取报价单详情失败');
      setQuote(null);
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <FileTextOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> }
    };
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
    return <Tag color={typeColors[type]} style={{ fontSize: '14px', padding: '4px 12px' }}>{type}</Tag>;
  };

  const handleEdit = () => {
    message.info(`编辑报价单 ${quote.id}`);
  };

  const handleDelete = () => {
    confirm({
      title: '确认删除',
      content: `确定要删除报价单 ${quote.id} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await QuoteApiService.deleteQuote(quote.quoteId);
          message.success('删除成功');
          navigate(-1);
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  const handleDownload = () => {
    message.info(`下载报价单 ${quote.id}`);
  };

  const handleSubmitApproval = async () => {
    try {
      await QuoteApiService.submitForApproval(quote.quoteId);
      message.success('审批提交成功！审批人将在企业微信中收到通知。');
      fetchQuoteDetail(); // 重新获取数据
    } catch (error) {
      console.error('提交审批失败:', error);
      message.error('提交审批失败');
    }
  };

  const itemColumns = [
    {
      title: '测试类型',
      dataIndex: 'itemName',
      key: 'itemName',
      render: (text) => text || '-'
    },
    {
      title: '设备类型',
      dataIndex: 'machineType',
      key: 'machineType',
      render: (text) => text || '-'
    },
    {
      title: '设备型号',
      dataIndex: 'machine',
      key: 'machine',
      render: (text) => text || '-'
    },
    {
      title: '小时费率',
      dataIndex: 'unitPrice',
      key: 'unitPrice',
      render: (price) => price ? `¥${price.toLocaleString()}/小时` : '-'
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!quote) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Empty description="报价单不存在" />
        <Button type="primary" onClick={() => navigate(-1)} style={{ marginTop: '16px' }}>
          返回
        </Button>
      </div>
    );
  }

  return (
    <div className="quote-detail">
      {/* Header */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
              返回
            </Button>
            <h2 style={{ margin: 0 }}>{quote.title}</h2>
            {getStatusTag(quote.status)}
            {getTypeTag(quote.type)}
          </div>
          
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleDownload}>
              下载
            </Button>
            {quote.status === 'draft' && (
              <>
                <Button icon={<EditOutlined />} onClick={handleEdit}>
                  编辑
                </Button>
                <Button 
                  type="primary" 
                  icon={<SendOutlined />} 
                  onClick={handleSubmitApproval}
                >
                  提交审批
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                  删除
                </Button>
              </>
            )}
          </Space>
        </div>
      </Card>

      <Row gutter={16} style={{ marginTop: '16px' }}>
        {/* Basic Information */}
        <Col xs={24}>
          <Card title="基本信息">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="报价单号">{quote.id}</Descriptions.Item>
              <Descriptions.Item label="客户">{quote.customer}</Descriptions.Item>
              <Descriptions.Item label="报价类型">{quote.type}</Descriptions.Item>
              <Descriptions.Item label="币种">{quote.currency}</Descriptions.Item>
              <Descriptions.Item label="创建人">{quote.createdBy}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{quote.createdAt}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{quote.updatedAt}</Descriptions.Item>
              <Descriptions.Item label="有效期至">{quote.validUntil}</Descriptions.Item>
              {quote.approvedBy && (
                <>
                  <Descriptions.Item label="审批人">{quote.approvedBy}</Descriptions.Item>
                  <Descriptions.Item label="审批时间">{quote.approvedAt}</Descriptions.Item>
                </>
              )}
            </Descriptions>
            
            {quote.description && (
              <>
                <Divider />
                <div>
                  <h4>报价说明：</h4>
                  <p>{quote.description}</p>
                </div>
              </>
            )}
          </Card>
        </Col>
      </Row>

      {/* Items Detail */}
      <Card title="报价明细" style={{ marginTop: '16px' }}>
        {(quote.type === '工装夹具报价') ? (
          <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
            
            {/* 1. 工装夹具清单 */}
            {(() => {
              const toolingItems = quote.items.filter(item => 
                item.unit === '件' && !item.itemName?.includes('程序') && !item.itemName?.includes('调试') && !item.itemName?.includes('设计')
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
                        <span>工装夹具</span>
                        <span>{item.itemName || '-'}</span>
                        <span>¥{(item.unitPrice || 0).toFixed(2)}</span>
                        <span>{item.quantity || 0}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.totalPrice || 0).toFixed(2)}
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
                      工装夹具总价: ¥{toolingItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              );
            })()}
            
            {/* 2. 工程费用 */}
            {(() => {
              const engineeringItems = quote.items.filter(item => 
                item.unit === '项' && (item.itemName?.includes('测试程序') || item.itemName?.includes('程序开发') || item.itemName?.includes('夹具设计') || 
                                     item.itemName?.includes('测试验证') || item.itemName?.includes('文档') || item.itemName?.includes('设计'))
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
                        <span>{item.itemName}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{item.totalPrice?.toFixed(2)}
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
                      工程费用总价: ¥{engineeringItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              );
            })()}
            
            {/* 3. 量产准备费用 */}
            {(() => {
              const productionItems = quote.items.filter(item => 
                item.unit === '项' && (item.itemName?.includes('调试') || item.itemName?.includes('校准') || item.itemName?.includes('检验') || 
                                     item.itemName?.includes('设备调试') || item.itemName?.includes('调试费'))
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
                        <span>{item.itemName}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{item.totalPrice?.toFixed(2)}
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
                      量产准备费用总价: ¥{productionItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        ) : quote.type === '工程机时报价' ? (
          <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
            
            {/* 1. 机器设备 */}
            {(() => {
              const machineItems = quote.items.filter(item => 
                item.machineType && item.machineType !== '人员'
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
                        <span>{item.machineType}</span>
                        <span>{item.machineModel || item.itemName}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.unitPrice || 0).toFixed(2)}/小时
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
            
            {/* 2. 人员费用 */}
            {(() => {
              const personnelItems = quote.items.filter(item => 
                item.machineType === '人员' || 
                (item.itemName && (item.itemName === '工程师' || item.itemName === '技术员'))
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
                        <span>{item.itemName || item.machineModel}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.unitPrice || 0).toFixed(2)}/小时
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        ) : quote.type === '量产机时报价' ? (
          <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px' }}>报价明细</h4>
            
            {/* FT测试设备 */}
            {(() => {
              const ftItems = quote.items.filter(item => 
                item.itemDescription && item.itemDescription.includes('FT')
              );
              
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
                        <span>{item.machineType || '-'}</span>
                        <span>{item.machine || item.itemName || '-'}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.unitPrice || 0).toFixed(2)}/小时
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
                        ¥{ftItems.reduce((sum, item) => sum + (item.unitPrice || 0), 0).toFixed(2)}/小时
                      </span>
                    </div>
                  </div>
                </div>
              );
            })()}
            
            {/* CP测试设备 */}
            {(() => {
              const cpItems = quote.items.filter(item => 
                item.itemDescription && item.itemDescription.includes('CP')
              );
              
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
                        <span>{item.machineType || '-'}</span>
                        <span>{item.machine || item.itemName || '-'}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.unitPrice || 0).toFixed(2)}/小时
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
                        ¥{cpItems.reduce((sum, item) => sum + (item.unitPrice || 0), 0).toFixed(2)}/小时
                      </span>
                    </div>
                  </div>
                </div>
              );
            })()}
            
            {/* 辅助设备 */}
            {(() => {
              const auxItems = quote.items.filter(item => 
                item.machineType === '辅助设备' || 
                (!item.itemName?.includes('FT') && !item.itemName?.includes('CP') && 
                 item.machineType && item.machineType !== '测试机' && item.machineType !== '分选机' && item.machineType !== '探针台')
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
                        <span>{item.machineType || '-'}</span>
                        <span>{item.machine || item.itemName || '-'}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          ¥{(item.unitPrice || 0).toFixed(2)}/小时
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        ) : (quote.type === '量产工序报价' || quote.type === '工序报价' || quote.quote_type === 'process') ? (
          (() => {
            // 定义工序表格列
            const processColumns = [
              {
                title: '工序名称',
                dataIndex: 'itemName',
                key: 'itemName',
                render: (text) => text || '-'
              },
              {
                title: '设备类型',
                dataIndex: 'machineType',
                key: 'machineType',
                render: (text) => text || '-'
              },
              {
                title: '设备型号',
                dataIndex: 'machine',
                key: 'machine',
                render: (text, record) => text || record.itemName?.split('-')[1] || '-'
              },
              {
                title: '机时费率',
                dataIndex: 'hourlyRate',
                key: 'hourlyRate',
                render: (rate) => rate || '¥0.00/小时'
              },
              {
                title: 'UPH',
                dataIndex: 'uph',
                key: 'uph',
                render: (text) => text || '-'
              },
              {
                title: '单颗报价',
                dataIndex: 'unitPrice',
                key: 'unitPrice',
                render: (price) => price ? `¥${price.toFixed(4)}` : '¥0.0000'
              }
            ];

            // 分离CP和FT工序
            const cpProcesses = quote.items.filter(item => {
              const name = item.itemName || '';
              const description = item.itemDescription || '';
              const machineType = item.machineType || '';
              return name.includes('CP') || description.includes('CP') || machineType.includes('CP');
            });

            const ftProcesses = quote.items.filter(item => {
              const name = item.itemName || '';
              const description = item.itemDescription || '';
              const machineType = item.machineType || '';
              return name.includes('FT') || description.includes('FT') || machineType.includes('FT');
            });

            return (
              <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
                <h4 style={{ marginBottom: '16px', color: '#1890ff' }}>报价明细</h4>
                
                {/* CP工序表格 */}
                {cpProcesses.length > 0 && (
                  <div style={{ marginBottom: '20px' }}>
                    <h5 style={{ marginBottom: '8px', color: '#52c41a' }}>🔬 CP工序</h5>
                    <Table
                      columns={processColumns}
                      dataSource={cpProcesses}
                      pagination={false}
                      size="small"
                      bordered
                      rowKey={(item, index) => `cp_${index}`}
                      style={{ marginBottom: '8px' }}
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
                      columns={processColumns}
                      dataSource={ftProcesses}
                      pagination={false}
                      size="small"
                      bordered
                      rowKey={(item, index) => `ft_${index}`}
                      style={{ marginBottom: '8px' }}
                    />
                    <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                      💡 注：FT工序各道工序报价不可直接相加，请根据实际工艺流程选择
                    </div>
                  </div>
                )}
              </div>
            );
          })()
        ) : (
          // 其他报价类型使用普通表格显示
          <Table
            columns={itemColumns}
            dataSource={quote.items}
            pagination={false}
            bordered
          />
        )}
      </Card>
    </div>
  );
};

export default QuoteDetail;