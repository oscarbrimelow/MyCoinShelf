# Reliable Gold/Silver Price Setup Guide

## Overview
I've created a multi-source price fetching system that tries multiple reliable APIs to get live gold and silver prices. This is much more reliable than the previous single API approach.

## How It Works

### 1. **Yahoo Finance (Primary - No API Key Required)**
- Uses Yahoo Finance's public API
- Gets gold futures (GC=F), silver futures (SI=F), and USD/ZAR exchange rate
- Very reliable and doesn't require API keys
- Updates every 30 minutes

### 2. **Alpha Vantage (Secondary - Free API Key)**
- Professional financial data API
- Free tier: 500 requests per day
- Get free API key at: https://www.alphavantage.co/support/#api-key
- More reliable than CoinGecko

### 3. **CoinGecko (Fallback)**
- Current fallback system
- Sometimes unreliable but good backup

## Setup Instructions

### Option 1: Yahoo Finance (Recommended - No Setup Required)
The system will automatically use Yahoo Finance as the primary source. No setup needed!

### Option 2: Alpha Vantage (More Reliable)
1. Go to https://www.alphavantage.co/support/#api-key
2. Sign up for a free account
3. Get your API key
4. Add to your environment variables:
   ```bash
   export ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```
5. Or add to your Render environment variables in the dashboard

### Option 3: Google Sheets with Google Finance (Most Reliable)
1. Create a Google Sheet
2. Add these formulas:
   - Cell A1: `=GOOGLEFINANCE("GCUSD")` (Gold price)
   - Cell A2: `=GOOGLEFINANCE("SIUSD")` (Silver price)  
   - Cell A3: `=GOOGLEFINANCE("CURRENCY:USDZAR")` (Exchange rate)
3. Get Google Sheets API key from Google Cloud Console
4. Set environment variables:
   ```bash
   export GOOGLE_SHEETS_API_KEY=your_api_key_here
   export GOOGLE_SHEET_ID=your_sheet_id_here
   ```

## Features

### ✅ **Multiple Fallback Sources**
- If one API fails, automatically tries the next
- Always returns prices (with fallback values if needed)

### ✅ **Smart Caching**
- Caches prices for 30 minutes to avoid API rate limits
- Saves to local file for persistence across server restarts

### ✅ **Currency Support**
- Automatically calculates both USD and ZAR prices
- Uses live exchange rates

### ✅ **Error Handling**
- Graceful degradation if APIs are down
- Detailed logging for debugging

## Testing the New System

1. **Deploy the updated backend** with the new `google_finance_prices.py` file
2. **Test the API endpoint**: `GET /api/prices/metals`
3. **Check the response** - it should show the source being used

## Expected Response Format
```json
{
  "gold_usd_per_oz": 2345.67,
  "silver_usd_per_oz": 28.45,
  "gold_zar_per_oz": 45678.90,
  "silver_zar_per_oz": 553.21,
  "timestamp": "2024-01-15T10:30:00.123456",
  "source": "reliable_apis",
  "lastUpdate": "2024-01-15T10:00:00.123456"
}
```

## Troubleshooting

### If prices aren't updating:
1. Check the backend logs for error messages
2. Verify API keys are set correctly (if using Alpha Vantage)
3. Check if the APIs are responding: test the URLs directly

### If you want to force a price update:
1. Delete the `cached_prices.json` file (if it exists)
2. Restart the backend server
3. Make a new request to `/api/prices/metals`

## Performance Benefits

- **Faster**: Cached prices load instantly
- **More Reliable**: Multiple fallback sources
- **Cost Effective**: Uses free APIs with smart rate limiting
- **Always Available**: Never returns empty results

## Next Steps

1. Deploy the updated backend code
2. Test the new price fetching system
3. Monitor the logs to see which source is being used
4. Optionally set up Alpha Vantage for even better reliability

The system will automatically start using the most reliable available source! 