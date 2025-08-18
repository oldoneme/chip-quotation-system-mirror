import api from './api';
import dataCache from './dataCache';

// 获取所有机器列表
export const getMachines = async () => {
  const cacheKey = 'machines_list';
  
  // 先检查缓存
  const cachedData = dataCache.get(cacheKey);
  if (cachedData) {
    console.log('Returning machines from cache');
    return cachedData;
  }

  try {
    console.log('Fetching machines from API...');
    const response = await api.get('/machines/');
    console.log('Machines fetched successfully:', response.data);
    
    // 保存到缓存
    dataCache.set(cacheKey, response.data);
    
    return response.data;
  } catch (error) {
    console.error('Error fetching machines:', error);
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

// 根据ID获取特定机器
export const getMachineById = async (id) => {
  try {
    const response = await api.get(`/machines/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching machine with id ${id}:`, error);
    throw error;
  }
};

// 创建新机器
export const createMachine = async (machineData) => {
  try {
    const response = await api.post('/machines/', machineData);
    return response.data;
  } catch (error) {
    console.error('Error creating machine:', error);
    throw error;
  }
};

// 更新机器信息
export const updateMachine = async (id, machineData) => {
  try {
    const response = await api.put(`/machines/${id}`, machineData);
    return response.data;
  } catch (error) {
    console.error(`Error updating machine with id ${id}:`, error);
    throw error;
  }
};

// 删除机器
export const deleteMachine = async (id) => {
  try {
    const response = await api.delete(`/machines/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting machine with id ${id}:`, error);
    throw error;
  }
};