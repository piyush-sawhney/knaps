import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from knaps.utils.constants import (
	DOCTYPE_CLIENT,
	DOCTYPE_HOLDING_TYPE,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_PAYMENT_TYPE,
	DOCTYPE_PO_INVESTMENT,
	DOCTYPE_PO_SCHEME,
	DOCTYPE_RD_ACCOUNT,
	DOCTYPE_RELATIONSHIP,
)


class TestKNAPSRDAccount(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.db.savepoint("knaps_rd_account_sp")

		self.holding_type_single = self._create_holding_type("Single")
		self.scheme = self._create_scheme("RD Scheme", "RD")
		self.individual = self._create_individual("Test", "Male", "Mr", "1990-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.client = self._create_client("Individual", self.individual)
		self.relationship = self._create_relationship("Spouse")
		self.payment_type = self._create_payment_type("Cash")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_rd_account_sp")
		super().tearDown()

	def _create_holding_type(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_HOLDING_TYPE, name):
			return name
		doc = frappe.get_doc({"doctype": DOCTYPE_HOLDING_TYPE, "holding_type": name})
		doc.insert()
		return name

	def _create_scheme(self, name: str, code: str) -> str:
		if frappe.db.exists(DOCTYPE_PO_SCHEME, code):
			return code
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_PO_SCHEME,
				"scheme_name": name,
				"scheme_code": code,
			}
		)
		doc.insert()
		return code

	def _create_individual(self, first_name: str, gender: str, salutation: str, dob: str) -> str:
		self._ensure_doctype_exists("Gender", gender)
		self._ensure_doctype_exists("Salutation", salutation)

		ind = frappe.get_doc(
			{
				"doctype": DOCTYPE_INDIVIDUAL,
				"first_name": first_name,
				"gender": gender,
				"salutation": salutation,
				"date_of_birth": dob,
				"status": "Active",
			}
		)
		ind.insert()
		return ind.name

	def _ensure_doctype_exists(self, doctype: str, name: str) -> None:
		if not frappe.db.exists(doctype, name):
			frappe.get_doc({"doctype": doctype, "name": name}).insert()

	def _create_client(self, client_type: str, individual: str) -> str:
		client = frappe.get_doc(
			{
				"doctype": DOCTYPE_CLIENT,
				"client_type": client_type,
				"individual": individual,
			}
		)
		client.insert()
		return client.name

	def _create_relationship(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_RELATIONSHIP, name):
			return name
		frappe.get_doc(
			{
				"doctype": DOCTYPE_RELATIONSHIP,
				"relationship_name": name,
			}
		).insert()
		return name

	def _create_payment_type(self, name: str) -> str:
		existing = frappe.db.get_value(DOCTYPE_PAYMENT_TYPE, {"payment_type": name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_PAYMENT_TYPE,
				"payment_type": name,
			}
		)
		doc.insert()
		return doc.name

	def _create_po_investment(self, **kwargs) -> str:
		defaults = {
			"doctype": DOCTYPE_PO_INVESTMENT,
			"entry_date": today(),
			"status": "Active",
			"holding_type": self.holding_type_single,
			"scheme_name": self.scheme,
			"passbook_status": "Not Created",
			"period_in_months": 12,
			"rate_of_interest": 7.5,
			"amount": 10000,
			"currency": "INR",
			"account_number": "1234567890",
			"start_date": today(),
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.append(
			"holders",
			{
				"holder": self.client,
				"order": "First",
				"is_minor": 0,
			},
		)
		doc.append(
			"nominees",
			{
				"nominee_name": self.nominee_individual,
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
			},
		)
		doc.append(
			"payments",
			{
				"payment_date": today(),
				"payment_amount": 10000,
				"payment_type": self.payment_type,
				"status": "Pending",
			},
		)
		doc.insert()
		return doc.name

	def _make_rd_account(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_RD_ACCOUNT,
			"rd_account_number": "1234567890",
			"denomination": 10000,
			"account_opening_date": today(),
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def test_title_computed_with_client_and_account(self):
		po_inv = self._create_po_investment()
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
		)
		rd.insert()

		client_name = frappe.db.get_value(DOCTYPE_PO_INVESTMENT, po_inv, "client_name")
		self.assertEqual(rd.title, f"{client_name}-RD-7890")

	def test_title_without_account_number(self):
		po_inv = self._create_po_investment(account_number="AB")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			rd_account_number="AB",
		)
		rd.insert()

		client_name = frappe.db.get_value(DOCTYPE_PO_INVESTMENT, po_inv, "client_name")
		self.assertEqual(rd.title, f"{client_name}-RD-AB")

	def test_title_without_client_name(self):
		po_inv = self._create_po_investment()
		client_name = frappe.db.get_value(DOCTYPE_PO_INVESTMENT, po_inv, "client_name")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			client_name=client_name,
		)
		rd.insert()

		self.assertIsNotNone(rd.title)
		self.assertIn(client_name, rd.title)

	def test_effective_card_from_card_number(self):
		po_inv = self._create_po_investment()
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			card_number="CARD001",
		)
		rd.insert()

		self.assertEqual(rd.effective_card_number, "CARD001")
		self.assertEqual(rd.is_updated, 1)

	def test_effective_card_from_extension_when_renewed(self):
		po_inv = self._create_po_investment()
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			card_number="CARD001",
			extension_card_number="CARD002",
		)
		rd.insert()

		self.assertEqual(rd.effective_card_number, "CARD002")
		self.assertEqual(rd.is_updated, 1)

	def test_effective_card_falls_back_to_card_when_extension_empty(self):
		po_inv = self._create_po_investment()
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			card_number="CARD001",
			extension_card_number=None,
		)
		rd.insert()

		self.assertEqual(rd.effective_card_number, "CARD001")

	def test_is_updated_false_when_no_card(self):
		po_inv = self._create_po_investment()
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			card_number=None,
			extension_card_number=None,
		)
		rd.insert()

		self.assertEqual(rd.is_updated, 0)
		self.assertIsNone(rd.effective_card_number)

	def test_account_number_match_succeeds(self):
		po_inv = self._create_po_investment(account_number="ACC123")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			rd_account_number="ACC123",
		)
		rd.insert()

		self.assertEqual(rd.rd_account_number, "ACC123")

	def test_account_number_mismatch_rejected(self):
		po_inv = self._create_po_investment(account_number="ACC123")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			rd_account_number="WRONG",
		)

		with self.assertRaises(ValidationError):
			rd.insert()

	def test_denomination_match_succeeds(self):
		po_inv = self._create_po_investment(amount=5000)
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			denomination=5000,
		)
		rd.insert()

		self.assertEqual(rd.denomination, 5000)

	def test_denomination_mismatch_rejected(self):
		po_inv = self._create_po_investment(amount=5000)
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			denomination=9999,
		)

		with self.assertRaises(ValidationError):
			rd.insert()

	def test_start_date_match_succeeds(self):
		po_inv = self._create_po_investment(start_date="2026-06-01")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			account_opening_date="2026-06-01",
		)
		rd.insert()

		self.assertEqual(str(rd.account_opening_date), "2026-06-01")

	def test_start_date_mismatch_rejected(self):
		po_inv = self._create_po_investment(start_date="2026-06-01")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			account_opening_date="2026-07-01",
		)

		with self.assertRaises(ValidationError):
			rd.insert()

	def test_unique_rd_account_number(self):
		po_inv = self._create_po_investment(account_number="UNIQUE01")
		rd1 = self._make_rd_account(
			po_rd_investment=po_inv,
			rd_account_number="UNIQUE01",
		)
		rd1.insert()

		po_inv2 = self._create_po_investment(account_number="UNIQUE02")
		rd2 = self._make_rd_account(
			po_rd_investment=po_inv2,
			rd_account_number="UNIQUE01",
		)

		with self.assertRaises(ValidationError):
			rd2.insert()

	def test_fetch_from_po_investment_auto_populates(self):
		po_inv = self._create_po_investment(
			account_number="FETCH001",
			amount=7500,
			start_date="2026-04-01",
		)
		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.client, "client_name")
		rd = self._make_rd_account(
			po_rd_investment=po_inv,
			rd_account_number="FETCH001",
			denomination=7500,
			client_name=client_name,
			account_number="FETCH001",
			amount=7500,
			account_opening_date="2026-04-01",
			start_date="2026-04-01",
		)
		rd.insert()

		self.assertEqual(rd.account_number, "FETCH001")
		self.assertEqual(rd.amount, 7500)
		self.assertEqual(str(rd.start_date), "2026-04-01")
		self.assertEqual(rd.client_name, client_name)

	def test_create_without_po_investment(self) -> None:
		rd = self._make_rd_account(
			rd_account_number="NOLINK01",
			denomination=10000,
			account_opening_date=today(),
			holder_name="Test Holder",
			card_number="CARD001",
		)
		rd.insert()
		self.assertIsNone(rd.po_rd_investment)
		self.assertIsNotNone(rd.name)

	def test_scheduler_links_matching_po_investment(self) -> None:
		from knaps.tasks.daily import update_po_investment_in_rd_account

		po_inv = self._create_po_investment(account_number="SCHED01")
		rd = self._make_rd_account(
			rd_account_number="SCHED01",
			denomination=10000,
			account_opening_date=today(),
			holder_name="Test Holder",
		)
		rd.insert()
		self.assertIsNone(rd.po_rd_investment)

		update_po_investment_in_rd_account()

		rd.reload()
		self.assertEqual(rd.po_rd_investment, po_inv)

	def test_scheduler_skips_when_no_match(self) -> None:
		from knaps.tasks.daily import update_po_investment_in_rd_account

		self._create_po_investment(account_number="SCHED02")
		rd = self._make_rd_account(
			rd_account_number="NO_MATCH",
			denomination=10000,
			account_opening_date=today(),
			holder_name="Test Holder",
		)
		rd.insert()
		self.assertIsNone(rd.po_rd_investment)

		update_po_investment_in_rd_account()

		rd.reload()
		self.assertIsNone(rd.po_rd_investment)
