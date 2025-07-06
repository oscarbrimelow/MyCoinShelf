# Password Reset Setup Guide

## 🚀 **Option 1: SendGrid (Recommended)**

### **Step 1: Create SendGrid Account**
1. Go to [sendgrid.com](https://sendgrid.com)
2. Click "Start for Free"
3. Sign up with your email
4. Verify your email address

### **Step 2: Get API Key**
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Name it "CoinShelf Password Reset"
4. Choose "Restricted Access" → "Mail Send"
5. Copy the API key

### **Step 3: Set Environment Variables**
Add these to your Render environment variables:

```
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=noreply@mycoinshelf.com
```

### **Step 4: Verify Sender**
1. Go to Settings → Sender Authentication
2. Verify your domain or at least your sender email
3. This improves email delivery

---

## 📧 **Option 2: Gmail SMTP (Fallback)**

If you prefer to use Gmail as a fallback:

### **Step 1: Create App Password**
1. Go to your Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "CoinShelf"
4. Copy the 16-character password

### **Step 2: Set Environment Variables**
Add these to your Render environment variables:

```
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM_EMAIL=noreply@mycoinshelf.com
```

---

## 🔧 **Frontend Integration**

The backend now has these new endpoints:

- `POST /api/forgot_password` - Request password reset
- `POST /api/reset_password` - Reset password with token

### **Usage Example:**
```javascript
// Request password reset
fetch('/api/forgot_password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'user@example.com' })
});

// Reset password with token
fetch('/api/reset_password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        token: 'reset_token_from_email',
        new_password: 'new_password_here'
    })
});
```

---

## 🎯 **Benefits of This System**

✅ **Professional**: Uses SendGrid for reliable email delivery
✅ **Secure**: Tokens expire in 1 hour and can only be used once
✅ **User-friendly**: Beautiful HTML emails with clear instructions
✅ **Fallback**: Gmail SMTP as backup if SendGrid fails
✅ **Privacy**: Doesn't reveal if email exists or not

---

## 📊 **SendGrid Free Tier Limits**
- 100 emails/day
- 3,000 emails/month
- Perfect for most small to medium applications

---

## 🔒 **Security Features**
- Tokens expire after 1 hour
- Tokens can only be used once
- No information disclosure about email existence
- Secure token generation using UUID4
- Password validation (minimum 6 characters) 