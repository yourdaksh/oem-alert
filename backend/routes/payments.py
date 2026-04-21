from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import stripe
import os
import uuid
from supabase import Client
from backend.dependencies import get_supabase, get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class OnboardingRequest(BaseModel):
    organizationName: str
    email: str
    selectedOems: list[str]

@router.post("/onboarding-checkout")
async def create_onboarding_checkout(
    request: OnboardingRequest,
    supabase: Client = Depends(get_supabase),
):
    """Create a guest checkout session strictly from the Next.js Onboarding wizard.

    Before charging, reject the request if this email is already linked to an
    active organization — the caller should finish signing up with the existing
    paid org instead of paying again. This is the main defense against
    double-charging users who paid but abandoned the setup step.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured in .env")

    if supabase:
        try:
            # If a user record already exists for this email, redirect them to sign-in
            existing_user = supabase.table("users").select(
                "id, organization_id"
            ).eq("email", request.email).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=409,
                    detail="An account with this email already exists. Please sign in instead.",
                )
            # If an active paid org exists with this name, the user paid already —
            # they just never completed setup. Route them back through /login to
            # finish the setup step with their existing session_id, not a new one.
            existing_org = supabase.table("organizations").select(
                "id, name, subscription_status"
            ).eq("name", request.organizationName).eq(
                "subscription_status", "active"
            ).execute()
            if existing_org.data:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "This organization has already been paid for. Check the "
                        "email used at checkout for your setup link, or contact "
                        "support if you need it resent."
                    ),
                )
        except HTTPException:
            raise
        except Exception:
            # Don't block checkout on an unrelated DB hiccup — the setup step
            # still verifies the Stripe session before provisioning anything.
            pass

    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    temp_org_id = str(uuid.uuid4())
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'OEM Alert Platform - PRO Plan',
                        'description': f'Enterprise monitoring for {", ".join(request.selectedOems[:3])} and more.',
                    },
                    'unit_amount': 49900, # $499.00 annual
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_creation='always',
            success_url=f"{frontend_url}/login?onboarded=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/onboarding",
            customer_email=request.email,
            client_reference_id=temp_org_id,
            metadata={
                "organization_name": request.organizationName,
                "oems": ",".join(request.selectedOems)
            }
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session-status/{session_id}")
async def get_session_status(session_id: str):
    """Read-only probe used by the onboarding page to recover abandoned setups.

    If the browser has a persisted session_id from a prior successful payment,
    we check Stripe here to decide whether to nudge the user back to /login to
    finish setup — versus charging them again.
    """
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {e}")

    raw_metadata = getattr(session, "metadata", None)
    metadata = raw_metadata.to_dict() if raw_metadata is not None and hasattr(raw_metadata, "to_dict") else (dict(raw_metadata) if raw_metadata else {})

    return {
        "id": session.id,
        "payment_status": getattr(session, "payment_status", None),  # "paid" | "unpaid" | "no_payment_required"
        "customer_email": getattr(session, "customer_email", None),
        "organization_name": metadata.get("organization_name"),
    }


@router.post("/create-checkout-session")
async def create_checkout_session(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Create a Stripe checkout session for the user's organization."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
        
    user_db = supabase.table("users").select("organization_id, email").eq("id", user.id).execute()
    if not user_db.data:
        raise HTTPException(status_code=404, detail="User organization not found")
        
    org_id = user_db.data[0]["organization_id"]
    customer_email = user_db.data[0]["email"]
    
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'OEM Alert Platform - PRO Plan',
                        'description': 'Full access to 24+ vulnerability scrapers and CRM.',
                    },
                    'unit_amount': 29900, # $299.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{frontend_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/pricing",
            customer_email=customer_email,
            client_reference_id=org_id,
        )
        
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, supabase: Client = Depends(get_supabase)):
    """Handle incoming Stripe webhooks (e.g. successful payment)."""
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        return {"status": "Webhook secret not configured, skipping validation."}
        
    signature = request.headers.get("stripe-signature")
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_id = session.get("customer")
        metadata = session.get("metadata") or {}
        org_name = metadata.get("organization_name", "Unknown Org")
        oems = metadata.get("oems", "")

        try:
            existing_org = supabase.table("organizations").select("id").eq("name", org_name).execute()

            payload = {
                "subscription_status": "active",
                "stripe_customer_id": customer_id,
                "enabled_oems": oems,
            }
            if existing_org.data:
                supabase.table("organizations").update(payload).eq(
                    "id", existing_org.data[0]["id"]
                ).execute()
            else:
                supabase.table("organizations").insert({"name": org_name, **payload}).execute()

        except Exception as e:
            print(f"Webhook provisioning error: {str(e)}")

    return {"status": "success"}
