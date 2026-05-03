import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { message } from 'antd';
import ProcessQuote from './ProcessQuote';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { QuoteApiService } from '../services/quoteApi';

jest.setTimeout(15000);

const mockNavigate = jest.fn();
const mockEditContext = {
  isEditMode: false,
  editingQuote: null,
  convertQuoteToFormData: jest.fn()
};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: null, search: '' })
}));

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } })
}));

jest.mock('../hooks/useQuoteEditMode', () => () => ({
  isEditMode: mockEditContext.isEditMode,
  editingQuote: mockEditContext.editingQuote,
  loading: false,
  convertQuoteToFormData: mockEditContext.convertQuoteToFormData
}));

jest.mock('../services/machines', () => ({
  getMachines: jest.fn()
}));

jest.mock('../services/cardTypes', () => ({
  getCardTypes: jest.fn()
}));

jest.mock('../services/quoteApi', () => ({
  QuoteApiService: {
    updateQuote: jest.fn()
  },
  default: {
    createQuote: jest.fn(),
    updateQuote: jest.fn()
  }
}));

describe('ProcessQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockEditContext.isEditMode = false;
    mockEditContext.editingQuote = null;
    mockEditContext.convertQuoteToFormData.mockReset();
    jest.spyOn(message, 'error').mockImplementation(jest.fn());
    getMachines.mockResolvedValue([
      {
        id: 1,
        name: 'J750',
        currency: 'CNY',
        exchange_rate: 1,
        discount_rate: 1,
        supplier: { machine_type: { name: '测试机' } }
      },
      {
        id: 2,
        name: 'AP3000',
        currency: 'CNY',
        exchange_rate: 1,
        discount_rate: 1,
        supplier: { machine_type: { name: '探针台' } }
      },
      {
        id: 3,
        name: 'HND-01',
        currency: 'CNY',
        exchange_rate: 1,
        discount_rate: 1,
        supplier: { machine_type: { name: '分选机' } }
      }
    ]);
    getCardTypes.mockResolvedValue([
      { id: 11, machine_id: 1, part_number: 'PN-1', board_name: 'Board A', unit_price: 10000 },
      { id: 22, machine_id: 2, part_number: 'PN-2', board_name: 'Board B', unit_price: 20000 },
      { id: 33, machine_id: 3, part_number: 'PN-3', board_name: 'Board C', unit_price: 30000 }
    ]);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('prevents creating a CP test process quote when both devices are selected but no cards are selected', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    const selects = Array.from(container.querySelectorAll('select'));
    const testMachineSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'J750'));
    const proberSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'AP3000'));

    expect(testMachineSelect).toBeTruthy();
    expect(proberSelect).toBeTruthy();

    fireEvent.change(testMachineSelect, { target: { value: 'J750' } });
    fireEvent.change(proberSelect, { target: { value: 'AP3000' } });
    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('必须同时完成测试机和探针台的板卡选择'));
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('prevents creating a CP test process quote when the prober is missing', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    const selects = Array.from(container.querySelectorAll('select'));
    const testMachineSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'J750'));

    fireEvent.change(testMachineSelect, { target: { value: 'J750' } });
    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('必须同时完成测试机和探针台的板卡选择'));
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('prevents creating a CP test process quote when only the test-machine cards are selected', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    const selects = Array.from(container.querySelectorAll('select'));
    const testMachineSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'J750'));
    const proberSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'AP3000'));

    fireEvent.change(testMachineSelect, { target: { value: 'J750' } });
    fireEvent.change(proberSelect, { target: { value: 'AP3000' } });

    const expander = container.querySelector('.ant-table-row-expand-icon');
    expect(expander).toBeTruthy();
    fireEvent.click(expander);

    await waitFor(() => expect(container.textContent).toContain('测试机 板卡配置'));

    const expandedCheckboxes = Array.from(container.querySelectorAll('.ant-table-expanded-row input.ant-checkbox-input'));
    expect(expandedCheckboxes.length).toBeGreaterThan(0);
    fireEvent.click(expandedCheckboxes[1]);

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('必须同时完成测试机和探针台的板卡选择'));
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('prevents creating an FT test process quote when the handler is missing', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    fireEvent.click(screen.getByLabelText('FT工序报价'));

    const selects = Array.from(container.querySelectorAll('select'));
    const ftProcessSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'FT1测试'));
    const testMachineSelects = selects.filter((select) => Array.from(select.options).some((option) => option.value === 'J750'));

    fireEvent.change(ftProcessSelect, { target: { value: 'FT1测试' } });
    fireEvent.change(testMachineSelects[testMachineSelects.length - 1], { target: { value: 'J750' } });
    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('必须同时完成测试机和分选机的板卡选择'));
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('prevents creating an FT test process quote when the handler cards are missing', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    fireEvent.click(screen.getByLabelText('FT工序报价'));

    const selects = Array.from(container.querySelectorAll('select'));
    const ftProcessSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'FT1测试'));
    const deviceSelects = selects.filter((select) => Array.from(select.options).some((option) => option.value === 'J750' || option.value === 'HND-01'));

    fireEvent.change(ftProcessSelect, { target: { value: 'FT1测试' } });
    fireEvent.change(deviceSelects[deviceSelects.length - 2], { target: { value: 'J750' } });
    fireEvent.change(deviceSelects[deviceSelects.length - 1], { target: { value: 'HND-01' } });

    const expanders = Array.from(container.querySelectorAll('.ant-table-row-expand-icon'));
    fireEvent.click(expanders[expanders.length - 1]);

    await waitFor(() => expect(container.textContent).toContain('分选机 板卡配置'));

    const expandedCheckboxes = Array.from(container.querySelectorAll('.ant-table-expanded-row input.ant-checkbox-input'));
    expect(expandedCheckboxes.length).toBeGreaterThan(0);
    fireEvent.click(expandedCheckboxes[1]);

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith(expect.stringContaining('必须同时完成测试机和分选机的板卡选择'));
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('navigates to quote-result for a valid CP process quote', async () => {
    const { container } = render(<ProcessQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    const selects = Array.from(container.querySelectorAll('select'));
    const testMachineSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'J750'));
    const proberSelect = selects.find((select) => Array.from(select.options).some((option) => option.value === 'AP3000'));

    fireEvent.change(testMachineSelect, { target: { value: 'J750' } });
    fireEvent.change(proberSelect, { target: { value: 'AP3000' } });

    const expander = container.querySelector('.ant-table-row-expand-icon');
    fireEvent.click(expander);

    await waitFor(() => expect(container.textContent).toContain('测试机 板卡配置'));

    const expandedCheckboxes = Array.from(container.querySelectorAll('.ant-table-expanded-row input.ant-checkbox-input'));
    fireEvent.click(expandedCheckboxes[1]);
    fireEvent.click(expandedCheckboxes[3]);

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        type: '工序报价',
        quoteCreateData: expect.objectContaining({ quote_type: '工序报价' })
      })
    })));
  });

  it('updates an existing process quote in edit mode', async () => {
    mockEditContext.isEditMode = true;
    mockEditContext.editingQuote = { id: 46, quote_number: 'PC-001' };
    mockEditContext.convertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: 'Process Edit Co', contactPerson: 'Paul', phone: '', email: '' },
      projectInfo: { projectName: 'Process Edit Project', chipPackage: 'QFN48', testType: 'process', quoteUnit: '昆山芯信安' },
      selectedTypes: ['cp'],
      cpProcesses: [{
        id: 1,
        name: 'CP1测试',
        testMachine: 'J750',
        testMachineData: { id: 1, name: 'J750', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { name: '测试机' } } },
        testMachineCardQuantities: { 11: 1 },
        prober: 'AP3000',
        proberData: { id: 2, name: 'AP3000', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { name: '探针台' } } },
        proberCardQuantities: { 22: 1 },
        uph: 1000,
        adjustedMachineRate: 0,
        quantityPerOven: 1000,
        bakingTime: 60,
        packageType: '',
        quantityPerReel: 3000,
        adjustedUnitPrice: 0,
        unitCost: 0
      }],
      ftProcesses: [{ id: 1, name: 'FT1测试', testMachine: '', testMachineData: null, testMachineCardQuantities: {}, handler: '', handlerData: null, handlerCardQuantities: {}, uph: 1000, unitCost: 0 }],
      pricing: { laborCostPerHour: 0, overheadRate: 0, profitMargin: 0 },
      currency: 'CNY',
      exchangeRate: 7.2,
      remarks: ''
    });

    render(<ProcessQuote />);

    await waitFor(() => expect(screen.getByDisplayValue('Process Edit Co')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: '保存修改' }));

    await waitFor(() => expect(QuoteApiService.updateQuote).toHaveBeenCalledWith(46, expect.objectContaining({
      quote_type: '工序报价',
      customer_name: 'Process Edit Co'
    })));
    expect(mockNavigate).toHaveBeenCalledWith('/quote-detail/PC-001', expect.anything());
  });
});
