from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import Client
import stripe
import os

from backend.dependencies import get_supabase
from backend.models_pydantic import UserLogin, AuthResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


class SetupAccountRequest(BaseModel):
    email: EmailStr
    password: str
    organizationName: str
    stripeSessionId: str


def _verify_stripe_session(session_id: str, expected_email: str, expected_org: str) -> dict:
    """Confirm a Stripe Checkout session is paid and matches the claimed email/org."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured on the server")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe session: {e}")

    payment_status = getattr(session, "payment_status", None)
    if payment_status != "paid":
        raise HTTPException(status_code=402, detail="Payment has not been completed")

    details = getattr(session, "customer_details", None) or {}
    details_email = getattr(details, "email", None) if hasattr(details, "email") else (
        details.get("email") if isinstance(details, dict) else None
    )
    session_email = (getattr(session, "customer_email", None) or details_email or "").lower()
    if session_email and session_email != expected_email.lower():
        raise HTTPException(status_code=403, detail="Email does not match the checkout session")

    raw_metadata = getattr(session, "metadata", None)
    # StripeObject for metadata does not support .get() or dict() in SDK 15+;
    # .to_dict() produces a plain dict we can use like any other.
    if raw_metadata is None:
        metadata = {}
    elif hasattr(raw_metadata, "to_dict"):
        metadata = raw_metadata.to_dict()
    else:
        metadata = dict(raw_metadata)

    session_org = metadata.get("organization_name")
    if session_org and session_org.strip().lower() != expected_org.strip().lower():
        raise HTTPException(status_code=403, detail="Organization does not match the checkout session")

    return {
        "customer_id": getattr(session, "customer", None),
        "oems": metadata.get("oems", ""),
    }


@router.post("/setup-account")
async def setup_account(data: SetupAccountRequest,
                        supabase: Client = Depends(get_supabase)):
    """Post-payment account provisioning.

    The flow is: Stripe session verified → Supabase Auth sign-up →
    organization upserted → users row linked with Owner role. If the
    organization already exists (e.g. webhook fired first) we attach to it
    instead of creating a duplicate.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    stripe_info = _verify_stripe_session(
        data.stripeSessionId, data.email, data.organizationName
    )

    try:
        auth_res = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
        if not auth_res.user:
            raise HTTPException(status_code=400, detail="Signup failed")
        user_id = auth_res.user.id
    except HTTPException:
        raise
    except Exception as e:
        # If a prior attempt created the auth user but failed mid-provisioning,
        # fall back to sign-in so the caller can complete onboarding idempotently.
        msg = str(e).lower()
        if "already" in msg or "registered" in msg:
            try:
                signin = supabase.auth.sign_in_with_password({
                    "email": data.email,
                    "password": data.password,
                })
                auth_res = signin
                user_id = signin.user.id
            except Exception as ie:
                raise HTTPException(status_code=400, detail=f"Account exists with a different password: {ie}")
        else:
            raise HTTPException(status_code=400, detail=f"Auth signup failed: {e}")

    try:
        existing_org = supabase.table("organizations").select("id").eq(
            "name", data.organizationName
        ).execute()

        if existing_org.data:
            org_id = existing_org.data[0]["id"]
            supabase.table("organizations").update({
                "subscription_status": "active",
                "stripe_customer_id": stripe_info["customer_id"],
                "enabled_oems": stripe_info["oems"],
            }).eq("id", org_id).execute()
        else:
            org_res = supabase.table("organizations").insert({
                "name": data.organizationName,
                "subscription_status": "active",
                "stripe_customer_id": stripe_info["customer_id"],
                "enabled_oems": stripe_info["oems"],
            }).execute()
            if not org_res.data:
                raise HTTPException(status_code=500, detail="Failed to create organization")
            org_id = org_res.data[0]["id"]

        supabase.table("users").upsert({
            "id": user_id,
            "email": data.email,
            "organization_id": org_id,
            "role": "Owner",
        }).execute()

        session = auth_res.session
        return {
            "status": "success",
            "user": {
                "id": user_id,
                "email": data.email,
                "organization_id": org_id,
                "role": "Owner",
            },
            "access_token": session.access_token if session else None,
            "refresh_token": session.refresh_token if session else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {e}")


@router.post("/login", response_model=AuthResponse)
async def login(data: UserLogin, supabase: Client = Depends(get_supabase)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    try:
        res = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })

        user_db = supabase.table("users").select(
            "role, organization_id"
        ).eq("id", res.user.id).execute()
        user_data = user_db.data[0] if user_db.data else {}

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "organization_id": user_data.get("organization_id"),
                "role": user_data.get("role", "Member"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {e}")


@router.get("/invitation/{token}")
async def get_invitation(token: str, supabase: Client = Depends(get_supabase)):
    """Public endpoint used by the accept-invite page to pre-fill org/role/email."""
    res = supabase.table("invitations").select(
        "id, email, organization_id, role, status, expires_at"
    ).eq("token", token).eq("status", "Pending").execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")

    invite = res.data[0]
    org = supabase.table("organizations").select("name").eq(
        "id", invite["organization_id"]
    ).execute()
    return {
        "email": invite["email"],
        "role": invite["role"],
        "organization_name": org.data[0]["name"] if org.data else None,
        "expires_at": invite["expires_at"],
    }


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str
    full_name: str | None = None


@router.post("/accept-invitation")
async def accept_invitation(data: AcceptInvitationRequest,
                            supabase: Client = Depends(get_supabase)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    res = supabase.table("invitations").select("*").eq(
        "token", data.token
    ).eq("status", "Pending").execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")

    invite = res.data[0]

    try:
        auth_res = supabase.auth.sign_up({
            "email": invite["email"],
            "password": data.password,
        })
        if not auth_res.user:
            raise HTTPException(status_code=400, detail="Signup failed")
        user_id = auth_res.user.id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Auth signup failed: {e}")

    supabase.table("users").upsert({
        "id": user_id,
        "email": invite["email"],
        "full_name": data.full_name,
        "organization_id": invite["organization_id"],
        "role": invite["role"],
    }).execute()

    supabase.table("invitations").update({"status": "Accepted"}).eq(
        "id", invite["id"]
    ).execute()

    session = auth_res.session
    return {
        "status": "success",
        "user": {
            "id": user_id,
            "email": invite["email"],
            "organization_id": invite["organization_id"],
            "role": invite["role"],
        },
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
    }
