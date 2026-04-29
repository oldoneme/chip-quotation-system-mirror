from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
import asyncio
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, '/home/qixin/projects/chip-quotation-system/backend')

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.main import app
from app.api.v1.endpoints.quotes import get_quote_detail_by_id, get_quote_detail_test
from app.auth_routes import get_current_user_strict_multi_source
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


class StubUserQuery:
    def __init__(self, user):
        self.user = user

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.user


class StubAuthDb:
    def __init__(self, user):
        self.user = user

    def query(self, model):
        return StubUserQuery(self.user)


class StubAuthService:
    def __init__(self, session_user=None, token_user=None, session_exists=True, permission=True):
        self.session_user = session_user
        self.token_user = token_user if token_user is not None else session_user
        self.session_exists = session_exists
        self.permission = permission
        self.db = StubAuthDb(self.token_user)

    def get_session_by_token(self, token):
        if not self.session_exists or not self.session_user:
            return None
        return SimpleNamespace(user=self.session_user)

    def check_user_permission(self, user):
        return self.permission


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


def build_request(path="/api/v1/quotes/detail/by-id/10", headers=None, cookies=None, query_string=""):
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
        raw_headers.append((b"cookie", cookie_header.encode("latin-1")))

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": raw_headers,
        "query_string": query_string.encode("latin-1"),
        "client": ("127.0.0.1", 8000),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope)


class QuoteLogicRegressionTests(unittest.TestCase):
    def test_strict_multi_source_auth_accepts_session_token(self):
        user = SimpleNamespace(id=1, userid="owner", role="user")
        request = build_request(cookies={"session_token": "session-123"})

        resolved = get_current_user_strict_multi_source(
            request,
            session_token="session-123",
            credentials=None,
            auth_service=StubAuthService(session_user=user),
        )

        self.assertEqual(resolved.userid, "owner")

    def test_strict_multi_source_auth_accepts_bearer_token(self):
        user = SimpleNamespace(id=2, userid="snapshot-user", role="user")
        request = build_request(headers={"authorization": "Bearer snapshot-token"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="snapshot-token")

        with patch("app.auth_routes.decode_jwt", return_value={"sub": "snapshot-user"}):
            resolved = get_current_user_strict_multi_source(
                request,
                session_token=None,
                credentials=credentials,
                auth_service=StubAuthService(session_user=None, token_user=user, session_exists=False),
            )

        self.assertEqual(resolved.userid, "snapshot-user")

    def test_strict_multi_source_auth_accepts_auth_token_cookie(self):
        user = SimpleNamespace(id=3, userid="cookie-user", role="user")
        request = build_request(cookies={"auth_token": "cookie-token"})

        with patch("app.auth_routes.decode_jwt", return_value={"sub": "cookie-user"}):
            resolved = get_current_user_strict_multi_source(
                request,
                session_token=None,
                credentials=None,
                auth_service=StubAuthService(session_user=None, token_user=user, session_exists=False),
            )

        self.assertEqual(resolved.userid, "cookie-user")

    def test_strict_multi_source_auth_accepts_jwt_query_param(self):
        user = SimpleNamespace(id=4, userid="query-user", role="user")
        request = build_request(query_string="jwt=query-token")

        with patch("app.auth_routes.decode_jwt", return_value={"sub": "query-user"}):
            resolved = get_current_user_strict_multi_source(
                request,
                session_token=None,
                credentials=None,
                auth_service=StubAuthService(session_user=None, token_user=user, session_exists=False),
            )

        self.assertEqual(resolved.userid, "query-user")

    def test_strict_multi_source_auth_rejects_missing_credentials(self):
        request = build_request()

        with self.assertRaises(HTTPException) as ctx:
            get_current_user_strict_multi_source(
                request,
                session_token=None,
                credentials=None,
                auth_service=StubAuthService(session_user=None, token_user=None, session_exists=False),
            )

        self.assertEqual(ctx.exception.status_code, 401)

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
