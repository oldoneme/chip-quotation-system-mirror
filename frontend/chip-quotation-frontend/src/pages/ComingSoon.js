import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const ComingSoon = ({ title = '功能开发中' }) => {
  const navigate = useNavigate();

  return (
    <Result
      status="info"
      title={title}
      subTitle="此功能正在开发中，敬请期待"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回首页
        </Button>
      }
    />
  );
};

export default ComingSoon;