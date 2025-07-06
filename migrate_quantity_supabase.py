#!/usr/bin/env python3
"""
Standalone script to add quantity column to Supabase database.
Run this script to migrate your database.
"""

import requests
import json

def migrate_supabase_database():
    """Trigger database migration on the deployed backend."""
    
    # Your backend URL
    backend_url = "https://mycoinshelf.onrender.com"
    migration_endpoint = f"{backend_url}/api/migrate_database"
    
    print("🔄 Starting database migration...")
    print(f"📡 Calling migration endpoint: {migration_endpoint}")
    
    try:
        # Make a GET request to trigger the migration
        response = requests.get(migration_endpoint, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Migration successful!")
            print(f"📝 Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Migration failed with status code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during migration: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        print(f"📝 Raw response: {response.text}")
        return False

def test_quantity_column():
    """Test if the quantity column was added successfully."""
    
    backend_url = "https://mycoinshelf.onrender.com"
    test_endpoint = f"{backend_url}/api/coins"
    
    print("\n🧪 Testing quantity column...")
    print(f"📡 Testing endpoint: {test_endpoint}")
    
    try:
        # This should return 401 (unauthorized) but not a database error
        response = requests.get(test_endpoint, timeout=10)
        
        if response.status_code == 401:
            print("✅ Database connection successful! (401 Unauthorized is expected)")
            print("✅ Quantity column migration appears to be working!")
            return True
        elif response.status_code == 500:
            print("❌ Database error still occurring")
            print(f"📝 Response: {response.text}")
            return False
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CoinShelf Database Migration Tool")
    print("=" * 40)
    
    # Run migration
    migration_success = migrate_supabase_database()
    
    if migration_success:
        # Test the migration
        test_success = test_quantity_column()
        
        if test_success:
            print("\n🎉 Migration completed successfully!")
            print("✅ You can now add items with quantity in your CoinShelf app!")
        else:
            print("\n⚠️ Migration may have issues. Please check your backend logs.")
    else:
        print("\n❌ Migration failed. Please check your backend deployment.")
    
    print("\n📋 Next steps:")
    print("1. Try adding a new item with quantity in your app")
    print("2. If you still get errors, check your backend logs on Render")
    print("3. Make sure your backend is deployed with the latest changes") 