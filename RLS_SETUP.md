# Row Level Security (RLS) Setup Guide

## Why This Matters

Your security audit shows that **Row Level Security (RLS) is disabled** on 8 public tables. This is a **real security issue** if PostgREST is enabled in Supabase.

### The Problem

Supabase automatically exposes a REST API (PostgREST) for all tables in the `public` schema. Without RLS:
- Anyone who knows your Supabase project URL can access/modify data directly
- They can bypass all your Flask security (authentication, rate limiting, etc.)
- Sensitive tables like `password_reset_token` and `user` are exposed

### The Solution

Enable RLS on all tables. This blocks PostgREST access while allowing your Flask app to work normally.

## How to Apply

### Step 1: Verify Your Database Connection

**CRITICAL:** Your Flask app must use the **service_role** connection string, which bypasses RLS.

1. Go to Supabase Dashboard → Settings → Database
2. Find "Connection string" → Select "Service role" (not "URI" or "Session")
3. Your `DATABASE_URL` should look like:
   ```
   postgresql://postgres.[project-ref]:[service-role-password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
   The password should be the **service_role** password (starts with a long random string)

4. If you're using a regular user connection, switch to service_role before enabling RLS!

### Step 2: Run the SQL Script

1. Go to Supabase Dashboard → SQL Editor
2. Copy and paste the contents of `enable_rls.sql`
3. Click "Run" to execute

### Step 3: Verify It Works

1. Test your Flask app - everything should work normally
2. Try accessing PostgREST directly (should fail):
   ```
   https://[your-project-ref].supabase.co/rest/v1/user?select=*
   ```
   Should return: `{"message":"new row violates row-level security policy"}`

### Step 4: Verify Security Audit

Run your security audit again - all 8 RLS errors should be resolved.

## How It Works

- **RLS Enabled** = Blocks all access by default
- **Service Role Connection** = Bypasses RLS (your Flask app)
- **PostgREST** = Uses 'anon'/'authenticated' roles → Blocked by RLS ✅

## Troubleshooting

**Problem:** Flask app stops working after enabling RLS
- **Solution:** You're using a regular user connection. Switch to service_role connection string.

**Problem:** Still seeing RLS errors in security audit
- **Solution:** Make sure you ran the SQL script on all 8 tables listed in the audit.

**Problem:** Not sure which connection string you're using
- **Solution:** Check your `DATABASE_URL` environment variable. It should contain "service_role" in the password field.

## Alternative: Disable PostgREST

If you don't want to enable RLS, you can disable PostgREST entirely:
1. Supabase Dashboard → Settings → API
2. Disable "Enable REST API"
3. This is less secure than RLS (if you re-enable it later, tables are still exposed)

**Recommendation:** Enable RLS instead - it's the proper security solution.

