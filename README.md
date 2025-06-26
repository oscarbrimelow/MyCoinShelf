# 🪙 Coin Collection Showcase Website

A web app to proudly display your coin and banknote collection – made for collectors, by someone who had no clue what they were doing 😄

https://mycoinshelf.com

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

![image](https://github.com/user-attachments/assets/d669fe04-a35a-4e27-a50b-6da10ecaf199)
![image](https://github.com/user-attachments/assets/43ab234c-d53f-4dc1-81a0-eb4aeb9c2ff7)
![image](https://github.com/user-attachments/assets/be1d1373-40c9-48a4-ba0d-4d10664eaf8c)
![image](https://github.com/user-attachments/assets/f14d22f1-7c49-4645-82d4-821ddf2e0a12)
![image](https://github.com/user-attachments/assets/2df655f9-124f-49ed-8622-e5df48ac09ff)
![image](https://github.com/user-attachments/assets/046f9880-c3ea-4dc4-84b1-dec8199f6d60)







## 📝 Notes

- ⚠️ **Demo Account** – user/pass = demo@demo/DEMO
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
