import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import InquiryQuote from './InquiryQuote';
import { getMachines } from '../services/machines';
import { getCardTypes } from '../services/cardTypes';
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

jest.mock('../services/quoteApi', () => ({
  QuoteApiService: {
    updateQuote: jest.fn()
  }
}));

describe('InquiryQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockConvertQuoteToFormData.mockReset();
    mockLocationState = { fromResultPage: true };
    getMachines.mockResolvedValue([]);
    getCardTypes.mockResolvedValue([]);
    global.fetch = jest.fn().mockResolvedValue({ json: async () => [] });
    window.sessionStorage.clear();
    window.sessionStorage.setItem('inquiryQuoteState', JSON.stringify({
      formData: {
        customerInfo: { companyName: 'Restore Co', contactPerson: 'Restore User', phone: '', email: '' },
        projectInfo: { projectName: 'Restore Project', chipPackage: 'QFN48', testType: 'mixed', urgency: 'normal', quoteUnit: '昆山芯信安' },
        machines: [{ id: 1, category: '', model: '', machineData: null, selectedCards: [], hourlyRate: 0 }],
        currency: 'CNY',
        exchangeRate: 7.2,
        inquiryFactor: 1.5,
        remarks: ''
      },
      persistedCardQuantities: { '1-11': 2 }
    }));
  });

  it('restores saved inquiry form state when returning from result page', async () => {
    render(<InquiryQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());

    expect(await screen.findByDisplayValue('Restore Co')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Restore User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Restore Project')).toBeInTheDocument();
    expect(screen.getByDisplayValue('QFN48')).toBeInTheDocument();
  });

  it('navigates to quote-result in create mode', async () => {
    mockLocationState = null;

    render(<InquiryQuote />);

    await waitFor(() => expect(getMachines).toHaveBeenCalled());

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Create Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Nina' } });
    fireEvent.change(screen.getByPlaceholderText('如：QFN48, BGA256等'), { target: { value: 'QFN48' } });

    fireEvent.click(screen.getByRole('button', { name: /完成报价/ }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        type: '询价报价',
        quoteCreateData: expect.objectContaining({
          quote_type: 'inquiry',
          customer_name: 'Create Co'
        })
      })
    })));
  });

  it('updates an inquiry quote directly in edit mode', async () => {
    mockLocationState = {
      isEditing: true,
      editingQuote: { id: 42, quote_number: 'INQ-001' }
    };
    mockConvertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: 'Edit Co', contactPerson: 'Eva', phone: '', email: '' },
      projectInfo: { projectName: 'Edit Project', chipPackage: 'QFN48', testType: 'mixed', urgency: 'normal', quoteUnit: '昆山芯信安' },
      machines: [{ id: 1, category: '', model: '', machineData: null, selectedCards: [], hourlyRate: 0 }],
      currency: 'CNY',
      exchangeRate: 7.2,
      inquiryFactor: 1.5,
      remarks: ''
    });

    render(<InquiryQuote />);

    await waitFor(() => expect(screen.getByDisplayValue('Edit Co')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /更新.*询价单/ }));

    await waitFor(() => expect(QuoteApiService.updateQuote).toHaveBeenCalledWith(42, expect.objectContaining({
      quote_type: 'inquiry',
      customer_name: 'Edit Co'
    })));
    expect(mockNavigate).toHaveBeenCalledWith('/quote-detail/INQ-001', expect.anything());
  });
});
