/**
 * 前端权限检查中间件
 * 用于在前端界面中根据用户角色控制功能可见性和操作权限
 */

// 角色权限映射
const ROLE_PERMISSIONS = {
    'super_admin': [
        // 系统管理权限
        'system:admin_panel',
        'system:user_management',
        'system:role_management',
        'system:system_settings',
        'system:backup_restore',
        'system:view_all_logs',
        
        // 用户管理权限
        'user:view_all',
        'user:create',
        'user:edit_all',
        'user:delete',
        'user:change_role',
        'user:disable_enable',
        
        // 报价管理权限
        'quotation:view_all',
        'quotation:create',
        'quotation:edit_all',
        'quotation:delete',
        'quotation:approve_reject',
        'quotation:set_priority',
        'quotation:export',
        
        // 统计分析权限
        'statistics:view_all',
        'statistics:export_data',
        'statistics:system_dashboard',
        
        // 操作日志权限
        'logs:view_all',
        'logs:export',
        
        // 配置管理权限
        'config:machines',
        'config:suppliers',
        'config:machine_types'
    ],
    
    'admin': [
        // 用户管理权限（除了超级管理员操作）
        'user:view_all',
        'user:create',
        'user:edit_all',
        'user:disable_enable',
        
        // 报价管理权限
        'quotation:view_all',
        'quotation:create',
        'quotation:edit_all',
        'quotation:delete',
        'quotation:approve_reject',
        'quotation:set_priority',
        'quotation:export',
        
        // 统计分析权限
        'statistics:view_all',
        'statistics:export_data',
        'statistics:admin_dashboard',
        
        // 操作日志权限
        'logs:view_all',
        'logs:export',
        
        // 配置管理权限
        'config:machines',
        'config:suppliers',
        'config:machine_types'
    ],
    
    'manager': [
        // 用户管理权限（查看）
        'user:view_all',
        
        // 报价管理权限
        'quotation:view_all',
        'quotation:create',
        'quotation:edit_all',
        'quotation:approve_reject',
        'quotation:set_priority',
        'quotation:export',
        
        // 统计分析权限
        'statistics:view_all',
        'statistics:export_data',
        'statistics:manager_dashboard',
        
        // 操作日志权限（有限）
        'logs:view_all',
        
        // 配置管理权限（查看）
        'config:view_machines',
        'config:view_suppliers',
        'config:view_machine_types'
    ],
    
    'user': [
        // 个人信息权限
        'user:view_self',
        'user:edit_self',
        
        // 报价管理权限（限制）
        'quotation:view_own',
        'quotation:create',
        'quotation:edit_own_pending',
        
        // 统计分析权限（个人）
        'statistics:view_own',
        'statistics:personal_dashboard',
        
        // 操作日志权限（个人）
        'logs:view_own',
        
        // 配置查看权限
        'config:view_machines',
        'config:view_suppliers',
        'config:view_machine_types'
    ]
};

/**
 * 权限检查类
 */
class PermissionChecker {
    constructor() {
        this.currentUser = null;
        this.userPermissions = [];
    }
    
    /**
     * 初始化用户权限
     * @param {Object} user 用户信息对象
     */
    initUser(user) {
        this.currentUser = user;
        this.userPermissions = ROLE_PERMISSIONS[user.role] || [];
        console.log(`用户 ${user.name} (${user.role}) 权限初始化完成`);
    }
    
    /**
     * 检查是否有指定权限
     * @param {string} permission 权限标识
     * @returns {boolean}
     */
    hasPermission(permission) {
        return this.userPermissions.includes(permission);
    }
    
    /**
     * 检查是否有任一权限
     * @param {string[]} permissions 权限列表
     * @returns {boolean}
     */
    hasAnyPermission(permissions) {
        return permissions.some(permission => this.hasPermission(permission));
    }
    
    /**
     * 检查是否有所有权限
     * @param {string[]} permissions 权限列表
     * @returns {boolean}
     */
    hasAllPermissions(permissions) {
        return permissions.every(permission => this.hasPermission(permission));
    }
    
    /**
     * 根据角色检查权限
     * @param {string|string[]} allowedRoles 允许的角色
     * @returns {boolean}
     */
    hasRole(allowedRoles) {
        if (!this.currentUser) return false;
        const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
        return roles.includes(this.currentUser.role);
    }
    
    /**
     * 检查是否为管理员或以上角色
     * @returns {boolean}
     */
    isAdminOrAbove() {
        return this.hasRole(['admin', 'super_admin']);
    }
    
    /**
     * 检查是否为销售经理或以上角色
     * @returns {boolean}
     */
    isManagerOrAbove() {
        return this.hasRole(['manager', 'admin', 'super_admin']);
    }
    
    /**
     * 检查是否可以操作特定用户
     * @param {Object} targetUser 目标用户
     * @returns {boolean}
     */
    canManageUser(targetUser) {
        if (!this.currentUser || !targetUser) return false;
        
        // 超级管理员可以管理所有用户
        if (this.currentUser.role === 'super_admin') return true;
        
        // 管理员可以管理除超级管理员外的用户
        if (this.currentUser.role === 'admin') {
            return targetUser.role !== 'super_admin';
        }
        
        // 销售经理和普通用户不能管理其他用户
        return false;
    }
    
    /**
     * 检查是否可以查看特定报价
     * @param {Object} quotation 报价对象
     * @returns {boolean}
     */
    canViewQuotation(quotation) {
        if (!this.currentUser || !quotation) return false;
        
        // 管理员及以上可以查看所有报价
        if (this.isManagerOrAbove()) return true;
        
        // 普通用户只能查看自己的报价
        return quotation.created_by === this.currentUser.id;
    }
    
    /**
     * 检查是否可以编辑特定报价
     * @param {Object} quotation 报价对象
     * @returns {boolean}
     */
    canEditQuotation(quotation) {
        if (!this.currentUser || !quotation) return false;
        
        // 管理员及以上可以编辑所有报价
        if (this.isManagerOrAbove()) return true;
        
        // 普通用户只能编辑自己的待审核报价
        return quotation.created_by === this.currentUser.id && quotation.status === 'pending';
    }
}

/**
 * DOM 元素权限控制工具
 */
class UIPermissionController {
    constructor(permissionChecker) {
        this.checker = permissionChecker;
    }
    
    /**
     * 根据权限隐藏/显示元素
     * @param {string} selector CSS选择器
     * @param {string} permission 所需权限
     */
    toggleElementByPermission(selector, permission) {
        const elements = document.querySelectorAll(selector);
        const hasPermission = this.checker.hasPermission(permission);
        
        elements.forEach(element => {
            element.style.display = hasPermission ? '' : 'none';
        });
    }
    
    /**
     * 根据角色隐藏/显示元素
     * @param {string} selector CSS选择器
     * @param {string|string[]} allowedRoles 允许的角色
     */
    toggleElementByRole(selector, allowedRoles) {
        const elements = document.querySelectorAll(selector);
        const hasRole = this.checker.hasRole(allowedRoles);
        
        elements.forEach(element => {
            element.style.display = hasRole ? '' : 'none';
        });
    }
    
    /**
     * 禁用/启用按钮
     * @param {string} selector CSS选择器
     * @param {string} permission 所需权限
     */
    toggleButtonByPermission(selector, permission) {
        const buttons = document.querySelectorAll(selector);
        const hasPermission = this.checker.hasPermission(permission);
        
        buttons.forEach(button => {
            button.disabled = !hasPermission;
            if (!hasPermission) {
                button.title = '权限不足';
                button.classList.add('permission-disabled');
            } else {
                button.classList.remove('permission-disabled');
            }
        });
    }
    
    /**
     * 初始化页面权限控制
     */
    initPagePermissions() {
        // 通过 data-permission 属性控制元素显示
        document.querySelectorAll('[data-permission]').forEach(element => {
            const permission = element.dataset.permission;
            const hasPermission = this.checker.hasPermission(permission);
            element.style.display = hasPermission ? '' : 'none';
        });
        
        // 通过 data-role 属性控制元素显示
        document.querySelectorAll('[data-role]').forEach(element => {
            const roles = element.dataset.role.split(',').map(r => r.trim());
            const hasRole = this.checker.hasRole(roles);
            element.style.display = hasRole ? '' : 'none';
        });
        
        // 通过 data-min-role 属性控制元素显示（最低角色要求）
        document.querySelectorAll('[data-min-role]').forEach(element => {
            const minRole = element.dataset.minRole;
            let hasPermission = false;
            
            switch (minRole) {
                case 'user':
                    hasPermission = true;
                    break;
                case 'manager':
                    hasPermission = this.checker.isManagerOrAbove();
                    break;
                case 'admin':
                    hasPermission = this.checker.isAdminOrAbove();
                    break;
                case 'super_admin':
                    hasPermission = this.checker.hasRole('super_admin');
                    break;
            }
            
            element.style.display = hasPermission ? '' : 'none';
        });
    }
}

/**
 * API 请求权限检查工具
 */
class APIPermissionController {
    constructor(permissionChecker) {
        this.checker = permissionChecker;
    }
    
    /**
     * 检查API调用权限
     * @param {string} endpoint API端点
     * @param {string} method HTTP方法
     * @returns {boolean}
     */
    canCallAPI(endpoint, method = 'GET') {
        // API权限映射
        const apiPermissions = {
            '/api/v1/users': {
                'GET': 'user:view_all',
                'POST': 'user:create',
                'PUT': 'user:edit_all',
                'DELETE': 'user:delete'
            },
            '/api/v1/users/me': {
                'GET': 'user:view_self',
                'PUT': 'user:edit_self'
            },
            '/api/v1/quotations': {
                'GET': ['quotation:view_all', 'quotation:view_own'],
                'POST': 'quotation:create',
                'PUT': ['quotation:edit_all', 'quotation:edit_own_pending'],
                'DELETE': 'quotation:delete'
            },
            '/api/v1/statistics': {
                'GET': ['statistics:view_all', 'statistics:view_own']
            },
            '/api/v1/operation-logs': {
                'GET': ['logs:view_all', 'logs:view_own']
            }
        };
        
        const requiredPermissions = apiPermissions[endpoint]?.[method];
        if (!requiredPermissions) return true; // 如果没有定义权限，默认允许
        
        if (Array.isArray(requiredPermissions)) {
            return this.checker.hasAnyPermission(requiredPermissions);
        } else {
            return this.checker.hasPermission(requiredPermissions);
        }
    }
    
    /**
     * 创建带权限检查的fetch函数
     * @param {string} url 请求URL
     * @param {Object} options fetch选项
     * @returns {Promise}
     */
    async secureFetch(url, options = {}) {
        const method = options.method || 'GET';
        
        if (!this.canCallAPI(url, method)) {
            throw new Error('权限不足：无法访问此API');
        }
        
        return fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }
}

// 全局实例
let globalPermissionChecker = new PermissionChecker();
let globalUIController = new UIPermissionController(globalPermissionChecker);
let globalAPIController = new APIPermissionController(globalPermissionChecker);

// 导出（支持CommonJS和ES6模块）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PermissionChecker,
        UIPermissionController,
        APIPermissionController,
        ROLE_PERMISSIONS,
        permissionChecker: globalPermissionChecker,
        uiController: globalUIController,
        apiController: globalAPIController
    };
}

if (typeof window !== 'undefined') {
    window.PermissionChecker = PermissionChecker;
    window.UIPermissionController = UIPermissionController;
    window.APIPermissionController = APIPermissionController;
    window.permissionChecker = globalPermissionChecker;
    window.uiController = globalUIController;
    window.apiController = globalAPIController;
}