from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, deque

class DependencyCycleError(Exception):
    """Raised when a circular prerequisite dependency is detected."""
    pass

class ServiceNotFoundError(Exception):
    """Raised when a requested service ID does not exist in the catalog."""
    pass

class DependencyPlanner:
    """
    Deterministic Graph Planner for Government Services.
    Constructs a Directed Acyclic Graph (DAG) of service dependencies,
    detects cycles, computes topological ordering, and generates
    personalized step-by-step action plans.
    """

    def __init__(self, service_catalog: Dict[str, Dict[str, Any]]):
        """
        :param service_catalog: Mapping of service_id to service playbook dictionary.
        """
        self.catalog = service_catalog

    def resolve_prerequisites_recursive(self, target_service_id: str) -> List[str]:
        """
        Recursively resolves all prerequisites for a target service.
        Detects cycles using DFS with recursion stack tracking.
        Returns a list of service IDs in topological dependency order (prerequisites first).
        """
        if target_service_id not in self.catalog:
            raise ServiceNotFoundError(f"Service '{target_service_id}' not found in catalog.")

        # Build subgraph of all reachable nodes
        visited = set()
        rec_stack = set()
        resolved_order = []

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                cycle_str = " -> ".join(path + [node])
                raise DependencyCycleError(f"Circular dependency detected: {cycle_str}")
            if node in visited:
                return

            if node not in self.catalog:
                raise ServiceNotFoundError(f"Prerequisite service '{node}' referenced by '{path[-1]}' does not exist.")

            rec_stack.add(node)
            path.append(node)

            service_data = self.catalog[node]
            prerequisites = service_data.get("dependencies", [])

            for prereq in prerequisites:
                dfs(prereq, path)

            path.pop()
            rec_stack.remove(node)
            visited.add(node)
            resolved_order.append(node)

        dfs(target_service_id, [])
        return resolved_order

    def generate_action_plan(
        self,
        target_service_id: str,
        user_completed_services: Optional[Set[str]] = None,
        user_available_documents: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a personalized, deterministic action plan for a target service.
        Filters out already completed prerequisite services.
        Aggregates missing required documents.
        """
        user_completed = set(user_completed_services or [])
        user_docs = set(user_available_documents or [])

        full_order = self.resolve_prerequisites_recursive(target_service_id)

        # Plan steps to complete
        pending_service_ids = [s_id for s_id in full_order if s_id not in user_completed]

        plan_steps = []
        all_required_documents = []
        missing_documents = []
        total_estimated_fee = 0.0
        total_working_days = 0

        for idx, s_id in enumerate(pending_service_ids, start=1):
            s_data = self.catalog[s_id]
            is_target = (s_id == target_service_id)

            fee_info = s_data.get("fee", {})
            fee_amount = float(fee_info.get("amount_inr", 0.0))
            total_estimated_fee += fee_amount

            proc_info = s_data.get("processing_time", {})
            days = int(proc_info.get("working_days", 0))
            # Sequential turnaround estimate
            total_working_days += days

            # Document requirements for this step
            req_docs = s_data.get("required_documents", [])
            step_missing_docs = []

            for doc in req_docs:
                doc_code = doc.get("doc_code")
                doc_item = {
                    "service_id": s_id,
                    "service_name_en": s_data.get("name_en"),
                    "service_name_ta": s_data.get("name_ta"),
                    "doc_code": doc_code,
                    "name_en": doc.get("name_en"),
                    "name_ta": doc.get("name_ta"),
                    "mandatory": doc.get("mandatory", True)
                }
                all_required_documents.append(doc_item)
                if doc_code not in user_docs and doc.get("mandatory", True):
                    step_missing_docs.append(doc_item)
                    missing_documents.append(doc_item)

            plan_steps.append({
                "step_order": idx,
                "service_id": s_id,
                "is_target_service": is_target,
                "service_name_en": s_data.get("name_en"),
                "service_name_ta": s_data.get("name_ta"),
                "department": s_data.get("department"),
                "portal_url": s_data.get("portal_url"),
                "fee_inr": fee_amount,
                "processing_days": days,
                "required_documents_count": len(req_docs),
                "missing_documents_count": len(step_missing_docs),
                "application_steps": s_data.get("application_steps", []),
                "official_sources": s_data.get("official_sources", [])
            })

        return {
            "target_service_id": target_service_id,
            "target_service_name_en": self.catalog[target_service_id].get("name_en"),
            "target_service_name_ta": self.catalog[target_service_id].get("name_ta"),
            "total_prerequisite_services": len(full_order) - 1,
            "pending_services_count": len(pending_service_ids),
            "plan_steps": plan_steps,
            "total_estimated_fee_inr": total_estimated_fee,
            "total_estimated_working_days": total_working_days,
            "all_required_documents": all_required_documents,
            "missing_documents": missing_documents,
            "is_ready_for_target": (len(pending_service_ids) == 1 and len(missing_documents) == 0)
        }
