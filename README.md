# 🪙 CoinShelf - Professional Coin & Bullion Collection Manager

A comprehensive web application for coin collectors, numismatists, and precious metal investors to organize, track, and value their collections with live market data.

**Live Site:** https://mycoinshelf.com

---

## ✨ Features

### 🔐 **Authentication & Security**
- **Secure User Registration & Login** - Full authentication system with encrypted passwords
- **Password Reset System** - Professional email-based password recovery via Resend API
- **Account Management** - Change passwords, manage preferences, update profile settings
- **Session Management** - Secure JWT-based authentication with token expiration
- **Rate Limiting** - API protection with configurable rate limits
- **Password Security** - Encrypted password storage using Werkzeug

### 👤 **User Profiles & Social Features**
- **Custom User Profiles** - Username, display name, and bio customization
- **Public/Private Profiles** - Control visibility of your collection and wishlist
- **Follow System** - Follow other collectors and discover new collections
- **Followers & Following** - Track your social connections in the community
- **User Search** - Find other collectors by username
- **Collection Comments** - Comment on public collections and interact with other users
- **User Comparison** - Compare your collection with other collectors
- **Public Profile Views** - Browse public collections and wishlists

### 📱 **Core Collection Management**
- **Mobile-Responsive Design** - Works perfectly on all devices
- **Add Items Individually** - Detailed forms for coins, banknotes, and bullion
- **Edit & Delete Items** - Full CRUD operations for collection items
- **Quantity Tracking** - Track multiple copies of the same item
- **Bulk Import/Export** - Mass upload and download of collection data in JSON format
- **Advanced Search & Filtering** - Find items quickly by type, country, year, value, and more
- **Favorites System** - Mark favorite items for quick access
- **Duplicate Detection** - Automatically find duplicate items in your collection
- **Smart Merging** - Merge duplicate items while preserving all data
- **Clear All Items** - Bulk delete functionality for collection management

### 🔍 **Numista Integration**
- **Coin & Banknote Search** - Search Numista's extensive catalog via official API
- **Rich Item Details** - Import descriptions, composition, weight, diameter, and images
- **Wishlist Integration** - Add Numista items directly to your wishlist
- **Reference Links** - Automatic linking to Numista catalog entries
- **Image Import** - Import high-quality images from Numista

### 📋 **Wishlist Management**
- **Comprehensive Wishlist** - Track coins, banknotes, and bullion you want
- **Move to Collection** - Easily transfer items from wishlist to collection
- **Numista Integration** - Search and add items from Numista catalog
- **Reference URLs** - Store links to purchase sources or catalog pages
- **Item Details** - Track composition, weight, diameter, and descriptions
- **Creation Tracking** - See when items were added to your wishlist

### 🪙 **Bullion & Precious Metals**
- **Multi-Source Price Data** - Yahoo Finance (primary), Alpha Vantage, and CoinGecko fallbacks
- **Live Gold & Silver Prices** - Real-time market data updated every 30 minutes
- **Smart Caching** - Efficient price caching to minimize API calls
- **Bullion Tracking** - Track weight, purity, and calculate melt value
- **Multi-Currency Support** - USD and South African Rand (ZAR) with live exchange rates
- **Automatic Value Calculation** - Live pricing for precious metal investments
- **Purity Tracking** - Track percentage purity (e.g., 99.9% for fine gold/silver)
- **Weight in Grams** - Precise weight tracking for accurate value calculation

### 🌍 **Geographic Features**
- **Interactive World Map** - Visualize your collection by country
- **Missing Countries Tracker** - Discover new territories to collect
- **Regional Analytics** - Breakdown by continent and region
- **Collection Highlights** - Top countries by item count and value
- **Automatic Region Detection** - Automatic region assignment based on country
- **Historical Items Tracking** - Identify items from historical entities or pre-1900

### 📊 **Advanced Analytics**
- **Dashboard Overview** - Key metrics and collection insights at a glance
- **Value Tracking** - Total collection value with live updates
- **Regional Breakdown** - Geographic distribution analysis
- **Historical Data** - Track collection growth over time
- **Item Statistics** - Counts by type, country, and region
- **Collection Metrics** - Total items, unique countries, total value

### 🔗 **Sharing & Collaboration**
- **Public Collection Links** - Generate unique, shareable UUID-based links
- **Secure Sharing** - Share read-only views of your collection
- **Insurance Documentation** - Generate shareable links for insurance purposes
- **Collection Export** - Download your data in JSON format
- **Public Collection Views** - Browse collections via public links
- **Link Management** - Generate, view, and revoke public collection links

### 🎨 **User Experience**
- **Dark Mode Interface** - Modern, professional dark theme design
- **Intuitive Navigation** - Organized sidebar with logical feature grouping
- **Quick Actions** - Fast access to common tasks
- **Responsive Design** - Optimized for desktop, tablet, and mobile
- **SPA Routing** - Clean URLs with client-side routing
- **Modal Interfaces** - User-friendly modals for forms and interactions
- **Real-time Updates** - Live data updates without page refresh

---

## 🚀 **Latest Features**

### **Social & Community Features** (Latest)
- **Follow System** - Follow other collectors and build your network
- **User Profiles** - Customizable profiles with usernames, display names, and bios
- **Public Collections** - Share your collection with the community
- **Comments** - Engage with other collectors through comments
- **User Comparison** - Compare collections side-by-side with other users
- **Follower/Following Lists** - See who follows you and who you follow

### **Collection Management Enhancements** (Latest)
- **Duplicate Detection** - Automatically identify duplicate items in your collection
- **Smart Merging** - Merge duplicates while preserving all data and notes
- **Favorites System** - Mark your most prized items for quick access
- **Quantity Tracking** - Track multiple copies of the same item
- **Enhanced Search** - Improved filtering and search capabilities

### **Numista Integration** (Latest)
- **Official API Integration** - Direct access to Numista's catalog via API
- **Rich Data Import** - Import detailed coin/banknote information automatically
- **Image Integration** - High-quality images from Numista catalog
- **Wishlist Enhancement** - Add items directly from Numista search results

### **Professional Email System**
- Welcome emails for new users
- Password reset functionality via Resend API
- Security notifications for account changes
- Professional HTML email templates with CoinShelf branding
- Free tier: 3,000 emails/month (Resend)

### **Enhanced Price System**
- **Multi-Source Pricing** - Yahoo Finance (primary), Alpha Vantage, CoinGecko
- **Smart Caching** - 30-minute cache to reduce API calls
- **Automatic Fallbacks** - Never returns empty results
- **Live Exchange Rates** - Real-time USD/ZAR conversion
- **No API Key Required** - Works with Yahoo Finance out of the box

### **Enhanced Security**
- Encrypted password storage with Werkzeug
- Secure token-based JWT authentication
- Rate limiting on API endpoints
- Password reset tokens with expiration (1 hour)
- One-time use tokens for security

---

![image](https://github.com/user-attachments/assets/d669fe04-a35a-4e27-a50b-6da10ecaf199)
![image](https://github.com/user-attachments/assets/43ab234c-d53f-4dc1-81a0-eb4aeb9c2ff7)
![image](https://github.com/user-attachments/assets/be1d1373-40c9-48a4-ba0d-4d10664eaf8c)
![image](https://github.com/user-attachments/assets/f14d22f1-7c49-4645-82d4-821ddf2e0a12)
![image](https://github.com/user-attachments/assets/2df655f9-124f-49ed-8622-e5df48ac09ff)
![image](https://github.com/user-attachments/assets/046f9880-c3ea-4dc4-84b1-dec8199f6d60)

---

## 📝 **Technical Notes**

- ✅ **Full Authentication System** - Secure user accounts with password recovery
- ✅ **Professional Email Integration** - Resend-powered email system (3,000 emails/month free)
- ✅ **Live Market Data** - Multi-source real-time precious metal prices with caching
- ✅ **Numista API Integration** - Official API integration for coin/banknote search
- ✅ **Social Features** - Follow system, comments, user profiles, and collection comparison
- ✅ **Duplicate Management** - Automatic detection and smart merging of duplicate items
- ✅ **Responsive Design** - Works on all devices (desktop, tablet, mobile)
- ✅ **Rate Limiting** - API protection with configurable limits
- ✅ **Database Migrations** - Automatic schema migrations for new features
- ⚠️ **Image Storage** - Currently using placeholder images; Numista images available via API

---

## 📥 **Mass Import Format**

When using mass import, use the following format:

```json
[
  {
    "id": 1,
    "region": "Africa",
    "type": "Banknote",
    "country": "South Africa",
    "year": null,
    "denomination": "R10",
    "isHistorical": false,
    "value": 0.56,
    "quantity": 1,
    "notes": "New R10",
    "referenceUrl": "https://www.ebay.com/itm/374489892395?...",
    "localImagePath": "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"
  },
  {
    "id": 2,
    "region": "Africa",
    "type": "Gold Bullion",
    "country": "South Africa",
    "year": 2023,
    "denomination": "1 oz Gold Bar",
    "isHistorical": false,
    "value": 2300.00,
    "quantity": 1,
    "weight_grams": 31.1035,
    "purity_percent": 99.9,
    "notes": "Krugerrand Gold Bar",
    "referenceUrl": "https://example.com",
    "localImagePath": "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"
  }
]
```

**New Fields for Bullion:**
- `weight_grams` - Weight in grams
- `purity_percent` - Purity percentage (e.g., 99.9 for 99.9% pure)
- `quantity` - Number of items (defaults to 1)

---

## 👨‍💻 **About the Creator**

**Oscar Brimelow** - A passionate developer and collector who understands the unique needs of the numismatic community. CoinShelf was born from a desire to create a modern, user-friendly platform that combines traditional collection management with cutting-edge technology.

**Follow on Instagram:** [@oscarbrimelow](https://www.instagram.com/oscarbrimelow/)

---

## 🛠️ **Technology Stack**

- **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS
- **Backend:** Python Flask, SQLAlchemy
- **Database:** PostgreSQL (Supabase)
- **Email:** Resend API (primary), Gmail SMTP (fallback)
- **Authentication:** JWT tokens (Flask-JWT-Extended)
- **Rate Limiting:** Flask-Limiter
- **CORS:** Flask-CORS for cross-origin requests
- **Price APIs:** Yahoo Finance, Alpha Vantage, CoinGecko
- **Coin Catalog:** Numista API (official integration)
- **Web Scraping:** Cloudscraper (for Cloudflare-protected sites)
- **Charts:** Chart.js, Google Charts
- **Deployment:** Render (Backend), Netlify (Frontend)

---

## 🔧 **Setup Instructions**

### Environment Variables

Create a `.env` file in the `backend/` directory (or set environment variables) with the following:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
DATABASE_URL=postgresql://user:password@host:port/database

# Email Configuration (Resend - Recommended)
RESEND_API_KEY=your-resend-api-key-here
RESEND_FROM_EMAIL=noreply@mycoinshelf.com

# Alternative: Gmail SMTP (Fallback)
# SMTP_EMAIL=your-email@gmail.com
# SMTP_PASSWORD=your-app-password-here
# SMTP_FROM_EMAIL=noreply@mycoinshelf.com

# Numista API Credentials (Optional - for coin search feature)
# Get your API key from: https://en.numista.com/api/
NUMISTA_API_KEY=your-numista-api-key-here
NUMISTA_CLIENT_ID=your-numista-client-id-here

# Alpha Vantage API (Optional - for enhanced price data)
# Get your API key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key-here

# CORS Configuration (Optional)
CORS_ALLOWED_ORIGINS=https://mycoinshelf.com,https://www.mycoinshelf.com
```

**Important:** Never commit your `.env` file or API keys to version control! The `.gitignore` file is configured to exclude `.env` files.

### Installing Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Run the Flask server
python app.py
```

---

## 📚 **Additional Documentation**

- **[Password Reset Setup Guide](PASSWORD_RESET_SETUP.md)** - Complete guide for setting up email-based password recovery
- **[Price Setup Guide](PRICE_SETUP_GUIDE.md)** - Detailed instructions for configuring multi-source price data

---

## 🔌 **API Endpoints Overview**

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/forgot_password` - Request password reset
- `POST /api/reset_password` - Reset password with token
- `POST /api/change_password` - Change password (authenticated)
- `POST /api/set_username` - Set username (authenticated)

### User Profiles & Social
- `GET /api/profile` - Get current user profile
- `PUT /api/profile` - Update user profile
- `GET /api/users/search` - Search users by username
- `GET /api/users/<username>` - Get public user profile
- `POST /api/users/<username>/follow` - Follow/unfollow user
- `GET /api/users/<username>/followers` - Get user's followers
- `GET /api/users/<username>/following` - Get users following
- `GET /api/users/compare` - Compare collections between users
- `POST /api/comments` - Add comment to collection
- `GET /api/comments` - Get comments for collection

### Collection Management
- `GET /api/coins` - Get user's collection
- `POST /api/coins` - Add new item to collection
- `PUT /api/coins/<id>` - Update collection item
- `DELETE /api/coins/<id>` - Delete collection item
- `POST /api/coins/<id>/toggle-favorite` - Toggle favorite status
- `POST /api/coins/bulk_upload` - Bulk import items
- `DELETE /api/coins/clear_all` - Clear all items
- `GET /api/coins/duplicates` - Find duplicate items
- `POST /api/coins/merge` - Merge duplicate items

### Wishlist
- `GET /api/wishlist` - Get wishlist items
- `POST /api/wishlist` - Add item to wishlist
- `DELETE /api/wishlist/<id>` - Remove wishlist item
- `POST /api/wishlist/<id>/move-to-collection` - Move to collection

### Numista Integration
- `GET /api/search-numista` - Search Numista catalog
- `GET /api/test-numista` - Test Numista API connection

### Price Data
- `GET /api/prices/metals` - Get live gold/silver prices

### Public Collections
- `POST /api/generate_public_collection_link` - Generate shareable link
- `GET /api/public_collection_link` - Get current public link
- `POST /api/revoke_public_collection_link` - Revoke public link
- `GET /api/public_coins/<public_id>` - View public collection

---

*CoinShelf - Where passion meets technology in the world of numismatics* 🪙✨
