import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  withCredentials: true,
});


// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    
    // 从URL参数或localStorage获取JWT token
    const urlParams = new URLSearchParams(window.location.search);
    const snapshotTokenFromUrl = urlParams.get('__snapshot_token');
    const snapshotTokenStored = sessionStorage.getItem('__snapshot_token');
    const jwtFromUrl = urlParams.get('jwt');

    if (snapshotTokenFromUrl) {
      sessionStorage.setItem('__snapshot_token', snapshotTokenFromUrl);
      config.headers.Authorization = `Bearer ${snapshotTokenFromUrl}`;
      console.log('Using snapshot token from URL');
    } else if (snapshotTokenStored) {
      config.headers.Authorization = `Bearer ${snapshotTokenStored}`;
      console.log('Using snapshot token from sessionStorage');
    } else if (jwtFromUrl) {
      localStorage.setItem('jwt_token', jwtFromUrl);
      config.headers.Authorization = `Bearer ${jwtFromUrl}`;
      console.log('Using JWT from URL');
    } else {
      const storedJwt = localStorage.getItem('jwt_token');
      if (storedJwt) {
        config.headers.Authorization = `Bearer ${storedJwt}`;
        console.log('Using JWT from localStorage');
      }
    }
    
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    
    
    return response;
  },
  (error) => {
    let errorMessage = '请求失败';
    
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API Error Response:', error.response.status, error.response.data);
      
      switch (error.response.status) {
        case 400:
          errorMessage = '请求参数错误';
          break;
        case 401:
          errorMessage = '未授权访问';
          break;
        case 403:
          errorMessage = '访问被禁止';
          break;
        case 404:
          errorMessage = '请求的资源不存在';
          break;
        case 500:
          errorMessage = '服务器内部错误';
          break;
        case 502:
          errorMessage = '网关错误';
          break;
        case 503:
          errorMessage = '服务不可用';
          break;
        default:
          errorMessage = `请求失败 (${error.response.status})`;
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('API Timeout:', error.message);
      errorMessage = '请求超时，请稍后重试';
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error (No Response):', error.request);
      errorMessage = '网络连接失败，请检查网络设置';
    } else {
      // 其他错误
      console.error('API Error:', error.message);
      errorMessage = error.message || '未知错误';
    }
    
    console.error('API Error Message:', errorMessage);
    
    return Promise.reject(error);
  }
);

export default api;