import { useAuth } from '../contexts/AuthContext';
import { hasPermission, hasAnyPermission, canAccessRoute, ROLE_LABELS } from '../config/permissions';

// 权限管理Hook
export const usePermissions = () => {
  const { user } = useAuth();
  
  // 检查单个权限
  const checkPermission = (permission) => {
    if (!user?.role) return false;
    return hasPermission(user.role, permission);
  };
  
  // 检查多个权限（任一满足）
  const checkAnyPermission = (permissions) => {
    if (!user?.role) return false;
    return hasAnyPermission(user.role, permissions);
  };
  
  // 检查路由访问权限
  const checkRouteAccess = (route) => {
    if (!user?.role) return false;
    return canAccessRoute(user.role, route);
  };
  
  // 获取用户角色显示名称
  const getRoleLabel = () => {
    if (!user?.role) return '未知角色';
    return ROLE_LABELS[user.role] || user.role;
  };
  
  // 是否为管理员级别
  const isAdmin = () => {
    return user?.role === 'super_admin' || user?.role === 'admin';
  };
  
  // 是否为业务管理级别
  const isManager = () => {
    return user?.role === 'super_admin' || user?.role === 'admin' || user?.role === 'manager';
  };
  
  return {
    user,
    checkPermission,
    checkAnyPermission,
    checkRouteAccess,
    getRoleLabel,
    isAdmin,
    isManager,
    hasPermission: checkPermission, // 别名，保持向后兼容
  };
};