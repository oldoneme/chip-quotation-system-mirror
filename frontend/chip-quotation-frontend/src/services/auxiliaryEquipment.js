import api from './api';
import dataCache from './dataCache';

// 获取所有辅助设备列表
export const getAuxiliaryEquipment = async () => {
  const cacheKey = 'auxiliary_equipment_list';
  
  // 先检查缓存
  const cachedData = dataCache.get(cacheKey);
  if (cachedData) {
    console.log('Returning auxiliary equipment from cache');
    return cachedData;
  }

  try {
    console.log('Fetching auxiliary equipment from API...');
    const response = await api.get('/auxiliary-equipment/');
    console.log('Auxiliary equipment fetched successfully:', response.data);
    
    // 保存到缓存
    dataCache.set(cacheKey, response.data);
    
    return response.data;
  } catch (error) {
    console.error('Error fetching auxiliary equipment:', error);
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

// 根据ID获取特定辅助设备
export const getAuxiliaryEquipmentById = async (id) => {
  try {
    const response = await api.get(`/auxiliary-equipment/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching auxiliary equipment with id ${id}:`, error);
    throw error;
  }
};

// 创建新辅助设备
export const createAuxiliaryEquipment = async (equipmentData) => {
  try {
    const response = await api.post('/auxiliary-equipment/', equipmentData);
    return response.data;
  } catch (error) {
    console.error('Error creating auxiliary equipment:', error);
    throw error;
  }
};

// 更新辅助设备信息
export const updateAuxiliaryEquipment = async (id, equipmentData) => {
  try {
    const response = await api.put(`/auxiliary-equipment/${id}`, equipmentData);
    return response.data;
  } catch (error) {
    console.error(`Error updating auxiliary equipment with id ${id}:`, error);
    throw error;
  }
};

// 删除辅助设备
export const deleteAuxiliaryEquipment = async (id) => {
  try {
    const response = await api.delete(`/auxiliary-equipment/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting auxiliary equipment with id ${id}:`, error);
    throw error;
  }
};