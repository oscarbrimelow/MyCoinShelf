-- Enable Row Level Security (RLS) on all public tables
-- This prevents unauthorized access via PostgREST/Supabase REST API
-- 
-- IMPORTANT: Before running this script, ensure your Flask app uses a database connection
-- that bypasses RLS. In Supabase, this means using the "service_role" connection string
-- (found in Settings > Database > Connection string > Service role)
--
-- If your Flask app uses a regular user connection, RLS will block it too!
-- Check your DATABASE_URL environment variable - it should contain "service_role" in the password

-- Enable RLS on all tables
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE coin ENABLE ROW LEVEL SECURITY;
ALTER TABLE public_collection ENABLE ROW LEVEL SECURITY;
ALTER TABLE bullion ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_reset_token ENABLE ROW LEVEL SECURITY;
ALTER TABLE wishlist_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow ENABLE ROW LEVEL SECURITY;
ALTER TABLE comment ENABLE ROW LEVEL SECURITY;

-- Note: When RLS is enabled with NO policies, it blocks ALL access (including PostgREST)
-- Since your Flask app uses service_role (which bypasses RLS), this is safe.
-- PostgREST uses 'anon' and 'authenticated' roles, which will be blocked by RLS.
--
-- If you want to be extra explicit, you can create deny policies, but it's not necessary
-- because RLS with no policies = deny all by default

