# Password Reset Setup Guide

## 🚀 **Option 1: Resend (Recommended - Permanent Free)**

### **Step 1: Create Resend Account**
1. Go to [resend.com](https://resend.com)
2. Click "Get Started for Free"
3. Sign up with your email (no credit card required)
4. Verify your email address

### **Step 2: Get API Key**
1. Go to API Keys section
2. Click "Create API Key"
3. Name it "CoinShelf Password Reset"
4. Copy the API key

### **Step 3: Set Environment Variables**
Add these to your Render environment variables:

```
RESEND_API_KEY=your_api_key_here
RESEND_FROM_EMAIL=noreply@mycoinshelf.com
```

### **Step 4: Verify Domain (Optional)**
1. Go to Domains section
2. Add your domain for better deliverability
3. Or use the default Resend domain

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

## 📊 **Resend Free Tier Limits**
- 3,000 emails/month
- **Permanent free tier** - no expiration
- No credit card required
- Perfect for most small to medium applications

---

## 🔒 **Security Features**
- Tokens expire after 1 hour
- Tokens can only be used once
- No information disclosure about email existence
- Secure token generation using UUID4
- Password validation (minimum 6 characters) 