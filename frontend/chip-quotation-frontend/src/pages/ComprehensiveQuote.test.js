import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ComprehensiveQuote from './ComprehensiveQuote';
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

describe('ComprehensiveQuote', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockConvertQuoteToFormData.mockReset();
    mockLocationState = null;
    window.sessionStorage.clear();
  });

  it('builds a comprehensive custom quote payload and navigates to quote-result', async () => {
    const { container } = render(<ComprehensiveQuote />);

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Comprehensive Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Cathy' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Comprehensive Project' } });

    fireEvent.click(screen.getByRole('radio', { name: /自定义报价/ }));

    fireEvent.change(screen.getByPlaceholderText('请输入详细描述'), { target: { value: 'Custom Service' } });
    const customCard = container.querySelector('.custom-item-card');
    const numberInputs = customCard.querySelectorAll('input[type="number"]');
    fireEvent.change(numberInputs[1], { target: { value: '100' } });

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalled());

    expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        type: '综合报价',
        quoteType: 'custom',
        quoteCreateData: expect.objectContaining({
          quote_type: 'comprehensive',
          customer_name: 'Comprehensive Co',
          total_amount: 100
        })
      })
    }));
  });

  it('updates a comprehensive quote directly in edit mode', async () => {
    mockLocationState = {
      isEditing: true,
      editingQuote: { id: 45, quote_number: 'CQ-001' }
    };
    mockConvertQuoteToFormData.mockReturnValue({
      customerInfo: { companyName: 'Comp Edit Co', contactPerson: 'Cora', phone: '', email: '', customerLevel: 'standard' },
      projectInfo: { projectName: 'Comp Edit Project', projectType: 'new', chipPackage: 'QFN48', complexity: 'medium', priority: 'normal', expectedVolume: 0, projectDuration: '' },
      quoteType: 'custom',
      baseDataSelection: { referenceProject: '', baseTemplate: '', historicalData: '' },
      packageQuote: { testServices: [], engineeringServices: [], supportServices: [], packageDiscount: 0 },
      volumeQuote: { volumeTiers: [
        { min: 0, max: 10000, unitPrice: 0, discount: 0 },
        { min: 10001, max: 50000, unitPrice: 0, discount: 0.05 },
        { min: 50001, max: 100000, unitPrice: 0, discount: 0.1 },
        { min: 100001, max: 999999999, unitPrice: 0, discount: 0.15 }
      ] },
      timeQuote: { contractDuration: 12, monthlyCommitment: 0, timeDiscount: 0, escalationRate: 0.03 },
      customQuote: { customItems: [{ id: 1, category: 'testing', description: 'Updated Custom', quantity: 1, unitPrice: 100, discount: 0, totalPrice: 100 }] },
      priceAdjustments: { urgencyMultiplier: 1, complexityMultiplier: 1, customerDiscount: 0, seasonalAdjustment: 0 },
      agreementTerms: { validityPeriod: 180, paymentTerms: '30_days', deliveryTerms: 'standard', warrantyPeriod: 90, revisionPolicy: 'included', cancellationPolicy: 'standard' },
      currency: 'CNY',
      remarks: ''
    });

    render(<ComprehensiveQuote />);

    await waitFor(() => expect(screen.getByDisplayValue('Comp Edit Co')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: '更新报价单' }));

    await waitFor(() => expect(QuoteApiService.updateQuote).toHaveBeenCalledWith(45, expect.objectContaining({
      quote_type: 'comprehensive',
      customer_name: 'Comp Edit Co'
    })));
    expect(mockNavigate).toHaveBeenCalledWith('/quote-detail/CQ-001', expect.anything());
  });

  it('builds a comprehensive package quote payload', async () => {
    render(<ComprehensiveQuote />);

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Package Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Pam' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Package Project' } });

    fireEvent.click(screen.getByRole('checkbox', { name: /CP测试服务/ }));

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        quoteType: 'package',
        quoteCreateData: expect.objectContaining({
          total_amount: 800,
          items: expect.arrayContaining([
            expect.objectContaining({ item_name: 'CP测试服务' })
          ])
        })
      })
    })));
  });

  it('builds a comprehensive volume quote payload', async () => {
    const { container } = render(<ComprehensiveQuote />);

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Volume Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Vera' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Volume Project' } });

    fireEvent.click(screen.getByRole('radio', { name: /数量分级报价/ }));
    fireEvent.change(screen.getAllByPlaceholderText('单价')[0], { target: { value: '5' } });
    const projectInfoSection = container.querySelectorAll('.form-section')[1];
    const expectedVolumeInput = projectInfoSection.querySelector('input[type="number"]');
    fireEvent.change(expectedVolumeInput, { target: { value: '5000' } });

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        quoteType: 'volume',
        quoteCreateData: expect.objectContaining({
          total_amount: 25000,
          items: expect.arrayContaining([
            expect.objectContaining({ item_name: '数量分级报价' })
          ])
        })
      })
    })));
  });

  it('builds a comprehensive time quote payload', async () => {
    render(<ComprehensiveQuote />);

    fireEvent.change(screen.getByPlaceholderText('请输入公司名称'), { target: { value: 'Time Co' } });
    fireEvent.change(screen.getByPlaceholderText('请输入联系人姓名'), { target: { value: 'Tim' } });
    fireEvent.change(screen.getByPlaceholderText('请输入项目名称'), { target: { value: 'Time Project' } });

    fireEvent.click(screen.getByRole('radio', { name: /时间合约报价/ }));
    fireEvent.change(screen.getAllByDisplayValue('0')[0], { target: { value: '1000' } });

    fireEvent.click(screen.getByRole('button', { name: '完成报价' }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/quote-result', expect.objectContaining({
      state: expect.objectContaining({
        quoteType: 'time',
        quoteCreateData: expect.objectContaining({
          items: expect.arrayContaining([
            expect.objectContaining({ item_name: '时间合约报价' })
          ])
        })
      })
    })));
  });
});
