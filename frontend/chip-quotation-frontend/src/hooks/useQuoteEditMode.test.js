import React from 'react';
import { render, screen } from '@testing-library/react';
import useQuoteEditMode from './useQuoteEditMode';

jest.mock('react-router-dom', () => ({
  useLocation: () => ({ state: null, search: '' })
}));

jest.mock('../services/quoteApi', () => ({
  QuoteApiService: {
    getQuoteDetailById: jest.fn()
  }
}));

const HookHarness = ({ quote, quoteType, availableCardTypes = [], availableMachines = [] }) => {
  const { convertQuoteToFormData } = useQuoteEditMode();
  const result = convertQuoteToFormData(quote, quoteType, availableCardTypes, availableMachines);
  return <pre data-testid="result">{JSON.stringify(result)}</pre>;
};

describe('useQuoteEditMode convertQuoteToFormData', () => {
  it('converts inquiry quotes into form data', () => {
    render(
      <HookHarness
        quoteType="inquiry"
        quote={{
          customer_name: 'Inquiry Hook Co',
          customer_contact: 'Ivy',
          currency: 'USD',
          description: '项目：Hook Inquiry，芯片封装：QFN48，测试类型：混合测试',
          notes: '备注：hook remark',
          items: [{ machine_type: '测试机', machine_model: 'J750', unit_price: 8, item_description: '询价系数: 1.8' }]
        }}
      />
    );

    const result = JSON.parse(screen.getByTestId('result').textContent);
    expect(result.customerInfo.companyName).toBe('Inquiry Hook Co');
    expect(result.projectInfo.projectName).toBe('Hook Inquiry');
    expect(result.projectInfo.chipPackage).toBe('QFN48');
    expect(result.machines[0].model).toBe('J750');
    expect(result.inquiryFactor).toBe(1.8);
  });

  it('converts tooling quotes into form data', () => {
    render(
      <HookHarness
        quoteType="tooling"
        quote={{
          customer_name: 'Tooling Hook Co',
          customer_contact: 'Tom',
          currency: 'CNY',
          description: '项目：Hook Tooling，芯片封装：BGA256，测试类型：CP测试',
          notes: '交期：4周，备注：tooling remark',
          items: [
            { item_name: 'loadboard', item_description: 'fixture - spec', quantity: 1, unit_price: 8000, total_price: 8000 },
            { item_name: '测试程序开发', item_description: '工程开发服务费', unit_price: 5000 },
            { item_name: '设备调试费', item_description: '量产准备服务费', unit_price: 1000 }
          ]
        }}
      />
    );

    const result = JSON.parse(screen.getByTestId('result').textContent);
    expect(result.projectInfo.projectName).toBe('Hook Tooling');
    expect(result.toolingItems[0].category).toBe('fixture');
    expect(result.toolingItems[0].type).toBe('loadboard');
    expect(result.engineeringFees.testProgramDevelopment).toBe(5000);
    expect(result.productionSetup.setupFee).toBe(1000);
  });

  it('converts mass production quotes into form data', () => {
    render(
      <HookHarness
        quoteType="mass_production"
        availableCardTypes={[{ id: 11, board_name: 'Board A', part_number: 'PN-1', unit_price: 10000 }]}
        availableMachines={[{ id: 1, name: 'J750' }]}
        quote={{
          customer_name: 'Mass Hook Co',
          customer_contact: 'Mia',
          currency: 'USD',
          description: '项目：Hook Mass，芯片封装：QFN48，测试类型：FT',
          notes: '汇率：7.2，紧急程度：紧急',
          items: [
            { item_name: 'J750', machine_model: 'J750', configuration: JSON.stringify({ device_type: '测试机', device_model: 'J750', test_type: 'FT', cards: [{ id: 11, quantity: 1 }] }) }
          ]
        }}
      />
    );

    const result = JSON.parse(screen.getByTestId('result').textContent);
    expect(result.projectInfo.projectName).toBe('Hook Mass');
    expect(result.quoteCurrency).toBe('USD');
    expect(result.quoteExchangeRate).toBe(7.2);
    expect(result.deviceConfig.selectedTypes).toContain('ft');
  });

  it('converts process quotes into form data', () => {
    render(
      <HookHarness
        quoteType="process"
        availableCardTypes={[{ id: 11, board_name: 'Board A', part_number: 'PN-1', unit_price: 10000 }]}
        availableMachines={[{ id: 1, name: 'J750' }, { id: 2, name: 'AP3000' }]}
        quote={{
          customer_name: 'Process Hook Co',
          customer_contact: 'Paul',
          currency: 'CNY',
          exchange_rate: 7.2,
          description: '项目：Hook Process，芯片封装：QFN48，测试类型：工序报价',
          notes: '汇率：7.2，紧急程度：正常',
          items: [
            { item_name: 'CP工序 - CP1测试', configuration: JSON.stringify({ process_type: 'CP1测试', uph: 1000, test_machine: { id: 1, name: 'J750', cards: [{ id: 11, quantity: 1 }] }, prober: { id: 2, name: 'AP3000', cards: [] }, adjusted_machine_rate: 0, adjusted_unit_price: 0 }) }
          ]
        }}
      />
    );

    const result = JSON.parse(screen.getByTestId('result').textContent);
    expect(result.projectInfo.projectName).toBe('Hook Process');
    expect(result.selectedTypes).toContain('cp');
    expect(result.cpProcesses[0].name).toBe('CP1测试');
  });

  it('converts comprehensive quotes into form data basics', () => {
    render(
      <HookHarness
        quoteType="comprehensive"
        quote={{
          customer_name: 'Comprehensive Hook Co',
          customer_contact: 'Cora',
          currency: 'CNY',
          description: '项目：Hook Comprehensive，芯片封装：BGA256，客户等级：standard',
          notes: '备注：comp remark'
        }}
      />
    );

    const result = JSON.parse(screen.getByTestId('result').textContent);
    expect(result.customerInfo.companyName).toBe('Comprehensive Hook Co');
    expect(result.projectInfo.projectName).toBe('Hook Comprehensive');
    expect(result.projectInfo.chipPackage).toBe('BGA256');
    expect(result.remarks).toBe('comp remark');
  });
});
