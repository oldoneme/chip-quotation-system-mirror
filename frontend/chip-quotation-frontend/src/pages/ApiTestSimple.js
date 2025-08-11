import React, { useState, useEffect } from 'react';
import { Button, Card, Alert } from 'antd';
import api from '../services/api';

const ApiTestSimple = () => {
  const [status, setStatus] = useState('准备测试...');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const testApi = async () => {
    setStatus('正在测试API连接...');
    setError(null);
    setResult(null);
    
    try {
      console.log('开始API测试');
      const response = await api.get('/machines/');
      console.log('API响应:', response.data);
      setResult(response.data);
      setStatus(`成功获取${response.data.length}条机器数据`);
    } catch (err) {
      console.error('API测试失败:', err);
      setError(err.message);
      setStatus('API测试失败');
    }
  };

  // 自动测试
  useEffect(() => {
    testApi();
  }, []);

  return (
    <Card title="API连接测试" style={{ margin: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3>状态: {status}</h3>
        <Button type="primary" onClick={testApi}>重新测试</Button>
      </div>
      
      {error && (
        <Alert 
          message="错误信息"
          description={error}
          type="error"
          style={{ marginBottom: '20px' }}
        />
      )}
      
      {result && (
        <div>
          <h4>成功获取数据:</h4>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto' 
          }}>
            {JSON.stringify(result.slice(0, 2), null, 2)}
          </pre>
          {result.length > 2 && <p>...还有{result.length - 2}条数据</p>}
        </div>
      )}
    </Card>
  );
};

export default ApiTestSimple;