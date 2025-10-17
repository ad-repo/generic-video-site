// Storage manager that syncs with server and falls back to localStorage
class StorageManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.syncQueue = new Set();
        this.serverPreferences = {};
        this.initialized = false;
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.syncPendingChanges();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }

    async initialize() {
        if (this.initialized) return;
        
        try {
            // Load preferences from server
            await this.loadFromServer();
            
            // Sync any localStorage data to server (migration)
            await this.migrateLocalStorageToServer();
            
            this.initialized = true;
            console.log('✅ Storage manager initialized with server sync');
        } catch (error) {
            console.warn('⚠️ Server sync unavailable, using localStorage:', error.message);
            this.initialized = true;
        }
    }

    async loadFromServer() {
        if (!this.isOnline) throw new Error('Offline');
        
        const response = await fetch('/api/preferences');
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        
        this.serverPreferences = await response.json();
        console.log('📥 Loaded preferences from server:', Object.keys(this.serverPreferences).length, 'items');
    }

    async migrateLocalStorageToServer() {
        const localData = {};
        const keysToMigrate = [];
        
        // Collect all relevant localStorage keys
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('progress:') || key.startsWith('played:') || 
                       key.startsWith('rating:') || key.startsWith('videoRating:'))) {
                localData[key] = localStorage.getItem(key);
                keysToMigrate.push(key);
            }
        }
        
        if (keysToMigrate.length === 0) return;
        
        console.log('🔄 Migrating', keysToMigrate.length, 'localStorage items to server');
        
        try {
            const response = await fetch(`/api/preferences/sync?preferences=${encodeURIComponent(JSON.stringify(localData))}`);
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Migration complete:', result.synced_count, 'items synced');
                
                // Clear migrated items from localStorage
                keysToMigrate.forEach(key => localStorage.removeItem(key));
            }
        } catch (error) {
            console.warn('⚠️ Migration failed, keeping localStorage data:', error);
        }
    }

    async saveToServer(key, value, type) {
        if (!this.isOnline) {
            this.syncQueue.add({key, value, type});
            return false;
        }

        try {
            const response = await fetch('/api/preferences', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key, value: String(value), type})
            });
            
            if (response.ok) {
                this.serverPreferences[key] = {value: String(value), type, updated_at: new Date().toISOString()};
                return true;
            }
        } catch (error) {
            console.warn('⚠️ Failed to save to server:', error);
            this.syncQueue.add({key, value, type});
        }
        
        return false;
    }

    async syncPendingChanges() {
        if (!this.isOnline || this.syncQueue.size === 0) return;
        
        console.log('🔄 Syncing', this.syncQueue.size, 'pending changes to server');
        
        for (const change of this.syncQueue) {
            const success = await this.saveToServer(change.key, change.value, change.type);
            if (success) {
                this.syncQueue.delete(change);
            }
        }
    }

    // Public API methods
    getItem(key) {
        // Try server data first, fallback to localStorage
        if (this.serverPreferences[key]) {
            return this.serverPreferences[key].value;
        }
        return localStorage.getItem(key);
    }

    async setItem(key, value) {
        // Determine preference type from key
        let type = 'unknown';
        if (key.startsWith('progress:')) type = 'progress';
        else if (key.startsWith('played:')) type = 'played';
        else if (key.startsWith('rating:')) type = 'course_rating';
        else if (key.startsWith('videoRating:')) type = 'video_rating';

        // Always save to localStorage as backup
        localStorage.setItem(key, value);

        // Try to save to server
        if (this.initialized) {
            const success = await this.saveToServer(key, value, type);
            if (!success) {
                console.log('📱 Saved to localStorage (server sync pending)');
            }
        }
    }

    removeItem(key) {
        localStorage.removeItem(key);
        
        if (this.serverPreferences[key]) {
            delete this.serverPreferences[key];
        }
        
        // Try to remove from server
        if (this.isOnline && this.initialized) {
            fetch(`/api/preferences/${encodeURIComponent(key)}`, {method: 'DELETE'})
                .catch(error => console.warn('⚠️ Failed to remove from server:', error));
        }
    }

    // Get sync status
    getSyncStatus() {
        return {
            online: this.isOnline,
            initialized: this.initialized,
            pendingChanges: this.syncQueue.size,
            serverItems: Object.keys(this.serverPreferences).length
        };
    }
}

// Global storage manager instance
window.storageManager = new StorageManager();
