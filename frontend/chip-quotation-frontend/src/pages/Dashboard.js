import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Button, Avatar, Timeline, List, Tag } from 'antd';
import {
  FileAddOutlined,
  CopyOutlined,
  ReloadOutlined,
  BarChartOutlined,
  SaveOutlined,
  ExportOutlined,
  ArrowUpOutlined,
  UserOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { usePermissions } from '../hooks/usePermissions';
import { PERMISSIONS } from '../config/permissions';
import { ConditionalRender } from '../components/PermissionGuard';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user } = useAuth();
  const { checkPermission, getRoleLabel } = usePermissions();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    metrics: {
      pending: { value: 0, change: 0 },
      processing: { value: 0, change: 0 },
      completed: { value: 0, change: 0 },
      monthlyAmount: { value: 0, change: 0 }
    },
    recentActivities: [],
    processingOrders: []
  });

  // 模拟数据（后续会连接真实API）
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      // 模拟API调用延迟
      setTimeout(() => {
        setDashboardData({
          metrics: {
            pending: { value: 3, change: 2 },
            processing: { value: 5, change: 0 },
            completed: { value: 12, change: 3 },
            monthlyAmount: { value: 128500, change: 15 }
          },
          recentActivities: [
            {
              id: 1,
              type: "order_completed",
              title: "订单 #Q20240118001 测试完成，待确认",
              time: "2小时前",
              description: "客户：某科技公司 | 芯片型号：XX芯片FT测试"
            },
            {
              id: 2,
              type: "quote_submitted", 
              title: "新报价单已提交 #Q20240118002",
              time: "4小时前",
              description: "报价类型：工程机时报价 | 预估金额：¥15,600"
            },
            {
              id: 3,
              type: "order_created",
              title: "新订单创建 #Q20240118003", 
              time: "6小时前",
              description: "客户：ABC电子 | 芯片型号：YY芯片CP测试"
            },
            {
              id: 4,
              type: "quote_approved",
              title: "报价单 #Q20240117001 已通过审核",
              time: "昨天",
              description: "报价类型：量产工序报价 | 金额：¥28,900"
            }
          ],
          processingOrders: [
            {
              id: "Q20240118001",
              customerName: "某科技公司",
              chipModel: "XX芯片CP测试",
              status: "processing",
              progress: 75,
              estimatedCompletion: "今天 18:00",
              amount: 8500
            },
            {
              id: "Q20240118002", 
              customerName: "ABC电子",
              chipModel: "YY芯片FT测试",
              status: "processing",
              progress: 40,
              estimatedCompletion: "明天 14:00",
              amount: 12300
            }
          ]
        });
        setLoading(false);
      }, 1000);
    };

    fetchDashboardData();
  }, []);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(amount);
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'order_completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'quote_submitted':
        return <FileAddOutlined style={{ color: '#1890ff' }} />;
      case 'order_created':
        return <CopyOutlined style={{ color: '#fa8c16' }} />;
      case 'quote_approved':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      default:
        return <SyncOutlined style={{ color: '#666' }} />;
    }
  };

  // 根据权限生成可用的快速操作
  const getAllQuickActions = () => [
    {
      title: '询价报价',
      icon: <FileAddOutlined />,
      description: '快速询价咨询',
      action: () => navigate('/inquiry-quote'),
      color: '#52c41a',
      permission: PERMISSIONS.QUOTE_INQUIRY
    },
    {
      title: '工程机时报价',
      icon: <BarChartOutlined />,
      description: '研发阶段测试',
      action: () => navigate('/engineering-quote'),
      color: '#1890ff',
      permission: PERMISSIONS.QUOTE_ENGINEERING
    },
    {
      title: '量产机时报价',
      icon: <ExportOutlined />,
      description: '大批量生产测试',
      action: () => navigate('/mass-production-quote'),
      color: '#fa8c16',
      permission: PERMISSIONS.QUOTE_MASS_PRODUCTION
    },
    {
      title: '工装夹具报价',
      icon: <SaveOutlined />,
      description: '定制工装夹具',
      action: () => navigate('/tooling-quote'),
      color: '#722ed1',
      permission: PERMISSIONS.QUOTE_TOOLING
    }
  ];

  // 过滤用户有权限的快速操作
  const quickActions = getAllQuickActions().filter(action => 
    checkPermission(action.permission)
  );

  return (
    <div className="dashboard-container">
      {/* 欢迎区域 */}
      <Card className="dashboard-welcome-card" style={{ marginBottom: 24 }}>
        <Row align="middle">
          <Col>
            <Avatar size={64} src={user?.avatar} icon={<UserOutlined />} />
          </Col>
          <Col flex="auto" style={{ paddingLeft: 16 }}>
            <h2 style={{ margin: 0, fontSize: 24 }}>
              欢迎回来，{user?.name || '用户'}！
              <Tag color={user?.role === 'admin' || user?.role === 'super_admin' ? 'red' : 'blue'} style={{ marginLeft: 4 }}>
                {getRoleLabel()}
              </Tag>
            </h2>
            <div className="user-info" style={{ margin: '8px 0 0', color: '#666', fontSize: 14 }}>
              <div style={{ marginBottom: 4 }}>
                <span style={{ fontWeight: 500 }}>部门：</span>
                <span>{user?.department || '芯信安电子科技有限公司'}</span>
              </div>
              <div style={{ marginBottom: 4 }}>
                <span style={{ fontWeight: 500 }}>职位：</span>
                <span>{user?.position || (user?.role === 'admin' ? '系统管理员' : '业务专员')}</span>
              </div>
              <div className="user-greeting" style={{ color: '#999', fontSize: 12, marginTop: 8 }}>
                今天是个美好的一天，让我们开始工作吧！
              </div>
            </div>
          </Col>
          <Col>
            <Button 
              type="primary" 
              icon={<FileAddOutlined />}
              size="large"
              onClick={() => navigate('/quote-types')}
            >
              新建报价
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 数据指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待办报价"
              value={dashboardData.metrics.pending.value}
              prefix={<FileAddOutlined style={{ color: '#fa8c16' }} />}
              suffix="个"
              valueStyle={{ color: '#fa8c16' }}
            />
            {dashboardData.metrics.pending.change > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#52c41a' }}>
                <ArrowUpOutlined /> 较昨日 +{dashboardData.metrics.pending.change}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="进行中"
              value={dashboardData.metrics.processing.value}
              prefix={<SyncOutlined spin style={{ color: '#1890ff' }} />}
              suffix="个"
              valueStyle={{ color: '#1890ff' }}
            />
            {dashboardData.metrics.processing.change > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#52c41a' }}>
                <ArrowUpOutlined /> 较昨日 +{dashboardData.metrics.processing.change}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成"
              value={dashboardData.metrics.completed.value}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              suffix="个"
              valueStyle={{ color: '#52c41a' }}
            />
            {dashboardData.metrics.completed.change > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#52c41a' }}>
                <ArrowUpOutlined /> 较昨日 +{dashboardData.metrics.completed.change}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="本月金额"
              value={dashboardData.metrics.monthlyAmount.value}
              prefix="¥"
              precision={0}
              valueStyle={{ color: '#cf1322' }}
            />
            {dashboardData.metrics.monthlyAmount.change > 0 && (
              <div style={{ marginTop: 8, fontSize: 12, color: '#52c41a' }}>
                <ArrowUpOutlined /> 较上月 +{dashboardData.metrics.monthlyAmount.change}%
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 快速操作 */}
        <Col xs={24} lg={12}>
          <Card title="快速操作" extra={<ReloadOutlined />}>
            <Row gutter={[8, 8]}>
              {quickActions.map((action, index) => (
                <Col xs={12} sm={12} md={12} key={index}>
                  <Card 
                    className="dashboard-action-card"
                    hoverable 
                    size="small"
                    onClick={action.action}
                    style={{ 
                      textAlign: 'center',
                      border: `1px solid ${action.color}20`,
                      borderRadius: 8
                    }}
                  >
                    <div style={{ fontSize: 24, color: action.color, marginBottom: 8 }}>
                      {action.icon}
                    </div>
                    <div className="action-title" style={{ fontWeight: 'bold', fontSize: 14, marginBottom: 4 }}>
                      {action.title}
                    </div>
                    <div className="action-description" style={{ fontSize: 12, color: '#666' }}>
                      {action.description}
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={12}>
          <Card title="最近活动" extra={<ReloadOutlined />}>
            <Timeline mode="left">
              {dashboardData.recentActivities.map((activity) => (
                <Timeline.Item 
                  key={activity.id}
                  dot={getActivityIcon(activity.type)}
                >
                  <div style={{ marginBottom: 4 }}>
                    <strong>{activity.title}</strong>
                    <span style={{ fontSize: 12, color: '#999', marginLeft: 8 }}>
                      {activity.time}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    {activity.description}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;