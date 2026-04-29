from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
import asyncio
import sys
import unittest

sys.path.insert(0, '/home/qixin/projects/chip-quotation-system/backend')

from fastapi import HTTPException

from app.main import app
from app.api.v1.endpoints.quotes import get_quote_detail_by_id, get_quote_detail_test
from app.api.v1.endpoints.quote_route_helpers import ensure_quote_access, get_quote_by_identifier
from app.schemas import Quote as QuoteSchema, QuoteList
from app.services.quote_service import QuoteService


class StubQuoteService:
    def __init__(self):
        self.calls = []

    def get_quote_by_id(self, value):
        self.calls.append(("id", value))
        return "ID"

    def get_quote_by_number(self, value):
        self.calls.append(("number", value))
        return "NUMBER"

    def get_quote_by_approval_token(self, value):
        self.calls.append(("token", value))
        return "TOKEN"


class StubQuery:
    def __init__(self, quote):
        self.quote = quote
        self.filters = []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        self.filters.append((args, kwargs))
        return self

    def first(self):
        return self.quote


class StubSession:
    def __init__(self, quote):
        self.quote = quote
        self.last_query = None

    def query(self, model):
        self.last_query = StubQuery(self.quote)
        return self.last_query


class FailingSession:
    def query(self, model):
        raise RuntimeError("database password leaked")


def build_quote(**overrides):
    values = {
        "id": 10,
        "quote_number": "CIS-KS20250101001",
        "title": "Regression quote",
        "quote_type": "standard",
        "customer_name": "Customer",
        "customer_contact": None,
        "customer_phone": None,
        "customer_email": None,
        "customer_address": None,
        "quote_unit": None,
        "currency": "CNY",
        "subtotal": 0,
        "discount": 0,
        "tax_rate": 0,
        "tax_amount": 0,
        "total_amount": 0,
        "valid_until": None,
        "payment_terms": None,
        "description": None,
        "notes": None,
        "status": "draft",
        "approval_status": "pending",
        "version": 1,
        "submitted_at": None,
        "approved_at": None,
        "approved_by": None,
        "rejection_reason": None,
        "wecom_approval_id": None,
        "created_by": 1,
        "current_approver_id": 2,
        "creator": SimpleNamespace(name="Owner"),
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 1),
        "items": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class QuoteLogicRegressionTests(unittest.TestCase):
    def test_quote_identifier_routes_to_correct_lookup(self):
        service = StubQuoteService()

        self.assertEqual(get_quote_by_identifier(service, "123"), "ID")
        self.assertEqual(service.calls[-1], ("id", 123))

        self.assertEqual(get_quote_by_identifier(service, "550e8400-e29b-41d4-a716-446655440000"), "TOKEN")
        self.assertEqual(service.calls[-1], ("token", "550e8400-e29b-41d4-a716-446655440000"))

        self.assertEqual(get_quote_by_identifier(service, "CIS-KS20250101001"), "NUMBER")
        self.assertEqual(service.calls[-1], ("number", "CIS-KS20250101001"))

    def test_quote_access_allows_owner_and_current_approver_paths(self):
        quote = SimpleNamespace(created_by=1, current_approver_id=2, approval_status='pending')

        owner = SimpleNamespace(id=1, role='user')
        approver = SimpleNamespace(id=2, role='manager')
        admin = SimpleNamespace(id=3, role='admin')

        self.assertIs(ensure_quote_access(quote, owner), quote)
        self.assertIs(ensure_quote_access(quote, approver), quote)

        approved_quote = SimpleNamespace(created_by=9, current_approver_id=None, approval_status='approved')
        self.assertIs(ensure_quote_access(approved_quote, admin), approved_quote)

    def test_quote_access_denies_unrelated_user(self):
        quote = SimpleNamespace(created_by=1, current_approver_id=2, approval_status='pending')
        other_user = SimpleNamespace(id=99, role='user')

        with self.assertRaises(HTTPException) as ctx:
            ensure_quote_access(quote, other_user)

        self.assertEqual(ctx.exception.status_code, 403)

    def test_adjusted_price_drives_totals(self):
        service = QuoteService(None)
        quote = SimpleNamespace(
            items=[SimpleNamespace(quantity=2, unit_price=100, adjusted_price=80)],
            discount=0,
            tax_rate=Decimal('0'),
        )

        totals = service._prepare_items(quote)

        self.assertEqual(totals["subtotal"], 160.0)
        self.assertEqual(totals["total_amount"], 160.0)
        self.assertEqual(quote.items[0].total_price, 160.0)

    def test_adjusted_price_payload_drives_totals(self):
        service = QuoteService(None)
        prepared = service._prepare_items_payload([
            {"quantity": 2, "unit_price": 100, "adjusted_price": 80}
        ])

        self.assertEqual(prepared["items"][0]["total_price"], 160.0)
        self.assertEqual(prepared["subtotal"], Decimal('160.00'))

    def test_quote_schemas_expose_approval_status(self):
        self.assertIn("approval_status", QuoteSchema.model_fields)
        self.assertIn("approval_status", QuoteList.model_fields)

    def test_active_quote_routes_registered_and_legacy_export_absent(self):
        paths = {route.path for route in app.routes}

        self.assertIn('/api/v1/quotes/by-uuid/{quote_uuid}', paths)
        self.assertIn('/api/v1/quotes/{quote_id}/pdf', paths)
        self.assertIn('/api/v1/quotes/{quote_id}/export/pdf', paths)
        self.assertIn('/api/v1/quotes/{quote_id}/export/excel', paths)
        self.assertNotIn('/api/v1/export/quote/{quote_id}/pdf', paths)

    def test_detail_by_id_rejects_unrelated_user(self):
        quote = build_quote(created_by=1, current_approver_id=2, approval_status='pending')
        other_user = SimpleNamespace(id=99, role='user')

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(get_quote_detail_by_id("10", StubSession(quote), other_user))

        self.assertEqual(ctx.exception.status_code, 403)

    def test_detail_by_number_rejects_unrelated_user(self):
        quote = build_quote(created_by=1, current_approver_id=2, approval_status='pending')
        other_user = SimpleNamespace(id=99, role='user')

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(get_quote_detail_test("CIS-KS20250101001", StubSession(quote), other_user))

        self.assertEqual(ctx.exception.status_code, 403)

    def test_detail_by_number_preserves_owner_response_shape(self):
        quote = build_quote(created_by=1)
        owner = SimpleNamespace(id=1, role='user')

        result = asyncio.run(get_quote_detail_test("CIS-KS20250101001", StubSession(quote), owner))

        self.assertEqual(result["id"], 10)
        self.assertEqual(result["quote_number"], "CIS-KS20250101001")
        self.assertEqual(result["creator_name"], "Owner")
        self.assertEqual(result["items"], [])

    def test_detail_routes_apply_soft_delete_filter(self):
        quote = build_quote(created_by=1)
        owner = SimpleNamespace(id=1, role='user')

        by_id_session = StubSession(quote)
        asyncio.run(get_quote_detail_by_id("10", by_id_session, owner))
        self.assertEqual(len(by_id_session.last_query.filters[0][0]), 2)

        by_number_session = StubSession(quote)
        asyncio.run(get_quote_detail_test("CIS-KS20250101001", by_number_session, owner))
        self.assertEqual(len(by_number_session.last_query.filters[0][0]), 2)

    def test_detail_routes_hide_unexpected_error_details(self):
        owner = SimpleNamespace(id=1, role='user')

        with self.assertRaises(HTTPException) as by_id_ctx:
            asyncio.run(get_quote_detail_by_id("10", FailingSession(), owner))
        self.assertEqual(by_id_ctx.exception.status_code, 500)
        self.assertNotIn("database password leaked", by_id_ctx.exception.detail)

        with self.assertRaises(HTTPException) as by_number_ctx:
            asyncio.run(get_quote_detail_test("CIS-KS20250101001", FailingSession(), owner))
        self.assertEqual(by_number_ctx.exception.status_code, 500)
        self.assertNotIn("database password leaked", by_number_ctx.exception.detail)


if __name__ == '__main__':
    unittest.main()
