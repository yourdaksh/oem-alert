# 🚀 Supabase Integration Guide

This guide will help you set up Supabase for the Vulnerability Scrapper.

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:
- **PostgreSQL Database**: Production-ready PostgreSQL database
- **Authentication**: Built-in user authentication system
- **Real-time**: Real-time subscriptions to database changes
- **Storage**: File storage capabilities
- **API**: Auto-generated REST API

## Prerequisites

1. A Supabase account (sign up at [supabase.com](https://supabase.com))
2. A Supabase project created

## Setup Steps

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in your project details:
   - **Name**: Your project name (e.g., "vulnerability-scrapper")
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose the closest region to you
4. Wait for the project to be created (takes ~2 minutes)

### 2. Get Your Supabase Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`) - Keep this secret!

3. Go to **Settings** → **Database**
4. Find the **Connection string** section
5. Copy the **URI** connection string (it looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`)
   - Replace `[YOUR-PASSWORD]` with your actual database password

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```env
   # Database Configuration
   DATABASE_TYPE=supabase

   # Supabase Configuration
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=your-anon-key-here
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   SUPABASE_DB_URL=postgresql://postgres:your-password@db.xxxxx.supabase.co:5432/postgres
   ```

### 4. Install Dependencies

Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 5. Initialize Database

Run the database setup script to create all tables:
```bash
python3 setup_database.py
```

This will create the following tables in your Supabase database:
- `vulnerabilities`
- `subscriptions`
- `scan_logs`
- `notification_logs`

### 6. Enable Email Authentication (Optional)

If you want to use Supabase authentication:

1. Go to **Authentication** → **Providers** in your Supabase dashboard
2. Enable **Email** provider
3. Configure email templates if needed
4. Set up email service (SMTP) in **Settings** → **Auth** → **SMTP Settings**

### 7. Start the Application

```bash
streamlit run app.py
```

## Features Enabled with Supabase

### ✅ Database
- **PostgreSQL**: Production-ready database instead of SQLite
- **Scalability**: Handle large amounts of data
- **Backups**: Automatic backups (on paid plans)
- **Connection Pooling**: Better performance

### ✅ Authentication
- **User Sign Up**: Users can create accounts
- **Email/Password Login**: Secure authentication
- **Session Management**: Automatic session handling
- **Password Reset**: Built-in password reset flow

### ✅ Real-time (Future Enhancement)
- Subscribe to vulnerability updates in real-time
- Get instant notifications when new vulnerabilities are added

## Switching Back to SQLite

If you want to use SQLite instead:

1. Update `.env`:
   ```env
   DATABASE_TYPE=sqlite
   ```

2. Restart the application

## Troubleshooting

### Connection Issues

**Error: "connection refused"**
- Check that your `SUPABASE_DB_URL` is correct
- Verify your database password is correct
- Make sure your IP is allowed (check Supabase dashboard → Settings → Database → Connection Pooling)

**Error: "SSL required"**
- Supabase requires SSL connections. The code handles this automatically, but if you see this error, check your connection string includes SSL parameters.

### Authentication Issues

**Error: "Invalid API key"**
- Verify your `SUPABASE_KEY` is the anon/public key, not the service_role key
- Make sure there are no extra spaces in your `.env` file

**Error: "Email already registered"**
- The email is already in use. Try signing in instead of signing up.

### Database Schema Issues

**Tables not created**
- Make sure you ran `python3 setup_database.py`
- Check that your database user has CREATE TABLE permissions
- Verify the connection string is correct

## Security Best Practices

1. **Never commit `.env` file**: It contains sensitive credentials
2. **Use environment variables**: Keep secrets out of code
3. **Rotate keys regularly**: Update your Supabase keys periodically
4. **Use Row Level Security (RLS)**: Enable RLS policies in Supabase for additional security
5. **Service Role Key**: Only use service_role key server-side, never expose it to clients

## Migration from SQLite to Supabase

If you have existing data in SQLite:

1. Export data from SQLite:
   ```bash
   sqlite3 vulnerability_alerts.db .dump > backup.sql
   ```

2. Convert SQLite schema to PostgreSQL (manual conversion may be needed)

3. Import into Supabase using the Supabase SQL editor or pgAdmin

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

If you encounter issues:
1. Check the application logs
2. Review Supabase dashboard logs
3. Verify all environment variables are set correctly
4. Check Supabase status page for service issues
