import pytest
from backend.app.playbooks.loader import PlaybookLoader
from backend.app.planning.dependency_graph import DependencyPlanner, DependencyCycleError, ServiceNotFoundError

def test_playbooks_load_and_validate():
    loader = PlaybookLoader()
    assert len(loader.catalog) >= 5
    
    # Check all candidate services are present
    expected_services = [
        "community_certificate",
        "income_certificate",
        "nativity_certificate",
        "first_graduate_certificate",
        "post_matric_scholarship"
    ]
    for s_id in expected_services:
        service = loader.get_service(s_id)
        assert service is not None, f"Service {s_id} should be present"
        assert service["service_id"] == s_id
        assert service["name_en"]
        assert service["name_ta"]
        assert service["verification_status"] == "NEEDS_VERIFICATION"
        assert service["verified_by"] == "PENDING_OFFICIAL_VERIFICATION"

def test_dependency_resolution_post_matric_scholarship():
    loader = PlaybookLoader()
    planner = DependencyPlanner(loader.catalog)
    
    order = planner.resolve_prerequisites_recursive("post_matric_scholarship")
    
    # Prerequisites must appear BEFORE the target service
    assert "community_certificate" in order
    assert "income_certificate" in order
    assert "nativity_certificate" in order
    assert order[-1] == "post_matric_scholarship"
    
    # Ensure all prerequisites come before post_matric_scholarship
    target_idx = order.index("post_matric_scholarship")
    assert order.index("community_certificate") < target_idx
    assert order.index("income_certificate") < target_idx
    assert order.index("nativity_certificate") < target_idx

def test_first_graduate_dependencies():
    loader = PlaybookLoader()
    planner = DependencyPlanner(loader.catalog)
    
    order = planner.resolve_prerequisites_recursive("first_graduate_certificate")
    assert order == ["nativity_certificate", "first_graduate_certificate"]

def test_action_plan_generation_with_completed_prerequisites():
    loader = PlaybookLoader()
    planner = DependencyPlanner(loader.catalog)
    
    # User already has community_certificate and nativity_certificate
    completed = {"community_certificate", "nativity_certificate"}
    available_docs = {"photo", "address_proof", "income_proof", "self_declaration"}
    
    plan = planner.generate_action_plan(
        target_service_id="post_matric_scholarship",
        user_completed_services=completed,
        user_available_documents=available_docs
    )
    
    assert plan["target_service_id"] == "post_matric_scholarship"
    assert plan["total_prerequisite_services"] == 3
    # Only income_certificate and post_matric_scholarship are pending
    assert plan["pending_services_count"] == 2
    step_ids = [s["service_id"] for s in plan["plan_steps"]]
    assert step_ids == ["income_certificate", "post_matric_scholarship"]

def test_cycle_detection():
    # Construct catalog with circular dependency: A -> B -> C -> A
    fake_catalog = {
        "srv_a": {"dependencies": ["srv_b"], "name_en": "A"},
        "srv_b": {"dependencies": ["srv_c"], "name_en": "B"},
        "srv_c": {"dependencies": ["srv_a"], "name_en": "C"}
    }
    planner = DependencyPlanner(fake_catalog)
    with pytest.raises(DependencyCycleError) as exc_info:
        planner.resolve_prerequisites_recursive("srv_a")
    assert "Circular dependency detected" in str(exc_info.value)

def test_service_search_bilingual():
    loader = PlaybookLoader()
    
    # Search in Tamil
    tamil_results = loader.list_services(query="சாதி")
    assert len(tamil_results) >= 1
    assert tamil_results[0]["service_id"] == "community_certificate"
    
    # Search in English
    eng_results = loader.list_services(query="scholarship")
    assert len(eng_results) >= 1
    assert any(s["service_id"] == "post_matric_scholarship" for s in eng_results)
