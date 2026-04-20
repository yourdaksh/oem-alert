# Supabase Platform Setup

One-time configuration to do in the Supabase dashboard for [mxuavhvnwvuwycnzpcgo.supabase.co](https://mxuavhvnwvuwycnzpcgo.supabase.co). Everything else is handled by code.

---

## 1. Disable RLS on backend-owned tables

The FastAPI backend uses the service-role key and enforces tenancy in the API layer. Leaving RLS on with no policies silently blocks inserts. Open the **SQL Editor** and run:

```sql
alter table organizations disable row level security;
alter table users          disable row level security;
alter table invitations    disable row level security;
alter table vulnerabilities disable row level security;
alter table tasks          disable row level security;
alter table audit_logs     disable row level security;
alter table scan_logs      disable row level security;
alter table subscriptions  disable row level security;
```

> I already ran this against your DB during QA — kept here for reference if you ever rebuild the DB.

## 2. Add missing columns (already done for your DB)

The `vulnerabilities` and `scan_logs` tables were missing `organization_id`. Run this only if you rebuild from scratch:

```sql
alter table vulnerabilities add column if not exists organization_id uuid references organizations(id);
alter table scan_logs        add column if not exists organization_id uuid references organizations(id);
```

## 3. Authentication → Settings

Go to **Authentication → Providers → Email** and verify:

- **Confirm email**: **turn OFF** for the current flow.
  The onboarding and invite flows call `sign_up` and expect a session back immediately. If "Confirm email" is ON, the session is `null` until the user clicks the verification email, and invite acceptance will hang. If you want email confirmation later, we'll need to rework the invite-accept UX to show "check your email" instead of auto-login.

- **Secure email change** / **Secure password change**: up to you; both are fine with the current code.

## 4. Authentication → URL Configuration

Add your production URLs so Supabase allows redirects back to them:

- **Site URL**: `https://<your-vercel-domain>` (e.g. `https://oem-alert.vercel.app`)
- **Redirect URLs** (one per line):
  ```
  http://localhost:3000/**
  https://<your-vercel-domain>/**
  ```

This matters for password-reset and magic-link flows if you add them later.

## 5. Authentication → Rate limits (optional)

Defaults are fine. If you end up running load tests and hit limits, bump:
- **Sign-ups per hour**: default 30 is low for testing
- **Email sends per hour**: irrelevant if you've disabled "Confirm email"

## 6. Optional: auth.users → public.users trigger

Not required because the backend does `upsert` into `public.users` after sign-up. But if you ever want the row to exist immediately on any Supabase Auth signup (e.g. for OAuth), add:

```sql
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.users (id, email) values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

## 7. Storage / Edge Functions

Not used by this project. Skip.

## 8. Secret rotation checklist before go-live

The following secrets were pasted in chat during setup — **rotate them** before shipping:

- **Database password** (Settings → Database → Reset database password)
  Current password contains `$@%?` special chars — the new one will auto-propagate if you update `SUPABASE_DB_URL` everywhere.
- **Supabase service key** (Settings → API → Rotate `service_role` / secret key)
- **Stripe test keys** — fine to keep for dev. For prod, switch to `sk_live_...` + `pk_live_...`.

After rotation, update:
- Local `.env`
- `frontend/.env.local`
- Render → API service → environment
- Render → Dashboard service → environment
- Vercel → Project settings → Environment Variables
- Stripe Dashboard → Webhooks → endpoint URL (if API domain changed)
