# 🪙 CoinShelf - Professional Coin & Bullion Collection Manager

A comprehensive web application for coin collectors, numismatists, and precious metal investors to organize, track, and value their collections with live market data.

**Live Site:** https://mycoinshelf.com

---

## ✨ Features

### 🔐 **Authentication & Security**
- **Secure User Registration & Login** - Full authentication system with encrypted passwords
- **Password Reset System** - Professional email-based password recovery
- **Account Management** - Change passwords, manage preferences
- **Session Management** - Secure JWT-based authentication

### 📱 **Core Collection Management**
- **Mobile-Responsive Design** - Works perfectly on all devices
- **Add Items Individually** - Detailed forms for coins, banknotes, and bullion
- **Bulk Import/Export** - Mass upload and download of collection data
- **Advanced Search & Filtering** - Find items quickly by type, country, year, value
- **Collection Analytics** - Comprehensive statistics and insights

### 🪙 **Bullion & Precious Metals**
- **Live Gold & Silver Prices** - Real-time market data from multiple sources
- **Bullion Tracking** - Track weight, purity, and calculate melt value
- **Multi-Currency Support** - USD and South African Rand (ZAR)
- **Automatic Value Calculation** - Live pricing for precious metal investments

### 🌍 **Geographic Features**
- **Interactive World Map** - Visualize your collection by country
- **Missing Countries Tracker** - Discover new territories to collect
- **Regional Analytics** - Breakdown by continent and region
- **Collection Highlights** - Top countries by item count and value

### 📊 **Advanced Analytics**
- **Dashboard Overview** - Key metrics and collection insights
- **Value Tracking** - Total collection value with live updates
- **Regional Breakdown** - Geographic distribution analysis
- **Historical Data** - Track collection growth over time

### 🔗 **Sharing & Collaboration**
- **Public Collection Links** - Share read-only views of your collection
- **Secure Sharing** - Generate unique URLs for insurance or showcasing
- **Collection Export** - Download your data in JSON format

### 🎨 **User Experience**
- **Dark Mode Interface** - Modern, professional design
- **Intuitive Navigation** - Organized sidebar with logical flow
- **Quick Actions** - Fast access to common tasks
- **Responsive Design** - Optimized for desktop, tablet, and mobile

---

## 🚀 **What's New**

### **Professional Email System**
- Welcome emails for new users
- Password reset functionality
- Security notifications for account changes
- Professional branding with CoinShelf styling

### **Enhanced Security**
- Encrypted password storage
- Secure token-based authentication
- Account activity notifications
- Professional password management

### **Bullion Portfolio Management**
- Live precious metal pricing
- Weight and purity tracking
- Automatic value calculations
- Multi-currency support

### **Improved Organization**
- Reorganized sidebar navigation
- Better data management tools
- Enhanced user interface
- Logical feature grouping

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
- ✅ **Professional Email Integration** - Resend-powered email system
- ✅ **Live Market Data** - Real-time precious metal prices
- ✅ **Responsive Design** - Works on all devices
- ⚠️ **Local images aren't available yet** – placeholder images are shown for now

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
- **Email:** Resend API
- **Authentication:** JWT tokens
- **Charts:** Chart.js, Google Charts
- **Deployment:** Render (Backend and Frontend)

---

## 🔧 **Setup Instructions**

### Environment Variables

Create a `.env` file in the `backend/` directory (or set environment variables) with the following:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
DATABASE_URL=sqlite:///database.db

# Numista API Credentials (Optional - for coin search feature)
# Get your API key from: https://en.numista.com/api/
NUMISTA_API_KEY=your-numista-api-key-here
NUMISTA_CLIENT_ID=your-numista-client-id-here
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

*CoinShelf - Where passion meets technology in the world of numismatics* 🪙✨
