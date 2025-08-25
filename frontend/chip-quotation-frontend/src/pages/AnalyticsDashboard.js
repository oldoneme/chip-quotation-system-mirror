import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Button, 
  Select, 
  DatePicker, 
  Space,
  Divider,
  Progress,
  Tag,
  Table,
  Avatar,
  List
} from 'antd';
import { 
  Column, 
  Line, 
  Pie, 
  Area,
  DualAxes 
} from '@ant-design/charts';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  FileTextOutlined,
  UserOutlined,
  CalendarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import '../styles/AnalyticsDashboard.css';

const { RangePicker } = DatePicker;
const { Option } = Select;

const AnalyticsDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('month');
  const [metrics, setMetrics] = useState({});
  const [chartData, setChartData] = useState({
    quotesTrend: [],
    quotesByType: [],
    quotesByStatus: [],
    monthlyRevenue: [],
    topCustomers: [],
    recentActivities: []
  });

  useEffect(() => {
    loadDashboardData();
  }, [timeRange]);

  const loadDashboardData = () => {
    setLoading(true);
    
    // 模拟数据
    setTimeout(() => {
      setMetrics({
        totalQuotes: { value: 156, change: 12.5, trend: 'up' },
        pendingQuotes: { value: 23, change: -5.2, trend: 'down' },
        approvedQuotes: { value: 89, change: 18.9, trend: 'up' },
        totalRevenue: { value: 2580000, change: 25.8, trend: 'up' },
        avgQuoteValue: { value: 16500, change: 8.3, trend: 'up' },
        conversionRate: { value: 68.5, change: 3.2, trend: 'up' }
      });

      // 报价趋势数据
      const quotesTrendData = [
        { date: '2024-12-01', quotes: 12, revenue: 180000 },
        { date: '2024-12-02', quotes: 8, revenue: 120000 },
        { date: '2024-12-03', quotes: 15, revenue: 250000 },
        { date: '2024-12-04', quotes: 20, revenue: 320000 },
        { date: '2024-12-05', quotes: 18, revenue: 290000 },
        { date: '2024-12-06', quotes: 25, revenue: 380000 },
        { date: '2024-12-07', quotes: 22, revenue: 350000 }
      ];

      // 报价类型分布
      const quotesByTypeData = [
        { type: '工程报价', count: 45, percentage: 28.8 },
        { type: '量产报价', count: 38, percentage: 24.4 },
        { type: '询价报价', count: 32, percentage: 20.5 },
        { type: '工装夹具', count: 25, percentage: 16.0 },
        { type: '综合报价', count: 16, percentage: 10.3 }
      ];

      // 报价状态分布
      const quotesByStatusData = [
        { status: '已批准', count: 89, color: '#52c41a' },
        { status: '待审批', count: 23, color: '#1890ff' },
        { status: '已拒绝', count: 18, color: '#ff4d4f' },
        { status: '草稿', count: 26, color: '#d9d9d9' }
      ];

      // 月度营收数据
      const monthlyRevenueData = [
        { month: '2024-08', revenue: 1850000, target: 2000000 },
        { month: '2024-09', revenue: 2150000, target: 2000000 },
        { month: '2024-10', revenue: 1980000, target: 2000000 },
        { month: '2024-11', revenue: 2380000, target: 2200000 },
        { month: '2024-12', revenue: 2580000, target: 2400000 }
      ];

      // 主要客户数据
      const topCustomersData = [
        { 
          customer: '芯片科技有限公司', 
          quotes: 18, 
          revenue: 580000, 
          conversionRate: 72.2,
          avatar: null
        },
        { 
          customer: '半导体制造公司', 
          quotes: 15, 
          revenue: 450000, 
          conversionRate: 66.7,
          avatar: null
        },
        { 
          customer: '智能设备有限公司', 
          quotes: 12, 
          revenue: 320000, 
          conversionRate: 75.0,
          avatar: null
        },
        { 
          customer: '通信技术公司', 
          quotes: 10, 
          revenue: 280000, 
          conversionRate: 60.0,
          avatar: null
        }
      ];

      // 最近活动
      const recentActivitiesData = [
        {
          id: 1,
          type: 'quote_approved',
          title: '报价单 QT-20241224-001 已批准',
          description: '芯片科技有限公司的5G射频芯片测试项目',
          time: '2024-12-24 14:30',
          user: '李主管',
          status: 'success'
        },
        {
          id: 2,
          type: 'quote_created',
          title: '新建报价单 QT-20241224-005',
          description: 'AI芯片测试方案报价',
          time: '2024-12-24 13:45',
          user: '张三',
          status: 'info'
        },
        {
          id: 3,
          type: 'quote_rejected',
          title: '报价单 QT-20241223-002 被拒绝',
          description: '价格过高，需要重新评估',
          time: '2024-12-23 17:30',
          user: '李主管',
          status: 'error'
        }
      ];

      setChartData({
        quotesTrend: quotesTrendData,
        quotesByType: quotesByTypeData,
        quotesByStatus: quotesByStatusData,
        monthlyRevenue: monthlyRevenueData,
        topCustomers: topCustomersData,
        recentActivities: recentActivitiesData
      });

      setLoading(false);
    }, 1000);
  };

  // 格式化数字
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
  };

  // 趋势指示器
  const TrendIndicator = ({ value, trend }) => {
    const isUp = trend === 'up';
    return (
      <span style={{ 
        color: isUp ? '#52c41a' : '#ff4d4f',
        fontSize: '14px',
        marginLeft: '8px'
      }}>
        {isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
        {Math.abs(value)}%
      </span>
    );
  };

  // 报价趋势图表配置
  const quotesTrendConfig = {
    data: chartData.quotesTrend,
    xField: 'date',
    yField: ['quotes', 'revenue'],
    geometryOptions: [
      {
        geometry: 'column',
        color: '#1890ff',
      },
      {
        geometry: 'line',
        color: '#52c41a',
        lineStyle: { lineWidth: 2 },
      },
    ],
    yAxis: {
      quotes: { position: 'left' },
      revenue: { position: 'right' },
    },
  };

  // 报价类型饼图配置
  const quoteTypeConfig = {
    data: chartData.quotesByType,
    angleField: 'count',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [{ type: 'element-active' }],
  };

  // 月度营收配置
  const revenueConfig = {
    data: chartData.monthlyRevenue,
    xField: 'month',
    yField: 'revenue',
    color: '#1890ff',
    point: { size: 5, shape: 'diamond' },
    label: {
      style: { fill: '#aaa' },
    },
    smooth: true,
  };

  return (
    <div className="analytics-dashboard">
      {/* 页面标题和控制器 */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>数据分析</h1>
          <span className="subtitle">实时报价业务数据洞察</span>
        </div>
        <div className="header-controls">
          <Space size="middle">
            <Select 
              value={timeRange} 
              onChange={setTimeRange}
              style={{ width: 120 }}
            >
              <Option value="week">近7天</Option>
              <Option value="month">近30天</Option>
              <Option value="quarter">近3个月</Option>
              <Option value="year">近一年</Option>
            </Select>
            <RangePicker />
            <Button icon={<BarChartOutlined />}>导出报告</Button>
          </Space>
        </div>
      </div>

      {/* 核心指标卡片 */}
      <Row gutter={[16, 16]} className="metrics-row">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总报价单"
              value={metrics.totalQuotes?.value}
              prefix={<FileTextOutlined />}
              suffix={<TrendIndicator value={metrics.totalQuotes?.change} trend={metrics.totalQuotes?.trend} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待审批"
              value={metrics.pendingQuotes?.value}
              prefix={<CalendarOutlined />}
              suffix={<TrendIndicator value={metrics.pendingQuotes?.change} trend={metrics.pendingQuotes?.trend} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总营收"
              value={metrics.totalRevenue?.value}
              prefix={<DollarOutlined />}
              formatter={(value) => `¥${formatNumber(value)}`}
              suffix={<TrendIndicator value={metrics.totalRevenue?.change} trend={metrics.totalRevenue?.trend} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="转化率"
              value={metrics.conversionRate?.value}
              prefix={<RiseOutlined />}
              suffix={<span>% <TrendIndicator value={metrics.conversionRate?.change} trend={metrics.conversionRate?.trend} /></span>}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} className="charts-row">
        {/* 报价趋势 */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <LineChartOutlined />
                报价趋势分析
              </Space>
            }
            extra={<Button size="small">查看详情</Button>}
          >
            <DualAxes {...quotesTrendConfig} height={300} />
          </Card>
        </Col>

        {/* 报价类型分布 */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <PieChartOutlined />
                报价类型分布
              </Space>
            }
          >
            <Pie {...quoteTypeConfig} height={300} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="charts-row">
        {/* 月度营收趋势 */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <BarChartOutlined />
                月度营收趋势
              </Space>
            }
          >
            <Area {...revenueConfig} height={250} />
          </Card>
        </Col>

        {/* 主要客户 */}
        <Col xs={24} lg={12}>
          <Card title="主要客户">
            <List
              itemLayout="horizontal"
              dataSource={chartData.topCustomers}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} />}
                    title={item.customer}
                    description={
                      <Space>
                        <span>报价: {item.quotes}单</span>
                        <span>营收: ¥{formatNumber(item.revenue)}</span>
                        <Tag color={item.conversionRate > 70 ? 'green' : 'orange'}>
                          转化率: {item.conversionRate}%
                        </Tag>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 状态分布和最近活动 */}
      <Row gutter={[16, 16]} className="bottom-row">
        <Col xs={24} lg={8}>
          <Card title="报价状态分布">
            <div className="status-distribution">
              {chartData.quotesByStatus.map(item => (
                <div key={item.status} className="status-item">
                  <div className="status-info">
                    <Tag color={item.color}>{item.status}</Tag>
                    <span className="status-count">{item.count}</span>
                  </div>
                  <Progress 
                    percent={item.count / 156 * 100} 
                    showInfo={false}
                    strokeColor={item.color}
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="最近活动">
            <List
              itemLayout="horizontal"
              dataSource={chartData.recentActivities}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar 
                        style={{ 
                          backgroundColor: item.status === 'success' ? '#52c41a' : 
                                          item.status === 'error' ? '#ff4d4f' : '#1890ff'
                        }}
                      >
                        {item.user.charAt(0)}
                      </Avatar>
                    }
                    title={item.title}
                    description={
                      <div>
                        <div>{item.description}</div>
                        <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                          {item.time} · {item.user}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AnalyticsDashboard;