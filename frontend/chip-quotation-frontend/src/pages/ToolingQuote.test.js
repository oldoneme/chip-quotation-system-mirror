import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ToolingQuote from './ToolingQuote';
import { QuoteApiService } from '../services/quoteApi';

const mockNavigate = jest.fn();
let mockLocationState = null;
const mockConvertQuoteToFormData = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: mockLocationState })
}));

jest.mock('../hooks/useQuoteEditMode', () => () => ({
  isEditMode: mockLocationState?.isEditing || false,
  editingQuote: mockLocationState?.editingQuote || null,
  loading: false,
  convertQuoteToFormData: mockConvertQuoteToFormData
}));

jest.mock('../services/quoteApi', () => ({
  QuoteApiService: {
    updateQuote: jest.fn()
  }
}));

describe('ToolingQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockConvertQuoteToFormData.mockReset();
    mockLocationState = null;
    window.sessionStorage.clear();
  });

  it('navigates to quote-result with tooling quoteCreateData on submit', async () => {
    render(<ToolingQuote />);

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Tooling Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Alice' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Tooling Project' } });
    fireEvent.change(screen.getByPlaceholderText('如：QFN48, BGA256等'), { target: { value: 'QFN48' } });

    const selects = screen.getAllByRole('combobox');
    fireEvent.change(selects[0], { target: { value: 'CP' } });
    fireEvent.change(selects[3], { target: { value: 'fixture' } });
    fireEvent.change(selects[4], { target: { value: 'loadboard' } });

    fireEvent.change(screen.getByDisplayValue('1'), { target: { value: '2' } });

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalled());

    expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        type: '工装夹具报价',
        totalCost: 16000,
        quoteCreateData: expect.objectContaining({
          quote_type: 'tooling',
          customer_name: 'Tooling Co',
          total_amount: 16000
        })
      })
    }));
  });

  it('updates a tooling quote directly in edit mode', async () => {
    mockLocationState = {
      isEditing: true,
      editingQuote: { id: 43, quote_number: 'TL-001' }
    };
    mockConvertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: 'Tooling Edit Co', contactPerson: 'Tom', phone: '', email: '' },
      projectInfo: { projectName: 'Tooling Edit Project', chipPackage: 'QFN48', testType: 'CP', productStyle: 'new', quoteUnit: '昆山芯信安' },
      toolingItems: [{ id: 1, category: 'fixture', type: 'loadboard', specification: '', quantity: 1, unitPrice: 8000, totalPrice: 8000 }],
      engineeringFees: { testProgramDevelopment: 0, fixtureDesign: 0, testValidation: 0, documentation: 0 },
      productionSetup: { setupFee: 0, calibrationFee: 0, firstArticleInspection: 0 },
      currency: 'CNY',
      paymentTerms: '30_days',
      deliveryTime: '',
      remarks: ''
    });

    render(<ToolingQuote />);

    await waitFor(() => expect(screen.getByDisplayValue('Tooling Edit Co')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: '更新报价单' }));

    await waitFor(() => expect(QuoteApiService.updateQuote).toHaveBeenCalledWith(43, expect.objectContaining({
      quote_type: 'tooling',
      customer_name: 'Tooling Edit Co'
    })));
    expect(mockNavigate).toHaveBeenCalledWith('/quote-detail/TL-001', expect.anything());
  });
});
