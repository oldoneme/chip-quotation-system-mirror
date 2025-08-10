import api from './api';

// 获取所有板卡列表
export const getCards = async () => {
  try {
    console.log('Fetching card configs from API...');
    const response = await api.get('/card-configs/');
    console.log('Card configs fetched successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching card configs:', error);
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

// 根据ID获取特定板卡配置
export const getCardById = async (id) => {
  try {
    const response = await api.get(`/card-configs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching card config with id ${id}:`, error);
    throw error;
  }
};

// 创建新板卡配置
export const createCard = async (cardData) => {
  try {
    const response = await api.post('/card-configs/', cardData);
    return response.data;
  } catch (error) {
    console.error('Error creating card config:', error);
    throw error;
  }
};

// 更新板卡配置信息
export const updateCard = async (id, cardData) => {
  try {
    const response = await api.put(`/card-configs/${id}`, cardData);
    return response.data;
  } catch (error) {
    console.error(`Error updating card config with id ${id}:`, error);
    throw error;
  }
};

// 删除板卡配置
export const deleteCard = async (id) => {
  try {
    const response = await api.delete(`/card-configs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting card config with id ${id}:`, error);
    throw error;
  }
};