# Fixing Supabase Email Verification Issues

## Problem
When signing up, Supabase sends an email verification link that redirects to `localhost:3000` instead of `localhost:8501`, causing connection errors.

## Solutions

### Option 1: Disable Email Verification (Recommended for Development)

This is the easiest solution - users can login immediately after signup without email verification.

**Steps:**
1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **Authentication** → **Settings**
4. Scroll down to **Email Auth** section
5. **Uncheck** "Enable email confirmations"
6. Click **Save**

Now users can sign up and login immediately without email verification.

### Option 2: Configure Redirect URL in Supabase

If you want to keep email verification enabled, configure the correct redirect URL:

**Steps:**
1. Go to Supabase Dashboard → Your Project
2. Go to **Authentication** → **URL Configuration**
3. Set **Site URL** to: `http://localhost:8501`
4. Add **Redirect URLs**:
   - `http://localhost:8501`
   - `http://localhost:8501/**`
5. Click **Save**

Now email verification links will redirect to the correct URL.

### Option 3: Configure SMTP Settings (For Production)

If you want email verification to work properly:

1. Go to **Authentication** → **Settings** → **SMTP Settings**
2. Configure your SMTP server:
   - **SMTP Host**: Your SMTP server (e.g., `smtp.gmail.com`)
   - **SMTP Port**: 587
   - **SMTP User**: Your email
   - **SMTP Password**: Your email password or app password
   - **Sender Email**: Your email address
   - **Sender Name**: Your app name

3. Test the email configuration
4. Make sure **Enable email confirmations** is checked

## Current Configuration

The app is now configured to:
- Use `http://localhost:8501` as the redirect URL for email verification
- Handle both verified and unverified users
- Show appropriate messages based on verification status

## Testing

1. **With Email Verification Disabled:**
   - Sign up with any email
   - You should be able to login immediately

2. **With Email Verification Enabled:**
   - Sign up with any email
   - Check your email for verification link
   - Click the link (should redirect to `localhost:8501`)
   - Then login with your credentials

## Troubleshooting

**Issue: "Email link is invalid or has expired"**
- Email links expire after a certain time
- Disable email verification or configure SMTP properly
- Make sure redirect URL is configured correctly

**Issue: Redirects to wrong URL**
- Check Supabase Dashboard → Authentication → URL Configuration
- Make sure Site URL and Redirect URLs are set to `http://localhost:8501`

**Issue: Can't login after signup**
- Check if email verification is required
- If yes, verify your email first
- If no, check Supabase authentication settings

## Quick Fix

For immediate use, **disable email verification** in Supabase:
1. Dashboard → Authentication → Settings
2. Uncheck "Enable email confirmations"
3. Save
4. Users can now login immediately after signup
