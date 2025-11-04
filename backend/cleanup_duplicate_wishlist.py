"""
Script to clean up duplicate wishlist items in the database.
Run this script to remove duplicate wishlist entries.

Usage:
    python cleanup_duplicate_wishlist.py
"""

from app import app, db, WishlistItem, User

def cleanup_duplicate_wishlist_items():
    """Remove duplicate wishlist items based on country, denomination, year, and numista_id"""
    with app.app_context():
        # Get all users
        users = User.query.all()
        
        total_deleted = 0
        
        for user in users:
            print(f"\nProcessing user {user.id} ({user.email})...")
            
            # Get all wishlist items for this user
            items = WishlistItem.query.filter_by(user_id=user.id).order_by(WishlistItem.id).all()
            
            # Track seen items by (country, denomination, year, numista_id)
            seen_items = {}
            duplicates = []
            
            for item in items:
                # Create a unique key
                key = (
                    item.country,
                    item.denomination,
                    item.year,
                    item.numista_id
                )
                
                if key in seen_items:
                    # This is a duplicate
                    duplicates.append(item)
                    print(f"  Found duplicate: ID {item.id} - {item.denomination} from {item.country} ({item.year})")
                else:
                    # First occurrence, keep it
                    seen_items[key] = item
            
            # Delete duplicates (keep the first one)
            for duplicate in duplicates:
                print(f"  Deleting duplicate ID {duplicate.id}")
                db.session.delete(duplicate)
                total_deleted += 1
            
            if duplicates:
                db.session.commit()
                print(f"  Deleted {len(duplicates)} duplicates for user {user.id}")
        
        print(f"\nTotal duplicates deleted: {total_deleted}")
        print("Cleanup complete!")

if __name__ == '__main__':
    cleanup_duplicate_wishlist_items()

