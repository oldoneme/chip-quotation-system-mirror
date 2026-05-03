import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { message } from 'antd';
import QuoteResult from './QuoteResult';

const mockNavigate = jest.fn();
const mockCreateQuote = jest.fn();
const mockUpdateQuote = jest.fn();

let mockLocationState = null;

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: mockLocationState })
}));

jest.mock('../services/quoteApi', () => ({
  __esModule: true,
  QuoteApiService: {
    createQuote: jest.fn(),
    updateQuote: jest.fn(),
    getQuoteDetailById: jest.fn()
  },
  default: {
    createQuote: (...args) => mockCreateQuote(...args),
    updateQuote: (...args) => mockUpdateQuote(...args)
  }
}));

describe('QuoteResult', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockCreateQuote.mockReset();
    mockUpdateQuote.mockReset();
    jest.spyOn(message, 'error').mockImplementation(jest.fn());
    mockCreateQuote.mockResolvedValue({
      id: 1,
      quote_number: 'QT-001',
      status: 'draft'
    });
    mockUpdateQuote.mockResolvedValue({
      id: 2,
      quote_number: 'QT-EDIT-001',
      status: 'draft'
    });
    mockLocationState = {
      type: '工序报价',
      currency: 'CNY',
      customerInfo: { companyName: 'Acme', contactPerson: 'Alice', phone: '', email: '' },
      projectInfo: { projectName: 'Process Project', chipPackage: 'QFN', testType: 'process', quoteUnit: '昆山芯信安' },
      quoteCreateData: {
        title: 'Process Project - Acme',
        quote_type: '工序报价',
        customer_name: 'Acme',
        customer_contact: 'Alice',
        currency: 'CNY',
        subtotal: 0,
        total_amount: 0,
        items: [
          {
            item_name: 'CP工序 - CP1测试',
            quantity: 1,
            unit: '颗',
            unit_price: 0,
            total_price: 0,
            configuration: JSON.stringify({
              process_type: 'CP1测试',
              system_machine_rate: 12,
              adjusted_machine_rate: 12,
              uph: 3,
              test_machine: { id: 1, name: 'J750', cards: [{ id: 11, quantity: 1 }] },
              prober: { id: 2, name: 'AP3000', cards: [{ id: 22, quantity: 1 }] }
            })
          }
        ]
      }
    };
  });

  it('reconstructs process item pricing from saved rate data before createQuote', async () => {
    render(<QuoteResult />);

    expect(await screen.findByText('CP1测试')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '确认生成报价单' }));

    await waitFor(() => expect(mockCreateQuote).toHaveBeenCalled());

    const payload = mockCreateQuote.mock.calls[0][0];
    expect(payload.items[0].unit_price).toBe(4);
    expect(payload.items[0].total_price).toBe(4);
    expect(payload.subtotal).toBe(4);
    expect(payload.total_amount).toBe(4);
  });

  it('blocks confirming a process quote when the final unit price is zero', async () => {
    mockLocationState = {
      ...mockLocationState,
      quoteCreateData: {
        ...mockLocationState.quoteCreateData,
        items: [
          {
            item_name: 'CP工序 - CP1测试',
            quantity: 1,
            unit: '颗',
            unit_price: 0,
            total_price: 0,
            configuration: JSON.stringify({
              process_type: 'CP1测试',
              system_machine_rate: 0,
              adjusted_machine_rate: 0,
              uph: 0
            })
          }
        ]
      }
    };

    render(<QuoteResult />);

    fireEvent.click(await screen.findByRole('button', { name: '确认生成报价单' }));

    await waitFor(() => expect(mockCreateQuote).not.toHaveBeenCalled());
    expect(message.error).toHaveBeenCalledWith(expect.stringContaining('最终单价必须大于0'));
  });

  it('requires a reason when an engineering quote is adjusted below the system price', async () => {
    mockLocationState = {
      type: '工程报价',
      currency: 'CNY',
      customerInfo: { companyName: 'Eng Co', contactPerson: 'Bob', phone: '', email: '' },
      projectInfo: { projectName: 'Engineering Project', chipPackage: 'BGA', testType: 'engineering', quoteUnit: '昆山芯信安' },
      quoteCreateData: {
        title: 'Engineering Project - Eng Co',
        quote_type: 'engineering',
        customer_name: 'Eng Co',
        customer_contact: 'Bob',
        currency: 'CNY',
        subtotal: 7,
        total_amount: 7,
        items: [
          {
            item_name: 'J750',
            total_price: 7,
            machine_type: '测试机',
            machine_model: 'J750',
            supplier: 'Advantest',
            configuration: JSON.stringify({
              device_type: '测试机',
              device_model: 'J750',
              cards: [{ id: 1, part_number: 'APU12-001', quantity: 1 }]
            })
          }
        ]
      }
    };

    render(<QuoteResult />);

    const priceInput = await screen.findByDisplayValue('7.00');
    fireEvent.change(priceInput, { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: '确认生成报价单' }));

    await waitFor(() => expect(mockCreateQuote).not.toHaveBeenCalled());
    expect(message.error).toHaveBeenCalledWith(expect.stringContaining('请填写调整价格低于系统报价的项目的调整理由'));
  });

  it('uses updateQuote in edit mode for engineering quotes', async () => {
    mockLocationState = {
      type: '工程报价',
      isEditMode: true,
      editingQuoteId: 42,
      currency: 'CNY',
      customerInfo: { companyName: 'Eng Co', contactPerson: 'Bob', phone: '', email: '' },
      projectInfo: { projectName: 'Engineering Project', chipPackage: 'BGA', testType: 'engineering', quoteUnit: '昆山芯信安' },
      quoteCreateData: {
        title: 'Engineering Project - Eng Co',
        quote_type: 'engineering',
        customer_name: 'Eng Co',
        customer_contact: 'Bob',
        currency: 'CNY',
        subtotal: 7,
        total_amount: 7,
        items: [
          {
            item_name: 'J750',
            total_price: 7,
            machine_type: '测试机',
            machine_model: 'J750',
            supplier: 'Advantest',
            configuration: JSON.stringify({
              device_type: '测试机',
              device_model: 'J750',
              cards: [{ id: 1, part_number: 'APU12-001', quantity: 1 }]
            })
          }
        ]
      }
    };

    render(<QuoteResult />);

    fireEvent.click(await screen.findByRole('button', { name: '确认生成报价单' }));

    await waitFor(() => expect(mockUpdateQuote).toHaveBeenCalledWith(42, expect.objectContaining({ quote_type: 'engineering' })));
    expect(mockCreateQuote).not.toHaveBeenCalled();
  });
});
