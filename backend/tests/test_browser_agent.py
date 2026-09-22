import pytest
from app.agent.browser import WebsiteApplicationAgent
from app.verification.store import evidence_store


def test_browser_agent_discover_and_mapping():
    evidence_store.clear()
    agent = WebsiteApplicationAgent()

    # Test normalization
    assert agent._normalize("Full Name") == "fullname"
    assert agent._normalize("Date-of_Birth") == "dateofbirth"

    # Test date formatting
    formatted = agent._format_date_for_field("17 February 2008", "MM-DD-YYYY")
    assert formatted == "02-17-2008"


def test_browser_agent_jotform_form_values():
    evidence_store.clear()
    agent = WebsiteApplicationAgent()

    # Live test against Jotform without final submission
    result = agent.run(
        url="https://form.jotform.com/262642652527056",
        field_values={
            "Full Name": "Ananya Rao",
            "Date of Birth": "17 February 2008",
        },
        submit=False,
    )

    assert result["status"] == "VERIFIED"
    assert result["reason"] == "FORM_VALUES_CONFIRMED"
    assert len(result["verification"]) >= 2

    # Check evidence records
    ev_types = [e["evidence_type"] for e in result["evidence"]]
    assert "WEBSITE_OPEN" in ev_types
    assert "FORM_DISCOVERY" in ev_types
    assert "FIELD_MAPPING" in ev_types
    assert "FORM_FILLING" in ev_types
    assert "FORM_VALUE_VERIFICATION" in ev_types


def test_browser_agent_security_guard_on_blocked_pages():
    evidence_store.clear()
    agent = WebsiteApplicationAgent()

    # Test authentication detection on Google accounts
    result = agent.run(
        url="https://accounts.google.com",
        field_values={"Full Name": "Test User"},
        submit=False,
    )

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "UNEXPECTED_AUTHENTICATION_PAGE"
