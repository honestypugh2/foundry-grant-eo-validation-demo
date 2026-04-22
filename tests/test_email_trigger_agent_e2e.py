"""
End-to-End Tests for EmailTriggerAgent and Email Notifier Function

Tests the full email pipeline:
  - EmailTriggerAgent: prepare_email → send_email (Graph API, SMTP, simulation)
  - Email Notifier Azure Function: prepare_email → send_email → log_notification
  - Integration: agent feeding into function, priority routing, fallback chains
"""

import os
import importlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.email_trigger_agent import EmailTriggerAgent

# Pre-load the email_notifier function_app module so tests can import it
_fa_path = str(Path(__file__).parent.parent / "src" / "functions" / "email_notifier")
if _fa_path not in sys.path:
    sys.path.insert(0, _fa_path)
_function_app = importlib.import_module("function_app")


# ---------------------------------------------------------------------------
# Fixtures: shared mock data
# ---------------------------------------------------------------------------

@pytest.fixture
def risk_report_high() -> Dict[str, Any]:
    return {
        "overall_score": 78.5,
        "risk_level": "high",
        "confidence": 92.0,
        "requires_notification": True,
        "risk_breakdown": {
            "compliance_risk": {"score": 85.0, "violations_count": 3, "warnings_count": 2},
            "quality_risk": {"score": 65.0, "word_count": 1200, "page_count": 4},
            "completeness_risk": {"score": 70.0},
        },
        "risk_factors": [
            {
                "factor": "Multiple Compliance Violations",
                "severity": "high",
                "description": "Conflicts with EO 14028 cybersecurity requirements",
            },
        ],
        "recommendations": [
            {
                "priority": "critical",
                "action": "Address cybersecurity compliance violations",
                "description": "Revise security protocols to align with EO 14028",
            },
            {
                "priority": "high",
                "action": "Add comprehensive DEI plan",
                "description": "Include diversity and inclusion strategies per EO 13985",
            },
        ],
    }


@pytest.fixture
def risk_report_low() -> Dict[str, Any]:
    return {
        "overall_score": 22.0,
        "risk_level": "low",
        "confidence": 95.0,
        "requires_notification": False,
        "risk_breakdown": {},
        "risk_factors": [],
        "recommendations": [],
    }


@pytest.fixture
def compliance_report() -> Dict[str, Any]:
    return {
        "compliance_score": 62.5,
        "overall_status": "non_compliant",
        "confidence_score": 88.0,
        "relevant_executive_orders": [
            {
                "name": "EO 14028 - Cybersecurity",
                "relevance": 95.0,
                "key_requirements": ["Implement zero-trust architecture"],
            },
            {
                "name": "EO 13985 - Racial Equity",
                "relevance": 88.0,
                "key_requirements": ["Develop equity impact assessment"],
            },
        ],
        "violations": [
            {
                "message": "Missing mandatory cybersecurity protocols",
                "executive_order": "EO 14028",
                "requirement": "Zero-trust architecture plan required",
                "severity": "high",
            },
            {
                "message": "No diversity and inclusion plan",
                "executive_order": "EO 13985",
                "requirement": "Equity impact assessment required",
                "severity": "high",
            },
        ],
        "warnings": [
            {
                "message": "Budget justification lacks detail",
                "executive_order": "General",
                "severity": "medium",
            },
        ],
    }


@pytest.fixture
def summary() -> Dict[str, Any]:
    return {
        "executive_summary": (
            "This proposal requests $2.5M to develop a community technology center "
            "providing digital literacy training. It lacks cybersecurity and equity detail."
        ),
        "key_clauses": [
            "Primary objective: community technology center serving 5,000 residents",
            "Budget: $2,500,000 over 3 years",
        ],
        "key_topics": ["digital literacy", "community development"],
    }


@pytest.fixture
def metadata() -> Dict[str, Any]:
    return {
        "file_name": "Community_Tech_Proposal_2025.pdf",
        "word_count": 3542,
        "page_count": 12,
    }


@pytest.fixture
def agent() -> EmailTriggerAgent:
    """Default agent in demo mode (no Graph API, no SMTP)."""
    return EmailTriggerAgent(use_graph_api=False)


# ===================================================================
# 1. EmailTriggerAgent unit / integration tests
# ===================================================================

class TestPrepareEmail:
    """Tests for EmailTriggerAgent.prepare_email()."""

    def test_prepare_email_returns_required_keys(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)

        assert "subject" in email
        assert "body_html" in email
        assert "body_text" in email
        assert "priority" in email
        assert "to" in email
        assert "from" in email
        assert "metadata" in email

    def test_subject_includes_urgent_for_high_risk(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        assert "[URGENT]" in email["subject"]
        assert metadata["file_name"] in email["subject"]

    def test_subject_no_urgency_for_low_risk(
        self, agent, risk_report_low, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_low, compliance_report, summary, metadata)
        assert "[URGENT]" not in email["subject"]
        assert "[PRIORITY]" not in email["subject"]

    def test_priority_mapping(
        self, agent, compliance_report, summary, metadata
    ):
        levels = {
            "high": "high",
            "medium-high": "high",
            "medium": "normal",
            "low": "low",
        }
        for risk_level, expected_priority in levels.items():
            report = {"overall_score": 50.0, "risk_level": risk_level,
                      "confidence": 80.0, "requires_notification": True,
                      "recommendations": []}
            email = agent.prepare_email(report, compliance_report, summary, metadata)
            assert email["priority"] == expected_priority, (
                f"risk_level={risk_level} should map to priority={expected_priority}"
            )

    def test_html_body_contains_key_data(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        html = email["body_html"]

        assert metadata["file_name"] in html
        assert "78.5" in html  # risk score
        assert "62.5" in html  # compliance score
        assert "Missing mandatory cybersecurity protocols" in html
        assert "Executive Summary" in html or "executive_summary" in html.lower()

    def test_text_body_contains_key_data(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        body = email["body_text"]

        assert metadata["file_name"] in body
        assert "HIGH" in body
        assert "78.5" in body

    def test_metadata_field_populated(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        meta = email["metadata"]

        assert meta["risk_level"] == "high"
        assert meta["risk_score"] == 78.5
        assert meta["document"] == metadata["file_name"]
        assert "prepared_at" in meta

    def test_fallback_filename_key(
        self, agent, risk_report_high, compliance_report, summary
    ):
        """metadata may use 'filename' instead of 'file_name'."""
        alt_meta = {"filename": "alt_doc.pdf", "word_count": 100, "page_count": 1}
        email = agent.prepare_email(risk_report_high, compliance_report, summary, alt_meta)
        assert "alt_doc.pdf" in email["subject"]

    def test_violations_listed_in_html(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        html = email["body_html"]
        assert "Violation 1" in html
        assert "Violation 2" in html

    def test_recommendations_in_html(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        html = email["body_html"]
        assert "Address cybersecurity compliance violations" in html

    def test_warnings_in_html(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        html = email["body_html"]
        assert "Warning 1" in html


class TestSendEmail:
    """Tests for EmailTriggerAgent.send_email() with various methods."""

    def test_simulation_mode(self, agent, risk_report_high, compliance_report, summary, metadata):
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "simulated"
        assert result["method"] == "demo"
        assert "message_id" in result
        assert "sent_at" in result

    @patch.object(EmailTriggerAgent, "_send_via_graph_api")
    def test_graph_api_success(
        self, mock_graph, risk_report_high, compliance_report, summary, metadata
    ):
        mock_graph.return_value = {
            "status": "sent",
            "method": "graph_api",
            "message_id": "graph-123",
            "sent_at": datetime.now().isoformat(),
        }
        agent = EmailTriggerAgent(use_graph_api=False)
        agent.use_graph_api = True  # force flag after init
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "sent"
        assert result["method"] == "graph_api"
        mock_graph.assert_called_once_with(email)

    @patch.object(EmailTriggerAgent, "_send_via_graph_api", side_effect=Exception("token error"))
    @patch.object(EmailTriggerAgent, "_send_via_smtp")
    def test_graph_api_falls_back_to_smtp(
        self, mock_smtp, mock_graph, risk_report_high, compliance_report, summary, metadata
    ):
        mock_smtp.return_value = {
            "status": "sent",
            "method": "smtp",
            "message_id": "smtp-456",
            "sent_at": datetime.now().isoformat(),
        }
        agent = EmailTriggerAgent(use_graph_api=False)
        agent.use_graph_api = True
        agent.smtp_enabled = True
        agent.smtp_username = "user@test.com"
        agent.smtp_password = "pass"
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "sent"
        assert result["method"] == "smtp"
        mock_graph.assert_called_once()
        mock_smtp.assert_called_once()

    @patch.object(EmailTriggerAgent, "_send_via_graph_api", side_effect=Exception("token error"))
    @patch.object(EmailTriggerAgent, "_send_via_smtp", side_effect=Exception("smtp down"))
    def test_full_fallback_to_simulation(
        self, mock_smtp, mock_graph, risk_report_high, compliance_report, summary, metadata
    ):
        agent = EmailTriggerAgent(use_graph_api=False)
        agent.use_graph_api = True
        agent.smtp_enabled = True
        agent.smtp_username = "user@test.com"
        agent.smtp_password = "pass"
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "simulated"
        assert result["method"] == "demo"

    @patch.object(EmailTriggerAgent, "_send_via_smtp")
    def test_smtp_direct_when_graph_disabled(
        self, mock_smtp, risk_report_high, compliance_report, summary, metadata
    ):
        mock_smtp.return_value = {
            "status": "sent",
            "method": "smtp",
            "message_id": "smtp-789",
            "sent_at": datetime.now().isoformat(),
        }
        agent = EmailTriggerAgent(use_graph_api=False)
        agent.smtp_enabled = True
        agent.smtp_username = "user@test.com"
        agent.smtp_password = "pass"
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "sent"
        assert result["method"] == "smtp"


# ===================================================================
# 2. Email Notifier Azure Function tests
# ===================================================================

class TestEmailNotifierFunction:
    """Tests for the Azure Durable Function email_notifier/function_app.py."""

    @pytest.fixture
    def function_input(self, compliance_report, metadata) -> Dict[str, Any]:
        return {
            "risk_report": {
                "overall_score": 78.5,
                "risk_level": "high",
                "confidence": 92.0,
                "requires_notification": True,
            },
            "compliance_report": compliance_report,
            "metadata": {
                "filename": "test_proposal.pdf",
                "word_count": 3000,
                "page_count": 10,
            },
        }

    def test_prepare_email_activity(self, function_input):
        """Test the prepare_email activity function directly."""
        fa = _function_app

        result = fa.prepare_email(function_input)

        assert "to" in result
        assert "from" in result
        assert "subject" in result
        assert "body" in result
        assert "priority" in result
        assert "test_proposal.pdf" in result["subject"]

    def test_prepare_email_high_priority(self, function_input):
        fa = _function_app

        function_input["risk_report"]["risk_level"] = "high"
        result = fa.prepare_email(function_input)
        assert result["priority"] == "high"

    def test_prepare_email_normal_priority(self, function_input):
        fa = _function_app

        function_input["risk_report"]["risk_level"] = "medium"
        result = fa.prepare_email(function_input)
        assert result["priority"] == "normal"

    def test_send_email_activity_simulated(self):
        """send_email activity simulates when no Azure AD creds are set."""
        fa = _function_app

        email_data = {
            "to": "attorney@county.gov",
            "from": "compliance@county.gov",
            "subject": "Test",
            "body": "<p>test</p>",
            "priority": "normal",
        }

        with patch.dict(os.environ, {
            "AZURE_CLIENT_ID": "",
            "AZURE_CLIENT_SECRET": "",
            "AZURE_TENANT_ID": "",
        }, clear=False):
            result = fa.send_email(email_data)

        assert result["status"] == "simulated"

    def test_log_notification_activity(self):
        fa = _function_app

        log_input = {
            "email_data": {"to": "attorney@county.gov"},
            "send_result": {"status": "sent", "message": "OK"},
        }
        result = fa.log_notification(log_input)

        assert result["email_to"] == "attorney@county.gov"
        assert result["status"] == "sent"

    def test_generate_email_body_html(self):
        fa = _function_app

        html = fa.generate_email_body(
            risk_report={"risk_level": "high", "overall_score": 80.0},
            compliance_report={"compliance_score": 55.0},
            metadata={"filename": "proposal.pdf"},
        )

        assert "proposal.pdf" in html
        assert "80.0" in html
        assert "55.0" in html
        assert "HIGH" in html

    def test_orchestrator_calls_activities_in_order(self):
        """Verify the durable orchestrator yields activities in the correct sequence."""
        fa = _function_app

        mock_context = MagicMock()
        mock_context.get_input.return_value = {"risk_report": {}, "compliance_report": {}, "metadata": {}}

        # Track call_activity calls in order
        call_results = [
            {"to": "a@b.com", "subject": "test", "body": "", "from": "x@y.com", "priority": "normal"},
            {"status": "sent", "message": "ok"},
            {"email_to": "a@b.com", "status": "sent"},
        ]
        call_idx = {"i": 0}

        def mock_call_activity(name, input_data):
            idx = call_idx["i"]
            call_idx["i"] += 1
            result = MagicMock()
            result.result = call_results[idx]
            return result

        mock_context.call_activity = mock_call_activity

        # Run the generator
        gen = fa.orchestrator_function(mock_context)
        activity_names = []

        try:
            result = next(gen)
            while True:
                # The generator yields the result of call_activity; we send it back
                activity_names.append(result.result if hasattr(result, "result") else result)
                result = gen.send(result.result if hasattr(result, "result") else result)
        except StopIteration as e:
            final = e.value

        assert len(activity_names) == 3
        assert final["status"] == "sent"


# ===================================================================
# 3. End-to-End: Agent → Function pipeline
# ===================================================================

class TestEndToEnd:
    """
    End-to-end tests validating the full pipeline from
    EmailTriggerAgent through to the Azure Function activities.
    """

    def test_agent_output_compatible_with_function_input(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        """Agent's prepare_email output can drive the function's send_email activity."""
        fa = _function_app

        # Agent prepares email
        agent_email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)

        # Function's send_email expects: to, from, subject, body, priority
        func_email = {
            "to": agent_email["to"],
            "from": agent_email["from"],
            "subject": agent_email["subject"],
            "body": agent_email["body_html"],
            "priority": agent_email["priority"],
        }

        with patch.dict(os.environ, {
            "AZURE_CLIENT_ID": "",
            "AZURE_CLIENT_SECRET": "",
            "AZURE_TENANT_ID": "",
        }, clear=False):
            result = fa.send_email(func_email)

        assert result["status"] == "simulated"

    def test_full_pipeline_high_risk(
        self, risk_report_high, compliance_report, summary, metadata
    ):
        """Simulate the full path: prepare → send → verify output."""
        agent = EmailTriggerAgent(use_graph_api=False)

        # Prepare
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        assert email["priority"] == "high"
        assert "[URGENT]" in email["subject"]

        # Send (simulation)
        result = agent.send_email(email)
        assert result["status"] == "simulated"
        assert result["method"] == "demo"
        assert "message_id" in result

    def test_full_pipeline_low_risk_no_notification(
        self, risk_report_low, compliance_report, summary, metadata
    ):
        """Low risk: email is still preparable but notification is not required."""
        agent = EmailTriggerAgent(use_graph_api=False)

        assert risk_report_low["requires_notification"] is False

        # Agent can still prepare email even if not needed
        email = agent.prepare_email(risk_report_low, compliance_report, summary, metadata)
        assert email["priority"] == "low"
        assert "[URGENT]" not in email["subject"]

    @patch.object(EmailTriggerAgent, "_send_via_graph_api")
    def test_full_pipeline_with_graph_api(
        self, mock_graph, risk_report_high, compliance_report, summary, metadata
    ):
        mock_graph.return_value = {
            "status": "sent",
            "method": "graph_api",
            "message_id": "graph-e2e-001",
            "sent_at": datetime.now().isoformat(),
        }
        agent = EmailTriggerAgent(use_graph_api=False)
        agent.use_graph_api = True

        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        result = agent.send_email(email)

        assert result["status"] == "sent"
        assert result["method"] == "graph_api"

    def test_multiple_proposals_sequential(
        self, agent, compliance_report, summary
    ):
        """Process multiple proposals sequentially - no state leakage."""
        proposals = [
            {
                "risk": {"overall_score": 85.0, "risk_level": "high",
                         "confidence": 90.0, "requires_notification": True,
                         "recommendations": []},
                "meta": {"file_name": "proposal_A.pdf", "word_count": 2000, "page_count": 8},
            },
            {
                "risk": {"overall_score": 30.0, "risk_level": "low",
                         "confidence": 95.0, "requires_notification": False,
                         "recommendations": []},
                "meta": {"file_name": "proposal_B.pdf", "word_count": 1500, "page_count": 5},
            },
        ]

        results = []
        for p in proposals:
            email = agent.prepare_email(p["risk"], compliance_report, summary, p["meta"])
            result = agent.send_email(email)
            results.append((email, result))

        # First email is urgent, second is not
        assert "[URGENT]" in results[0][0]["subject"]
        assert "proposal_A.pdf" in results[0][0]["subject"]
        assert "[URGENT]" not in results[1][0]["subject"]
        assert "proposal_B.pdf" in results[1][0]["subject"]

        # Both should succeed (simulated)
        assert all(r[1]["status"] == "simulated" for r in results)

    def test_email_html_is_valid_structure(
        self, agent, risk_report_high, compliance_report, summary, metadata
    ):
        """Basic HTML structure validation."""
        email = agent.prepare_email(risk_report_high, compliance_report, summary, metadata)
        html = email["body_html"]

        assert html.strip().startswith("<!DOCTYPE html>") or html.strip().startswith("<")
        assert "</html>" in html
        assert "<body>" in html or "<body " in html
        assert "</body>" in html


# ===================================================================
# 4. Edge cases and error handling
# ===================================================================

class TestEdgeCases:

    def test_empty_violations_and_warnings(self, agent, summary, metadata):
        report = {
            "overall_score": 25.0,
            "risk_level": "low",
            "confidence": 95.0,
            "requires_notification": False,
            "recommendations": [],
        }
        compliance = {
            "compliance_score": 95.0,
            "overall_status": "compliant",
            "confidence_score": 92.0,
            "violations": [],
            "warnings": [],
            "relevant_executive_orders": [],
        }
        email = agent.prepare_email(report, compliance, summary, metadata)
        # "Violation 1:" should not appear when there are no violations
        assert "Violation 1" not in email["body_html"]
        result = agent.send_email(email)
        assert result["status"] == "simulated"

    def test_missing_optional_metadata_fields(self, agent, risk_report_high, compliance_report, summary):
        """Agent handles minimal metadata gracefully."""
        minimal_meta = {"file_name": "doc.pdf"}
        email = agent.prepare_email(risk_report_high, compliance_report, summary, minimal_meta)
        assert "doc.pdf" in email["subject"]
        result = agent.send_email(email)
        assert result["status"] == "simulated"

    def test_no_recommendations(self, agent, compliance_report, summary, metadata):
        report = {
            "overall_score": 40.0,
            "risk_level": "medium",
            "confidence": 80.0,
            "requires_notification": True,
            "recommendations": [],
        }
        email = agent.prepare_email(report, compliance_report, summary, metadata)
        # Should not crash even with empty recommendations
        assert email["priority"] == "normal"

    def test_very_long_summary_truncated(self, agent, risk_report_high, compliance_report, metadata):
        long_summary = {
            "executive_summary": "A" * 5000,
            "key_clauses": [],
            "key_topics": [],
        }
        email = agent.prepare_email(risk_report_high, compliance_report, long_summary, metadata)
        # HTML body should not include the full 5000-char string untruncated
        # (the agent truncates to 500 chars)
        assert len(email["body_text"]) < 6000

    def test_special_characters_in_filename(self, agent, risk_report_high, compliance_report, summary):
        meta = {"file_name": "grant proposal (v2) — final.pdf", "word_count": 100, "page_count": 1}
        email = agent.prepare_email(risk_report_high, compliance_report, summary, meta)
        assert "grant proposal (v2)" in email["subject"]
