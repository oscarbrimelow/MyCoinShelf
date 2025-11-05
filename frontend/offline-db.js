// IndexedDB wrapper for offline data storage
class OfflineDB {
  constructor() {
    this.dbName = 'CoinShelfDB';
    this.dbVersion = 1;
    this.db = null;
  }

  // Initialize database
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('IndexedDB error:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Object store for collection items
        if (!db.objectStoreNames.contains('collection')) {
          const collectionStore = db.createObjectStore('collection', { keyPath: 'id', autoIncrement: true });
          collectionStore.createIndex('offlineId', 'offlineId', { unique: true });
          collectionStore.createIndex('synced', 'synced', { unique: false });
        }

        // Object store for wishlist items
        if (!db.objectStoreNames.contains('wishlist')) {
          const wishlistStore = db.createObjectStore('wishlist', { keyPath: 'id', autoIncrement: true });
          wishlistStore.createIndex('offlineId', 'offlineId', { unique: true });
          wishlistStore.createIndex('synced', 'synced', { unique: false });
        }

        // Object store for sync queue (pending operations)
        if (!db.objectStoreNames.contains('syncQueue')) {
          const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
          syncStore.createIndex('timestamp', 'timestamp', { unique: false });
          syncStore.createIndex('type', 'type', { unique: false });
        }

        // Object store for cached API responses
        if (!db.objectStoreNames.contains('apiCache')) {
          const cacheStore = db.createObjectStore('apiCache', { keyPath: 'key', unique: true });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Object store for user profile
        if (!db.objectStoreNames.contains('profile')) {
          db.createObjectStore('profile', { keyPath: 'id', unique: true });
        }

        console.log('IndexedDB schema created/updated');
      };
    });
  }

  // Collection operations
  async saveCollectionItem(item) {
    const transaction = this.db.transaction(['collection'], 'readwrite');
    const store = transaction.objectStore('collection');
    
    // Mark as not synced if it's a new item
    if (!item.id || item.id.toString().startsWith('offline_')) {
      item.offlineId = item.offlineId || `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      item.synced = false;
      item.id = item.offlineId; // Use offline ID temporarily
    }
    
    return store.put(item);
  }

  async getCollectionItems() {
    const transaction = this.db.transaction(['collection'], 'readonly');
    const store = transaction.objectStore('collection');
    return store.getAll();
  }

  async deleteCollectionItem(id) {
    const transaction = this.db.transaction(['collection'], 'readwrite');
    const store = transaction.objectStore('collection');
    return store.delete(id);
  }

  // Wishlist operations
  async saveWishlistItem(item) {
    const transaction = this.db.transaction(['wishlist'], 'readwrite');
    const store = transaction.objectStore('wishlist');
    
    if (!item.id || item.id.toString().startsWith('offline_')) {
      item.offlineId = item.offlineId || `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      item.synced = false;
      item.id = item.offlineId;
    }
    
    return store.put(item);
  }

  async getWishlistItems() {
    const transaction = this.db.transaction(['wishlist'], 'readonly');
    const store = transaction.objectStore('wishlist');
    return store.getAll();
  }

  async deleteWishlistItem(id) {
    const transaction = this.db.transaction(['wishlist'], 'readwrite');
    const store = transaction.objectStore('wishlist');
    return store.delete(id);
  }

  // Sync queue operations
  async addToSyncQueue(operation) {
    const transaction = this.db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');
    
    const queueItem = {
      ...operation,
      timestamp: Date.now(),
      attempts: 0,
      status: 'pending'
    };
    
    return store.add(queueItem);
  }

  async getSyncQueue() {
    const transaction = this.db.transaction(['syncQueue'], 'readonly');
    const store = transaction.objectStore('syncQueue');
    return store.getAll();
  }

  async removeFromSyncQueue(id) {
    const transaction = this.db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');
    return store.delete(id);
  }

  async clearSyncQueue() {
    const transaction = this.db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');
    return store.clear();
  }

  // API cache operations
  async cacheAPIResponse(key, data) {
    const transaction = this.db.transaction(['apiCache'], 'readwrite');
    const store = transaction.objectStore('apiCache');
    
    const cacheItem = {
      key: key,
      data: data,
      timestamp: Date.now()
    };
    
    return store.put(cacheItem);
  }

  async getCachedAPIResponse(key) {
    const transaction = this.db.transaction(['apiCache'], 'readonly');
    const store = transaction.objectStore('apiCache');
    return store.get(key);
  }

  // Profile operations
  async saveProfile(profile) {
    const transaction = this.db.transaction(['profile'], 'readwrite');
    const store = transaction.objectStore('profile');
    profile.id = 'current';
    return store.put(profile);
  }

  async getProfile() {
    const transaction = this.db.transaction(['profile'], 'readonly');
    const store = transaction.objectStore('profile');
    return store.get('current');
  }

  // Clear all data (for logout)
  async clearAll() {
    const stores = ['collection', 'wishlist', 'syncQueue', 'apiCache', 'profile'];
    const transaction = this.db.transaction(stores, 'readwrite');
    
    stores.forEach(storeName => {
      transaction.objectStore(storeName).clear();
    });
    
    return transaction.complete;
  }
}

// Export singleton instance
const offlineDB = new OfflineDB();

