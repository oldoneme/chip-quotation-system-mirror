const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// 静态资源长缓存（带哈希的JS/CSS文件）
app.use('/static', express.static(path.join(__dirname, 'build', 'static'), {
  immutable: true,
  maxAge: '1y',
  setHeaders: (res, path) => {
    // 对带哈希的静态资源设置长缓存
    if (path.endsWith('.js') || path.endsWith('.css')) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
      res.setHeader('X-Content-Type', 'Static-Hashed');
    }
  }
}));

// 其他静态资源（图片、字体等）适中缓存
app.use(express.static(path.join(__dirname, 'build'), {
  maxAge: '1h',
  setHeaders: (res, path, stat) => {
    // HTML文件不缓存
    if (path.endsWith('.html') || path === '/') {
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      res.setHeader('X-Content-Type', 'HTML');
    }
    // 图片、字体等资源适中缓存
    else if (path.match(/\.(png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
      res.setHeader('Cache-Control', 'public, max-age=86400'); // 1天
      res.setHeader('X-Content-Type', 'Asset');
    }
  }
}));

// HTML路由（确保SPA路由正确处理）
app.get(['/', '/index.html'], (req, res) => {
  res.set({
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache',
    'Expires': '0',
    'X-Content-Type': 'HTML-Route'
  });
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// SPA fallback - 所有其他路由都返回index.html
app.get('*', (req, res) => {
  res.set({
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache', 
    'Expires': '0',
    'X-Content-Type': 'SPA-Fallback'
  });
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 Static server running at http://localhost:${PORT}`);
  console.log('📦 Cache Strategy:');
  console.log('  - HTML: no-cache');
  console.log('  - Static JS/CSS: 1 year immutable');
  console.log('  - Assets: 1 day');
});