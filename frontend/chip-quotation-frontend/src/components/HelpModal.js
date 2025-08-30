import React, { useState } from 'react';
import { Modal, Button, Tabs, Typography, List, Tag } from 'antd';
import { QuestionCircleOutlined, SettingOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const HelpModal = () => {
  const [visible, setVisible] = useState(false);

  const keyboardShortcuts = [
    { key: 'ESC', description: '关闭对话框/返回上页' },
    { key: 'F1', description: '打开帮助' },
    { key: 'Ctrl/Cmd + S', description: '保存当前报价（如适用）' },
  ];

  const usageGuide = [
    {
      title: '报价类型说明',
      content: [
        '• 询价报价：初期项目咨询和价格评估',
        '• 工装夹具报价：测试夹具和工装设备报价',
        '• 工程机时报价：工程验证阶段的设备使用费',
        '• 量产机时报价：量产阶段的设备小时费率',
        '• 量产工序报价：基于工序的单颗芯片成本',
        '• 综合报价：灵活的多项目组合报价'
      ]
    },
    {
      title: '基本操作流程',
      content: [
        '1. 从首页选择合适的报价类型',
        '2. 填写客户信息和项目基本信息',
        '3. 选择设备配置和相关参数',
        '4. 设置成本参数和币种汇率',
        '5. 生成报价单并可导出或管理'
      ]
    },
    {
      title: '报价单管理',
      content: [
        '• 查看所有历史报价单列表',
        '• 支持按状态、类型、日期筛选',
        '• 可查看详细信息、编辑或删除',
        '• 移动端适配，支持手机操作',
        '• 管理员可管理所有用户报价单'
      ]
    },
    {
      title: '系统特性',
      content: [
        '• 支持企业微信集成登录',
        '• 响应式设计，支持PC和移动端',
        '• 多币种支持（人民币/美元）',
        '• 实时汇率计算和成本分析',
        '• 基于角色的权限管理'
      ]
    }
  ];

  return (
    <>
      <Button
        type="text"
        icon={<QuestionCircleOutlined />}
        onClick={() => setVisible(true)}
        style={{ color: 'white' }}
        title="帮助"
      >
        帮助
      </Button>

      <Modal
        title={
          <span>
            <InfoCircleOutlined style={{ marginRight: 8 }} />
            使用帮助
          </span>
        }
        open={visible}
        onCancel={() => setVisible(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setVisible(false)}>
            知道了
          </Button>
        ]}
        width={600}
      >
        <Tabs 
          defaultActiveKey="guide"
          items={[
            {
              key: 'guide',
              tab: (
                <span>
                  <InfoCircleOutlined />
                  使用指南
                </span>
              ),
              children: (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {usageGuide.map((section, index) => (
                    <div key={index} style={{ marginBottom: 24 }}>
                      <Title level={5}>{section.title}</Title>
                      <List
                        size="small"
                        dataSource={section.content}
                        renderItem={(item) => (
                          <List.Item>
                            <Text>{item}</Text>
                          </List.Item>
                        )}
                      />
                    </div>
                  ))}
                </div>
              )
            },
            {
              key: 'shortcuts',
              tab: (
                <span>
                  <SettingOutlined />
                  快捷键
                </span>
              ),
              children: (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <Paragraph>
                    系统支持的键盘快捷键：
                  </Paragraph>
                  <List
                    size="small"
                    dataSource={keyboardShortcuts}
                    renderItem={(item) => (
                      <List.Item>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                          <Tag color="blue" style={{ fontFamily: 'monospace' }}>
                            {item.key}
                          </Tag>
                          <span>{item.description}</span>
                        </div>
                      </List.Item>
                    )}
                  />
                  <Paragraph style={{ marginTop: 16, color: '#666', fontSize: '12px' }}>
                    注意：快捷键在输入框获得焦点时可能不会触发
                  </Paragraph>
                </div>
              )
            }
          ]}
        />
      </Modal>
    </>
  );
};

export default HelpModal;