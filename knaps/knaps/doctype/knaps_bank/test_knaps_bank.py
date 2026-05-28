import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, nowdate

from knaps.utils.constants import (
	DOCTYPE_BANK,
	DOCTYPE_HOLDING_TYPE,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL,
)

MINOR_DOB = add_months(nowdate(), -12 * 10)
ADULT_DOB = add_months(nowdate(), -12 * 30)


def create_holding_type(name):
	if not frappe.db.exists(DOCTYPE_HOLDING_TYPE, name):
		frappe.get_doc({"doctype": DOCTYPE_HOLDING_TYPE, "holding_type": name}).insert()
	return name


def create_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_INDIVIDUAL,
			"first_name": kwargs.get("first_name", "Test"),
			"last_name": kwargs.get("last_name", "Person"),
			"salutation": kwargs.get("salutation", "Mr"),
			"gender": kwargs.get("gender", "Male"),
			"date_of_birth": kwargs.get("date_of_birth"),
			"status": kwargs.get("status", "Active"),
			"phone_numbers": kwargs.get("phone_numbers", []),
			"email_address": kwargs.get("email_address", []),
		}
	)
	doc.insert()
	return doc


def create_non_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_NON_INDIVIDUAL,
			"legal_name": kwargs.get("legal_name", "Test Entity"),
			"non_individual_type": kwargs.get("non_individual_type", "Company"),
			"status": kwargs.get("status", "Active"),
			"pan": kwargs.get("pan", ""),
			"phone_numbers": kwargs.get("phone_numbers", []),
			"email_addresses": kwargs.get("email_addresses", []),
		}
	)
	doc.insert()
	return doc


class IntegrationTestKNAPSBank(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for t in ["Single", "Anyone or Survivor", "Joint"]:
			create_holding_type(t)

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_bank_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_bank_sp")
		super().tearDown()

	def _make_bank(self, holders=None, **kwargs):
		defaults = dict(
			bank_name="Test Bank",
			account_number=frappe.generate_hash("acc", 10),
			ifsc="HDFC0001234",
			account_type="Saving",
			holding_type="Single",
			is_active=1,
			is_name_same=1,
		)
		data = {**defaults, **kwargs}
		if holders is None:
			person = create_individual(first_name="Default")
			data["holders"] = [
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			]
		else:
			data["holders"] = holders
		doc = frappe.get_doc({"doctype": DOCTYPE_BANK, **data})
		doc.insert()
		return doc

	# --- Rule 2: Individual + Single ---

	def test_individual_single_one_first_passes(self):
		bank = self._make_bank()
		self.assertIsNotNone(bank.name)

	def test_individual_single_second_holder_rejected(self):
		first = create_individual(first_name="First")
		second = create_individual(first_name="Second")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": first.name},
					{"order": "Second", "holder_type": DOCTYPE_INDIVIDUAL, "holder": second.name},
				],
			)

	# --- Rule 3: Individual + Non-Single ---

	def test_individual_nonsingle_one_holder_rejected(self):
		person = create_individual(first_name="Solo")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Anyone or Survivor",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	def test_individual_nonsingle_two_holders_passes(self):
		first = create_individual(first_name="First")
		second = create_individual(first_name="Second")
		bank = self._make_bank(
			holding_type="Anyone or Survivor",
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": first.name},
				{"order": "Second", "holder_type": DOCTYPE_INDIVIDUAL, "holder": second.name},
			],
		)
		self.assertIsNotNone(bank.name)

	# --- Rule 4: Individual + Minor ---

	def test_individual_single_minor_with_guardian_passes(self):
		minor = create_individual(first_name="Minor", date_of_birth=MINOR_DOB)
		guardian = create_individual(first_name="Guardian")
		bank = self._make_bank(
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": minor.name},
				{
					"order": "Guardian",
					"holder_type": DOCTYPE_INDIVIDUAL,
					"holder": guardian.name,
				},
			],
		)
		self.assertIsNotNone(bank.name)

	def test_individual_single_minor_no_guardian_rejected(self):
		minor = create_individual(first_name="Minor", date_of_birth=MINOR_DOB)
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": minor.name},
				],
			)

	def test_individual_single_guardian_is_minor_rejected(self):
		minor = create_individual(first_name="Minor", date_of_birth=MINOR_DOB)
		guardian = create_individual(first_name="Guardian", date_of_birth=MINOR_DOB)
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": minor.name},
					{
						"order": "Guardian",
						"holder_type": DOCTYPE_INDIVIDUAL,
						"holder": guardian.name,
					},
				],
			)

	def test_individual_single_guardian_without_minor_rejected(self):
		adult = create_individual(first_name="Adult")
		guardian = create_individual(first_name="Guardian")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": adult.name},
					{
						"order": "Guardian",
						"holder_type": DOCTYPE_INDIVIDUAL,
						"holder": guardian.name,
					},
				],
			)

	# --- Rule 5: Non Individual ---

	def test_non_individual_one_first_passes(self):
		entity = create_non_individual(legal_name="Acme Corp")
		bank = self._make_bank(
			holders=[
				{"order": "First", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": entity.name},
			],
		)
		self.assertIsNotNone(bank.name)

	def test_non_individual_two_holders_rejected(self):
		entity = create_non_individual(legal_name="Acme Corp")
		second = create_non_individual(legal_name="Beta Corp")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Anyone or Survivor",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": entity.name},
					{"order": "Second", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": second.name},
				],
			)

	def test_non_individual_non_single_holding_rejected(self):
		entity = create_non_individual(legal_name="Acme Corp")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Anyone or Survivor",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": entity.name},
				],
			)

	def test_non_individual_saving_msgprint(self):
		entity = create_non_individual(legal_name="Acme Corp")
		bank = self._make_bank(
			account_type="Saving",
			holders=[
				{"order": "First", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": entity.name},
			],
		)
		self.assertIsNotNone(bank.name)

	# --- Mixed Types ---

	def test_mixed_individual_non_individual_rejected(self):
		person = create_individual(first_name="Person")
		entity = create_non_individual(legal_name="Acme Corp")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Joint",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
					{
						"order": "Second",
						"holder_type": DOCTYPE_NON_INDIVIDUAL,
						"holder": entity.name,
					},
				],
			)

	# --- Duplicate Checks ---

	def test_same_holder_duplicate_order_rejected(self):
		person = create_individual(first_name="Dupe")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Joint",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	def test_same_holder_different_orders_rejected(self):
		person = create_individual(first_name="Dupe")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Anyone or Survivor",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
					{"order": "Second", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	# --- Duplicate order check ---

	def test_duplicate_orders_rejected(self):
		first = create_individual(first_name="First")
		second = create_individual(first_name="Second")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Joint",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": first.name},
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": second.name},
				],
			)

	# --- Minor position check ---

	def test_minor_not_in_first_position_rejected(self):
		first = create_individual(first_name="First")
		minor = create_individual(first_name="Minor", date_of_birth=MINOR_DOB)
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Joint",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": first.name},
					{"order": "Second", "holder_type": DOCTYPE_INDIVIDUAL, "holder": minor.name},
				],
			)

	# --- IFSC ---

	def test_invalid_ifsc_rejected(self):
		person = create_individual(first_name="Test")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				ifsc="INVALID",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	def test_ifsc_lowercase_rejected(self):
		person = create_individual(first_name="Test")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				ifsc="hdfc0001234",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	def test_ifsc_without_zero_at_5th_rejected(self):
		person = create_individual(first_name="Test")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				ifsc="HDFCC001234",
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
				],
			)

	# --- Duplicate account number ---

	def test_duplicate_account_number_rejected(self):
		person1 = create_individual(first_name="One")
		person2 = create_individual(first_name="Two")
		account_number = "UNIQUEACC01"
		bank = self._make_bank(
			account_number=account_number,
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person1.name},
			],
		)
		self.assertIsNotNone(bank.name)
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				account_number=account_number,
				holders=[
					{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person2.name},
				],
			)

	# --- primary_holder_name with is_name_same ---

	def test_primary_holder_name_populated_when_name_same(self):
		person = create_individual(first_name="John", last_name="Doe")
		bank = self._make_bank(
			is_name_same=1,
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			],
		)
		self.assertEqual(bank.primary_holder_name, "Mr John Doe")

	def test_primary_holder_name_not_overwritten_when_name_not_same(self):
		person = create_individual(first_name="John", last_name="Doe")
		custom_name = "John D. Enterprises"
		bank = self._make_bank(
			is_name_same=0,
			primary_holder_name=custom_name,
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			],
		)
		self.assertEqual(bank.primary_holder_name, custom_name)

	def test_primary_holder_name_from_non_individual(self):
		entity = create_non_individual(legal_name="Acme Corp")
		bank = self._make_bank(
			is_name_same=1,
			holders=[
				{"order": "First", "holder_type": DOCTYPE_NON_INDIVIDUAL, "holder": entity.name},
			],
		)
		self.assertEqual(bank.primary_holder_name, "Acme Corp")

	# --- Title ---

	def test_title_from_holder_name_and_account(self):
		person = create_individual(first_name="John", last_name="Doe")
		bank = self._make_bank(
			account_number="HDFC0012345",
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			],
		)
		self.assertEqual(bank.title, "Mr John Doe - 2345")

	def test_title_with_only_holder_name(self):
		person = create_individual(first_name="Jane", last_name="Doe")
		bank = self._make_bank(
			account_number="SHORT",
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			],
		)
		self.assertEqual(bank.title, "Mr Jane Doe - HORT")

	def test_title_without_holder_name(self):
		person = create_individual(first_name="NoName", last_name="")
		bank = self._make_bank(
			holders=[
				{"order": "First", "holder_type": DOCTYPE_INDIVIDUAL, "holder": person.name},
			],
		)
		self.assertTrue(bank.title.endswith(bank.account_number[-4:]))
