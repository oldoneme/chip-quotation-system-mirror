/**
 * 前端统一审批API测试脚本
 * 验证新创建的UnifiedApprovalApiService功能
 */

import UnifiedApprovalApiService from './services/unifiedApprovalApi';

// 测试数据
const TEST_QUOTE_ID = '2a72d639-1486-442d-bce3-02a20672de28'; // 已知存在的报价单

class UnifiedApprovalFrontendTest {
  constructor() {
    this.testResults = [];
  }

  async runAllTests() {
    console.log('🧪 开始前端统一审批API测试');
    console.log('=' * 50);

    try {
      await this.testStatusQuery();
      await this.testHistoryQuery();
      await this.testPermissionCheck();
      await this.testUtilityMethods();

      this.printSummary();
    } catch (error) {
      console.error('💥 测试执行异常:', error);
    }
  }

  async testStatusQuery() {
    console.log('\n🔍 测试1: 状态查询功能');
    try {
      const status = await UnifiedApprovalApiService.getApprovalStatus(TEST_QUOTE_ID);

      if (status && status.quote_id && status.approval_status) {
        console.log('   ✅ 状态查询成功');
        console.log(`   📋 报价单号: ${status.quote_number}`);
        console.log(`   📊 状态: ${status.approval_status}`);
        console.log(`   🏢 审批方式: ${status.has_wecom_approval ? '企业微信' : '内部审批'}`);
        this.testResults.push({ test: '状态查询', result: 'PASS' });
      } else {
        throw new Error('状态数据格式不正确');
      }
    } catch (error) {
      console.log('   ❌ 状态查询失败:', error.message);
      this.testResults.push({ test: '状态查询', result: 'FAIL', error: error.message });
    }
  }

  async testHistoryQuery() {
    console.log('\n📚 测试2: 历史查询功能');
    try {
      const history = await UnifiedApprovalApiService.getApprovalHistory(TEST_QUOTE_ID);

      if (history && typeof history.total === 'number' && Array.isArray(history.history)) {
        console.log('   ✅ 历史查询成功');
        console.log(`   📝 历史记录数: ${history.total}`);
        this.testResults.push({ test: '历史查询', result: 'PASS' });
      } else {
        throw new Error('历史数据格式不正确');
      }
    } catch (error) {
      console.log('   ❌ 历史查询失败:', error.message);
      this.testResults.push({ test: '历史查询', result: 'FAIL', error: error.message });
    }
  }

  testPermissionCheck() {
    console.log('\n🔐 测试3: 权限检查功能');
    try {
      // 模拟报价单和用户数据
      const mockQuote = {
        id: TEST_QUOTE_ID,
        creator_id: 'user1',
        approval_status: 'draft'
      };

      const mockUser = {
        id: 'user1',
        role: 'user'
      };

      const permissions = UnifiedApprovalApiService.checkApprovalPermissions(mockQuote, mockUser);

      if (permissions && typeof permissions.canSubmit === 'boolean') {
        console.log('   ✅ 权限检查成功');
        console.log(`   📤 可提交: ${permissions.canSubmit}`);
        console.log(`   ✅ 可批准: ${permissions.canApprove}`);
        console.log(`   🚫 可拒绝: ${permissions.canReject}`);
        this.testResults.push({ test: '权限检查', result: 'PASS' });
      } else {
        throw new Error('权限检查结果格式不正确');
      }
    } catch (error) {
      console.log('   ❌ 权限检查失败:', error.message);
      this.testResults.push({ test: '权限检查', result: 'FAIL', error: error.message });
    }
  }

  testUtilityMethods() {
    console.log('\n🔧 测试4: 工具方法功能');
    try {
      // 测试状态配置获取
      const statusConfig = UnifiedApprovalApiService.getApprovalStatusConfig('pending');
      if (!statusConfig || !statusConfig.text || !statusConfig.color) {
        throw new Error('状态配置获取失败');
      }

      // 测试审批方式名称获取
      const methodName = UnifiedApprovalApiService.getApprovalMethodName('wecom');
      if (!methodName || methodName === 'wecom') {
        throw new Error('审批方式名称获取失败');
      }

      console.log('   ✅ 工具方法测试成功');
      console.log(`   🏷️ 状态标签: ${statusConfig.text} (${statusConfig.color})`);
      console.log(`   📱 审批方式: ${methodName}`);
      this.testResults.push({ test: '工具方法', result: 'PASS' });
    } catch (error) {
      console.log('   ❌ 工具方法测试失败:', error.message);
      this.testResults.push({ test: '工具方法', result: 'FAIL', error: error.message });
    }
  }

  printSummary() {
    console.log('\n' + '='.repeat(50));
    console.log('📊 测试结果总结:');

    let passCount = 0;
    let failCount = 0;

    this.testResults.forEach((result, index) => {
      const status = result.result === 'PASS' ? '✅ 通过' : '❌ 失败';
      console.log(`   测试${index + 1} (${result.test}): ${status}`);
      if (result.error) {
        console.log(`      错误: ${result.error}`);
      }

      if (result.result === 'PASS') passCount++;
      else failCount++;
    });

    console.log(`\n总体结果: ${passCount}/${this.testResults.length} 测试通过`);

    if (failCount === 0) {
      console.log('🎉 所有前端API测试通过！统一审批界面已准备就绪。');
      return true;
    } else {
      console.log('⚠️ 部分测试失败，需要进一步检查。');
      return false;
    }
  }
}

// 执行测试
const testRunner = new UnifiedApprovalFrontendTest();
testRunner.runAllTests()
  .then(() => {
    console.log('\n✅ 前端测试执行完成');
  })
  .catch(error => {
    console.error('\n💥 前端测试执行失败:', error);
  });

export default UnifiedApprovalFrontendTest;