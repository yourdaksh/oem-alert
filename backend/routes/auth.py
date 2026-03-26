from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from backend.dependencies import get_supabase
from backend.models_pydantic import UserLogin, UserRegister, AuthResponse
from database import get_db
from database.operations import DatabaseOperations
from database.models import User, Organization
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

from pydantic import BaseModel
class SetupAccountRequest(BaseModel):
    email: str
    password: str
    organizationName: str

@router.post("/setup-account")
async def setup_account(data: SetupAccountRequest, 
                        supabase: Client = Depends(get_supabase),
                        db: Session = Depends(get_db)):
    """Bridge endpoint to create user in both Supabase Auth and Supabase PostgreSQL after Stripe payment"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
        
    try:
        org_check = supabase.table("organizations").select("id").eq("name", data.organizationName).execute()
        if not org_check.data:
            org_res = supabase.table("organizations").insert({"name": data.organizationName}).execute()
            org_id_sb = org_res.data[0]["id"]
        else:
            org_id_sb = org_check.data[0]["id"]

        res = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })
        
        db_ops = DatabaseOperations(db)
        
        local_user = db_ops.get_user_by_email(data.email)
        
        if not local_user:
            local_org = db.query(Organization).filter(func.lower(Organization.name) == data.organizationName.lower()).first()
            if not local_org:
                local_org = db_ops.create_organization(data.organizationName)
            
            local_org_id = local_org.id if local_org else None
            
            db_ops.create_user(
                username=data.email,
                email=data.email,
                password=data.password,
                role="Owner",
                org_id=local_org_id
            )
        else:
            local_user.username = data.email 
            local_user.password_hash = db_ops._hash_password(data.password)
            db.commit()
        
        return {"status": "success", "message": "Account provisioned across all subsystems."}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register", response_model=AuthResponse)
async def register_organization(data: UserRegister, supabase: Client = Depends(get_supabase)):
    """Register a new organization and its owner"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
        
    try:
        res = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "full_name": data.full_name
                }
            }
        })
        
        user = res.user
        if not user:
            raise HTTPException(status_code=400, detail="Signup failed")
            
        org_res = supabase.table("organizations").insert({
            "name": data.organization_name
        }).execute()
        
        if not org_res.data:
            raise HTTPException(status_code=500, detail="Failed to create organization")
            
        org_id = org_res.data[0]["id"]
        
        supabase.table("users").update({
            "organization_id": org_id,
            "role": "Owner"
        }).eq("id", user.id).execute()
        
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "organization_id": org_id,
                "role": "Owner"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(data: UserLogin, supabase: Client = Depends(get_supabase)):
    """Authenticate a user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
        
    try:
        res = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
        
        user_db = supabase.table("users").select("role, organization_id").eq("id", res.user.id).execute()
        user_data = user_db.data[0] if user_db.data else {}
        
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "organization_id": user_data.get("organization_id"),
                "role": user_data.get("role", "Member")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")
