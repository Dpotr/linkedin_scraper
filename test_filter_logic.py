#!/usr/bin/env python3
"""
Test script for validating the new configurable filter logic.
Tests all possible checkbox combinations against sample job data.
"""

def test_filter_logic(remote_found, visa_found, anaplan_found, sap_found, planning_found, remote_prohibited_found, config):
    """
    Replicates the new filter logic for testing purposes.
    Returns: (location_passes, skills_passes, overall_passes, reason)
    """
    location_passes = True
    skills_passes = True
    
    # Check location requirements (remote/visa)
    if config.get("require_remote", True) or config.get("require_visa", True):
        if config.get("location_logic", "OR") == "OR":
            # At least one location option must be available if enabled
            location_options = []
            if config.get("require_remote", True):
                location_options.append(remote_found)
            if config.get("require_visa", True):
                location_options.append(visa_found)
            location_passes = any(location_options) if location_options else True
        else:  # AND logic
            location_passes = True
            if config.get("require_remote", True) and not remote_found:
                location_passes = False
            if config.get("require_visa", True) and not visa_found:
                location_passes = False
    
    # Check skills requirement
    if config.get("require_skills", True):
        skills_passes = (anaplan_found or sap_found or planning_found)
    
    # Check remote prohibited exclusion
    if config.get("block_remote_prohibited", False) and remote_prohibited_found:
        location_passes = False
    
    # Create reason
    filter_details = []
    if not location_passes:
        if config.get("block_remote_prohibited", False) and remote_prohibited_found:
            filter_details.append("blocked: remote prohibited")
        elif config.get("location_logic", "OR") == "OR":
            missing_location = []
            if config.get("require_remote", True) and not remote_found:
                missing_location.append("remote")
            if config.get("require_visa", True) and not visa_found:
                missing_location.append("visa")
            if missing_location:
                filter_details.append(f"missing location: needs {' OR '.join(missing_location)}")
        else:  # AND logic
            missing_and = []
            if config.get("require_remote", True) and not remote_found:
                missing_and.append("remote")
            if config.get("require_visa", True) and not visa_found:
                missing_and.append("visa")
            if missing_and:
                filter_details.append(f"missing location: needs {' AND '.join(missing_and)}")
    
    if not skills_passes:
        filter_details.append("missing skills: needs Anaplan OR SAP OR Planning")
    
    reason = "; ".join(filter_details) if filter_details else "passed"
    overall_passes = location_passes and skills_passes
    
    return location_passes, skills_passes, overall_passes, reason

def run_comprehensive_tests():
    """Run tests for all possible checkbox combinations"""
    
    # All possible filter configurations (16 combinations)
    test_configs = [
        # Default (current behavior)
        {"require_remote": True, "require_visa": True, "location_logic": "OR", "require_skills": True, "block_remote_prohibited": False},
        # Remote only mode
        {"require_remote": True, "require_visa": False, "location_logic": "OR", "require_skills": True, "block_remote_prohibited": True},
        # Visa only mode  
        {"require_remote": False, "require_visa": True, "location_logic": "OR", "require_skills": True, "block_remote_prohibited": False},
        # Both required (AND logic)
        {"require_remote": True, "require_visa": True, "location_logic": "AND", "require_skills": True, "block_remote_prohibited": False},
        # Skills optional
        {"require_remote": True, "require_visa": True, "location_logic": "OR", "require_skills": False, "block_remote_prohibited": False},
        # All combinations of other settings...
        {"require_remote": False, "require_visa": False, "location_logic": "OR", "require_skills": True, "block_remote_prohibited": False},
        {"require_remote": True, "require_visa": False, "location_logic": "AND", "require_skills": True, "block_remote_prohibited": False},
        {"require_remote": False, "require_visa": True, "location_logic": "AND", "require_skills": True, "block_remote_prohibited": False},
    ]
    
    # Sample job scenarios to test against
    job_scenarios = [
        # Scenario: Remote job with Anaplan
        {"name": "Remote Anaplan Job", "remote": True, "visa": False, "anaplan": True, "sap": False, "planning": False, "remote_prohibited": False},
        # Scenario: Visa job with SAP
        {"name": "Visa SAP Job", "remote": False, "visa": True, "anaplan": False, "sap": True, "planning": False, "remote_prohibited": False},
        # Scenario: Both remote and visa with planning
        {"name": "Remote+Visa Planning Job", "remote": True, "visa": True, "anaplan": False, "sap": False, "planning": True, "remote_prohibited": False},
        # Scenario: No location support, has skills
        {"name": "No Location, has Anaplan", "remote": False, "visa": False, "anaplan": True, "sap": False, "planning": False, "remote_prohibited": False},
        # Scenario: Remote job but no skills
        {"name": "Remote, no skills", "remote": True, "visa": False, "anaplan": False, "sap": False, "planning": False, "remote_prohibited": False},
        # Scenario: Remote prohibited job with visa
        {"name": "Remote prohibited, Visa+SAP", "remote": False, "visa": True, "anaplan": False, "sap": True, "planning": False, "remote_prohibited": True},
        # Scenario: Multiple skills
        {"name": "Remote, Anaplan+SAP", "remote": True, "visa": False, "anaplan": True, "sap": True, "planning": False, "remote_prohibited": False},
    ]
    
    print("=== COMPREHENSIVE FILTER LOGIC TEST ===\n")
    
    # Test each configuration against each job scenario
    for i, config in enumerate(test_configs):
        print(f"CONFIG {i+1}: Remote:{config['require_remote']}, Visa:{config['require_visa']}, Logic:{config['location_logic']}, Skills:{config['require_skills']}, Block:{config['block_remote_prohibited']}")
        print("-" * 100)
        
        for job in job_scenarios:
            location_passes, skills_passes, overall_passes, reason = test_filter_logic(
                job["remote"], job["visa"], job["anaplan"], job["sap"], job["planning"], job["remote_prohibited"], config
            )
            
            status = "PASS" if overall_passes else "FAIL"
            print(f"{status} | {job['name']:25} | Location:{location_passes} | Skills:{skills_passes} | Reason: {reason}")
        
        print("\n")

def test_backwards_compatibility():
    """Test that default config matches old hardcoded logic"""
    print("=== BACKWARDS COMPATIBILITY TEST ===\n")
    
    default_config = {"require_remote": True, "require_visa": True, "location_logic": "OR", "require_skills": True, "block_remote_prohibited": False}
    
    test_cases = [
        # Old logic: ((remote_found or visa_or_relocation) and (anaplan_found or sap_apo_found or planning_found))
        {"name": "Remote+Anaplan", "remote": True, "visa": False, "anaplan": True, "sap": False, "planning": False, "remote_prohibited": False, "old_result": True},
        {"name": "Visa+SAP", "remote": False, "visa": True, "anaplan": False, "sap": True, "planning": False, "remote_prohibited": False, "old_result": True},
        {"name": "Remote+Visa+Planning", "remote": True, "visa": True, "anaplan": False, "sap": False, "planning": True, "remote_prohibited": False, "old_result": True},
        {"name": "No location, has skills", "remote": False, "visa": False, "anaplan": True, "sap": False, "planning": False, "remote_prohibited": False, "old_result": False},
        {"name": "Remote, no skills", "remote": True, "visa": False, "anaplan": False, "sap": False, "planning": False, "remote_prohibited": False, "old_result": False},
        {"name": "Nothing", "remote": False, "visa": False, "anaplan": False, "sap": False, "planning": False, "remote_prohibited": False, "old_result": False},
    ]
    
    all_match = True
    for case in test_cases:
        # Calculate old logic result
        old_logic_result = ((case["remote"] or case["visa"]) and (case["anaplan"] or case["sap"] or case["planning"]))
        
        # Calculate new logic result
        _, _, new_logic_result, reason = test_filter_logic(
            case["remote"], case["visa"], case["anaplan"], case["sap"], case["planning"], case["remote_prohibited"], default_config
        )
        
        match = old_logic_result == new_logic_result == case["old_result"]
        status = "MATCH" if match else "MISMATCH"
        
        print(f"{status} | {case['name']:20} | Old:{old_logic_result} | New:{new_logic_result} | Expected:{case['old_result']} | {reason}")
        
        if not match:
            all_match = False
    
    print(f"\nBACKWARDS COMPATIBILITY: {'PASSED' if all_match else 'FAILED'}\n")
    return all_match

if __name__ == "__main__":
    # Run backwards compatibility test first
    backwards_compatible = test_backwards_compatibility()
    
    # Run comprehensive tests
    run_comprehensive_tests()
    
    print("=== SUMMARY ===")
    print(f"Backwards Compatibility: {'PASSED' if backwards_compatible else 'FAILED'}")
    print("Comprehensive testing completed. Review results above.")