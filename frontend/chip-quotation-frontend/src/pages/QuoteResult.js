import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Table, Button, Card, Divider, message } from 'antd';
import { formatNumber } from '../utils';
import '../App.css';

const QuoteResult = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [quoteData, setQuoteData] = useState(null);

  // 格式化价格显示（包含币种符号）
  const formatPrice = (number) => {
    const formattedNumber = formatNumber(number);
    const currency = quoteData?.quoteCurrency || 'CNY';
    if (currency === 'USD') {
      return `$${formattedNumber}`;
    } else {
      return `¥${formattedNumber}`;
    }
  };

  useEffect(() => {
    let newData = null;
    
    // 优先从location.state中读取报价数据
    if (location.state) {
      // 检查是否已经包含了正确的type字段
      if (location.state.type) {
        newData = location.state;
      } else {
        // 兼容原有逻辑，默认为量产报价
        newData = {
          type: '量产报价',
          ...location.state
        };
      }
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
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    const baseCost = cards.reduce((total, card) => {
      let adjustedPrice = card.unit_price / 10000;
      
      // 根据报价币种和机器币种进行转换
      if (quoteCurrency === 'USD') {
        if (equipment.currency === 'CNY' || equipment.currency === 'RMB') {
          // RMB机器转USD：除以报价汇率
          adjustedPrice = adjustedPrice / quoteExchangeRate;
        }
        // USD机器：不做汇率转换，直接使用unit_price
      } else {
        // 报价币种是CNY，保持原逻辑
        adjustedPrice = adjustedPrice * equipment.exchange_rate;
      }
      
      return total + (adjustedPrice * equipment.discount_rate * (card.quantity || 1));
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
    
    let rate = 350; // 工程师费用固定为350元/小时
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    if (quoteCurrency === 'USD') {
      rate = rate / quoteExchangeRate;
    }
    return rate;
  };
  
  // 计算技术员费用（不乘以工程系数）
  const calculateTechnicianCost = () => {
    if (!quoteData || !quoteData.selectedPersonnel || !quoteData.selectedPersonnel.includes('技术员')) return 0;
    
    let rate = 200; // 技术员费用固定为200元/小时
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    if (quoteCurrency === 'USD') {
      rate = rate / quoteExchangeRate;
    }
    return rate;
  };
  
  // 计算辅助设备费用（不乘以工程系数）
  const calculateAuxDeviceCost = () => {
    if (!quoteData || !quoteData.selectedAuxDevices || !quoteData.cardTypes) return 0;
    
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    return quoteData.selectedAuxDevices.reduce((total, device) => {
      // 如果是机器类型的辅助设备，计算板卡费用
      if (device.supplier || device.machine_type) {
        // 查找该机器的板卡
        const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
        console.log(`报价结果-计算设备 ${device.name} 的费用，板卡数量: ${machineCards.length}`, machineCards);
        return total + machineCards.reduce((sum, card) => {
          let adjustedPrice = card.unit_price / 10000;
          
          // 根据报价币种和机器币种进行转换
          if (quoteCurrency === 'USD') {
            if (device.currency === 'CNY' || device.currency === 'RMB') {
              // RMB机器转USD：除以报价汇率
              adjustedPrice = adjustedPrice / quoteExchangeRate;
            }
            // USD机器：不做汇率转换，直接使用unit_price
          } else {
            // 报价币种是CNY，保持原逻辑
            adjustedPrice = adjustedPrice * device.exchange_rate;
          }
          
          const cardCost = adjustedPrice * device.discount_rate * (card.quantity || 1);
          console.log(`板卡 ${card.board_name} 费用: ${cardCost}`);
          return sum + cardCost;
        }, 0);
      } else {
        // 如果是原来的辅助设备类型，使用小时费率（默认RMB）
        let hourlyRate = device.hourly_rate || 0;
        if (quoteCurrency === 'USD') {
          hourlyRate = hourlyRate / quoteExchangeRate;
        }
        return total + hourlyRate;
      }
    }, 0);
  };

  // 计算单个辅助设备费用
  const calculateSingleAuxDeviceCost = (device) => {
    if (!quoteData || !quoteData.cardTypes) return 0;
    
    const quoteCurrency = quoteData.quoteCurrency || 'CNY';
    const quoteExchangeRate = quoteData.quoteExchangeRate || 7.2;
    
    // 如果是机器类型的辅助设备，计算板卡费用
    if (device.supplier || device.machine_type) {
      // 查找该机器的板卡
      const machineCards = quoteData.cardTypes.filter(card => card.machine_id === device.id);
      return machineCards.reduce((sum, card) => {
        let adjustedPrice = card.unit_price / 10000;
        
        // 根据报价币种和机器币种进行转换
        if (quoteCurrency === 'USD') {
          if (device.currency === 'CNY' || device.currency === 'RMB') {
            // RMB机器转USD：除以报价汇率
            adjustedPrice = adjustedPrice / quoteExchangeRate;
          }
          // USD机器：不做汇率转换，直接使用unit_price
        } else {
          // 报价币种是CNY，保持原逻辑
          adjustedPrice = adjustedPrice * device.exchange_rate;
        }
        
        return sum + (adjustedPrice * device.discount_rate * (card.quantity || 1));
      }, 0);
    } else {
      // 如果是原来的辅助设备类型，使用小时费率（默认RMB）
      let hourlyRate = device.hourly_rate || 0;
      if (quoteCurrency === 'USD') {
        hourlyRate = hourlyRate / quoteExchangeRate;
      }
      return hourlyRate;
    }
  };


  return (
    <div>
      <Card title={quoteData ? `${quoteData.type}结果` : '报价结果'}>
        <div className="quote-result-content">
          <h3>费用明细</h3>
          {/* 显示各项费用 */}
          {quoteData && quoteData.type === '工程报价' && (
            <>
              {/* 设备费用 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>测试机机时费（含工程系数）:</span>
                <span>{formatPrice(calculateTestMachineCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>分选机机时费（含工程系数）:</span>
                <span>{formatPrice(calculateHandlerCost())}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <span>探针台机时费（含工程系数）:</span>
                <span>{formatPrice(calculateProberCost())}</span>
              </div>
              
              {/* 辅助设备费用 */}
              {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span>辅助设备:</span>
                    <span></span>
                  </div>
                  <div style={{ paddingLeft: 20 }}>
                    {quoteData.selectedAuxDevices.map((device, index) => {
                      // 获取设备类型名称
                      let typeName = '';
                      if (device.supplier?.machine_type?.name) {
                        typeName = device.supplier.machine_type.name;
                      } else if (device.machine_type?.name) {
                        typeName = device.machine_type.name;
                      } else if (device.type === 'handler') {
                        typeName = '分选机';
                      } else if (device.type === 'prober') {
                        typeName = '探针台';
                      } else if (device.type) {
                        typeName = device.type;
                      }
                      
                      return (
                        <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span>
                            {device.name}
                            {typeName && ` (${typeName})`}
                          </span>
                          <span>{formatPrice(calculateSingleAuxDeviceCost(device))}</span>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
              
              {/* 人员费用 */}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('工程师') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>工程师小时费:</span>
                  <span>{formatPrice(calculateEngineerCost())}</span>
                </div>
              )}
              {quoteData.selectedPersonnel && quoteData.selectedPersonnel.includes('技术员') && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>技术员小时费:</span>
                  <span>{formatPrice(calculateTechnicianCost())}</span>
                </div>
              )}
            </>
          )}
          
          {/* 询价报价显示 */}
          {quoteData && quoteData.type === '询价报价' && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>项目名称: {quoteData.projectInfo?.projectName || '-'}</div>
                  <div>芯片封装: {quoteData.projectInfo?.chipPackage || '-'}</div>
                  <div>测试类型: {quoteData.projectInfo?.testType || '-'}</div>
                  <div>紧急程度: {quoteData.projectInfo?.urgency || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>设备配置及费用</h4>
                {quoteData.machines && quoteData.machines.map((machine, index) => (
                  <div key={index} style={{ marginBottom: 15, paddingLeft: 15, border: '1px solid #f0f0f0', borderRadius: '4px', padding: '10px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 5 }}>
                      机器 {index + 1}: {machine.model || '未选择'}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>机时费率（含询价系数 {quoteData.inquiryFactor || 1.5}）:</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        {formatPrice(machine.hourlyRate || 0)}/小时
                      </span>
                    </div>
                    {machine.selectedCards && machine.selectedCards.length > 0 && (
                      <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                        选用板卡: {machine.selectedCards.map(card => card.board_name).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              <div style={{ marginBottom: 20, fontSize: '18px', fontWeight: 'bold', textAlign: 'right', color: '#1890ff' }}>
                总机时费率: {formatPrice(quoteData.totalHourlyRate || 0)}/小时
              </div>
              
              {quoteData.remarks && (
                <div style={{ marginBottom: 20 }}>
                  <h4>备注说明</h4>
                  <div style={{ paddingLeft: 15, color: '#666' }}>
                    {quoteData.remarks}
                  </div>
                </div>
              )}
            </>
          )}
          
          {/* 工装夹具报价显示 */}
          {quoteData && quoteData.type === '工装夹具报价' && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>项目名称: {quoteData.projectInfo?.projectName || '-'}</div>
                  <div>芯片封装: {quoteData.projectInfo?.chipPackage || '-'}</div>
                  <div>测试类型: {quoteData.projectInfo?.testType || '-'}</div>
                  <div>产品性质: {quoteData.projectInfo?.productStyle === 'new' ? '新产品' : '改良产品'}</div>
                </div>
              </div>
              
              {quoteData.toolingItems && quoteData.toolingItems.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4>工装夹具明细</h4>
                  {quoteData.toolingItems.map((item, index) => (
                    <div key={index} style={{ 
                      marginBottom: 10, 
                      paddingLeft: 15, 
                      border: '1px solid #f0f0f0', 
                      borderRadius: '4px', 
                      padding: '10px' 
                    }}>
                      <div style={{ fontWeight: 'bold', marginBottom: 5 }}>
                        {item.category} - {item.type}
                      </div>
                      <div>规格说明: {item.specification || '-'}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
                        <span>数量: {item.quantity}</span>
                        <span>单价: {formatPrice(item.unitPrice || 0)}</span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                          小计: {formatPrice(item.totalPrice || 0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <div style={{ marginBottom: 20 }}>
                <h4>工程费用</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>测试程序开发:</span>
                    <span>{formatPrice(quoteData.engineeringFees?.testProgramDevelopment || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>夹具设计:</span>
                    <span>{formatPrice(quoteData.engineeringFees?.fixtureDesign || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>测试验证:</span>
                    <span>{formatPrice(quoteData.engineeringFees?.testValidation || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>文档编制:</span>
                    <span>{formatPrice(quoteData.engineeringFees?.documentation || 0)}</span>
                  </div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>产线设置费用</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>设置费:</span>
                    <span>{formatPrice(quoteData.productionSetup?.setupFee || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>校准费:</span>
                    <span>{formatPrice(quoteData.productionSetup?.calibrationFee || 0)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>首件检验:</span>
                    <span>{formatPrice(quoteData.productionSetup?.firstArticleInspection || 0)}</span>
                  </div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20, fontSize: '18px', fontWeight: 'bold', textAlign: 'right', color: '#1890ff' }}>
                报价总额: {formatPrice(quoteData.totalCost || 0)}
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>商务条款</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>付款条件: {quoteData.paymentTerms === '30_days' ? '30天付款' : 
                    quoteData.paymentTerms === '60_days' ? '60天付款' : 
                    quoteData.paymentTerms === 'advance' ? '预付款' : 
                    quoteData.paymentTerms || '-'}</div>
                  <div>交期要求: {quoteData.deliveryTime || '-'}</div>
                  {quoteData.remarks && <div>备注: {quoteData.remarks}</div>}
                </div>
              </div>
            </>
          )}
          
          {/* 工序报价显示 */}
          {quoteData && quoteData.type === '工序报价' && (
            <>
              <div style={{ marginBottom: 20 }}>
                <h4>客户信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>公司名称: {quoteData.customerInfo?.companyName || '-'}</div>
                  <div>联系人: {quoteData.customerInfo?.contactPerson || '-'}</div>
                  <div>联系电话: {quoteData.customerInfo?.phone || '-'}</div>
                  <div>邮箱: {quoteData.customerInfo?.email || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>项目信息</h4>
                <div style={{ paddingLeft: 15 }}>
                  <div>项目名称: {quoteData.projectInfo?.projectName || '-'}</div>
                  <div>芯片封装: {quoteData.projectInfo?.chipPackage || '-'}</div>
                  <div>测试类型: {quoteData.projectInfo?.testType || '-'}</div>
                  <div>年产量: {quoteData.projectInfo?.volume ? `${quoteData.projectInfo.volume.toLocaleString()} 颗` : '-'}</div>
                  <div>交期计划: {quoteData.projectInfo?.deliverySchedule || '-'}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>工序配置及成本</h4>
                
                {/* CP工序显示 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('cp') && quoteData.cpProcesses && (
                  <div style={{ marginBottom: 20 }}>
                    <h5 style={{ color: '#52c41a', marginBottom: 10 }}>CP工序</h5>
                    {quoteData.cpProcesses.map((process, index) => (
                      <div key={index} style={{ 
                        marginBottom: 15, 
                        paddingLeft: 15, 
                        border: '1px solid #f0f0f0', 
                        borderRadius: '4px', 
                        padding: '15px',
                        backgroundColor: '#f6ffed'
                      }}>
                        <div style={{ fontWeight: 'bold', marginBottom: 10, color: '#52c41a' }}>
                          {process.name}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
                          <div>设备型号: {process.machine || '-'}</div>
                          <div>单位产能: {process.uph || 0} UPH</div>
                          <div style={{ gridColumn: '1 / -1', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #e8e8e8' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                              <span>单颗成本:</span>
                              <span style={{ color: '#52c41a' }}>{formatPrice(process.unitCost || 0)}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    <div style={{ textAlign: 'right', marginTop: 10, fontSize: '16px', fontWeight: 'bold', color: '#52c41a' }}>
                      CP工序小计: {formatPrice(quoteData.cpProcesses.reduce((sum, p) => sum + (p.unitCost || 0), 0))}
                    </div>
                  </div>
                )}
                
                {/* FT工序显示 */}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('ft') && quoteData.ftProcesses && (
                  <div style={{ marginBottom: 20 }}>
                    <h5 style={{ color: '#1890ff', marginBottom: 10 }}>FT工序</h5>
                    {quoteData.ftProcesses.map((process, index) => (
                      <div key={index} style={{ 
                        marginBottom: 15, 
                        paddingLeft: 15, 
                        border: '1px solid #f0f0f0', 
                        borderRadius: '4px', 
                        padding: '15px',
                        backgroundColor: '#e6f7ff'
                      }}>
                        <div style={{ fontWeight: 'bold', marginBottom: 10, color: '#1890ff' }}>
                          {process.name}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
                          <div>设备型号: {process.machine || '-'}</div>
                          <div>单位产能: {process.uph || 0} UPH</div>
                          <div style={{ gridColumn: '1 / -1', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #e8e8e8' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                              <span>单颗成本:</span>
                              <span style={{ color: '#1890ff' }}>{formatPrice(process.unitCost || 0)}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    <div style={{ textAlign: 'right', marginTop: 10, fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                      FT工序小计: {formatPrice(quoteData.ftProcesses.reduce((sum, p) => sum + (p.unitCost || 0), 0))}
                    </div>
                  </div>
                )}
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <h4>成本汇总</h4>
                <div style={{ paddingLeft: 15, border: '1px solid #e8e8e8', borderRadius: '6px', padding: '15px', backgroundColor: '#f6ffed' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10, fontSize: '16px' }}>
                    <span>单颗总成本:</span>
                    <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                      {formatPrice(quoteData.totalUnitCost || 0)}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: 'bold', color: '#52c41a', paddingTop: '10px', borderTop: '1px solid #d9f7be' }}>
                    <span>项目总成本:</span>
                    <span>{formatPrice(quoteData.totalProjectCost || 0)}</span>
                  </div>
                </div>
              </div>
              
              {quoteData.remarks && (
                <div style={{ marginBottom: 20 }}>
                  <h4>备注说明</h4>
                  <div style={{ paddingLeft: 15, color: '#666', fontStyle: 'italic' }}>
                    {quoteData.remarks}
                  </div>
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
                    <span>{formatPrice(quoteData.ftHourlyFee || 0)}</span>
                  </div>
                )}
                {quoteData.selectedTypes && quoteData.selectedTypes.includes('cp') && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                    <span>CP小时费:</span>
                    <span>{formatPrice(quoteData.cpHourlyFee || 0)}</span>
                  </div>
                )}
                {quoteData.selectedAuxDevices && quoteData.selectedAuxDevices.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                      <span>辅助设备:</span>
                      <span></span>
                    </div>
                    {quoteData.selectedAuxDevices.map((device, index) => {
                      // 获取设备类型名称
                      let typeName = '';
                      if (device.supplier?.machine_type?.name) {
                        typeName = device.supplier.machine_type.name;
                      } else if (device.machine_type?.name) {
                        typeName = device.machine_type.name;
                      } else if (device.type === 'handler') {
                        typeName = '分选机';
                      } else if (device.type === 'prober') {
                        typeName = '探针台';
                      } else if (device.type) {
                        typeName = device.type;
                      }
                      
                      return (
                        <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingLeft: 20 }}>
                          <span>
                            {device.name}
                            {typeName && ` (${typeName})`}
                          </span>
                          <span>{formatPrice(calculateSingleAuxDeviceCost(device))}/小时</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
        <Divider />
        <div className="quote-result-actions">
          <Button onClick={() => {
            if (quoteData && quoteData.type === '询价报价') {
              // 询价报价：直接返回到询价页面
              navigate('/inquiry-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工装夹具报价') {
              navigate('/tooling-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工序报价') {
              navigate('/process-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '综合报价') {
              navigate('/comprehensive-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工程报价') {
              // 工程报价：真正的上一步，回到步骤1并保留所有数据
              const previousStepData = {
                currentStep: 1, // 返回到步骤1（人员和辅助设备选择）
                testMachine: quoteData.testMachine,
                handler: quoteData.handler,
                prober: quoteData.prober,
                testMachineCards: quoteData.testMachineCards || [],
                handlerCards: quoteData.handlerCards || [],
                proberCards: quoteData.proberCards || [],
                selectedPersonnel: quoteData.selectedPersonnel || [],
                selectedAuxDevices: quoteData.selectedAuxDevices || [],
                engineeringRate: quoteData.engineeringRate || 1.2,
                quoteCurrency: quoteData.quoteCurrency || 'CNY',
                quoteExchangeRate: quoteData.quoteExchangeRate || 7.2,
                persistedCardQuantities: quoteData.persistedCardQuantities || {},
                fromResultPage: true
              };
              sessionStorage.setItem('quoteData', JSON.stringify(previousStepData));
              navigate('/engineering-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else {
              // 量产报价：真正的上一步，回到步骤1并保留所有数据
              const previousStepData = {
                currentStep: 1, // 返回到步骤1（辅助设备选择）
                selectedTypes: quoteData.selectedTypes || ['ft', 'cp'],
                ftData: quoteData.ftData || { 
                  testMachine: null, 
                  handler: null, 
                  testMachineCards: [], 
                  handlerCards: [] 
                },
                cpData: quoteData.cpData || { 
                  testMachine: null, 
                  prober: null, 
                  testMachineCards: [], 
                  proberCards: [] 
                },
                selectedAuxDevices: quoteData.selectedAuxDevices || [],
                persistedCardQuantities: quoteData.persistedCardQuantities || {},
                quoteCurrency: quoteData.quoteCurrency || 'CNY',
                quoteExchangeRate: quoteData.quoteExchangeRate || 7.2,
                fromResultPage: true
              };
              sessionStorage.setItem('massProductionQuoteState', JSON.stringify(previousStepData));
              navigate('/mass-production-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            }
          }}>
            上一步
          </Button>
          <Button type="primary" onClick={() => {
            if (quoteData && quoteData.type === '工程报价') {
              navigate('/engineering-quote');
            } else if (quoteData && quoteData.type === '询价报价') {
              navigate('/inquiry-quote');
            } else if (quoteData && quoteData.type === '工装夹具报价') {
              navigate('/tooling-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '工序报价') {
              navigate('/process-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else if (quoteData && quoteData.type === '综合报价') {
              navigate('/comprehensive-quote', { 
                state: { 
                  fromResultPage: true
                } 
              });
            } else {
              navigate('/mass-production-quote');
            }
          }}>
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