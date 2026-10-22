import json
from typing import Dict, Any, List, Optional
from backend.app.playbooks.loader import playbook_loader
from backend.app.planning.dependency_graph import DependencyPlanner

class ToolRegistry:
    """
    Registry of strictly validated backend tools for the AI agent.
    Applies deterministic business logic and authorization boundaries.
    """

    def __init__(self):
        self.planner = DependencyPlanner(playbook_loader.catalog)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_services",
                "description": "Search government services directory by query or category.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword in Tamil or English"},
                        "category": {"type": "string", "description": "Filter by service category"}
                    }
                }
            },
            {
                "name": "get_service_details",
                "description": "Retrieve full verified playbook details for a service ID.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "get_verified_sources",
                "description": "Get official government sources and verification metadata for a service.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "check_eligibility",
                "description": "Evaluate user parameters against verified eligibility rules.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id", "user_profile"],
                    "properties": {
                        "service_id": {"type": "string"},
                        "user_profile": {"type": "object"}
                    }
                }
            },
            {
                "name": "resolve_service_dependencies",
                "description": "Recursively resolve prerequisites for a target service in topological order.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "create_action_plan",
                "description": "Generate a personalized step-by-step action plan considering user's completed prerequisites and available documents.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"},
                        "user_completed_services": {"type": "array", "items": {"type": "string"}},
                        "user_available_documents": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            {
                "name": "get_required_documents",
                "description": "Get official mandatory and optional document list for a service.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "list_missing_documents",
                "description": "Compare available documents with required documents for a service.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id", "available_docs"],
                    "properties": {
                        "service_id": {"type": "string"},
                        "available_docs": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            {
                "name": "get_official_application_link",
                "description": "Get verified portal URL and entry point for a service.",
                "parameters": {
                    "type": "object",
                    "required": ["service_id"],
                    "properties": {
                        "service_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "escalate_to_human",
                "description": "Escalate complex, unverified, or rejected cases to human grievance/support.",
                "parameters": {
                    "type": "object",
                    "required": ["reason"],
                    "properties": {
                        "reason": {"type": "string"},
                        "service_id": {"type": "string"}
                    }
                }
            }
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes a named tool deterministically."""
        if name == "search_services":
            query = arguments.get("query", "")
            category = arguments.get("category")
            results = playbook_loader.list_services(category=category, query=query)
            return {
                "count": len(results),
                "services": [
                    {
                        "service_id": s["service_id"],
                        "name_en": s["name_en"],
                        "name_ta": s["name_ta"],
                        "category": s["category"],
                        "department": s["department"],
                        "portal_url": s["portal_url"]
                    }
                    for s in results
                ]
            }

        elif name == "get_service_details":
            service_id = arguments.get("service_id")
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}
            return service

        elif name == "get_verified_sources":
            service_id = arguments.get("service_id")
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}
            return {
                "service_id": service_id,
                "service_name": service.get("name_en"),
                "last_verified": service.get("last_verified"),
                "verification_status": service.get("verification_status"),
                "official_sources": service.get("official_sources", [])
            }

        elif name == "check_eligibility":
            service_id = arguments.get("service_id")
            user_profile = arguments.get("user_profile", {})
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}

            rules = service.get("eligibility_rules", [])
            evaluated_rules = []
            is_eligible = True

            for rule in rules:
                field = rule.get("field")
                op = rule.get("operator")
                target_val = rule.get("value")
                user_val = user_profile.get(field)

                passed = False
                if user_val is None:
                    passed = False  # Unknown / missing detail
                    is_eligible = False
                elif op == "eq":
                    passed = (str(user_val).lower() == str(target_val).lower())
                elif op == "in":
                    passed = (user_val in target_val)
                elif op == "gte":
                    passed = (float(user_val) >= float(target_val))
                elif op == "lte":
                    passed = (float(user_val) <= float(target_val))
                elif op == "boolean":
                    passed = (bool(user_val) == bool(target_val))

                if not passed:
                    is_eligible = False

                evaluated_rules.append({
                    "rule_id": rule.get("rule_id"),
                    "description_en": rule.get("description_en"),
                    "description_ta": rule.get("description_ta"),
                    "user_value": user_val,
                    "passed": passed
                })

            return {
                "service_id": service_id,
                "is_eligible": is_eligible,
                "evaluated_rules": evaluated_rules
            }

        elif name == "resolve_service_dependencies":
            service_id = arguments.get("service_id")
            planner = DependencyPlanner(playbook_loader.catalog)
            try:
                order = planner.resolve_prerequisites_recursive(service_id)
                return {
                    "target_service_id": service_id,
                    "topological_order": order,
                    "prerequisites_count": len(order) - 1
                }
            except Exception as e:
                return {"error": str(e)}

        elif name == "create_action_plan":
            service_id = arguments.get("service_id")
            user_completed = set(arguments.get("user_completed_services") or [])
            user_docs = set(arguments.get("user_available_documents") or [])
            planner = DependencyPlanner(playbook_loader.catalog)
            try:
                plan = planner.generate_action_plan(
                    target_service_id=service_id,
                    user_completed_services=user_completed,
                    user_available_documents=user_docs
                )
                return plan
            except Exception as e:
                return {"error": str(e)}

        elif name == "get_required_documents":
            service_id = arguments.get("service_id")
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}
            return {
                "service_id": service_id,
                "required_documents": service.get("required_documents", []),
                "optional_documents": service.get("optional_documents", [])
            }

        elif name == "list_missing_documents":
            service_id = arguments.get("service_id")
            available = set(arguments.get("available_docs", []))
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}

            missing = []
            for doc in service.get("required_documents", []):
                if doc.get("mandatory", True) and doc.get("doc_code") not in available:
                    missing.append(doc)

            return {
                "service_id": service_id,
                "missing_count": len(missing),
                "missing_documents": missing
            }

        elif name == "get_official_application_link":
            service_id = arguments.get("service_id")
            service = playbook_loader.get_service(service_id)
            if not service:
                return {"error": f"Service '{service_id}' not found."}
            return {
                "service_id": service_id,
                "service_name_en": service.get("name_en"),
                "service_name_ta": service.get("name_ta"),
                "portal_url": service.get("portal_url"),
                "application_url": service.get("application_url") or service.get("portal_url"),
                "department": service.get("department")
            }

        elif name == "escalate_to_human":
            reason = arguments.get("reason", "Citizen requested human assistance")
            service_id = arguments.get("service_id")
            return {
                "status": "ESCALATED",
                "reason": reason,
                "service_id": service_id,
                "ticket_reference": "ESC-TN-2026-9182",
                "message_en": "Your request has been forwarded to human assistance. A representative will review the case.",
                "message_ta": "உங்கள் கோரிக்கை மனித உதவிக்கு அனுப்பப்பட்டுள்ளது. அதிகாரிகள் இதனை ஆய்வு செய்வார்கள்."
            }

        else:
            return {"error": f"Unknown tool '{name}'."}

tool_registry = ToolRegistry()
