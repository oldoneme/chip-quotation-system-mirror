import axios from 'axios';
import cache from '../utils/cache';
import { showError } from '../utils/notifications';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
});

// 生成缓存key
const getCacheKey = (config) => {
  const method = config.method?.toLowerCase();
  const url = config.url;
  const params = JSON.stringify(config.params || {});
  return `${method}:${url}:${params}`;
};

// 可缓存的请求方法
const CACHEABLE_METHODS = ['get'];

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
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
    
    // 缓存GET请求的响应数据 (暂时禁用缓存来调试)
    // if (CACHEABLE_METHODS.includes(response.config.method?.toLowerCase())) {
    //   const cacheKey = getCacheKey(response.config);
    //   cache.set(cacheKey, response.data);
    // }
    
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
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error (No Response):', error.request);
      errorMessage = '网络连接失败，请检查网络设置';
    } else {
      // 其他错误
      console.error('API Error:', error.message);
      errorMessage = error.message || '未知错误';
    }
    
    // 显示用户友好的错误消息 (暂时禁用自动提示)
    // showError(errorMessage);
    console.error('API Error Message:', errorMessage);
    
    return Promise.reject(error);
  }
);

export default api;