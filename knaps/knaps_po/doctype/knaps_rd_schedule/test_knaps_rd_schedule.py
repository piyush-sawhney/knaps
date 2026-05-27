import frappe
from frappe.exceptions import MandatoryError, ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from knaps.utils.constants import (
	DOCTYPE_BANK,
	DOCTYPE_CLIENT,
	DOCTYPE_HOLDING_TYPE,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_PAYMENT_TYPE,
	DOCTYPE_PO_INVESTMENT,
	DOCTYPE_PO_SCHEME,
	DOCTYPE_RD_ACCOUNT,
	DOCTYPE_RD_SCHEDULE,
	DOCTYPE_RELATIONSHIP,
)


class TestKNAPSRDSchedule(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.db.savepoint("knaps_rd_schedule_sp")

		self.holding_type_single = self._create_holding_type("Single")
		self.scheme = self._create_scheme("RD Scheme", "RD")
		self.individual = self._create_individual("Test", "Male", "Mr", "1990-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.client = self._create_client("Individual", self.individual)
		self.relationship = self._create_relationship("Spouse")
		self.payment_type = self._create_payment_type("Cash")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_rd_schedule_sp")
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
			"account_number": "SCHEDULEACC01",
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

	def _create_rd_account(self, account_number: str, denomination: float = 10000, **kwargs) -> str:
		po_inv = self._create_po_investment(
			account_number=account_number,
			amount=denomination,
		)
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_RD_ACCOUNT,
				"po_rd_investment": po_inv,
				"rd_account_number": account_number,
				"denomination": denomination,
				"account_opening_date": today(),
				"card_number": "CARD001",
				**kwargs,
			}
		)
		doc.insert()
		return doc.name

	def _make_rd_schedule(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_RD_SCHEDULE,
			"schedule_type": "Cash",
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _create_bank(self, bank_name: str) -> str:
		existing = frappe.db.get_value(DOCTYPE_BANK, {"bank_name": bank_name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_BANK,
				"bank_name": bank_name,
				"bank_account_number": bank_name.replace(" ", "").upper(),
				"ifsc": f"{bank_name[:4].upper()}0001234",
				"holding_type": self.holding_type_single,
				"holder_type": DOCTYPE_INDIVIDUAL,
				"first_holder": self.individual,
			}
		)
		doc.insert()
		return doc.name

	def test_cash_schedule_accepts_no_cheque_numbers(self):
		rd_acc = self._create_rd_account("CASH001")
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
				"cheque_number": "123456",
			},
		)
		with self.assertRaises(ValidationError):
			schedule.insert()

	def test_cash_schedule_clears_bank_account_number(self):
		rd_acc = self._create_rd_account("CASH002")
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
				"bank_account_number": "SOME BANK",
			},
		)
		schedule.insert()
		self.assertIsNone(schedule.rd_accounts[0].bank_account_number)

	def test_cash_schedule_succeeds(self):
		rd_acc = self._create_rd_account("CASH003")
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
			},
		)
		schedule.insert()
		self.assertEqual(schedule.schedule_type, "Cash")
		self.assertEqual(len(schedule.rd_accounts), 1)

	def test_cheque_schedule_requires_six_digit_cheque_number(self):
		rd_acc = self._create_rd_account("CHQ001")
		schedule = self._make_rd_schedule(
			schedule_type="Cheque",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
				"cheque_number": "12345",
			},
		)
		with self.assertRaises(ValidationError):
			schedule.insert()

	def test_cheque_schedule_accepts_valid_cheque_number_format(self):
		bank = self._create_bank("HDFC Bank")
		rd_acc = self._create_rd_account("CHQ002", bank=bank)
		schedule = self._make_rd_schedule(
			schedule_type="Cheque",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
				"cheque_number": "123456",
			},
		)
		schedule.insert()
		self.assertEqual(schedule.rd_accounts[0].cheque_number, "123456")
		self.assertIsNotNone(schedule.rd_accounts[0].bank_account_number)

	def test_cheque_schedule_requires_bank_account(self):
		rd_acc = self._create_rd_account("CHQ003")
		schedule = self._make_rd_schedule(
			schedule_type="Cheque",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
				"cheque_number": "123456",
			},
		)
		with self.assertRaises(ValidationError):
			schedule.insert()

	def test_duplicate_account_number_rejected(self):
		rd_acc1 = self._create_rd_account("DUPE01")
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc1,
				"number_of_installments": 6,
			},
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc1,
				"number_of_installments": 3,
			},
		)
		with self.assertRaises(ValidationError):
			schedule.insert()

	def test_financial_computation(self):
		rd_acc1 = self._create_rd_account("FIN001", denomination=5000)
		rd_acc2 = self._create_rd_account("FIN002", denomination=3000)
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc1,
				"number_of_installments": 6,
			},
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc2,
				"number_of_installments": 3,
			},
		)
		schedule.insert()

		self.assertEqual(schedule.rd_accounts[0].rd_amount, 30000.0)
		self.assertEqual(schedule.rd_accounts[1].rd_amount, 9000.0)
		self.assertEqual(schedule.schedule_amount, 39000.0)
		self.assertEqual(schedule.rd_accounts[0].rd_deposit_amount, 30000.0)
		self.assertEqual(schedule.rd_accounts[1].rd_deposit_amount, 9000.0)
		self.assertEqual(schedule.deposit_amount, 39000.0)

	def test_rebate_and_surcharge_calculation(self):
		rd_acc = self._create_rd_account("REBATE01", denomination=10000)
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 12,
				"rebate": 500,
				"surcharge": 200,
			},
		)
		schedule.insert()

		self.assertEqual(schedule.rd_accounts[0].rd_amount, 120000.0)
		self.assertEqual(schedule.rd_accounts[0].rd_deposit_amount, 119700.0)
		self.assertEqual(schedule.total_rebate, 500.0)
		self.assertEqual(schedule.total_surcharge, 200.0)
		self.assertEqual(schedule.deposit_amount, 119700.0)

	def test_before_validate_resets_portal_fields_for_new_doc(self):
		rd_acc = self._create_rd_account("RESET01")
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
			schedule_number="EXT001",
			schedule_date="2026-06-01",
			total_rebate=100,
			total_surcharge=50,
			deposit_amount=99999,
			schedule_document="/assets/some/file.pdf",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
			},
		)
		schedule.insert()

		self.assertIsNone(schedule.schedule_number)
		self.assertIsNone(schedule.schedule_date)
		self.assertEqual(schedule.total_rebate, 0.0)
		self.assertEqual(schedule.total_surcharge, 0.0)
		self.assertEqual(schedule.deposit_amount, 60000.0)

	def test_invalid_schedule_type_rejected(self):
		rd_acc = self._create_rd_account("INVTYPE01")
		schedule = self._make_rd_schedule(
			schedule_type="Invalid",
		)
		schedule.append(
			"rd_accounts",
			{
				"rd_account_number": rd_acc,
				"number_of_installments": 6,
			},
		)
		with self.assertRaises(ValidationError):
			schedule.insert()

	def test_schedule_with_no_rows_rejected(self):
		schedule = self._make_rd_schedule(
			schedule_type="Cash",
		)
		with self.assertRaises(MandatoryError):
			schedule.insert()
