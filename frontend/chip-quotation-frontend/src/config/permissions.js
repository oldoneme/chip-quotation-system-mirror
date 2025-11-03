// 权限管理配置文件

// 用户角色定义
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',  // 超级管理员 - 系统最高权限
  ADMIN: 'admin',              // 管理员 - 完全访问权限
  MANAGER: 'manager',          // 销售管理 - 业务管理权限
  USER: 'user'                 // 普通用户 - 业务操作权限
};

// 权限定义
export const PERMISSIONS = {
  // 系统管理权限
  SYSTEM_MANAGE: 'system:manage',
  USER_MANAGE: 'user:manage',
  DATABASE_MANAGE: 'database:manage',
  API_TEST: 'api:test',
  
  // 报价功能权限
  QUOTE_INQUIRY: 'quote:inquiry',
  QUOTE_TOOLING: 'quote:tooling', 
  QUOTE_ENGINEERING: 'quote:engineering',
  QUOTE_MASS_PRODUCTION: 'quote:mass_production',
  QUOTE_PROCESS: 'quote:process',
  QUOTE_COMPREHENSIVE: 'quote:comprehensive',
  
  // 订单管理权限
  ORDER_VIEW_OWN: 'order:view:own',
  ORDER_VIEW_TEAM: 'order:view:team',
  ORDER_VIEW_ALL: 'order:view:all',
  ORDER_MANAGE: 'order:manage',
  
  // 数据查看权限
  DATA_VIEW_OWN: 'data:view:own',
  DATA_VIEW_TEAM: 'data:view:team', 
  DATA_VIEW_ALL: 'data:view:all',
  
  // 导航访问权限
  NAV_DASHBOARD: 'nav:dashboard',
  NAV_QUOTE_TYPES: 'nav:quote_types',
  NAV_ORDERS: 'nav:orders',
  NAV_DATABASE: 'nav:database',
  NAV_API_TEST: 'nav:api_test',
  NAV_USER_MANAGEMENT: 'nav:user_management'
};

// 角色权限映射
export const ROLE_PERMISSIONS = {
  [USER_ROLES.SUPER_ADMIN]: [
    // 超级管理员拥有所有权限 - 系统最高权限
    ...Object.values(PERMISSIONS)
  ],

  [USER_ROLES.ADMIN]: [
    // 管理员拥有所有权限 - 完全访问权限
    ...Object.values(PERMISSIONS)
  ],

  [USER_ROLES.MANAGER]: [
    // 所有报价功能
    PERMISSIONS.QUOTE_INQUIRY,
    PERMISSIONS.QUOTE_TOOLING,
    PERMISSIONS.QUOTE_ENGINEERING,
    PERMISSIONS.QUOTE_MASS_PRODUCTION,
    PERMISSIONS.QUOTE_PROCESS,
    PERMISSIONS.QUOTE_COMPREHENSIVE,
    
    // 查看所有报价和订单数据
    PERMISSIONS.ORDER_VIEW_ALL,
    PERMISSIONS.ORDER_MANAGE,
    PERMISSIONS.DATA_VIEW_ALL,
    
    // 导航权限
    PERMISSIONS.NAV_DASHBOARD,
    PERMISSIONS.NAV_QUOTE_TYPES,
    PERMISSIONS.NAV_ORDERS
  ],
  
  [USER_ROLES.USER]: [
    // 所有报价功能
    PERMISSIONS.QUOTE_INQUIRY,
    PERMISSIONS.QUOTE_TOOLING,
    PERMISSIONS.QUOTE_ENGINEERING,
    PERMISSIONS.QUOTE_MASS_PRODUCTION,
    PERMISSIONS.QUOTE_PROCESS,
    PERMISSIONS.QUOTE_COMPREHENSIVE,
    
    // 查看自己的订单和数据
    PERMISSIONS.ORDER_VIEW_OWN,
    PERMISSIONS.DATA_VIEW_OWN,
    
    // 导航权限
    PERMISSIONS.NAV_DASHBOARD,
    PERMISSIONS.NAV_QUOTE_TYPES,
    PERMISSIONS.NAV_ORDERS
  ]
};

// 权限检查函数
export const hasPermission = (userRole, permission) => {
  if (!userRole || !permission) return false;
  
  const rolePermissions = ROLE_PERMISSIONS[userRole] || [];
  return rolePermissions.includes(permission);
};

// 批量权限检查
export const hasAnyPermission = (userRole, permissions) => {
  return permissions.some(permission => hasPermission(userRole, permission));
};

// 检查用户是否有访问特定路由的权限
export const canAccessRoute = (userRole, route) => {
  const routePermissionMap = {
    '/': PERMISSIONS.NAV_DASHBOARD,
    '/quote-types': PERMISSIONS.NAV_QUOTE_TYPES,
    '/inquiry-quote': PERMISSIONS.QUOTE_INQUIRY,
    '/tooling-quote': PERMISSIONS.QUOTE_TOOLING,
    '/engineering-quote': PERMISSIONS.QUOTE_ENGINEERING,
    '/mass-production-quote': PERMISSIONS.QUOTE_MASS_PRODUCTION,
    '/process-quote': PERMISSIONS.QUOTE_PROCESS,
    '/comprehensive-quote': PERMISSIONS.QUOTE_COMPREHENSIVE,
    '/orders': PERMISSIONS.NAV_ORDERS,
    '/hierarchical-database-management': PERMISSIONS.DATABASE_MANAGE,
    '/api-test': PERMISSIONS.API_TEST,
    '/user-management': PERMISSIONS.NAV_USER_MANAGEMENT
  };
  
  const requiredPermission = routePermissionMap[route];
  return requiredPermission ? hasPermission(userRole, requiredPermission) : false;
};

// 角色显示名称
export const ROLE_LABELS = {
  [USER_ROLES.SUPER_ADMIN]: '超级管理员',
  [USER_ROLES.ADMIN]: '管理员',
  [USER_ROLES.MANAGER]: '销售管理',
  [USER_ROLES.USER]: '普通用户'
};

// 获取用户可访问的导航项
export const getAccessibleNavItems = (userRole) => {
  const allNavItems = [
    { key: '/', permission: PERMISSIONS.NAV_DASHBOARD },
    { key: '/quote-types', permission: PERMISSIONS.NAV_QUOTE_TYPES },
    { key: '/orders', permission: PERMISSIONS.NAV_ORDERS },
    { key: '/hierarchical-database-management', permission: PERMISSIONS.NAV_DATABASE },
    { key: '/api-test', permission: PERMISSIONS.NAV_API_TEST },
    { key: '/user-management', permission: PERMISSIONS.NAV_USER_MANAGEMENT }
  ];
  
  return allNavItems.filter(item => hasPermission(userRole, item.permission));
};