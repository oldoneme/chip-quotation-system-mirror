import React from 'react';
import { Modal } from 'antd';
import { ExclamationCircleOutlined, DeleteOutlined, SaveOutlined, ReloadOutlined } from '@ant-design/icons';

const { confirm } = Modal;

export const showDeleteConfirm = (options = {}) => {
  const {
    title = '确认删除',
    content = '您确定要删除这个项目吗？此操作不可恢复。',
    onOk,
    onCancel,
    okText = '删除',
    cancelText = '取消'
  } = options;

  console.log('showDeleteConfirm called with options:', options);

  confirm({
    title,
    icon: <ExclamationCircleOutlined />,
    content,
    okText,
    okType: 'danger',
    cancelText,
    onOk: () => {
      console.log('确认对话框的onOk被调用');
      if (onOk) {
        onOk();
      }
    },
    onCancel: () => {
      console.log('确认对话框的onCancel被调用');  
      if (onCancel) {
        onCancel();
      }
    },
    centered: true,
    maskClosable: false,
  });
};

export const showSaveConfirm = (options = {}) => {
  const {
    title = '确认保存',
    content = '您确定要保存这些更改吗？',
    onOk,
    onCancel,
    okText = '保存',
    cancelText = '取消'
  } = options;

  confirm({
    title,
    icon: <SaveOutlined />,
    content,
    okText,
    okType: 'primary',
    cancelText,
    onOk,
    onCancel,
    centered: true,
  });
};

export const showResetConfirm = (options = {}) => {
  const {
    title = '确认重置',
    content = '您确定要重置所有设置吗？这将清除您当前的所有选择。',
    onOk,
    onCancel,
    okText = '重置',
    cancelText = '取消'
  } = options;

  confirm({
    title,
    icon: <ReloadOutlined />,
    content,
    okText,
    okType: 'danger',
    cancelText,
    onOk,
    onCancel,
    centered: true,
  });
};

export const showCustomConfirm = (options = {}) => {
  const {
    title = '确认操作',
    icon = <ExclamationCircleOutlined />,
    content = '您确定要执行此操作吗？',
    onOk,
    onCancel,
    okText = '确定',
    cancelText = '取消',
    okType = 'primary'
  } = options;

  confirm({
    title,
    icon,
    content,
    okText,
    okType,
    cancelText,
    onOk,
    onCancel,
    centered: true,
  });
};

const ConfirmDialog = {
  showDeleteConfirm,
  showSaveConfirm,
  showResetConfirm,
  showCustomConfirm
};

export default ConfirmDialog;