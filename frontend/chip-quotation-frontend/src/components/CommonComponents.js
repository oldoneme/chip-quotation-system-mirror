import React from 'react';
import { Button, Card, Form, Input, InputNumber, Select, Spin, Empty } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

// 统一的按钮样式组件
export const PrimaryButton = ({ children, ...props }) => (
  <Button type="primary" size="middle" {...props}>
    {children}
  </Button>
);

export const SecondaryButton = ({ children, ...props }) => (
  <Button type="default" size="middle" {...props}>
    {children}
  </Button>
);

export const DangerButton = ({ children, ...props }) => (
  <Button type="primary" danger size="middle" {...props}>
    {children}
  </Button>
);

export const LinkButton = ({ children, ...props }) => (
  <Button type="link" size="middle" {...props}>
    {children}
  </Button>
);

// 统一的卡片样式组件
export const StyledCard = ({ children, title, extra, ...props }) => (
  <Card
    title={title}
    extra={extra}
    style={{
      marginBottom: 20,
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      ...props.style
    }}
    headStyle={{
      borderBottom: '1px solid #f0f0f0',
      fontSize: '16px',
      fontWeight: 'bold'
    }}
    bodyStyle={{
      padding: '20px'
    }}
    {...props}
  >
    {children}
  </Card>
);

// 统一的表单项组件
export const FormItem = ({ label, children, required = false, ...props }) => (
  <Form.Item
    label={label}
    rules={required ? [{ required: true, message: `请输入${label}!` }] : undefined}
    style={{ marginBottom: 16 }}
    {...props}
  >
    {children}
  </Form.Item>
);

// 统一的输入框组件
export const StyledInput = ({ placeholder, ...props }) => (
  <Input
    placeholder={placeholder}
    size="middle"
    style={{ borderRadius: 6 }}
    {...props}
  />
);

export const StyledInputNumber = ({ placeholder, ...props }) => (
  <InputNumber
    placeholder={placeholder}
    size="middle"
    style={{ width: '100%', borderRadius: 6 }}
    {...props}
  />
);

export const StyledSelect = ({ placeholder, children, ...props }) => (
  <Select
    placeholder={placeholder}
    size="middle"
    style={{ width: '100%' }}
    showSearch
    optionFilterProp="children"
    filterOption={(input, option) =>
      option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
    }
    {...props}
  >
    {children}
  </Select>
);

// 统一的加载组件
export const LoadingSpinner = ({ tip = "加载中...", size = "large" }) => (
  <div style={{ textAlign: 'center', padding: '50px 0' }}>
    <Spin
      indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />}
      tip={tip}
      size={size}
    />
  </div>
);

// 统一的空状态组件
export const EmptyState = ({ 
  description = "暂无数据", 
  imageStyle = { height: 60 },
  ...props 
}) => (
  <Empty
    image={Empty.PRESENTED_IMAGE_SIMPLE}
    imageStyle={imageStyle}
    description={description}
    {...props}
  />
);

// 统一的页面标题组件
export const PageTitle = ({ title, subtitle, extra, ...props }) => (
  <div style={{ 
    marginBottom: 24, 
    padding: '0 0 20px 0',
    borderBottom: '1px solid #f0f0f0'
  }} {...props}>
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center' 
    }}>
      <div>
        <h1 style={{ 
          margin: 0, 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#262626' 
        }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ 
            margin: '8px 0 0 0', 
            color: '#8c8c8c', 
            fontSize: '14px' 
          }}>
            {subtitle}
          </p>
        )}
      </div>
      {extra && <div>{extra}</div>}
    </div>
  </div>
);

// 统一的操作栏组件
export const ActionBar = ({ children, style, ...props }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    padding: '12px 0',
    ...style
  }} {...props}>
    {children}
  </div>
);

export default {
  PrimaryButton,
  SecondaryButton,
  DangerButton,
  LinkButton,
  StyledCard,
  FormItem,
  StyledInput,
  StyledInputNumber,
  StyledSelect,
  LoadingSpinner,
  EmptyState,
  PageTitle,
  ActionBar
};