/**
 * Step 4 前端组件适配测试
 * 验证升级后的UnifiedApprovalPanel组件功能
 */

import UnifiedApprovalApiV3 from './services/unifiedApprovalApi_v3';

// 测试V3 API服务
async function testApiV3Service() {
  console.log('=== 测试 V3 API 服务 ===');

  try {
    // 测试健康检查
    console.log('1. 测试健康检查...');
    const health = await UnifiedApprovalApiV3.checkHealth();
    console.log('✅ 健康检查成功:', health);

    // 测试获取审批列表
    console.log('2. 测试获取审批列表...');
    const list = await UnifiedApprovalApiV3.getApprovalList({ page: 1, pageSize: 10 });
    console.log('✅ 获取列表成功:', list);

    // 测试获取审批状态 (使用列表中的第一个ID)
    if (list.items && list.items.length > 0) {
      const firstQuote = list.items[0];
      console.log('3. 测试获取审批状态...');
      const status = await UnifiedApprovalApiV3.getApprovalStatus(firstQuote.quote_id);
      console.log('✅ 获取状态成功:', status);

      // 测试权限检查
      console.log('4. 测试权限检查...');
      const mockUser = { id: 1, role: 'admin' };
      const permissions = UnifiedApprovalApiV3.checkApprovalPermissions(status, mockUser);
      console.log('✅ 权限检查成功:', permissions);

      // 测试状态配置
      console.log('5. 测试状态配置...');
      const statusConfig = UnifiedApprovalApiV3.getApprovalStatusConfig(status.current_status);
      console.log('✅ 状态配置成功:', statusConfig);
    }

    return true;
  } catch (error) {
    console.error('❌ API测试失败:', error);
    return false;
  }
}

// 测试组件配置功能
function testComponentUtilities() {
  console.log('\n=== 测试组件配置功能 ===');

  try {
    // 测试状态配置
    console.log('1. 测试状态配置...');
    const statuses = ['draft', 'pending', 'approved', 'rejected', 'withdrawn'];
    statuses.forEach(status => {
      const config = UnifiedApprovalApiV3.getApprovalStatusConfig(status);
      console.log(`✅ ${status}:`, config);
    });

    // 测试操作按钮配置
    console.log('2. 测试操作按钮配置...');
    const actions = ['submit', 'approve', 'reject', 'withdraw', 'delegate'];
    actions.forEach(action => {
      const config = UnifiedApprovalApiV3.getActionButtonConfig(action);
      console.log(`✅ ${action}:`, config);
    });

    // 测试历史记录格式化
    console.log('3. 测试历史记录格式化...');
    const mockHistory = [
      { id: 1, action: 'submit', status: 'pending', created_at: new Date().toISOString(), comments: '提交审批' },
      { id: 2, action: 'approve', status: 'approved', created_at: new Date().toISOString(), comments: '批准' }
    ];
    const formatted = UnifiedApprovalApiV3.formatApprovalHistory(mockHistory);
    console.log('✅ 历史记录格式化成功:', formatted);

    return true;
  } catch (error) {
    console.error('❌ 组件功能测试失败:', error);
    return false;
  }
}

// 测试错误处理
function testErrorHandling() {
  console.log('\n=== 测试错误处理 ===');

  try {
    // 测试空数据处理
    console.log('1. 测试空数据处理...');
    const emptyPermissions = UnifiedApprovalApiV3.checkApprovalPermissions(null, null);
    console.log('✅ 空数据权限检查:', emptyPermissions);

    // 测试历史记录处理
    const emptyHistory = UnifiedApprovalApiV3.formatApprovalHistory(null);
    console.log('✅ 空历史记录处理:', emptyHistory);

    // 测试未知状态处理
    const unknownStatus = UnifiedApprovalApiV3.getApprovalStatusConfig('unknown');
    console.log('✅ 未知状态处理:', unknownStatus);

    return true;
  } catch (error) {
    console.error('❌ 错误处理测试失败:', error);
    return false;
  }
}

// 模拟组件测试
function testComponentIntegration() {
  console.log('\n=== 测试组件集成 ===');

  try {
    // 模拟组件属性
    const mockProps = {
      quote: { id: 1, quote_number: 'TEST-001' },
      currentUser: { id: 1, role: 'admin' },
      showHistory: true,
      layout: 'desktop',
      enableRealTimeUpdate: true,
      updateInterval: 30000
    };

    console.log('✅ 组件属性配置:', mockProps);

    // 模拟权限检查流程
    const mockApprovalData = {
      quote_id: 1,
      current_status: 'pending',
      can_approve: true,
      can_reject: true,
      can_withdraw: false
    };

    const permissions = UnifiedApprovalApiV3.checkApprovalPermissions(mockApprovalData, mockProps.currentUser);
    console.log('✅ 权限检查流程:', permissions);

    return true;
  } catch (error) {
    console.error('❌ 组件集成测试失败:', error);
    return false;
  }
}

// 主测试函数
async function runAllTests() {
  console.log('🚀 开始 Step 4 前端组件适配测试\n');

  const results = [];

  // 执行所有测试
  results.push(['API V3 服务测试', await testApiV3Service()]);
  results.push(['组件配置功能测试', testComponentUtilities()]);
  results.push(['错误处理测试', testErrorHandling()]);
  results.push(['组件集成测试', testComponentIntegration()]);

  // 输出测试结果
  console.log('\n' + '='.repeat(50));
  console.log('📊 测试结果总结');
  console.log('='.repeat(50));

  let passedCount = 0;
  results.forEach(([testName, passed]) => {
    const status = passed ? '✅ 通过' : '❌ 失败';
    console.log(`${testName}: ${status}`);
    if (passed) passedCount++;
  });

  console.log(`\n总体结果: ${passedCount}/${results.length} 通过`);

  if (passedCount === results.length) {
    console.log('🎉 所有测试通过！Step 4 前端组件适配成功！');
  } else {
    console.log(`⚠️ ${results.length - passedCount} 个测试失败，需要修复`);
  }

  return passedCount === results.length;
}

// 如果在浏览器环境中运行
if (typeof window !== 'undefined') {
  window.testStep4Frontend = runAllTests;
  console.log('📝 在浏览器控制台中运行 testStep4Frontend() 来执行测试');
}

// 如果在Node.js环境中运行
if (typeof module !== 'undefined' && module.exports) {
  module.exports = runAllTests;
}

export default runAllTests;