# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

from dateutil.relativedelta import relativedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate, today


class IntegrationTestKNAPSClient(IntegrationTestCase):
	"""Integration tests for KNAPSClient."""

	def setUp(self):
		self.individual = frappe.get_doc(
			{
				"doctype": "KNAPS Individual",
				"first_name": "John",
				"middle_name": "M",
				"last_name": "Doe",
				"salutation": "Mr",
				"gender": "Male",
				"status": "Active",
				"date_of_birth": (getdate(today()) - relativedelta(years=30)),
				"pan": "ABCPD1234E",
			}
		).insert()

	def tearDown(self):
		frappe.db.rollback()

	def _make_client(self, **kwargs):
		defaults = {"client_type": "Individual", "individual": self.individual.name}
		defaults.update(kwargs)
		return frappe.get_doc({"doctype": "KNAPS Client", **defaults})

	def test_syncs_data_from_individual_on_save(self):
		client = self._make_client()
		client.insert()

		self.assertEqual(client.client_name, "Mr John M Doe")
		self.assertEqual(client.pan, "ABCPD1234E")
		self.assertEqual(client.status, "Active")
		self.assertEqual(client.primary_phone, self.individual.primary_phone)
		self.assertEqual(client.primary_whatsapp, self.individual.primary_whatsapp)
		self.assertEqual(client.primary_email, self.individual.primary_email)
		self.assertEqual(client.preferred_contact_mode, self.individual.preferred_contact_mode)
		self.assertEqual(client.is_minor, 0)

	def test_marks_as_minor_when_individual_is_under_18(self):
		minor_dob = getdate(today()) - relativedelta(years=16)
		minor_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Individual",
				"first_name": "Jane",
				"salutation": "Ms",
				"gender": "Female",
				"status": "Active",
				"date_of_birth": minor_dob,
				"pan": "XYZPP5678K",
			}
		).insert()

		client = self._make_client(individual=minor_individual.name)
		client.insert()
		self.assertEqual(client.is_minor, 1)

	def test_syncs_data_from_non_individual_on_save(self):
		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Acme Corp",
				"non_individual_type": "Company",
				"status": "Active",
				"pan": "AABCC1234D",
			}
		).insert()

		client = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		client.insert()

		self.assertEqual(client.client_name, "Acme Corp")
		self.assertEqual(client.pan, "AABCC1234D")
		self.assertEqual(client.status, "Active")
		self.assertEqual(client.is_minor, 0)
		self.assertIsNone(client.individual)
		self.assertIsNone(client.primary_phone)
		self.assertIsNone(client.primary_email)
		self.assertIsNone(client.preferred_contact_mode)

	def test_syncs_data_from_non_individual_with_primary_contact(self):
		primary = frappe.get_doc(
			{
				"doctype": "KNAPS Individual",
				"first_name": "Alice",
				"salutation": "Ms",
				"gender": "Female",
				"status": "Active",
				"pan": "ZYXPW9876A",
				"preferred_contact_mode": "Phone",
				"phone_numbers": [
					{"number": "+919876543210", "is_primary": 1, "is_active": 1},
				],
				"email_address": [
					{"email_address": "alice@example.com", "is_primary": 1, "is_active": 1},
				],
			}
		).insert()

		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Beta Corp",
				"non_individual_type": "Company",
				"status": "Active",
				"pan": "BBCCE5678F",
			}
		).insert()

		non_individual.append("contacts", {
			"individual": primary.name,
			"designation": "Director",
			"is_primary_contact": 1,
		})
		non_individual.save()

		client = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		client.insert()

		self.assertEqual(client.client_name, "Beta Corp")
		self.assertEqual(client.non_individual, non_individual.name)
		self.assertEqual(client.individual, primary.name)
		self.assertEqual(client.primary_phone, primary.primary_phone)
		self.assertEqual(client.primary_email, primary.primary_email)
		self.assertEqual(client.preferred_contact_mode, primary.preferred_contact_mode)
		self.assertEqual(client.is_minor, 0)

	def test_sets_primary_contact_as_individual_when_changing_to_non_individual(self):
		primary = frappe.get_doc(
			{
				"doctype": "KNAPS Individual",
				"first_name": "Primary",
				"salutation": "Mr",
				"gender": "Male",
				"status": "Active",
				"pan": "PRIPM1234X",
			}
		).insert()

		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Beta LLC",
				"non_individual_type": "Limited Liability Partnership",
				"status": "Active",
				"pan": "AABEF5678G",
			}
		).insert()

		non_individual.append("contacts", {
			"individual": primary.name,
			"designation": "Director",
			"is_primary_contact": 1,
		})
		non_individual.save()

		client = self._make_client(non_individual=non_individual.name)
		client.client_type = "Non Individual"
		client.save()

		self.assertEqual(client.individual, primary.name)
		self.assertEqual(client.non_individual, non_individual.name)

	def test_clears_incompatible_link_when_changing_to_individual(self):
		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Gamma Inc",
				"non_individual_type": "Company",
				"status": "Active",
				"pan": "AABCG9012I",
			}
		).insert()

		client = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		client.insert()

		client.client_type = "Individual"
		client.individual = self.individual.name
		client.save()

		self.assertIsNone(client.non_individual)
		self.assertEqual(client.individual, self.individual.name)

	def test_sole_proprietor_does_not_overwrite_existing_client_name(self):
		client = self._make_client(
			client_type="Sole Proprietor",
			client_name="John's Consulting",
		)
		client.insert()

		self.assertEqual(client.client_name, "John's Consulting")

	def test_sanitizes_proprietor_name_on_save(self):
		client = self._make_client(
			client_type="Sole Proprietor",
			client_name="  John's   Consulting  ",
		)
		client.insert()
		self.assertEqual(client.client_name, "John's Consulting")

	def test_throws_when_proprietor_name_missing(self):
		client = self._make_client(
			client_type="Sole Proprietor",
			client_name=None,
		)
		with self.assertRaises(frappe.ValidationError):
			client.insert()

	def test_throws_when_proprietor_name_whitespace_only(self):
		client = self._make_client(
			client_type="Sole Proprietor",
			client_name="   ",
		)
		with self.assertRaises(frappe.ValidationError):
			client.insert()

	def test_throws_when_linked_individual_does_not_exist(self):
		client = self._make_client(individual="non-existent-uuid")
		with self.assertRaises(frappe.ValidationError):
			client.insert()

	def test_throws_when_individual_missing_for_individual_type(self):
		client = self._make_client(individual=None)
		with self.assertRaises(frappe.ValidationError):
			client.insert()

	def test_throws_when_non_individual_missing_for_non_individual_type(self):
		client = self._make_client(client_type="Non Individual", individual=None)
		with self.assertRaises(frappe.ValidationError):
			client.insert()

	def test_rejects_duplicate_pan_for_non_individual(self):
		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Shared Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"pan": "AABCC1234D",
			}
		).insert()

		first = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		first.insert()

		second = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		with self.assertRaises(frappe.ValidationError):
			second.insert()

	def test_allows_same_pan_across_individual_and_sole_proprietor(self):
		client = self._make_client()
		client.insert()

		sole = self._make_client(
			client_type="Sole Proprietor",
			client_name="John's Shop",
		)
		sole.insert()

		self.assertEqual(sole.pan, "ABCPD1234E")

	def test_rejects_duplicate_name_and_pan_for_individual(self):
		first = self._make_client()
		first.insert()

		second = self._make_client()
		with self.assertRaises(frappe.ValidationError):
			second.insert()

	def test_pan_spaces_do_not_interfere_between_individual_and_non_individual(self):
		client = self._make_client()
		client.insert()

		non_individual = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Separate Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"pan": "AABCC1234D",
			}
		).insert()

		ni_client = self._make_client(
			client_type="Non Individual",
			individual=None,
			non_individual=non_individual.name,
		)
		ni_client.insert()
		self.assertEqual(ni_client.pan, "AABCC1234D")
