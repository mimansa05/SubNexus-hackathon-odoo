import json
import os
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.services.orchestrator_service import _classify_request


class GroqIntentTests(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("app.services.orchestrator_service.requests.post")
    def test_parses_supported_intent(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": json.dumps({
            "intent": "generate_renewal_invoices", "days": 7,
        })}}]}
        post.return_value = response
        self.assertEqual(
            _classify_request("Find subscriptions expiring in 7 days and generate invoices"),
            {"intent": "generate_renewal_invoices", "days": 7},
        )
        self.assertEqual(post.call_args.kwargs["timeout"], 20)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("app.services.orchestrator_service.requests.post")
    def test_rejects_unapproved_model_intent(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": json.dumps({
            "intent": "delete_all_customers", "days": 7,
        })}}]}
        post.return_value = response
        with self.assertRaises(HTTPException) as error:
            _classify_request("do something")
        self.assertEqual(error.exception.status_code, 502)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("app.services.orchestrator_service.requests.post")
    def test_routes_unmatched_payment_request(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": json.dumps({
            "intent": "explain_unmatched_payments", "days": 7,
        })}}]}
        post.return_value = response
        self.assertEqual(
            _classify_request("Explain the unmatched bank payments"),
            {"intent": "explain_unmatched_payments", "days": 7},
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_requires_groq_configuration(self):
        with self.assertRaises(HTTPException) as error:
            _classify_request("expiring subscriptions")
        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
