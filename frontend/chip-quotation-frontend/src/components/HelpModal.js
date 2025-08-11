import React, { useState } from 'react';
import { Modal, Button, Tabs, Typography, List, Tag } from 'antd';
import { QuestionCircleOutlined, SettingOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

const HelpModal = () => {
  const [visible, setVisible] = useState(false);

  const keyboardShortcuts = [
    { key: 'Ctrl/Cmd + 1', description: '返回首页' },
    { key: 'Ctrl/Cmd + 2', description: '工程报价' },
    { key: 'Ctrl/Cmd + 3', description: '量产报价' },
    { key: 'Ctrl/Cmd + 4', description: '数据库管理' },
    { key: 'Ctrl/Cmd + 5', description: 'API测试' },
    { key: 'ESC', description: '返回首页' },
  ];

  const usageGuide = [
    {
      title: '工程报价流程',
      content: [
        '1. 选择测试机并配置板卡',
        '2. 选择分选机和探针台（可选）',
        '3. 选择人员配置和辅助设备',
        '4. 设置工程系数',
        '5. 查看报价结果'
      ]
    },
    {
      title: '数据库管理',
      content: [
        '1. 查看层级结构了解设备关系',
        '2. 管理测试机、配置和板卡',
        '3. 添加或编辑辅助设备',
        '4. 删除操作需要确认'
      ]
    },
    {
      title: '注意事项',
      content: [
        '• 删除操作不可恢复，请谨慎操作',
        '• 系统会自动保存报价进度',
        '• 支持多种币种和汇率设置',
        '• 可通过API测试验证数据'
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
        <Tabs defaultActiveKey="guide">
          <TabPane 
            tab={
              <span>
                <InfoCircleOutlined />
                使用指南
              </span>
            } 
            key="guide"
          >
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
          </TabPane>

          <TabPane 
            tab={
              <span>
                <SettingOutlined />
                快捷键
              </span>
            } 
            key="shortcuts"
          >
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Paragraph>
                使用键盘快捷键可以快速导航到不同页面：
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
                注意：快捷键在输入框获得焦点时不会触发
              </Paragraph>
            </div>
          </TabPane>
        </Tabs>
      </Modal>
    </>
  );
};

export default HelpModal;