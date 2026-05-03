import React from 'react';
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import EngineeringQuote from './EngineeringQuote';
import { getMachines } from '../services/machines';
import { getConfigurations } from '../services/configurations';
import { getCardTypes } from '../services/cardTypes';
import { getAuxiliaryEquipment } from '../services/auxiliaryEquipment';

jest.setTimeout(15000);

const mockNavigate = jest.fn();
const mockEditState = {
  isEditMode: true,
  editingQuote: { id: 1, quote_number: 'ENG-001' }
};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: null, search: '' })
}));

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } })
}));

const mockConvertQuoteToFormData = jest.fn();

jest.mock('../hooks/useQuoteEditMode', () => () => ({
  isEditMode: mockEditState.isEditMode,
  editingQuote: mockEditState.editingQuote,
  loading: false,
  convertQuoteToFormData: mockConvertQuoteToFormData
}));

jest.mock('../services/machines', () => ({
  getMachines: jest.fn()
}));

jest.mock('../services/configurations', () => ({
  getConfigurations: jest.fn()
}));

jest.mock('../services/cardTypes', () => ({
  getCardTypes: jest.fn()
}));

jest.mock('../services/auxiliaryEquipment', () => ({
  getAuxiliaryEquipment: jest.fn()
}));

describe('EngineeringQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockEditState.isEditMode = true;
    mockEditState.editingQuote = { id: 1, quote_number: 'ENG-001' };
    mockConvertQuoteToFormData.mockReset();
    getMachines.mockResolvedValue([
      {
        id: 1,
        name: 'J750',
        currency: 'CNY',
        exchange_rate: 1,
        discount_rate: 1,
        supplier: { machine_type: { id: 10, name: '测试机' } }
      }
    ]);
    getConfigurations.mockResolvedValue([
      { id: 999, name: 'Wrong config payload', machine_id: 1 }
    ]);
    getCardTypes.mockResolvedValue([
      { id: 11, machine_id: 1, part_number: 'PN-1', board_name: 'Board A', unit_price: 10000 }
    ]);
    mockConvertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: '', contactPerson: '', phone: '', email: '' },
      projectInfo: { projectName: '', chipPackage: '', testType: 'engineering', urgency: 'normal', quoteUnit: '昆山芯信安' },
      deviceConfig: {
        testMachine: {
          id: 1,
          name: 'J750',
          currency: 'CNY',
          exchange_rate: 1,
          discount_rate: 1,
          supplier: { machine_type: { id: 10, name: '测试机' } }
        },
        testMachineCards: [
          { id: 11, machine_id: 1, part_number: 'PN-1', board_name: 'Board A', unit_price: 10000, quantity: 1 }
        ]
      }
    });
    getAuxiliaryEquipment.mockResolvedValue([]);
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => [{ id: 10, name: '测试机' }]
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders card-config rows and restores selected board state', async () => {
    render(<EngineeringQuote />);

    await waitFor(() => expect(getCardTypes).toHaveBeenCalled());

    expect(await screen.findByText('PN-1')).toBeInTheDocument();
    expect(screen.getByText('Board A')).toBeInTheDocument();

    const table = screen.getByText('PN-1').closest('table');
    const checkboxes = within(table).getAllByRole('checkbox');
    const rowCheckbox = checkboxes[1];

    await waitFor(() => expect(rowCheckbox).toBeChecked());
    expect(screen.getByDisplayValue('1')).toBeInTheDocument();
  });

  it('creates an engineering quote preview in create mode', async () => {
    mockEditState.isEditMode = false;
    mockEditState.editingQuote = null;
    mockConvertQuoteToFormData.mockReturnValue(null);

    render(<EngineeringQuote />);

    await waitFor(() => expect(getCardTypes).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('加载中...')).not.toBeInTheDocument());

    fireEvent.change(await screen.findByPlaceholderText('请输入公司名称'), { target: { value: 'Engineering Create Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Ella' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Engineering Create Project' } });
    fireEvent.change(screen.getByPlaceholderText('如：QFN48, BGA256等'), { target: { value: 'QFN48' } });

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result'));
    expect(window.sessionStorage.getItem('quoteData')).toContain('Engineering Create Co');
  });
});
