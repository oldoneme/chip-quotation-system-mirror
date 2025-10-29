import React, { useState, useEffect, useMemo } from 'react';
import {
  Card, Descriptions, Table, Button, Space, Tag,
  Divider, Row, Col, Modal, message, List,
  Spin, Empty
} from 'antd';
import {
  ArrowLeftOutlined, DownloadOutlined, EyeOutlined,
  EditOutlined, DeleteOutlined, SendOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import QuoteApiService from '../services/quoteApi';
import api from '../services/api';
import ApprovalApiService from '../services/approvalApi';
import UnifiedApprovalPanel from '../components/UnifiedApprovalPanel';
import ApprovalHistory from '../components/ApprovalHistory';
import SubmitApprovalModal from '../components/SubmitApprovalModal';
import { useAuth } from '../contexts/AuthContext';
import { getColumnsForPDF } from '../utils/columnConfigurations';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import '../styles/QuoteDetail.css';

const { confirm } = Modal;

const QuoteDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const location = useLocation();
  const { user: currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const [approvers, setApprovers] = useState([]);
  const [submitApprovalModalVisible, setSubmitApprovalModalVisible] = useState(false);
  const [machines, setMachines] = useState([]);
  const [cardTypes, setCardTypes] = useState([]);

  // 解析URL上的JWT参数
  const urlJwt = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('jwt');
  }, [location.search]);

  const snapshotToken = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('__snapshot_token');
  }, [location.search]);

  // 检测是否是PDF快照生成模式
  const isSnapshotMode = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.get('userid') === 'snapshot-bot';
  }, [location.search]);

  // 检测移动端
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);

    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  // 加载设备和板卡数据（用于工序报价显示机时费率）
  useEffect(() => {
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

  useEffect(() => {
    (async () => {
      try {
        // 1) 处理一次性鉴权token（JWT 或 __snapshot_token），并清理URL
        const searchParams = new URLSearchParams(location.search);
        let urlMutated = false;

        if (urlJwt) {
          console.log('🔑 发现URL中的JWT，正在保存...');
          localStorage.setItem('jwt_token', urlJwt);
          searchParams.delete('jwt');
          urlMutated = true;
        }

        if (snapshotToken) {
          console.log('🪟 发现前端快照token，写入Cookie与请求头');
          document.cookie = `auth_token=${snapshotToken}; path=/; SameSite=Lax`;
          api.defaults.headers.common['Authorization'] = `Bearer ${snapshotToken}`;
          sessionStorage.setItem('__snapshot_token', snapshotToken);
          searchParams.delete('__snapshot_token');
          urlMutated = true;
        } else {
          const storedSnapshot = sessionStorage.getItem('__snapshot_token');
          if (storedSnapshot) {
            api.defaults.headers.common['Authorization'] = `Bearer ${storedSnapshot}`;
          }
        }

        if (urlMutated) {
          const cleanUrl = `${location.pathname}${searchParams.toString() ? `?${searchParams}` : ''}`;
          window.history.replaceState({}, '', cleanUrl);
          console.log('✅ 鉴权参数已处理，URL已清理');
        }

        // 2) 先探测登录状态（可选但推荐）
        try {
          console.log('🔍 检查认证状态...');
          await QuoteApiService.checkAuth();
          console.log('✅ 认证状态正常');
        } catch (e) {
          console.log('⚠️ 认证状态检查失败，将使用JWT兜底:', e.message);
        }

        // 3) 获取报价单详情，同时传递jwt作为兜底
        console.log('📋 开始获取报价单详情...');
        await fetchQuoteDetail();
        
      } catch (error) {
        console.error('❌ 初始化失败:', error);
        setLoading(false);
      }
    })();
  }, [id, urlJwt]); // 移除 location.pathname 和 location.search 以避免过度刷新

  const fetchQuoteDetail = async () => {
    setLoading(true);
    try {
      // 识别三类：UUID / 纯数字ID / 报价单号
      const isNumericId = /^\d+$/.test(id);
      const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
      
      // 获取存储的JWT作为兜底参数
      const storedJwt = localStorage.getItem('jwt_token');
      const params = storedJwt ? { jwt: storedJwt } : {};
      
      console.log('🔄 发起API请求:', { isUUID, isNumericId, id, hasJwtParam: !!params.jwt });
      
      let quoteData;
      if (isUUID) {
        // UUID格式，调用by-uuid接口（企业微信审批链接场景）
        console.log('📱 检测到UUID格式，调用by-uuid接口');
        quoteData = await QuoteApiService.getQuoteDetailByUuid(id, params);
      } else if (isNumericId) {
        // 纯数字，调用by-id接口
        console.log('🔢 检测到数字ID，调用by-id接口');
        quoteData = await QuoteApiService.getQuoteDetailById(id, params);
      } else {
        // 报价单号（如CIS-SH20250907001），调用detail接口
        console.log('📋 检测到报价单号，调用detail接口');
        quoteData = await QuoteApiService.getQuoteDetailTest(id, params);
      }
      
      if (quoteData.error) {
        throw new Error(quoteData.error);
      }
      
      console.log('✅ 报价单详情获取成功:', quoteData.quote_number);
      
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
        approvalStatus: quoteData.approval_status || 'not_submitted',
        currentApproverId: quoteData.current_approver_id,
        currentApproverName: quoteData.current_approver_name,
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
      console.error('❌ 获取报价单详情失败:', error);
      
      // 更友好的错误区分
      if (error?.response?.status === 401) {
        message.error('认证未生效，请返回企业微信重新进入');
      } else if (error?.response?.status === 404) {
        message.error('报价单不存在或已删除');
      } else {
        message.error('获取报价单详情失败，请稍后再试');
      }
      setQuote(null);
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status, approvalStatus) => {
    console.log('getStatusTag called with:', { status, approvalStatus });
    
    const statusConfig = {
      draft: { color: 'default', text: '草稿', icon: <FileTextOutlined /> },
      pending: { color: 'processing', text: '待审批', icon: <ClockCircleOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已驳回', icon: <CloseCircleOutlined /> }
    };
    
    // 特殊处理：被驳回后重新提交审批的状态
    if (status === 'rejected' && approvalStatus === 'pending') {
      console.log('显示重新审批中状态');
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
    return <Tag color={typeColors[type]} style={{ fontSize: '14px', padding: '4px 12px' }}>{type}</Tag>;
  };

  const handleEdit = async () => {
    // 根据报价类型跳转到对应的编辑页面
    const quoteTypeToPath = {
      '询价报价': '/inquiry-quote',
      '工装夹具报价': '/tooling-quote',
      '工程机时报价': '/engineering-quote',
      '量产机时报价': '/mass-production-quote',
      '量产工序报价': '/process-quote',
      '综合报价': '/comprehensive-quote'
    };

    const editPath = quoteTypeToPath[quote.type];
    if (editPath) {
      try {
        console.log('📝 从详情页编辑报价单:', quote.quoteId || quote.id);

        // 获取完整的报价单详情数据（包含items字段）
        // 使用原始的API数据，确保包含所有字段
        let fullQuoteData;
        if (quote.quoteId) {
          fullQuoteData = await QuoteApiService.getQuoteDetailById(quote.quoteId);
        } else {
          fullQuoteData = await QuoteApiService.getQuoteDetailById(quote.id);
        }
        console.log('📝 详情页获取完整报价数据:', fullQuoteData);

        // 传递完整的报价单数据到编辑页面
        navigate(editPath, {
          state: {
            editingQuote: fullQuoteData, // 使用完整的API数据
            isEditing: true,
            quoteId: quote.quoteId || quote.id
          }
        });
      } catch (error) {
        console.error('从详情页获取报价单详情失败:', error);
        message.error('获取报价单详情失败，请稍后重试');
      }
    } else {
      message.error('未知的报价类型，无法编辑');
    }
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
    // 获取列配置并传递给PDF生成
    const columnConfig = getColumnsForPDF(quote.type, quote.items);
    const configParam = encodeURIComponent(JSON.stringify(columnConfig));

    // 注意：api.js的baseURL已经是/api/v1，所以这里只需要/quotes/...
    const pdfUrl = `/api/v1/quotes/${quote.quoteId || quote.id}/pdf?download=true&columns=${configParam}`;
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `${quote.id}_报价单.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    message.success('PDF下载已开始');
  };

  const handlePreview = async () => {
    // 获取列配置并传递给PDF生成
    const columnConfig = getColumnsForPDF(quote.type, quote.items);
    const configParam = encodeURIComponent(JSON.stringify(columnConfig));

    // 使用报价单号或数字ID（后端支持报价单号、数字ID和UUID）
    const quoteIdentifier = quote.quoteId || quote.id;
    // 注意：axios api的baseURL已经是/api/v1，所以这里只用/quotes/...
    const pdfUrl = `/quotes/${quoteIdentifier}/pdf?download=false&columns=${configParam}`;

    console.log('=== PDF预览调试信息 ===');
    console.log('quote.id (报价单号):', quote.id);
    console.log('quote.quoteId (数字ID):', quote.quoteId);
    console.log('使用的标识符:', quoteIdentifier);
    console.log('API请求URL (会加上baseURL /api/v1):', pdfUrl);

    try {
      // 第一步：先发送请求检查状态，不设置responseType
      const checkResponse = await api.get(pdfUrl, {
        validateStatus: (status) => status === 200 || status === 202
      });

      console.log('PDF预览响应状态:', checkResponse.status);
      console.log('PDF预览响应数据:', checkResponse.data);

      if (checkResponse.status === 202) {
        // PDF正在生成，显示弹窗
        Modal.info({
          title: 'PDF生成中',
          content: 'PDF正在生成中，请稍后再试',
          okText: '确定',
          onOk: async () => {
            // 用户点击确定后，再次检查PDF状态
            try {
              const retryCheckResponse = await api.get(pdfUrl, {
                validateStatus: (status) => status === 200 || status === 202
              });

              if (retryCheckResponse.status === 200) {
                // PDF已经生成，重新获取blob并打开
                const blobResponse = await api.get(pdfUrl, {
                  responseType: 'blob'
                });

                const blob = new Blob([blobResponse.data], { type: 'application/pdf' });
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');

                // 清理URL对象
                setTimeout(() => window.URL.revokeObjectURL(url), 100);
              } else if (retryCheckResponse.status === 202) {
                // 还是没有生成，不做任何操作（用户需要手动再次点击预览）
                message.info('PDF仍在生成中，请稍后再次点击预览');
              }
            } catch (error) {
              console.error('重试获取PDF失败:', error);
              message.error('获取PDF失败，请稍后再试');
            }
          }
        });
      } else if (checkResponse.status === 200) {
        // PDF已生成，重新获取blob并直接打开
        const blobResponse = await api.get(pdfUrl, {
          responseType: 'blob'
        });

        const blob = new Blob([blobResponse.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');

        // 清理URL对象
        setTimeout(() => window.URL.revokeObjectURL(url), 100);
      }
    } catch (error) {
      console.error('预览PDF失败:', error);
      console.error('错误详情:', error.response);
      message.error(`预览PDF失败: ${error.message}`);
    }
  };

  const handleSubmitApproval = () => {
    setSubmitApprovalModalVisible(true);
  };

  const handleSubmitApprovalSuccess = (result) => {
    setSubmitApprovalModalVisible(false);
    
    // 立即更新本地状态，显示为审批中
    setQuote(prevQuote => ({
      ...prevQuote,
      status: 'pending', // 更新为审批中
      approval_status: 'pending' // 设置为审批中
    }));
    
    // 然后重新获取最新数据
    fetchQuoteDetail();
  };

  const handleSubmitApprovalCancel = () => {
    setSubmitApprovalModalVisible(false);
  };

  // 处理审批操作
  const handleApprovalAction = async (action, data) => {
    setApprovalLoading(true);
    try {
      await ApprovalApiService.performApprovalAction(action, quote.quoteId, data);
      message.success(`${ApprovalApiService.getActionText(action)}成功`);
      await fetchQuoteDetail(); // 重新获取报价单数据
    } catch (error) {
      console.error(`${action}操作失败:`, error);
      throw error; // 重新抛出错误让组件处理
    } finally {
      setApprovalLoading(false);
    }
  };

  // 获取可用的审批人列表
  const fetchApprovers = async () => {
    try {
      // 这里应该调用API获取审批人列表
      // 暂时使用模拟数据
      setApprovers([
        { id: 1, name: '张经理', role: 'manager' },
        { id: 2, name: '李主管', role: 'supervisor' },
        { id: 3, name: '王总监', role: 'director' }
      ]);
    } catch (error) {
      console.error('获取审批人列表失败:', error);
    }
  };

  useEffect(() => {
    fetchApprovers();
  }, []);

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

  // 移动端列表渲染
  const renderMobileItemList = (items) => {
    if (!items || items.length === 0) {
      return <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>暂无数据</div>;
    }

    return (
      <List
        dataSource={items}
        size="small"
        renderItem={(item, index) => (
          <List.Item 
            key={index}
            style={{ 
              padding: '12px 0',
              borderBottom: index < items.length - 1 ? '1px solid #f0f0f0' : 'none'
            }}
          >
            <div style={{ width: '100%' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                marginBottom: '4px'
              }}>
                <span style={{ 
                  fontWeight: 'bold', 
                  color: '#1890ff',
                  fontSize: '14px'
                }}>
                  {item.itemName || '-'}
                </span>
                <span style={{ 
                  fontWeight: 'bold', 
                  color: '#52c41a' 
                }}>
                  {item.unitPrice ? `¥${item.unitPrice.toLocaleString()}/小时` : '-'}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div>设备类型：{item.machineType || '-'}</div>
                <div>设备型号：{item.machine || '-'}</div>
              </div>
            </div>
          </List.Item>
        )}
      />
    );
  };

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
    <div className="quote-detail" style={{ 
      padding: isMobile ? '8px' : '24px',
      backgroundColor: isMobile ? '#f5f5f5' : 'inherit'
    }}>
      {/* Header */}
      <Card>
        {isMobile ? (
          <div>
            {/* 移动端标题行 */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
              <Button 
                icon={<ArrowLeftOutlined />} 
                size="small"
                onClick={() => navigate(-1)}
                style={{ marginRight: '8px' }}
              >
                返回
              </Button>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ 
                  margin: 0, 
                  fontSize: '16px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {quote.title}
                </h3>
              </div>
            </div>
            
            {/* 移动端标签行 */}
            <div style={{ marginBottom: '12px' }}>
              <Space size={[4, 4]} wrap>
                {getStatusTag(quote.status, quote.approval_status)}
                {getTypeTag(quote.type)}
              </Space>
            </div>
            
            {/* 移动端操作按钮 */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={handlePreview}
              >
                预览PDF
              </Button>
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={handleDownload}
              >
                下载PDF
              </Button>
              {(quote.status === 'draft' || quote.status === 'rejected') && (
                <>
                  <Button
                    size="small"
                    icon={<EditOutlined />}
                    onClick={handleEdit}
                  >
                    编辑
                  </Button>
                  <Button
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={handleDelete}
                  >
                    删除
                  </Button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
                返回
              </Button>
              <h2 style={{ margin: 0 }}>{quote.title}</h2>
              {getStatusTag(quote.status, quote.approval_status)}
              {getTypeTag(quote.type)}
            </div>
            
            <Space>
              <Button icon={<EyeOutlined />} onClick={handlePreview}>
                预览PDF
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                下载PDF
              </Button>
              {(quote.status === 'draft' || quote.status === 'rejected') && (
                <>
                  <Button icon={<EditOutlined />} onClick={handleEdit}>
                    编辑
                  </Button>
                  <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                    删除
                  </Button>
                </>
              )}
            </Space>
          </div>
        )}
      </Card>

      <Row gutter={isMobile ? [8, 8] : [16, 16]} style={{ marginTop: '16px' }}>
        {/* Basic Information */}
        <Col xs={24}>
          <Card 
            title="基本信息" 
            size={isMobile ? "small" : "default"}
          >
            <Descriptions 
              column={isMobile ? 1 : 2} 
              bordered={!isMobile}
              size={isMobile ? "small" : "default"}
              layout={isMobile ? "vertical" : "horizontal"}
            >
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
                  <h4 style={{ fontSize: isMobile ? '14px' : '16px' }}>报价说明：</h4>
                  <p style={{ 
                    fontSize: isMobile ? '12px' : '14px',
                    lineHeight: '1.5',
                    wordBreak: 'break-all'
                  }}>
                    {quote.description}
                  </p>
                </div>
              </>
            )}
          </Card>
        </Col>
      </Row>

      {/* Items Detail */}
      <Card title="报价明细" style={{ marginTop: '16px' }}>
        {(quote.type === '工装夹具报价') ? (
          <div style={{ padding: isMobile ? '8px' : '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px', fontSize: isMobile ? '14px' : '16px' }}>报价明细</h4>
            
            {/* 1. 工装夹具清单 */}
            {(() => {
              const toolingItems = quote.items.filter(item => 
                item.unit === '件' && !item.itemName?.includes('程序') && !item.itemName?.includes('调试') && !item.itemName?.includes('设计')
              );
              
              return toolingItems && toolingItems.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>🔧 1. 工装夹具清单</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {toolingItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{item.itemName || '-'}</span>
                            <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>¥{(item.totalPrice || 0).toFixed(2)}</span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            <div>类别: 工装夹具</div>
                            <div>单价: ¥{(item.unitPrice || 0).toFixed(2)}</div>
                            <div>数量: {item.quantity || 0}</div>
                          </div>
                        </div>
                      ))}
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        color: '#1890ff'
                      }}>
                        工装夹具总价: ¥{toolingItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                      </div>
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
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
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>⚙️ 2. 工程费用</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {engineeringItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span style={{ fontWeight: '500', fontSize: '13px' }}>{item.itemName}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                            ¥{item.totalPrice?.toFixed(2)}
                          </span>
                        </div>
                      ))}
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        color: '#1890ff'
                      }}>
                        工程费用总价: ¥{engineeringItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                      </div>
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
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
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>🏭 3. 量产准备费用</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {productionItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span style={{ fontWeight: '500', fontSize: '13px' }}>{item.itemName}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                            ¥{item.totalPrice?.toFixed(2)}
                          </span>
                        </div>
                      ))}
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        color: '#1890ff'
                      }}>
                        量产准备费用总价: ¥{productionItems.reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}
                      </div>
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
                </div>
              );
            })()}
          </div>
        ) : quote.type === '工程机时报价' ? (
          <div style={{ padding: isMobile ? '8px' : '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px', fontSize: isMobile ? '14px' : '16px' }}>报价明细</h4>
            
            {/* 1. 机器设备 */}
            {(() => {
              // 聚合同类设备的板卡为单一设备项
              const machineItemsRaw = quote.items.filter(item =>
                item.machineType && item.machineType !== '人员'
              );

              // 按设备类型聚合（不按型号，直接按类型）
              const aggregatedMachines = {};
              machineItemsRaw.forEach(item => {
                const machineKey = item.machineType;
                if (!aggregatedMachines[machineKey]) {
                  aggregatedMachines[machineKey] = {
                    machineType: item.machineType,
                    machineModel: item.machineModel || item.itemName,
                    itemName: item.machineModel || item.itemName,
                    totalPrice: 0,
                    itemCount: 0,
                    items: []
                  };
                }
                aggregatedMachines[machineKey].totalPrice += (item.unitPrice || 0);
                aggregatedMachines[machineKey].itemCount += 1;
                aggregatedMachines[machineKey].items.push(item);

                // 如果是同类型的第一个设备，使用其型号；如果有多个不同型号，显示类型名
                if (aggregatedMachines[machineKey].itemCount === 1) {
                  aggregatedMachines[machineKey].machineModel = item.machineModel || item.itemName;
                } else {
                  // 有多个项目时，检查是否同一型号
                  const currentModel = item.machineModel || item.itemName;
                  if (aggregatedMachines[machineKey].machineModel !== currentModel) {
                    aggregatedMachines[machineKey].machineModel = machineKey; // 使用设备类型名
                  }
                }
              });

              const machineItems = Object.values(aggregatedMachines).map(machine => ({
                ...machine,
                unitPrice: machine.totalPrice,
                // 显示名称：如果只有一个型号就显示型号，否则显示类型
                displayName: machine.itemCount > 1 && machine.machineModel === machine.machineType
                  ? `${machine.machineType}(${machine.itemCount}个板卡)`
                  : machine.machineModel
              }));
              
              return machineItems && machineItems.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>🔧 1. 机器设备</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {machineItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{item.displayName || item.machineModel || item.itemName}</span>
                            <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                              ¥{(item.unitPrice || 0).toFixed(2)}/小时
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            设备类型: {item.machineType}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                          <span>{item.displayName || item.machineModel || item.itemName}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                            ¥{(item.unitPrice || 0).toFixed(2)}/小时
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
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
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>👨‍💼 2. 人员费用</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {personnelItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span style={{ fontWeight: '500', fontSize: '13px' }}>{item.itemName || item.machineModel}</span>
                          <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                            ¥{(item.unitPrice || 0).toFixed(2)}/小时
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
                </div>
              );
            })()}
          </div>
        ) : quote.type === '量产机时报价' ? (
          <div style={{ padding: isMobile ? '8px' : '16px', backgroundColor: '#fafafa' }}>
            <h4 style={{ marginBottom: '16px', fontSize: isMobile ? '14px' : '16px' }}>报价明细</h4>
            
            {/* FT测试设备 */}
            {(() => {
              const ftItems = quote.items.filter(item => 
                item.itemDescription && item.itemDescription.includes('FT')
              );
              
              return ftItems && ftItems.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>📱 FT测试设备</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {ftItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{item.machine || item.itemName || '-'}</span>
                            <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                              ¥{(item.unitPrice || 0).toFixed(2)}/小时
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            设备类型: {item.machineType || '-'}
                          </div>
                        </div>
                      ))}
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        color: '#1890ff'
                      }}>
                        FT设备小计: ¥{ftItems.reduce((sum, item) => sum + (item.unitPrice || 0), 0).toFixed(2)}/小时
                      </div>
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
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
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>🔬 CP测试设备</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {cpItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{item.machine || item.itemName || '-'}</span>
                            <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                              ¥{(item.unitPrice || 0).toFixed(2)}/小时
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            设备类型: {item.machineType || '-'}
                          </div>
                        </div>
                      ))}
                      <div style={{
                        padding: '12px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        color: '#1890ff'
                      }}>
                        CP设备小计: ¥{cpItems.reduce((sum, item) => sum + (item.unitPrice || 0), 0).toFixed(2)}/小时
                      </div>
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
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
                  <h5 style={{ fontSize: isMobile ? '13px' : '14px' }}>🔧 辅助设备</h5>
                  {isMobile ? (
                    // Mobile: Card-based layout
                    <div>
                      {auxItems.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{item.machine || item.itemName || '-'}</span>
                            <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                              ¥{(item.unitPrice || 0).toFixed(2)}/小时
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            设备类型: {item.machineType || '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    // Desktop: Table layout
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
                  )}
                </div>
              );
            })()}
          </div>
        ) : (quote.type === '量产工序报价' || quote.type === '工序报价' || quote.quote_type === 'process') ? (
          (() => {
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
                  const calculateDeviceCost = (deviceConfig, deviceType) => {
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
                        if (quote.currency === 'USD') {
                          if (machine.currency === 'CNY' || machine.currency === 'RMB') {
                            adjustedPrice = adjustedPrice / (quote.exchange_rate || 7.2);
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
                      totalHourlyCost += calculateDeviceCost(config.test_machine, 'test_machine');
                    }

                    // 计算探针台费用（CP工序）
                    if (config.prober) {
                      totalHourlyCost += calculateDeviceCost(config.prober, 'prober');
                    }

                    // 计算分选机费用（FT工序）
                    if (config.handler) {
                      totalHourlyCost += calculateDeviceCost(config.handler, 'handler');
                    }

                    if (totalHourlyCost > 0) {
                      const currencySymbol = quote.currency === 'USD' ? '$' : '¥';
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
                hourlyRate: hourlyRate || '-'
              };
            };

            // 分离CP和FT工序，并解析配置
            const cpProcesses = quote.items
              .filter(item => {
                const name = item.itemName || '';
                const description = item.itemDescription || '';
                const machineType = item.machineType || '';
                return name.includes('CP') || description.includes('CP') || machineType.includes('CP');
              })
              .map(parseProcessItem);

            const ftProcesses = quote.items
              .filter(item => {
                const name = item.itemName || '';
                const description = item.itemDescription || '';
                const machineType = item.machineType || '';
                return name.includes('FT') || description.includes('FT') || machineType.includes('FT');
              })
              .map(parseProcessItem);

            // 定义工序表格列（仅桌面端使用）
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

            // 移动端卡片渲染函数
            const renderProcessCards = (processes, title, color, emoji) => {
              if (processes.length === 0) return null;
              
              return (
                <div style={{ marginBottom: '20px' }}>
                  <h5 style={{ marginBottom: '12px', color: color, fontSize: isMobile ? '13px' : '14px' }}>
                    {emoji} {title}
                  </h5>
                  {isMobile ? (
                    // 移动端：卡片布局
                    <div>
                      {processes.map((item, index) => (
                        <div key={index} style={{
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          backgroundColor: '#fff',
                          marginBottom: '8px',
                          padding: '12px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <div>
                              <div style={{ fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
                                {item.itemName || '-'}
                              </div>
                              <div style={{ fontSize: '11px', color: '#666' }}>
                                {item.machineType || '-'}
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                                {item.unitPrice ? `¥${item.unitPrice.toFixed(4)}` : '¥0.0000'}
                              </div>
                              <div style={{ fontSize: '10px', color: '#999' }}>
                                单颗报价
                              </div>
                            </div>
                          </div>
                          <div style={{ fontSize: '11px', color: '#666', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                            <div>设备: {item.machine || item.itemName?.split('-')[1] || '-'}</div>
                            <div>UPH: {item.uph || '-'}</div>
                          </div>
                          {item.hourlyRate && (
                            <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                              机时费率: {item.hourlyRate}
                            </div>
                          )}
                        </div>
                      ))}
                      <div style={{
                        padding: '10px',
                        backgroundColor: '#f0f9ff',
                        borderRadius: '6px',
                        fontSize: '11px',
                        color: '#666',
                        fontStyle: 'italic',
                        textAlign: 'center'
                      }}>
                        💡 注：{title}各道工序报价不可直接相加，请根据实际工艺流程选择
                      </div>
                    </div>
                  ) : (
                    // 桌面端：表格布局
                    <div>
                      <Table
                        columns={processColumns}
                        dataSource={processes}
                        pagination={false}
                        size="small"
                        bordered
                        rowKey={(item, index) => `${title.toLowerCase()}_${index}`}
                        style={{ marginBottom: '8px' }}
                      />
                      <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                        💡 注：{title}各道工序报价不可直接相加，请根据实际工艺流程选择
                      </div>
                    </div>
                  )}
                </div>
              );
            };

            return (
              <div style={{ padding: isMobile ? '8px' : '16px', backgroundColor: '#fafafa' }}>
                <h4 style={{ marginBottom: '16px', color: '#1890ff', fontSize: isMobile ? '14px' : '16px' }}>报价明细</h4>
                
                {/* CP工序 */}
                {renderProcessCards(cpProcesses, 'CP工序', '#52c41a', '🔬')}
                
                {/* FT工序 */}
                {renderProcessCards(ftProcesses, 'FT工序', '#1890ff', '📱')}
              </div>
            );
          })()
        ) : (
          // 其他报价类型使用普通表格显示
          <div style={{ padding: isMobile ? '8px' : '16px' }}>
            {isMobile ? (
              // 移动端：卡片布局
              <div>
                {quote.items && quote.items.length > 0 ? (
                  quote.items.map((item, index) => (
                    <div key={index} style={{
                      border: '1px solid #d9d9d9',
                      borderRadius: '6px',
                      backgroundColor: '#fff',
                      marginBottom: '8px',
                      padding: '12px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 'bold', fontSize: '13px' }}>
                          {item.itemName || item.name || '-'}
                        </span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '14px' }}>
                          ¥{(item.unitPrice || item.totalPrice || 0).toFixed(2)}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.4' }}>
                        {item.description && (
                          <div style={{ marginBottom: '4px' }}>{item.description}</div>
                        )}
                        {item.quantity && (
                          <div>数量: {item.quantity} {item.unit || ''}</div>
                        )}
                        {item.remarks && (
                          <div style={{ marginTop: '4px', color: '#999' }}>备注: {item.remarks}</div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{
                    textAlign: 'center',
                    padding: '40px 20px',
                    color: '#999',
                    fontSize: '14px'
                  }}>
                    暂无报价明细
                  </div>
                )}
              </div>
            ) : (
              // 桌面端：表格布局
              <Table
                columns={itemColumns}
                dataSource={quote.items}
                pagination={false}
                bordered
                size="small"
              />
            )}
          </div>
        )}
      </Card>

      {/* 统一审批面板 - PDF快照模式下不显示 */}
      {!isSnapshotMode && (
        <UnifiedApprovalPanel
          quote={quote}
          currentUser={currentUser}
          onApprovalStatusChange={(result) => {
            console.log('审批状态变更:', result);
            // 刷新报价详情
            fetchQuoteDetail();
          }}
          layout={isMobile ? 'mobile' : 'desktop'}
          showHistory={true}
        />
      )}

      {/* 提交审批模态框 */}
      <SubmitApprovalModal
        visible={submitApprovalModalVisible}
        onCancel={handleSubmitApprovalCancel}
        onSuccess={handleSubmitApprovalSuccess}
        quoteData={{
          id: quote?.quoteId,
          quote_number: quote?.id,
          customer_name: quote?.customer,
          total_amount: quote?.totalAmount,
          quote_type: quote?.type
        }}
      />

      <div id="quote-ready" style={{ display: "none" }} />

    </div>
  );
};

export default QuoteDetail;