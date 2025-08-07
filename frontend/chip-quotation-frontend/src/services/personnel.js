import api from './api';

// 获取所有人员列表
export const getPersonnel = async () => {
  try {
    console.log('Fetching personnel from API...');
    const response = await api.get('/personnel/');
    console.log('Personnel fetched successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching personnel:', error);
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

// 根据ID获取特定人员
export const getPersonnelById = async (id) => {
  try {
    const response = await api.get(`/personnel/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching personnel with id ${id}:`, error);
    throw error;
  }
};

// 创建新人员
export const createPersonnel = async (personnelData) => {
  try {
    const response = await api.post('/personnel/', personnelData);
    return response.data;
  } catch (error) {
    console.error('Error creating personnel:', error);
    throw error;
  }
};

// 更新人员信息
export const updatePersonnel = async (id, personnelData) => {
  try {
    const response = await api.put(`/personnel/${id}`, personnelData);
    return response.data;
  } catch (error) {
    console.error(`Error updating personnel with id ${id}:`, error);
    throw error;
  }
};

// 删除人员
export const deletePersonnel = async (id) => {
  try {
    const response = await api.delete(`/personnel/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting personnel with id ${id}:`, error);
    throw error;
  }
};