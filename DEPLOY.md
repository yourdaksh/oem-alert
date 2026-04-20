# Deployment Guide

This is a 3-service app:

| Service                  | Stack             | Host    | Purpose                                              |
| ------------------------ | ----------------- | ------- | ---------------------------------------------------- |
| `oem-alert-frontend`     | Next.js 16        | Vercel  | Landing page, onboarding, login, invite acceptance   |
| `oem-alert-api`          | FastAPI / uvicorn | Render  | Auth, Stripe, invitations, org-scoped data           |
| `oem-alert-dashboard`    | Streamlit         | Render  | Authenticated analyst dashboard                      |
| `oem-alert-db`           | Postgres          | Supabase | Data + auth                                         |

All three compute services are in this repo. `render.yaml` defines the two Python services; Vercel auto-detects the Next.js project in `frontend/`.

---

## 1. Provision Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Settings → API → copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/publishable** key → `SUPABASE_ANON_KEY` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **service_role/secret** key → `SUPABASE_SERVICE_KEY`
3. Settings → Database → Connection string (URI) → `SUPABASE_DB_URL`. Avoid special chars in the password, or URL-encode them.
4. Tables are created automatically on first API boot via `database.init_database()`. If you prefer explicit migrations, run `python -c "from database import init_database; init_database()"` from a shell with the env set.

**Auth row trigger (recommended).** The backend `UPSERTs` into the `users` table after signup, which works without triggers. But if you also need the row to pre-exist (e.g. for RLS), add this trigger in the Supabase SQL editor:

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

## 2. Provision Stripe

1. Dashboard → Developers → API keys → copy:
   - **Secret key** → `STRIPE_SECRET_KEY`
   - **Publishable key** → `STRIPE_PUBLIC_KEY`
2. Dashboard → Developers → Webhooks → Add endpoint:
   - URL: `https://<your-api-host>/payments/webhook`
   - Events: `checkout.session.completed`
   - Copy the signing secret → `STRIPE_WEBHOOK_SECRET`

Pricing is currently hardcoded to `$499` in `backend/routes/payments.py` via an inline `price_data` block. If you want to move to a Stripe Price object, swap the `line_items` for `{"price": "price_xxx", "quantity": 1}`.

## 3. Deploy the API + Dashboard to Render

1. Push this repo to GitHub.
2. [render.com](https://render.com) → New → Blueprint → point at this repo.
3. Render reads `render.yaml` and proposes both services. Set env vars when prompted — see the table below.
4. After first deploy, note the public URLs:
   - API: `https://oem-alert-api.onrender.com`
   - Dashboard: `https://oem-alert-dashboard.onrender.com`

### Required env vars (API service)

| Variable                 | Value                                         |
| ------------------------ | --------------------------------------------- |
| `SUPABASE_URL`           | From step 1                                   |
| `SUPABASE_SERVICE_KEY`   | service_role secret (do NOT expose publicly)  |
| `SUPABASE_ANON_KEY`      | publishable / anon                            |
| `SUPABASE_KEY`           | same as anon (legacy name used in utils)      |
| `SUPABASE_DB_URL`        | Direct connection string                      |
| `STRIPE_SECRET_KEY`      | sk_live_... or sk_test_...                    |
| `STRIPE_WEBHOOK_SECRET`  | whsec_...                                     |
| `STRIPE_PUBLIC_KEY`      | pk_live_...                                   |
| `FRONTEND_URL`           | `https://<your-vercel-domain>`                |

The dashboard service needs the Supabase vars plus SMTP if you want email notifications.

## 4. Deploy the frontend to Vercel

1. [vercel.com/new](https://vercel.com/new) → import the repo.
2. **Root directory**: `frontend`.
3. Framework preset: Next.js (auto-detected).
4. Env vars:

| Variable                           | Value                                                    |
| ---------------------------------- | -------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`              | `https://oem-alert-api.onrender.com`                     |
| `NEXT_PUBLIC_SUPABASE_URL`         | Supabase project URL                                     |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`    | anon / publishable                                       |
| `NEXT_PUBLIC_DASHBOARD_URL`        | `https://oem-alert-dashboard.onrender.com` (optional)    |

5. Deploy → note the Vercel URL and set it as `FRONTEND_URL` on the Render API service so Stripe redirects to the right place.

## 5. Stripe test flow (end-to-end)

1. Visit `https://<vercel-domain>/onboarding` → fill out org + email → continue.
2. Select OEMs → "Proceed to Stripe Checkout".
3. Use test card `4242 4242 4242 4242`, any future expiry, any CVC.
4. You'll be redirected to `/login?onboarded=true&session_id=cs_test_...`
5. Enter a password (min 8 chars) → backend verifies the Stripe session, creates the Supabase user + org, assigns Owner role.
6. Sign in → lands in `/dashboard`.
7. Navigate to **Team** → invite a teammate → share the invite link → teammate lands on `/invite/<token>` to accept.

## 6. Post-deploy checklist

- [ ] Set `CORS_ALLOWED_ORIGINS` on the Render API service to your Vercel domain (comma-separated if you have multiple), e.g. `https://oem-alert.vercel.app`. Defaults to `http://localhost:3000,http://localhost:3001`.
- [ ] Point Stripe webhook at the Render API and confirm `checkout.session.completed` deliveries succeed.
- [ ] In Supabase → Auth → URL configuration, add your Vercel domain to "Site URL" and allowed redirects.
- [ ] Disable RLS on app tables that the FastAPI backend owns, since all writes go through service_role and auth is enforced at the API layer. One-time SQL in Supabase SQL editor:
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
  If you prefer to keep RLS on, add policies that allow `service_role` to bypass.
- [ ] Rotate any secret that was pasted in chat during setup.

## Local development quickstart

```bash
# API (Python 3.12)
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # fill in values
uvicorn backend.main:app --reload

# Dashboard (Streamlit)
streamlit run app.py

# Frontend (Next.js)
cd frontend
cp .env.example .env.local   # fill in values
npm install
npm run dev
```
