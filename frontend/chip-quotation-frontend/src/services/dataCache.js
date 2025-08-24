// 简单的内存缓存服务
class DataCache {
  constructor() {
    this.cache = new Map();
    this.expirationTime = 30 * 60 * 1000; // 30分钟过期，延长缓存时间避免频繁刷新
  }

  // 设置缓存
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  // 获取缓存
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    // 检查是否过期
    if (Date.now() - item.timestamp > this.expirationTime) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  // 清除特定缓存
  delete(key) {
    this.cache.delete(key);
  }

  // 清除所有缓存
  clear() {
    this.cache.clear();
  }

  // 检查缓存是否存在且未过期
  has(key) {
    return this.get(key) !== null;
  }
}

// 创建全局缓存实例
const dataCache = new DataCache();

export default dataCache;