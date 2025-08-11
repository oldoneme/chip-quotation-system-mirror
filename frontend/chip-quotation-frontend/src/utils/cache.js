// 简单的内存缓存工具
class Cache {
  constructor(defaultTTL = 5 * 60 * 1000) { // 默认5分钟过期
    this.cache = new Map();
    this.defaultTTL = defaultTTL;
  }

  set(key, value, ttl = this.defaultTTL) {
    const expireTime = Date.now() + ttl;
    this.cache.set(key, { value, expireTime });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() > item.expireTime) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  has(key) {
    const item = this.cache.get(key);
    if (!item) return false;

    if (Date.now() > item.expireTime) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  delete(key) {
    return this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }

  // 清理过期的缓存项
  cleanup() {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expireTime) {
        this.cache.delete(key);
      }
    }
  }

  // 获取缓存统计信息
  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
}

// 创建全局缓存实例
const globalCache = new Cache();

// 定期清理过期缓存
setInterval(() => {
  globalCache.cleanup();
}, 60000); // 每分钟清理一次

export default globalCache;