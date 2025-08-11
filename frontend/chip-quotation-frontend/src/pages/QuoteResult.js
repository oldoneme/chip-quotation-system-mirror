import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Table, Button, Card, Divider, message } from 'antd';
import { formatNumber } from '../utils';
import '../App.css';

const QuoteResult = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [quoteData, setQuoteData] = useState(null);

  useEffect(() => {
    let newData = null;
    
    // 优先从location.state中读取报价数据（来自量产报价页面）
    if (location.state) {
      newData = {
        type: '量产报价',
        ...location.state
      };
    } else {
      // 其次从sessionStorage中读取报价数据（来自工程报价页面）
      const storedQuoteData = sessionStorage.getItem('quoteData');
      if (storedQuoteData) {
        newData = JSON.parse(storedQuoteData);
      }
    }
    
    // 如果没有找到有效数据，使用默认的模拟数据
    if (!newData) {
      newData = {
        type: '工程报价',
        number: `QT-${new Date().toISOString().slice(0,10).replace(/-/g,"")}-0001`,
        date: new Date().toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        items: [
          {
            category: '测试机配置',
            items: []
          }
        ],
        engineeringRate: 1.2, // 工程系数
        personnelCost: 0, // 人员费用
        auxiliaryEquipmentCost: 0, // 辅助设备费用
        testMachineCost: 0, // 测试机费用（乘以工程系数）
        handlerCost: 0, // 分选机费用（乘以工程系数）
        proberCost: 0, // 探针台费用（乘以工程系数）
        totalCost: 0 // 总费用
      };
    }
    
    setQuoteData(newData);
  }, [location]);

  // 计算设备费用（乘以工程系数）
  const calculateEquipmentCost = (equipmentType) => {
    if (!quoteData || !quoteData[equipmentType] || !quoteData[`${equipmentType}Cards`]) return 0;
    
    const equipment = quoteData[equipmentType];
    const cards = quoteData[`${equipmentType}Cards`];
    
    const baseCost = cards.reduce((total, card) => {
      return total + ((card.unit_price / 10000) * equipment.exchange_rate * equipment.discount_rate * (card.quantity || 1));
    }, 0);
    
    return baseCost * (quoteData.engineeringRate || 1.2);
  };
  
  // 计算测试机费用（乘以工程系数）
  const calculateTestMachineCost = () => {
    return calculateEquipmentCost('testMachine');
  };
  
  // 计算分选机费用（乘以工程系数）
  const calculateHandlerCost = () => {
    return calculateEquipmentCost('handler');
  };
  
  // 计算探针台费用（乘以工程系数）
  const calculateProberCost = () => {
    return calculateEquipmentCost('prober');
  };
  
  // 计算工程师费用（不乘以工程系数）
  const calculateEngineerCost = () => {
    if (!quoteData || !quoteData.selectedPersonnel || !quoteData.selectedPersonnel.includes('工程师')) return 0;
    return 350; // 工程师费用固定为350元/小时
  };
  
  // 计算技术员费用（不乘以工程系数）
  const calculateTechnicianCost = () => {
    if (!quoteData || !quoteData.selectedPersonnel || !quoteData.selectedPersonnel.includes('技术员')) return 0;
    return 200; // 技术员费用固定为200元/小时
  };
  
  // 计算辅助设备费用（不乘以工程系数）
  const calculateAuxDeviceCost = () => {
    if (!quoteData || !quoteData.selectedAuxDevices || !quoteData.cardTypes) return 0;
    
    return quoteData.selectedAuxDevices.reduce((total, device) => {
      // 如果是机器类型的辅助设备，计算板卡费用
      if (device.machine_type) {
        // 查找该机器的板卡
        const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
        return total + machineCards.reduce((sum, card) => {
          return sum + ((card.unit_price / 10000) * device.exchange_rate * device.discount_rate * (card.quantity || 1));
        }, 0);
      } else {
        // 如果是原来的辅助设备类型，使用小时费率
        return total + (device.hourly_rate || 0);
      }
    }, 0);
  };

  // 计算单个辅助设备费用
  const calculateSingleAuxDeviceCost = (device) => {
    if (!quoteData || !quoteData.cardTypes) return 0;
    
    // 如果是机器类型的辅助设备，计算板卡费用
    if (device.machine_type) {
      // 查找该机器的板卡
      const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
      return machineCards.reduce((sum, card) => {
        return sum + ((card.unit_price / 10000) * device.exchange_rate * device.discount_rate * (card.quantity || 1));
      }, 0);
    } else {
      // 如果是原来的辅助设备类型，使用小时费率
      return device.hourly_rate || 0;
    }
  };


  return (
    <div>
      <Card title={quoteData && quoteData.type === '工程报价' ? '工程报价结果' : '量产报价结果'}>
        <div className="quote-result-content">
          <h3>费用明细</h3>
          {/* 显示各项费用 */}
          {quoteData && quoteData.type === '工程报价' && (
            <>
              {/* 设备费用 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>测试机机时费（含工程系数）:</span>
                <span>¥{formatNumber(calculateTestMachineCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>分选机机时费（含工程系数）:</span>
                <span>¥{formatNumber(calculateHandlerCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>探针台机时费（含工程系数）:</span>
                <span>¥{formatNumber(calculateProberCost())}</span>
              </div>
              
              {/* 辅助设备费用 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>辅助设备机时费:</span>
                <span>¥{formatNumber(calculateAuxDeviceCost())}</span>
              </div>
              
              {/* 显示每个辅助设备的详细信息 */}
              {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                <div style={{ paddingLeft: 20 }}>
                  {quoteData.selectedAuxDevices.map((device, index) => (
                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>
                        {device.name}
                        {device.machine_type && ` (${device.machine_type.name})`}
                      </span>
                      <span>¥{formatNumber(calculateSingleAuxDeviceCost(device))}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* 人员费用 */}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('工程师') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>工程师小时费:</span>
                  <span>¥{formatNumber(calculateEngineerCost())}</span>
                </div>
              )}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('技术员') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>技术员小时费:</span>
                  <span>¥{formatNumber(calculateTechnicianCost())}</span>
                </div>
              )}
            </>
          )}
          
          {quoteData && quoteData.type === '量产报价' && (
            <>
              <div style={{ padding: '20px 0' }}>
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('ft') && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span>FT小时费:</span>
                    <span>¥{formatNumber(quoteData.ftHourlyFee || 0)}</span>
                  </div>
                )}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('cp') && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span>CP小时费:</span>
                    <span>¥{formatNumber(quoteData.cpHourlyFee || 0)}</span>
                  </div>
                )}
                {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                      <span>辅助设备:</span>
                      <span></span>
                    </div>
                    {quoteData.selectedAuxDevices.map((device, index) => (
                      <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingLeft: 20 }}>
                        <span>{device.name}</span>
                        <span>¥{formatNumber(device.hourly_rate || 0)}/小时</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
        <Divider />
        <div className="quote-result-actions">
          <Button onClick={() => navigate('/mass-production-quote', { 
            state: { 
              fromResultPage: true,
              quoteData: quoteData
            } 
          })}>
            上一步
          </Button>
          <Button type="primary" onClick={() => navigate('/mass-production-quote')}>
            重新编辑
          </Button>
          <Button type="primary" onClick={() => window.print()}>
            打印报价
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default QuoteResult;