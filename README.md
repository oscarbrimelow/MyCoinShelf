# 🪙 Coin Collection Showcase Website

A web app to proudly display your coin and banknote collection – made for collectors, by someone who had no clue what they were doing (thanks Gemini!) 😄

---

## ✨ Features

- 📱 **Mobile support**
- 🧹 **Mass Delete** – does exactly what it sounds like
- 📥 **Mass Import** – easily upload all your coins and notes in bulk
- 🔍 **Searchable Collection** – quickly find any item
- 🌍 **World Map View** – see where your collection spans across the globe
- 📊 **Pie Chart by Region** – visual breakdown of items per region
- 💰 **Value by Region** – track how much your collection is worth geographically
- 🏆 **Collection Highlights** – top 5 countries by item count
- 📅 **Sort** – by **Year**, **Country**, or **Price**
- 📌 **Track Missing Coins** – see which countries you're missing

### 🧾 Detailed Stats

- Total items (coins and notes)  
- Total value of collection  
- Number of unique countries  
- Remaining countries to collect  

### 🔍 Filters

- By Region  
- By Coin or Banknote  

### ➕ Add Items

- Add items one-by-one

---

## 📝 Notes

- ⚠️ **Local images aren't available yet** – placeholder images are shown for now.
- ⚠️ **No real login system** – username/password are just for your local session.  
  If you forget your password… tough luck 😅  
  But you can always just start fresh with a new login!

---

## 📥 Mass Import Format

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
    "notes": "New R10",
    "referenceUrl": "https://www.ebay.com/itm/374489892395?...",
    "localImagePath": "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"
  },
  {
    "id": 2,
    "region": "Africa",
    "type": "Coin",
    "country": "Eswatini",
    "year": 2005,
    "denomination": "10 cents",
    "isHistorical": false,
    "value": 1,
    "notes": "",
    "referenceUrl": "https://www.ebay.com/itm/277133143998?...",
    "localImagePath": "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"
  }
]
To continue adding more items, place a comma , after each object.

To end the list, close it with a ].
