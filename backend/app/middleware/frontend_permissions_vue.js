/**
 * Vue.js 权限控制集成
 * 提供Vue组件和指令用于权限控制
 */

import { PermissionChecker, UIPermissionController, APIPermissionController } from './frontend_permissions.js';

// Vue 3 权限插件
export const PermissionPlugin = {
    install(app, options = {}) {
        // 创建权限检查器实例
        const permissionChecker = new PermissionChecker();
        const uiController = new UIPermissionController(permissionChecker);
        const apiController = new APIPermissionController(permissionChecker);
        
        // 提供全局属性
        app.config.globalProperties.$permissions = permissionChecker;
        app.config.globalProperties.$uiController = uiController;
        app.config.globalProperties.$apiController = apiController;
        
        // 提供inject key
        app.provide('permissions', permissionChecker);
        app.provide('uiController', uiController);
        app.provide('apiController', apiController);
        
        // 注册全局指令
        
        // v-permission 指令 - 根据权限显示/隐藏元素
        app.directive('permission', {
            mounted(el, binding) {
                const permission = binding.value;
                if (!permissionChecker.hasPermission(permission)) {
                    el.style.display = 'none';
                }
            },
            updated(el, binding) {
                const permission = binding.value;
                if (!permissionChecker.hasPermission(permission)) {
                    el.style.display = 'none';
                } else {
                    el.style.display = '';
                }
            }
        });
        
        // v-role 指令 - 根据角色显示/隐藏元素
        app.directive('role', {
            mounted(el, binding) {
                const roles = Array.isArray(binding.value) ? binding.value : [binding.value];
                if (!permissionChecker.hasRole(roles)) {
                    el.style.display = 'none';
                }
            },
            updated(el, binding) {
                const roles = Array.isArray(binding.value) ? binding.value : [binding.value];
                if (!permissionChecker.hasRole(roles)) {
                    el.style.display = 'none';
                } else {
                    el.style.display = '';
                }
            }
        });
        
        // v-min-role 指令 - 最低角色要求
        app.directive('min-role', {
            mounted(el, binding) {
                const minRole = binding.value;
                let hasPermission = false;
                
                switch (minRole) {
                    case 'user':
                        hasPermission = true;
                        break;
                    case 'manager':
                        hasPermission = permissionChecker.isManagerOrAbove();
                        break;
                    case 'admin':
                        hasPermission = permissionChecker.isAdminOrAbove();
                        break;
                    case 'super_admin':
                        hasPermission = permissionChecker.hasRole('super_admin');
                        break;
                }
                
                if (!hasPermission) {
                    el.style.display = 'none';
                }
            },
            updated(el, binding) {
                const minRole = binding.value;
                let hasPermission = false;
                
                switch (minRole) {
                    case 'user':
                        hasPermission = true;
                        break;
                    case 'manager':
                        hasPermission = permissionChecker.isManagerOrAbove();
                        break;
                    case 'admin':
                        hasPermission = permissionChecker.isAdminOrAbove();
                        break;
                    case 'super_admin':
                        hasPermission = permissionChecker.hasRole('super_admin');
                        break;
                }
                
                if (!hasPermission) {
                    el.style.display = 'none';
                } else {
                    el.style.display = '';
                }
            }
        });
        
        // v-disable-permission 指令 - 根据权限禁用元素
        app.directive('disable-permission', {
            mounted(el, binding) {
                const permission = binding.value;
                if (!permissionChecker.hasPermission(permission)) {
                    el.disabled = true;
                    el.title = '权限不足';
                    el.classList.add('permission-disabled');
                }
            },
            updated(el, binding) {
                const permission = binding.value;
                if (!permissionChecker.hasPermission(permission)) {
                    el.disabled = true;
                    el.title = '权限不足';
                    el.classList.add('permission-disabled');
                } else {
                    el.disabled = false;
                    el.title = '';
                    el.classList.remove('permission-disabled');
                }
            }
        });
    }
};

// Vue 3 Composition API Composable
export function usePermissions() {
    const permissions = inject('permissions');
    const uiController = inject('uiController');
    const apiController = inject('apiController');
    
    if (!permissions) {
        throw new Error('usePermissions 必须在安装了 PermissionPlugin 的组件中使用');
    }
    
    return {
        permissions,
        uiController,
        apiController,
        hasPermission: (permission) => permissions.hasPermission(permission),
        hasRole: (roles) => permissions.hasRole(roles),
        isAdminOrAbove: () => permissions.isAdminOrAbove(),
        isManagerOrAbove: () => permissions.isManagerOrAbove(),
        canViewQuotation: (quotation) => permissions.canViewQuotation(quotation),
        canEditQuotation: (quotation) => permissions.canEditQuotation(quotation),
        canManageUser: (user) => permissions.canManageUser(user),
        secureFetch: (url, options) => apiController.secureFetch(url, options)
    };
}

// 权限控制 Mixin (Vue 2 兼容)
export const PermissionMixin = {
    data() {
        return {
            permissionChecker: new PermissionChecker(),
            uiController: null,
            apiController: null
        };
    },
    created() {
        this.uiController = new UIPermissionController(this.permissionChecker);
        this.apiController = new APIPermissionController(this.permissionChecker);
    },
    methods: {
        hasPermission(permission) {
            return this.permissionChecker.hasPermission(permission);
        },
        hasRole(roles) {
            return this.permissionChecker.hasRole(roles);
        },
        isAdminOrAbove() {
            return this.permissionChecker.isAdminOrAbove();
        },
        isManagerOrAbove() {
            return this.permissionChecker.isManagerOrAbove();
        },
        canViewQuotation(quotation) {
            return this.permissionChecker.canViewQuotation(quotation);
        },
        canEditQuotation(quotation) {
            return this.permissionChecker.canEditQuotation(quotation);
        },
        canManageUser(user) {
            return this.permissionChecker.canManageUser(user);
        },
        async secureFetch(url, options) {
            return await this.apiController.secureFetch(url, options);
        }
    }
};

// 权限路由守卫
export function createPermissionGuard(permissionChecker) {
    return (to, from, next) => {
        // 检查路由权限要求
        const requiredPermission = to.meta.permission;
        const requiredRole = to.meta.role;
        const minRole = to.meta.minRole;
        
        if (requiredPermission && !permissionChecker.hasPermission(requiredPermission)) {
            next({ name: 'Forbidden', params: { message: '权限不足' } });
            return;
        }
        
        if (requiredRole && !permissionChecker.hasRole(requiredRole)) {
            next({ name: 'Forbidden', params: { message: '角色权限不足' } });
            return;
        }
        
        if (minRole) {
            let hasPermission = false;
            switch (minRole) {
                case 'user':
                    hasPermission = true;
                    break;
                case 'manager':
                    hasPermission = permissionChecker.isManagerOrAbove();
                    break;
                case 'admin':
                    hasPermission = permissionChecker.isAdminOrAbove();
                    break;
                case 'super_admin':
                    hasPermission = permissionChecker.hasRole('super_admin');
                    break;
            }
            
            if (!hasPermission) {
                next({ name: 'Forbidden', params: { message: '权限等级不足' } });
                return;
            }
        }
        
        next();
    };
}

// 示例路由配置
export const exampleRoutes = [
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { minRole: 'user' }
    },
    {
        path: '/users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagement.vue'),
        meta: { permission: 'user:view_all' }
    },
    {
        path: '/quotations',
        name: 'QuotationManagement',
        component: () => import('@/views/QuotationManagement.vue'),
        meta: { minRole: 'user' }
    },
    {
        path: '/statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { minRole: 'manager' }
    },
    {
        path: '/admin',
        name: 'AdminPanel',
        component: () => import('@/views/AdminPanel.vue'),
        meta: { role: ['admin', 'super_admin'] }
    },
    {
        path: '/system',
        name: 'SystemManagement',
        component: () => import('@/views/SystemManagement.vue'),
        meta: { role: 'super_admin' }
    }
];

// Vue组件示例模板
export const PermissionComponentTemplate = `
<template>
  <div class="permission-demo">
    <!-- 使用指令控制显示 -->
    <div v-permission="'user:create'">
      <el-button type="primary">创建用户</el-button>
    </div>
    
    <div v-role="['admin', 'super_admin']">
      <el-button type="danger">管理员功能</el-button>
    </div>
    
    <div v-min-role="'manager'">
      <el-button type="warning">经理及以上功能</el-button>
    </div>
    
    <el-button 
      v-disable-permission="'quotation:delete'"
      type="danger"
    >
      删除报价
    </el-button>
    
    <!-- 在模板中使用方法 -->
    <div v-if="hasPermission('statistics:view_all')">
      <h3>统计数据</h3>
      <p>只有有权限的用户才能看到此内容</p>
    </div>
    
    <div v-if="isAdminOrAbove()">
      <h3>管理员功能区</h3>
      <el-button @click="handleAdminAction">管理操作</el-button>
    </div>
    
    <!-- 动态权限检查 -->
    <div v-for="quotation in quotations" :key="quotation.id">
      <div class="quotation-item">
        <span>报价 #{{ quotation.id }}</span>
        <el-button 
          v-if="canViewQuotation(quotation)"
          @click="viewQuotation(quotation)"
        >
          查看
        </el-button>
        <el-button 
          v-if="canEditQuotation(quotation)"
          @click="editQuotation(quotation)"
          type="primary"
        >
          编辑
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { usePermissions } from '@/utils/permissions';

export default {
  name: 'PermissionDemo',
  setup() {
    const {
      hasPermission,
      hasRole,
      isAdminOrAbove,
      isManagerOrAbove,
      canViewQuotation,
      canEditQuotation,
      secureFetch
    } = usePermissions();
    
    const handleAdminAction = async () => {
      try {
        const response = await secureFetch('/api/v1/admin/action', {
          method: 'POST'
        });
        // 处理响应
      } catch (error) {
        console.error('权限错误:', error.message);
      }
    };
    
    return {
      hasPermission,
      hasRole,
      isAdminOrAbove,
      isManagerOrAbove,
      canViewQuotation,
      canEditQuotation,
      handleAdminAction
    };
  }
};
</script>
`;