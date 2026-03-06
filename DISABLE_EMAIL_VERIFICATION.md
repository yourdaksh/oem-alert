# Disable Email Verification in Supabase

## Quick Steps

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Sign in if needed

2. **Select Your Project**
   - Click on your project: `mxuavhvnwvuwycnzpcgo`

3. **Navigate to Authentication Settings**
   - In the left sidebar, click **Authentication**
   - Then click **Settings** (or go directly to: Authentication → Settings)

4. **Disable Email Confirmations**
   - Scroll down to the **Email Auth** section
   - Find the toggle/checkbox for **"Enable email confirmations"**
   - **Uncheck** or **Turn OFF** this option

5. **Save Changes**
   - Click the **Save** button at the bottom of the page

6. **Verify**
   - You should see a success message
   - The setting should now show as disabled

## What This Does

- Users can sign up and login immediately without email verification
- No need to check email for verification links
- Perfect for development and testing
- You can re-enable it later for production

## After Disabling

1. Restart your Streamlit app (if running)
2. Try signing up with a new account
3. You should be able to login immediately after signup

## Alternative: Using Supabase CLI (Advanced)

If you have Supabase CLI installed:
```bash
supabase projects update --project-ref mxuavhvnwvuwycnzpcgo
```

But the dashboard method is much easier!
