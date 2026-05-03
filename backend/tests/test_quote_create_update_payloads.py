from datetime import datetime
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '/home/qixin/projects/chip-quotation-system/backend')

from app.database import Base
from app.models import Quote, QuoteItem, User
from app.schemas import QuoteCreate, QuoteItemCreate, QuoteUpdate, QuoteItemUpdate
from app.services.quote_service import QuoteService


class QuoteCreateUpdatePayloadTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()

        self.owner = User(userid='owner', name='Owner', role='user')
        self.admin = User(userid='admin', name='Admin', role='admin')
        self.db.add_all([self.owner, self.admin])
        self.db.commit()
        self.db.refresh(self.owner)
        self.db.refresh(self.admin)

        self.service = QuoteService(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_create_quote_recalculates_financials_from_items(self):
        payload = QuoteCreate(
            title='Tooling Regression Quote',
            quote_type='tooling',
            customer_name='Payload Co',
            customer_contact='Alice',
            quote_unit='昆山芯信安',
            currency='CNY',
            subtotal=1,
            total_amount=1,
            payment_terms='30_days',
            items=[
                QuoteItemCreate(
                    item_name='loadboard',
                    item_description='fixture - regression',
                    quantity=2,
                    unit='件',
                    unit_price=100,
                    total_price=9999,
                )
            ]
        )

        quote = self.service.create_quote(payload, self.owner.id)

        self.assertEqual(quote.quote_type, 'tooling')
        self.assertEqual(quote.subtotal, 200.0)
        self.assertEqual(quote.tax_amount, 26.0)
        self.assertEqual(quote.total_amount, 226.0)
        self.assertEqual(len(quote.items), 1)
        self.assertEqual(quote.items[0].total_price, 200.0)

    def test_create_inquiry_quote_is_auto_approved(self):
        payload = QuoteCreate(
            title='Inquiry Regression Quote',
            quote_type='inquiry',
            customer_name='Inquiry Co',
            customer_contact='Ivy',
            quote_unit='昆山芯信安',
            currency='CNY',
            items=[
                QuoteItemCreate(
                    item_name='混合测试',
                    quantity=1,
                    unit='台·小时',
                    unit_price=8,
                    total_price=8,
                )
            ]
        )

        quote = self.service.create_quote(payload, self.owner.id)

        self.assertEqual(quote.status, 'approved')
        self.assertEqual(quote.approval_status, 'approved')
        self.assertEqual(quote.approved_by, self.owner.id)
        self.assertIsNotNone(quote.approved_at)

    def test_update_quote_rewrites_items_and_recalculates_totals(self):
        created = self.service.create_quote(
            QuoteCreate(
                title='Mass Quote',
                quote_type='mass_production',
                customer_name='Mass Co',
                customer_contact='Mia',
                quote_unit='昆山芯信安',
                currency='CNY',
                items=[
                    QuoteItemCreate(
                        item_name='J750',
                        quantity=1,
                        unit='小时',
                        unit_price=6,
                        total_price=6,
                    )
                ]
            ),
            self.owner.id,
        )

        updated = self.service.update_quote(
            created.id,
            QuoteUpdate(
                customer_name='Mass Updated Co',
                items=[
                    QuoteItemUpdate(
                        item_name='J750',
                        quantity=2,
                        unit='小时',
                        unit_price=6,
                        total_price=0,
                    )
                ]
            ),
            self.owner.id,
        )

        self.assertEqual(updated.customer_name, 'Mass Updated Co')
        self.assertEqual(len(updated.items), 1)
        self.assertEqual(updated.items[0].total_price, 12.0)
        self.assertEqual(updated.subtotal, 12.0)
        self.assertEqual(updated.tax_amount, 1.56)
        self.assertEqual(updated.total_amount, 13.56)

    def test_update_quote_uses_adjusted_price_for_totals(self):
        created = self.service.create_quote(
            QuoteCreate(
                title='Engineering Quote',
                quote_type='engineering',
                customer_name='Engineering Co',
                customer_contact='Ella',
                quote_unit='昆山芯信安',
                currency='CNY',
                items=[
                    QuoteItemCreate(
                        item_name='J750',
                        quantity=1,
                        unit='小时',
                        unit_price=10,
                        total_price=10,
                    )
                ]
            ),
            self.owner.id,
        )

        updated = self.service.update_quote(
            created.id,
            QuoteUpdate(
                items=[
                    QuoteItemUpdate(
                        item_name='J750',
                        quantity=1,
                        unit='小时',
                        unit_price=10,
                        adjusted_price=8,
                        total_price=0,
                        adjustment_reason='discounted'
                    )
                ]
            ),
            self.owner.id,
        )

        self.assertEqual(updated.items[0].adjusted_price, 8)
        self.assertEqual(updated.items[0].total_price, 8.0)
        self.assertEqual(updated.subtotal, 8.0)
        self.assertEqual(updated.total_amount, 9.04)

    def test_update_quote_rejects_non_draft_status(self):
        created = self.service.create_quote(
            QuoteCreate(
                title='Approved Inquiry',
                quote_type='inquiry',
                customer_name='Approved Co',
                customer_contact='Ivy',
                quote_unit='昆山芯信安',
                currency='CNY',
                items=[QuoteItemCreate(item_name='混合测试', quantity=1, unit='台·小时', unit_price=8, total_price=8)]
            ),
            self.owner.id,
        )

        with self.assertRaises(ValueError):
            self.service.update_quote(
                created.id,
                QuoteUpdate(customer_name='Should Fail'),
                self.owner.id,
            )

    def test_update_quote_rejects_unauthorized_user(self):
        created = self.service.create_quote(
            QuoteCreate(
                title='Tooling Quote',
                quote_type='tooling',
                customer_name='Owner Co',
                customer_contact='Owen',
                quote_unit='昆山芯信安',
                currency='CNY',
                items=[QuoteItemCreate(item_name='loadboard', quantity=1, unit='件', unit_price=100, total_price=100)]
            ),
            self.owner.id,
        )

        outsider = User(userid='outsider', name='Outsider', role='user')
        self.db.add(outsider)
        self.db.commit()
        self.db.refresh(outsider)

        with self.assertRaises(PermissionError):
            self.service.update_quote(created.id, QuoteUpdate(customer_name='Nope'), outsider.id)
