import React, { useState, useEffect } from 'react';
import { getMachines } from '../services/machines';
import { getConfigurations } from '../services/configurations';
import { getCardTypes } from '../services/cardTypes';
import { getAuxiliaryEquipment } from '../services/auxiliaryEquipment';

const ApiTest = () => {
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState(false);

  const runTests = async () => {
    setLoading(true);
    const results = {};
    
    try {
      console.log('开始测试API调用...');
      
      // 测试获取机器列表
      try {
        console.log('测试获取机器列表...');
        const machines = await getMachines();
        results.machines = { success: true, data: machines, error: null };
        console.log('机器列表获取成功:', machines);
      } catch (error) {
        results.machines = { success: false, data: null, error: error.message };
        console.error('获取机器列表失败:', error);
      }
      
      // 测试获取配置列表
      try {
        console.log('测试获取配置列表...');
        const configurations = await getConfigurations();
        results.configurations = { success: true, data: configurations, error: null };
        console.log('配置列表获取成功:', configurations);
      } catch (error) {
        results.configurations = { success: false, data: null, error: error.message };
        console.error('获取配置列表失败:', error);
      }
      
      // 测试获取板卡类型列表
      try {
        console.log('测试获取板卡类型列表...');
        const cardTypes = await getCardTypes();
        results.cardTypes = { success: true, data: cardTypes, error: null };
        console.log('板卡类型列表获取成功:', cardTypes);
      } catch (error) {
        results.cardTypes = { success: false, data: null, error: error.message };
        console.error('获取板卡类型列表失败:', error);
      }
      
      // 测试获取辅助设备列表
      try {
        console.log('测试获取辅助设备列表...');
        const auxEquipment = await getAuxiliaryEquipment();
        results.auxEquipment = { success: true, data: auxEquipment, error: null };
        console.log('辅助设备列表获取成功:', auxEquipment);
      } catch (error) {
        results.auxEquipment = { success: false, data: null, error: error.message };
        console.error('获取辅助设备列表失败:', error);
      }
      
      
      setTestResults(results);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runTests();
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>API测试页面</h1>
      <button onClick={runTests} disabled={loading}>
        {loading ? '测试中...' : '重新运行测试'}
      </button>
      
      <div style={{ marginTop: '20px' }}>
        <h2>测试结果</h2>
        {Object.keys(testResults).map((key) => (
          <div key={key} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #ccc' }}>
            <h3>{key}</h3>
            <p>状态: {testResults[key].success ? '成功' : '失败'}</p>
            {testResults[key].error && (
              <p style={{ color: 'red' }}>错误: {testResults[key].error}</p>
            )}
            {testResults[key].data && (
              <p>数据: {JSON.stringify(testResults[key].data)}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ApiTest;