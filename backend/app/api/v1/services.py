from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.app.playbooks.loader import playbook_loader
from backend.app.planning.dependency_graph import DependencyPlanner
from backend.app.schemas.service import ServiceListItem, EligibilityCheckRequest, ActionPlanRequest
from backend.app.tools.registry import tool_registry

router = APIRouter(prefix="/services", tags=["Government Services Discovery"])

@router.get("", response_model=List[ServiceListItem])
async def list_services(
    query: Optional[str] = Query(None, description="Search query in Tamil or English"),
    category: Optional[str] = Query(None, description="Category filter"),
    department: Optional[str] = Query(None, description="Department filter")
):
    results = playbook_loader.list_services(category=category, department=department, query=query)
    return results

@router.get("/{service_id}")
async def get_service_details(service_id: str):
    service = playbook_loader.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")
    return service

@router.get("/{service_id}/sources")
async def get_service_sources(service_id: str):
    res = tool_registry.execute_tool("get_verified_sources", {"service_id": service_id})
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/check-eligibility")
async def check_eligibility(req: EligibilityCheckRequest):
    res = tool_registry.execute_tool("check_eligibility", {
        "service_id": req.service_id,
        "user_profile": req.user_profile
    })
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/{service_id}/dependencies")
async def resolve_dependencies(service_id: str):
    planner = DependencyPlanner(playbook_loader.catalog)
    try:
        order = planner.resolve_prerequisites_recursive(service_id)
        return {
            "target_service_id": service_id,
            "topological_order": order,
            "prerequisites": [s for s in order if s != service_id]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/action-plan")
async def generate_action_plan(req: ActionPlanRequest):
    planner = DependencyPlanner(playbook_loader.catalog)
    try:
        plan = planner.generate_action_plan(
            target_service_id=req.target_service_id,
            user_completed_services=set(req.user_completed_services or []),
            user_available_documents=set(req.user_available_documents or [])
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
