import api from './api';

// 获取所有板卡类型列表
export const getCardTypes = async () => {
  try {
    console.log('Fetching card types from API...');
    const response = await api.get('/card-types/');
    console.log('Card types fetched successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching card types:', error);
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

// 根据ID获取特定板卡类型
export const getCardTypeById = async (id) => {
  try {
    const response = await api.get(`/card-types/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching card type with id ${id}:`, error);
    throw error;
  }
};

// 创建新板卡类型
export const createCardType = async (cardTypeData) => {
  try {
    const response = await api.post('/card-types/', cardTypeData);
    return response.data;
  } catch (error) {
    console.error('Error creating card type:', error);
    throw error;
  }
};

// 更新板卡类型信息
export const updateCardType = async (id, cardTypeData) => {
  try {
    const response = await api.put(`/card-types/${id}`, cardTypeData);
    return response.data;
  } catch (error) {
    console.error(`Error updating card type with id ${id}:`, error);
    throw error;
  }
};

// 删除板卡类型
export const deleteCardType = async (id) => {
  try {
    const response = await api.delete(`/card-types/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting card type with id ${id}:`, error);
    throw error;
  }
};