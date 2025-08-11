import React from 'react';
import { Steps } from 'antd';
import { CheckCircleOutlined, NumberOutlined } from '@ant-design/icons';

const StepIndicator = ({ currentStep, steps, style }) => {
  const stepItems = steps.map((stepTitle, index) => ({
    title: stepTitle,
    status: currentStep > index ? 'finish' : currentStep === index ? 'process' : 'wait',
    icon: currentStep > index ? <CheckCircleOutlined /> : <NumberOutlined />
  }));

  return (
    <div style={{ 
      marginBottom: 30, 
      padding: '20px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      ...style 
    }}>
      <Steps
        current={currentStep}
        items={stepItems}
        size="default"
        style={{ maxWidth: '800px', margin: '0 auto' }}
      />
      <div style={{ 
        textAlign: 'center', 
        marginTop: 16, 
        color: '#666',
        fontSize: '14px'
      }}>
        第 {currentStep + 1} 步，共 {steps.length} 步
      </div>
    </div>
  );
};

export default StepIndicator;