import api from './api';

// 计算报价
export const calculateQuotation = async (quotationData) => {
  try {
    const response = await api.post('/quotations/calculate', quotationData);
    return response.data;
  } catch (error) {
    console.error('Error calculating quotation:', error);
    throw error;
  }
};