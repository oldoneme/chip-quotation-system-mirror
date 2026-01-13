import api from './api';
import dataCache from './dataCache';

// 获取所有板卡配置列表
export const getCardTypes = async () => {
  const cacheKey = 'card_types_list';
  
  // 先检查缓存
  const cachedData = dataCache.get(cacheKey);
  if (cachedData) {
    console.log('Returning card types from cache');
    return cachedData;
  }

  try {
    console.log('Fetching card configs from API...');
    const response = await api.get('/card-configs/');
    console.log('Card configs fetched successfully:', response.data);
    
    // 清洗板卡数据：强制移除 currency 和 exchange_rate 字段，避免对前端逻辑产生误导
    const cleanedData = response.data.map(card => {
      const newCard = { ...card };
      delete newCard.currency;
      delete newCard.exchange_rate;
      return newCard;
    });

    // 保存到缓存
    dataCache.set(cacheKey, cleanedData);
    
    return cleanedData;
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
export const getCardTypeById = async (id) => {
  try {
    const response = await api.get(`/card-configs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching card config with id ${id}:`, error);
    throw error;
  }
};

// 创建新板卡配置
export const createCardType = async (cardTypeData) => {
  try {
    const response = await api.post('/card-configs/', cardTypeData);
    return response.data;
  } catch (error) {
    console.error('Error creating card config:', error);
    throw error;
  }
};

// 更新板卡配置信息
export const updateCardType = async (id, cardTypeData) => {
  try {
    const response = await api.put(`/card-configs/${id}`, cardTypeData);
    return response.data;
  } catch (error) {
    console.error(`Error updating card config with id ${id}:`, error);
    throw error;
  }
};

// 删除板卡配置
export const deleteCardType = async (id) => {
  try {
    const response = await api.delete(`/card-configs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting card config with id ${id}:`, error);
    throw error;
  }
};