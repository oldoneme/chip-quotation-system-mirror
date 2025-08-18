import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../hooks/usePermissions';

// 权限保护组件 - 包装需要权限控制的内容
export const PermissionGuard = ({ 
  permission, 
  permissions, 
  children, 
  fallback,
  showFallback = true 
}) => {
  const { checkPermission, checkAnyPermission } = usePermissions();
  const navigate = useNavigate();
  
  let hasAccess = false;
  
  if (permission) {
    hasAccess = checkPermission(permission);
  } else if (permissions) {
    hasAccess = checkAnyPermission(permissions);
  }
  
  if (!hasAccess) {
    if (fallback) {
      return fallback;
    }
    
    if (!showFallback) {
      return null;
    }
    
    return (
      <Result
        status="403"
        title="访问受限"
        subTitle="抱歉，您没有权限访问此功能。如需帮助，请联系管理员。"
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            返回首页
          </Button>
        }
      />
    );
  }
  
  return children;
};

// 权限控制的导航项组件
export const PermissionNavItem = ({ permission, permissions, children, ...props }) => {
  const { checkPermission, checkAnyPermission } = usePermissions();
  
  let hasAccess = false;
  
  if (permission) {
    hasAccess = checkPermission(permission);
  } else if (permissions) {
    hasAccess = checkAnyPermission(permissions);
  }
  
  if (!hasAccess) {
    return null;
  }
  
  return React.cloneElement(children, props);
};

// 条件渲染组件 - 根据权限显示/隐藏内容
export const ConditionalRender = ({ 
  permission, 
  permissions, 
  children, 
  fallback = null,
  role
}) => {
  const { checkPermission, checkAnyPermission, user } = usePermissions();
  
  let shouldRender = false;
  
  // 基于角色的条件渲染
  if (role) {
    shouldRender = user?.role === role;
  }
  // 基于权限的条件渲染
  else if (permission) {
    shouldRender = checkPermission(permission);
  } else if (permissions) {
    shouldRender = checkAnyPermission(permissions);
  }
  
  return shouldRender ? children : fallback;
};