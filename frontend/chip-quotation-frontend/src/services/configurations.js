import api from './api';
import dataCache from './dataCache';

// 获取所有配置列表
export const getConfigurations = async () => {
  const cacheKey = 'configurations_list';
  
  // 先检查缓存
  const cachedData = dataCache.get(cacheKey);
  if (cachedData) {
    console.log('Returning configurations from cache');
    return cachedData;
  }

  try {
    console.log('Fetching configurations from API...');
    const response = await api.get('/configurations/');
    console.log('Configurations fetched successfully:', response.data);
    
    // 保存到缓存
    dataCache.set(cacheKey, response.data);
    
    return response.data;
  } catch (error) {
    console.error('Error fetching configurations:', error);
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

// 根据ID获取特定配置
export const getConfigurationById = async (id) => {
  try {
    const response = await api.get(`/configurations/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching configuration with id ${id}:`, error);
    throw error;
  }
};

// 创建新配置
export const createConfiguration = async (configData) => {
  try {
    const response = await api.post('/configurations/', configData);
    return response.data;
  } catch (error) {
    console.error('Error creating configuration:', error);
    throw error;
  }
};

// 更新配置信息
export const updateConfiguration = async (id, configData) => {
  try {
    const response = await api.put(`/configurations/${id}`, configData);
    return response.data;
  } catch (error) {
    console.error(`Error updating configuration with id ${id}:`, error);
    throw error;
  }
};

// 删除配置
export const deleteConfiguration = async (id) => {
  try {
    const response = await api.delete(`/configurations/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting configuration with id ${id}:`, error);
    throw error;
  }
};