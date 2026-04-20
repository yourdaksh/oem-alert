from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Optional

from backend.dependencies import get_supabase, get_current_user_with_org
from backend.models_pydantic import TaskCreate, TaskUpdate, TaskOut


router = APIRouter(prefix="/tasks", tags=["Tasks & CRM"])


@router.post("/", response_model=TaskOut)
async def create_task(
    task: TaskCreate,
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    """Assign a vulnerability to a team member (CRM action)."""
    assignee = supabase.table("users").select("organization_id").eq(
        "id", task.assigned_to_id
    ).execute()
    if not assignee.data or assignee.data[0]["organization_id"] != ctx["organization_id"]:
        raise HTTPException(status_code=403, detail="Assignee is not a member of your organization")

    try:
        res = supabase.table("tasks").insert({
            "vulnerability_id": task.vulnerability_id,
            "organization_id": ctx["organization_id"],
            "assigned_to_id": task.assigned_to_id,
            "assigned_by_id": ctx["id"],
            "resolution_notes": task.resolution_notes,
            "status": "Assigned",
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    update: TaskUpdate,
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    existing = supabase.table("tasks").select("organization_id").eq(
        "id", task_id
    ).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing.data[0]["organization_id"] != ctx["organization_id"]:
        raise HTTPException(status_code=403, detail="Cannot update tasks in another organization")

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    res = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
    return res.data[0]


@router.get("/", response_model=List[TaskOut])
async def get_org_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    ctx: dict = Depends(get_current_user_with_org),
    supabase: Client = Depends(get_supabase),
):
    query = supabase.table("tasks").select("*").eq(
        "organization_id", ctx["organization_id"]
    )
    if status:
        query = query.eq("status", status)
    if assigned_to:
        query = query.eq("assigned_to_id", assigned_to)

    res = query.execute()
    return res.data
