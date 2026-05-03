import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import MassProductionQuote from './MassProductionQuote';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
import { getAuxiliaryEquipment } from '../services/auxiliaryEquipment';
import { QuoteApiService } from '../services/quoteApi';

const mockNavigate = jest.fn();
let mockLocationState = null;
const mockConvertQuoteToFormData = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: mockLocationState })
}));

jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } })
}));

jest.mock('../hooks/useQuoteEditMode', () => () => ({
  isEditMode: mockLocationState?.isEditing || false,
  editingQuote: mockLocationState?.editingQuote || null,
  loading: false,
  convertQuoteToFormData: mockConvertQuoteToFormData
}));

jest.mock('../services/machines', () => ({
  getMachines: jest.fn()
}));

jest.mock('../services/cardTypes', () => ({
  getCardTypes: jest.fn()
}));

jest.mock('../services/auxiliaryEquipment', () => ({
  getAuxiliaryEquipment: jest.fn()
}));

jest.mock('../services/quoteApi', () => ({
  QuoteApiService: {
    updateQuote: jest.fn()
  }
}));

describe('MassProductionQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockConvertQuoteToFormData.mockReset();
    mockLocationState = { fromResultPage: true };
    getMachines.mockResolvedValue([]);
    getCardTypes.mockResolvedValue([]);
    getAuxiliaryEquipment.mockResolvedValue([]);
    global.fetch = jest.fn().mockResolvedValue({ json: async () => [] });
    window.sessionStorage.clear();
    window.sessionStorage.setItem('massProductionQuoteState', JSON.stringify({
      selectedTypes: ['ft'],
      ftData: {
        testMachine: { id: 1, name: 'J750' },
        handler: { id: 2, name: 'HND-01' },
        testMachineCards: [{ id: 11, quantity: 2 }],
        handlerCards: [{ id: 22, quantity: 1 }],
        proberCards: []
      },
      cpData: {
        testMachine: null,
        prober: null,
        testMachineCards: [],
        handlerCards: [],
        proberCards: []
      },
      selectedAuxDevices: [],
      persistedCardQuantities: { 'ft-testMachine-11': 2, 'ft-handler-22': 1 },
      quoteCurrency: 'USD',
      quoteExchangeRate: 7.3,
      customerInfo: { companyName: 'Mass Co', contactPerson: 'Mia', phone: '', email: '' },
      projectInfo: { projectName: 'Mass Project', chipPackage: 'BGA256', testType: 'mass_production', urgency: 'urgent', quoteUnit: '昆山芯信安' }
    }));
  });

  it('restores saved mass production state when returning from result page', async () => {
    render(<MassProductionQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());

    expect(await screen.findByDisplayValue('Mass Co')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Mia')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Mass Project')).toBeInTheDocument();
    expect(screen.getByDisplayValue('BGA256')).toBeInTheDocument();
    expect(screen.getByText('美元 ($)')).toBeInTheDocument();
    expect(screen.getByDisplayValue('7.3')).toBeInTheDocument();
  });

  it('navigates to quote-result in create mode', async () => {
    mockLocationState = null;
    getMachines.mockResolvedValue([]);
    getCardTypes.mockResolvedValue([]);

    render(<MassProductionQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText('正在加载量产报价数据...')).not.toBeInTheDocument());

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Mass Create Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Mona' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Mass Create Project' } });
    fireEvent.change(screen.getByPlaceholderText('如：QFN48, BGA256等'), { target: { value: 'QFN48' } });

    fireEvent.click(screen.getByRole('button', { name: /完成报价/ }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        type: '量产报价',
        quoteCreateData: expect.objectContaining({ quote_type: 'mass_production' })
      })
    })));
  });

  it('updates a mass production quote directly in edit mode', async () => {
    mockLocationState = {
      isEditing: true,
      editingQuote: { id: 44, quote_number: 'MP-001' }
    };
    getMachines.mockResolvedValue([
      { id: 1, name: 'J750', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { id: 10, name: '测试机' } } },
      { id: 2, name: 'HND-01', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { id: 11, name: '分选机' } } }
    ]);
    getCardTypes.mockResolvedValue([{ id: 11, machine_id: 1, board_name: 'Board A', part_number: 'PN-1', unit_price: 10000 }]);
    mockConvertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: 'Mass Edit Co', contactPerson: 'Max', phone: '', email: '' },
      projectInfo: { projectName: 'Mass Edit Project', chipPackage: 'BGA256', testType: 'mass_production', urgency: 'normal', quoteUnit: '昆山芯信安' },
      quoteCurrency: 'CNY',
      quoteExchangeRate: 7.2,
      deviceConfig: {
        selectedTypes: ['ft'],
        ftData: {
          testMachine: { id: 1, name: 'J750', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { id: 10, name: '测试机' } } },
          handler: { id: 2, name: 'HND-01', currency: 'CNY', exchange_rate: 1, discount_rate: 1, supplier: { machine_type: { id: 11, name: '分选机' } } },
          testMachineCards: [{ id: 11, quantity: 1, unit_price: 10000 }],
          handlerCards: [],
          proberCards: []
        },
        cpData: { testMachine: null, prober: null, testMachineCards: [], handlerCards: [], proberCards: [] },
        auxDevices: []
      }
    });

    render(<MassProductionQuote />);

    await waitFor(() => expect(screen.getByDisplayValue('Mass Edit Co')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: '保存编辑' }));

    await waitFor(() => expect(QuoteApiService.updateQuote).toHaveBeenCalledWith(44, expect.objectContaining({
      quote_type: 'mass_production',
      customer_name: 'Mass Edit Co'
    })));
    expect(mockNavigate).toHaveBeenCalledWith('/quote-detail/MP-001', expect.anything());
  });
});
