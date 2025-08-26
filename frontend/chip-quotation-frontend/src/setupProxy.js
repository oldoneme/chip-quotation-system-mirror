const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // 拦截所有响应并添加no-cache头
  app.use((req, res, next) => {
    // 保存原始的writeHead方法
    const originalWriteHead = res.writeHead;
    
    // 重写writeHead方法以添加缓存控制头
    res.writeHead = function(...args) {
      // 设置no-cache响应头
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      
      // 调用原始方法
      return originalWriteHead.apply(res, args);
    };
    
    next();
  });

  // API代理配置（如果需要）
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      onProxyRes: function(proxyRes, req, res) {
        // 对API响应也设置no-cache
        proxyRes.headers['cache-control'] = 'no-store, no-cache, must-revalidate, max-age=0';
        proxyRes.headers['pragma'] = 'no-cache';
        proxyRes.headers['expires'] = '0';
      }
    })
  );
};