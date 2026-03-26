-- Supabase Postgres Schema for OEM Alert SaaS Platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- DROP EXISTING TABLES TO RESET SCHEMA PROPERLY (Reverse order of dependencies)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS scan_logs CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS vulnerabilities CASCADE;
DROP TABLE IF EXISTS invitations CASCADE;
DROP TABLE IF EXISTS "users" CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- 1. Organizations (Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(100),
    subscription_status VARCHAR(50) DEFAULT 'inactive', -- active, past_due, canceled
    enabled_oems TEXT DEFAULT 'ALL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Users (Mapps to Supabase Auth UUID)
-- We use public.users to store app-specific profile data linked to auth.users
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    role VARCHAR(50) DEFAULT 'Member', -- Owner, Team Lead, Member
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enforce organization isolation with Row Level Security (RLS)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- 3. Invitations
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'Member',
    token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Accepted, Expired
    invited_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Vulnerabilities
CREATE TABLE vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unique_id VARCHAR(100) NOT NULL, -- CVE or Vendor ID
    product_name VARCHAR(255) NOT NULL,
    product_version VARCHAR(255),
    oem_name VARCHAR(100) NOT NULL,
    severity_level VARCHAR(50) NOT NULL,
    vulnerability_description TEXT NOT NULL,
    mitigation_strategy TEXT,
    published_date TIMESTAMP WITH TIME ZONE NOT NULL,
    source_url TEXT,
    cvss_score VARCHAR(20),
    affected_versions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(unique_id, oem_name)
);

-- 5. CRM Assignments (Tasks)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vulnerability_id UUID REFERENCES vulnerabilities(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    status VARCHAR(50) DEFAULT 'Open', -- Open, Investigating, Mitigated, False Positive, Resolved
    assigned_to_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    assigned_by_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    resolution_notes TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(vulnerability_id, organization_id)
);

-- 6. Subscriptions (Email/Slack alerts)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    email VARCHAR(255),
    slack_webhook_url TEXT,
    
    oem_name VARCHAR(100), -- Null means all OEMs
    product_name VARCHAR(255), -- Null means all products
    severity_filter VARCHAR(255) DEFAULT 'Critical,High',
    
    is_active BOOLEAN DEFAULT TRUE,
    last_notified TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Audit & Scan Logs
CREATE TABLE scan_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    oem_name VARCHAR(100) NOT NULL,
    scan_type VARCHAR(50) NOT NULL, -- scheduled, manual
    status VARCHAR(50) NOT NULL, -- success, error
    vulnerabilities_found INTEGER DEFAULT 0,
    new_vulnerabilities INTEGER DEFAULT 0,
    error_message TEXT,
    scan_duration INTEGER,
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    
    action VARCHAR(100) NOT NULL, -- status_change, assignment
    old_value TEXT,
    new_value TEXT,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Functions and Triggers for updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_tasks_modtime ON tasks;
CREATE TRIGGER update_tasks_modtime
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE PROCEDURE update_modified_column();

-- Note on Supabase Auth Setup:
-- Users should be created via Supabase Auth signup.
-- A trigger should insert a row into public.users automatically:
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
