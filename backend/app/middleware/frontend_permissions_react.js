/**
 * React 权限控制集成
 * 提供React Hooks和HOC用于权限控制
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { PermissionChecker, UIPermissionController, APIPermissionController } from './frontend_permissions.js';

// 权限上下文
const PermissionContext = createContext(null);

// 权限提供者组件
export const PermissionProvider = ({ children, initialUser = null }) => {
    const [permissionChecker] = useState(() => new PermissionChecker());
    const [uiController] = useState(() => new UIPermissionController(permissionChecker));
    const [apiController] = useState(() => new APIPermissionController(permissionChecker));
    const [currentUser, setCurrentUser] = useState(initialUser);
    
    // 初始化用户权限
    useEffect(() => {
        if (currentUser) {
            permissionChecker.initUser(currentUser);
        }
    }, [currentUser, permissionChecker]);
    
    const value = {
        permissionChecker,
        uiController,
        apiController,
        currentUser,
        setCurrentUser,
        // 便捷方法
        hasPermission: (permission) => permissionChecker.hasPermission(permission),
        hasRole: (roles) => permissionChecker.hasRole(roles),
        isAdminOrAbove: () => permissionChecker.isAdminOrAbove(),
        isManagerOrAbove: () => permissionChecker.isManagerOrAbove(),
        canViewQuotation: (quotation) => permissionChecker.canViewQuotation(quotation),
        canEditQuotation: (quotation) => permissionChecker.canEditQuotation(quotation),
        canManageUser: (user) => permissionChecker.canManageUser(user),
        secureFetch: (url, options) => apiController.secureFetch(url, options)
    };
    
    return (
        <PermissionContext.Provider value={value}>
            {children}
        </PermissionContext.Provider>
    );
};

// 权限Hook
export const usePermissions = () => {
    const context = useContext(PermissionContext);
    if (!context) {
        throw new Error('usePermissions must be used within a PermissionProvider');
    }
    return context;
};

// 权限检查Hook
export const usePermissionCheck = (permission) => {
    const { hasPermission } = usePermissions();
    return hasPermission(permission);
};

// 角色检查Hook
export const useRoleCheck = (roles) => {
    const { hasRole } = usePermissions();
    return hasRole(roles);
};

// 权限控制组件
export const PermissionGate = ({ 
    permission, 
    role, 
    minRole, 
    fallback = null, 
    children 
}) => {
    const { hasPermission, hasRole, isAdminOrAbove, isManagerOrAbove } = usePermissions();
    
    let hasAccess = true;
    
    if (permission) {
        hasAccess = hasPermission(permission);
    }
    
    if (role) {
        hasAccess = hasAccess && hasRole(role);
    }
    
    if (minRole) {
        switch (minRole) {
            case 'user':
                hasAccess = hasAccess && true;
                break;
            case 'manager':
                hasAccess = hasAccess && isManagerOrAbove();
                break;
            case 'admin':
                hasAccess = hasAccess && isAdminOrAbove();
                break;
            case 'super_admin':
                hasAccess = hasAccess && hasRole('super_admin');
                break;
            default:
                hasAccess = false;
        }
    }
    
    return hasAccess ? children : fallback;
};

// 权限按钮组件
export const PermissionButton = ({ 
    permission, 
    role, 
    minRole, 
    children, 
    disabled = false,
    className = '',
    ...props 
}) => {
    const { hasPermission, hasRole, isAdminOrAbove, isManagerOrAbove } = usePermissions();
    
    let hasAccess = true;
    
    if (permission) {
        hasAccess = hasPermission(permission);
    }
    
    if (role) {
        hasAccess = hasAccess && hasRole(role);
    }
    
    if (minRole) {
        switch (minRole) {
            case 'user':
                hasAccess = hasAccess && true;
                break;
            case 'manager':
                hasAccess = hasAccess && isManagerOrAbove();
                break;
            case 'admin':
                hasAccess = hasAccess && isAdminOrAbove();
                break;
            case 'super_admin':
                hasAccess = hasAccess && hasRole('super_admin');
                break;
            default:
                hasAccess = false;
        }
    }
    
    const finalDisabled = disabled || !hasAccess;
    const finalClassName = `${className} ${!hasAccess ? 'permission-disabled' : ''}`.trim();
    
    return (
        <button
            {...props}
            disabled={finalDisabled}
            className={finalClassName}
            title={!hasAccess ? '权限不足' : props.title}
        >
            {children}
        </button>
    );
};

// 高阶组件：权限保护
export const withPermissions = (WrappedComponent) => {
    return (props) => {
        const permissions = usePermissions();
        return <WrappedComponent {...props} permissions={permissions} />;
    };
};

// 高阶组件：角色保护
export const withRole = (allowedRoles, fallbackComponent = null) => (WrappedComponent) => {
    return (props) => {
        const { hasRole } = usePermissions();
        
        if (hasRole(allowedRoles)) {
            return <WrappedComponent {...props} />;
        }
        
        return fallbackComponent ? React.createElement(fallbackComponent, props) : null;
    };
};

// 高阶组件：权限保护
export const withPermission = (requiredPermission, fallbackComponent = null) => (WrappedComponent) => {
    return (props) => {
        const { hasPermission } = usePermissions();
        
        if (hasPermission(requiredPermission)) {
            return <WrappedComponent {...props} />;
        }
        
        return fallbackComponent ? React.createElement(fallbackComponent, props) : null;
    };
};

// React Router 权限路由组件
export const PermissionRoute = ({ 
    permission, 
    role, 
    minRole, 
    fallback, 
    children 
}) => {
    const { hasPermission, hasRole, isAdminOrAbove, isManagerOrAbove } = usePermissions();
    
    let hasAccess = true;
    
    if (permission) {
        hasAccess = hasPermission(permission);
    }
    
    if (role) {
        hasAccess = hasAccess && hasRole(role);
    }
    
    if (minRole) {
        switch (minRole) {
            case 'user':
                hasAccess = hasAccess && true;
                break;
            case 'manager':
                hasAccess = hasAccess && isManagerOrAbove();
                break;
            case 'admin':
                hasAccess = hasAccess && isAdminOrAbove();
                break;
            case 'super_admin':
                hasAccess = hasAccess && hasRole('super_admin');
                break;
            default:
                hasAccess = false;
        }
    }
    
    if (!hasAccess && fallback) {
        return fallback;
    }
    
    return hasAccess ? children : null;
};

// 示例组件
export const PermissionExample = () => {
    const { 
        hasPermission, 
        isAdminOrAbove, 
        canViewQuotation,
        canEditQuotation,
        secureFetch 
    } = usePermissions();
    
    const [quotations, setQuotations] = useState([]);
    
    // 使用安全的fetch
    const loadQuotations = async () => {
        try {
            const response = await secureFetch('/api/v1/quotations');
            const data = await response.json();
            setQuotations(data);
        } catch (error) {
            console.error('加载报价失败:', error.message);
        }
    };
    
    useEffect(() => {
        loadQuotations();
    }, []);
    
    return (
        <div className="permission-example">
            <h2>权限控制示例</h2>
            
            {/* 基于权限的条件渲染 */}
            <PermissionGate permission="user:create">
                <button>创建用户</button>
            </PermissionGate>
            
            <PermissionGate role={['admin', 'super_admin']}>
                <button>管理员功能</button>
            </PermissionGate>
            
            <PermissionGate minRole="manager">
                <button>经理功能</button>
            </PermissionGate>
            
            {/* 权限按钮 */}
            <PermissionButton 
                permission="quotation:delete"
                onClick={() => console.log('删除操作')}
            >
                删除报价
            </PermissionButton>
            
            {/* 条件渲染 */}
            {hasPermission('statistics:view_all') && (
                <div>
                    <h3>统计数据</h3>
                    <p>只有有权限的用户才能看到此内容</p>
                </div>
            )}
            
            {isAdminOrAbove() && (
                <div>
                    <h3>管理员功能区</h3>
                    <button onClick={() => console.log('管理员操作')}>
                        管理操作
                    </button>
                </div>
            )}
            
            {/* 动态权限检查 */}
            <div>
                <h3>报价列表</h3>
                {quotations.map(quotation => (
                    <div key={quotation.id} className="quotation-item">
                        <span>报价 #{quotation.id}</span>
                        {canViewQuotation(quotation) && (
                            <button onClick={() => console.log('查看报价', quotation.id)}>
                                查看
                            </button>
                        )}
                        {canEditQuotation(quotation) && (
                            <button onClick={() => console.log('编辑报价', quotation.id)}>
                                编辑
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

// 使用HOC的组件示例
const UserManagement = withPermission('user:view_all')(({ permissions }) => {
    return (
        <div>
            <h2>用户管理</h2>
            <p>只有有权限的用户才能看到此页面</p>
        </div>
    );
});

const AdminPanel = withRole(['admin', 'super_admin'])(({ permissions }) => {
    return (
        <div>
            <h2>管理员面板</h2>
            <p>只有管理员和超级管理员才能看到此页面</p>
        </div>
    );
});

// App根组件示例
export const App = () => {
    const [user, setUser] = useState(null);
    
    // 模拟用户登录
    const handleLogin = (role) => {
        const mockUser = {
            id: 1,
            name: `测试${role}`,
            role: role
        };
        setUser(mockUser);
    };
    
    return (
        <PermissionProvider initialUser={user}>
            <div className="app">
                <header>
                    <h1>权限控制系统示例</h1>
                    <div>
                        <button onClick={() => handleLogin('super_admin')}>
                            登录为超级管理员
                        </button>
                        <button onClick={() => handleLogin('admin')}>
                            登录为管理员
                        </button>
                        <button onClick={() => handleLogin('manager')}>
                            登录为经理
                        </button>
                        <button onClick={() => handleLogin('user')}>
                            登录为用户
                        </button>
                        <button onClick={() => setUser(null)}>
                            退出登录
                        </button>
                    </div>
                </header>
                
                <main>
                    {user ? (
                        <>
                            <PermissionExample />
                            <UserManagement />
                            <AdminPanel />
                        </>
                    ) : (
                        <p>请先登录</p>
                    )}
                </main>
            </div>
        </PermissionProvider>
    );
};

export default {
    PermissionProvider,
    usePermissions,
    usePermissionCheck,
    useRoleCheck,
    PermissionGate,
    PermissionButton,
    PermissionRoute,
    withPermissions,
    withRole,
    withPermission,
    PermissionExample,
    App
};