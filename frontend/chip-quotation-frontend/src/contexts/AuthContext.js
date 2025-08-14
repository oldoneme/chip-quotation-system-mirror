import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import api from '../services/api';


const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  const checkAuth = async () => {
    try {
      setLoading(true);
      
      const response = await axios.get('/api/me', { 
        withCredentials: true,
        timeout: 10000
      });
      
      setUser(response.data);
      setAuthenticated(true);
    } catch (error) {
      
      if (error.response?.status === 401) {
        // 检查是否在调试模式或企业微信环境
        const urlParams = new URLSearchParams(window.location.search);
        const debugMode = urlParams.get('debug') === 'true' || 
                         urlParams.get('dev') === 'true' ||
                         window.location.hostname === 'localhost' ||
                         window.location.port === '3000';
        
        const isWeWorkEnvironment = window.navigator.userAgent.includes('wxwork') || 
                                   window.navigator.userAgent.includes('MicroMessenger') ||
                                   document.referrer.includes('weixin.qq.com') ||
                                   document.referrer.includes('work.weixin.qq.com') ||
                                   sessionStorage.getItem('wework_authenticated') === 'true';
        
        if (debugMode) {
          console.log('🛠️ 调试模式：认证失败，不重定向');
          setUser(null);
          setAuthenticated(false);
          return;
        }
        
        // 未登录，跳转到登录
        window.location.href = `${window.location.origin}/auth/login`;
        return;
      }
      
      setUser(null);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // 静默处理登出错误
    } finally {
      setUser(null);
      setAuthenticated(false);
      window.location.href = `${window.location.origin}/auth/login`;
    }
  };

  useEffect(() => {
    // 检查URL参数中是否有错误信息
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const message = urlParams.get('message');
    
    if (error) {
      if (error === 'access_denied') {
        alert(`访问被拒绝: ${decodeURIComponent(message || '您暂无权限访问此系统')}`);
      } else if (error === 'auth_failed') {
        alert(`认证失败: ${decodeURIComponent(message || '登录失败，请重试')}`);
      }
      // 清除URL参数
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    checkAuth();
  }, []);

  const value = {
    user,
    authenticated,
    loading,
    checkAuth,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};