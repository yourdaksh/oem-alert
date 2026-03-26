from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from typing import List, Optional
from backend.dependencies import get_supabase, get_current_user
from backend.models_pydantic import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/tasks", tags=["Tasks & CRM"])

@router.post("/", response_model=TaskOut)
async def create_task(
    task: TaskCreate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Assign a vulnerability to a team member (CRM action)."""
    
    user_db = supabase.table("users").select("organization_id").eq("id", user.id).execute()
    if not user_db.data:
        raise HTTPException(status_code=403, detail="User not linked to an organization")
        
    org_id = user_db.data[0]["organization_id"]
    
    try:
        res = supabase.table("tasks").insert({
            "vulnerability_id": task.vulnerability_id,
            "organization_id": org_id,
            "assigned_to_id": task.assigned_to_id,
            "assigned_by_id": user.id,
            "resolution_notes": task.resolution_notes,
            "status": "Assigned"
        }).execute()
        
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    update: TaskUpdate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Update task status or notes."""
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
        
    res = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return res.data[0]


@router.get("/", response_model=List[TaskOut])
async def get_org_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Get all tasks for the current user's organization."""
    user_db = supabase.table("users").select("organization_id").eq("id", user.id).execute()
    org_id = user_db.data[0]["organization_id"]
    
    query = supabase.table("tasks").select("*").eq("organization_id", org_id)
    
    if status:
        query = query.eq("status", status)
    if assigned_to:
        query = query.eq("assigned_to_id", assigned_to)
        
    res = query.execute()
    return res.data
