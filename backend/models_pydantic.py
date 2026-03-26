from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    organization_name: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict

class OrganizationOut(BaseModel):
    id: str
    name: str
    stripe_customer_id: Optional[str]
    subscription_status: str
    enabled_oems: str
    created_at: datetime

class VulnerabilityOut(BaseModel):
    id: str
    unique_id: str
    product_name: str
    product_version: Optional[str]
    oem_name: str
    severity_level: str
    vulnerability_description: str
    mitigation_strategy: Optional[str]
    published_date: datetime
    source_url: Optional[str]
    cvss_score: Optional[str]
    affected_versions: Optional[str]
    created_at: datetime

class TaskCreate(BaseModel):
    vulnerability_id: str
    assigned_to_id: str
    resolution_notes: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    
class TaskOut(BaseModel):
    id: str
    vulnerability_id: str
    organization_id: str
    status: str
    assigned_to_id: Optional[str]
    assigned_by_id: Optional[str]
    resolution_notes: Optional[str]
    assigned_at: datetime
    updated_at: datetime
