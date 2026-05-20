# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


def create_holding_type(name):
	if not frappe.db.exists("KNAPS Holding Type", name):
		frappe.get_doc({"doctype": "KNAPS Holding Type", "holding_type": name}).insert()
	return name


def create_knaps_person(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Person",
			"first_name": kwargs.get("first_name", "Test Person"),
			"last_name": kwargs.get("last_name", ""),
			"salutation": kwargs.get("salutation", "Mr"),
			"gender": kwargs.get("gender", "Male"),
			"status": kwargs.get("status", "Active"),
			"phone_numbers": kwargs.get("phone_numbers", []),
			"email_address": kwargs.get("email_address", []),
		}
	)
	if kwargs.get("save", True):
		doc.insert()
	return doc


def create_knaps_non_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Non Individual",
			"legal_name": kwargs.get("legal_name", "Test Entity"),
			"non_individual_type": kwargs.get("non_individual_type", "Company"),
			"status": kwargs.get("status", "Active"),
			"pan": kwargs.get("pan", ""),
			"phone_numbers": kwargs.get("phone_numbers", []),
			"email_addresses": kwargs.get("email_addresses", []),
		}
	)
	if kwargs.get("save", True):
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

	def _make_bank(self, **kwargs):
		defaults = dict(
			bank_name="Test Bank",
			bank_account_number=frappe.generate_hash("acc", 10),
			ifsc="HDFC0001234",
			holder_type="KNAPS Person",
			holding_type="Single",
		)
		data = {**defaults, **kwargs}
		if "first_holder" not in data:
			person = create_knaps_person(first_name="Default")
			data["first_holder"] = person.name
		doc = frappe.get_doc({"doctype": "KNAPS Bank", **data})
		doc.insert()
		return doc

	def test_valid_bank_passes(self):
		bank = self._make_bank()
		self.assertIsNotNone(bank.name)

	def test_invalid_ifsc_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(ifsc="INVALID")

	def test_invalid_ifsc_wrong_length_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(ifsc="HDFC0XXXX")

	def test_second_holder_non_person_rejected(self):
		entity = create_knaps_non_individual()
		person = create_knaps_person()
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				first_holder=entity.name,
				holder_type="KNAPS Non Individual",
				second_holder=person.name,
			)

	def test_second_holder_single_holding_rejected(self):
		second = create_knaps_person(first_name="Second")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				holding_type="Single",
				second_holder=second.name,
			)

	def test_second_holder_same_as_first_rejected(self):
		same = create_knaps_person(first_name="Same")
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(
				first_holder=same.name,
				holding_type="Anyone or Survivor",
				second_holder=same.name,
			)

	def test_first_holder_name_populated_from_person(self):
		person = create_knaps_person(first_name="John", last_name="Doe")
		bank = self._make_bank(first_holder=person.name)
		self.assertEqual(bank.first_holder_name, "Mr John Doe")

	def test_first_holder_name_populated_from_non_individual(self):
		entity = create_knaps_non_individual(legal_name="Acme Corp")
		bank = self._make_bank(
			first_holder=entity.name,
			holder_type="KNAPS Non Individual",
		)
		self.assertEqual(bank.first_holder_name, "Acme Corp")

	def test_valid_second_holder_passes(self):
		person = create_knaps_person(first_name="First")
		second = create_knaps_person(first_name="Second")
		bank = self._make_bank(
			first_holder=person.name,
			holding_type="Anyone or Survivor",
			second_holder=second.name,
		)
		self.assertIsNotNone(bank.name)

	def test_clearing_second_holder_removes_second_holder_name(self):
		person = create_knaps_person(first_name="First")
		second = create_knaps_person(first_name="Second")
		bank = self._make_bank(
			first_holder=person.name,
			holding_type="Anyone or Survivor",
			second_holder=second.name,
		)
		self.assertIsNotNone(bank.second_holder_name)
		bank.second_holder = None
		bank.save()
		self.assertIsNone(bank.second_holder_name)

	def test_title_from_holder_name_and_account(self):
		person = create_knaps_person(first_name="John", last_name="Doe")
		bank = self._make_bank(
			first_holder=person.name,
			bank_account_number="HDFC0012345",
		)
		self.assertEqual(bank.title, "Mr John Doe - 2345")

	def test_ifsc_lowercase_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(ifsc="hdfc0001234")

	def test_ifsc_without_zero_at_5th_char_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(ifsc="HDFCC001234")

	def test_ifsc_with_digits_in_first_4_chars_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_bank(ifsc="12DF0001234")

	def test_second_holder_name_populated_from_person(self):
		person = create_knaps_person(first_name="First", last_name="Holder")
		second = create_knaps_person(first_name="Second", last_name="Person")
		bank = self._make_bank(
			first_holder=person.name,
			holding_type="Anyone or Survivor",
			second_holder=second.name,
		)
		self.assertEqual(bank.second_holder_name, "Mr Second Person")

	def test_title_with_only_holder_name(self):
		person = create_knaps_person(first_name="John", last_name="Doe")
		bank = self._make_bank(
			first_holder=person.name,
			bank_account_number="HDFC0000001",
		)
		self.assertEqual(bank.title, "Mr John Doe - 0001")

	def test_title_from_last_four_digits_with_short_account(self):
		person = create_knaps_person(first_name="Jane", last_name="Doe")
		bank = self._make_bank(
			first_holder=person.name,
			bank_account_number="123",
		)
		self.assertEqual(bank.title, "Mr Jane Doe - 123")

	def test_populate_first_holder_name_without_last_name(self):
		person = create_knaps_person(first_name="SingleName", last_name="")
		bank = self._make_bank(first_holder=person.name)
		self.assertEqual(bank.first_holder_name, "Mr SingleName")
