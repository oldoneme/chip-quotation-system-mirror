import { message, notification } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined, 
  InfoCircleOutlined 
} from '@ant-design/icons';

// 配置全局消息样式
message.config({
  top: 20,
  duration: 3,
  maxCount: 3,
});

notification.config({
  placement: 'topRight',
  top: 70,
  duration: 4.5,
});

export const showSuccess = (content, duration = 3) => {
  message.success({
    content,
    duration,
    icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  });
};

export const showError = (content, duration = 4) => {
  message.error({
    content,
    duration,
    icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
  });
};

export const showWarning = (content, duration = 4) => {
  message.warning({
    content,
    duration,
    icon: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
  });
};

export const showInfo = (content, duration = 3) => {
  message.info({
    content,
    duration,
    icon: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
  });
};

export const showNotification = (type, title, description, duration = 4.5) => {
  const icons = {
    success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
    warning: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
    info: <InfoCircleOutlined style={{ color: '#1890ff' }} />
  };

  notification[type]({
    message: title,
    description,
    duration,
    icon: icons[type],
    style: {
      borderRadius: 8,
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    },
  });
};

export const showLoadingMessage = (content = '处理中...') => {
  return message.loading(content, 0); // 0 means it won't auto close
};

export const hideMessage = (messageKey) => {
  message.destroy(messageKey);
};

export default {
  showSuccess,
  showError,
  showWarning,
  showInfo,
  showNotification,
  showLoadingMessage,
  hideMessage
};