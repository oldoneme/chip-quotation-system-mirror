import api from './api';

// 获取所有板卡列表
export const getCards = async () => {
  try {
    console.log('Fetching cards from API...');
    const response = await api.get('/cards/');
    console.log('Cards fetched successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching cards:', error);
    // 提供更具体的错误信息
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error message:', error.message);
    }
    throw error;
  }
};

// 根据ID获取特定板卡
export const getCardById = async (id) => {
  try {
    const response = await api.get(`/cards/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching card with id ${id}:`, error);
    throw error;
  }
};

// 创建新板卡
export const createCard = async (cardData) => {
  try {
    const response = await api.post('/cards/', cardData);
    return response.data;
  } catch (error) {
    console.error('Error creating card:', error);
    throw error;
  }
};

// 更新板卡信息
export const updateCard = async (id, cardData) => {
  try {
    const response = await api.put(`/cards/${id}`, cardData);
    return response.data;
  } catch (error) {
    console.error(`Error updating card with id ${id}:`, error);
    throw error;
  }
};

// 删除板卡
export const deleteCard = async (id) => {
  try {
    const response = await api.delete(`/cards/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting card with id ${id}:`, error);
    throw error;
  }
};