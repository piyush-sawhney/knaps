import unittest

import frappe
from frappe.tests import IntegrationTestCase

from knaps.utils.constants import (
	DOCTYPE_CLIENT,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
	DOCTYPE_OPPORTUNITY,
)

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender", DOCTYPE_NON_INDIVIDUAL_TYPE]
IGNORE_TEST_RECORD_DEPENDENCIES = []


def create_test_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_INDIVIDUAL,
			"first_name": kwargs.get("first_name", "Test"),
			"last_name": kwargs.get("last_name", "Individual"),
			"salutation": kwargs.get("salutation", "Mr"),
			"gender": kwargs.get("gender", "Male"),
			"status": kwargs.get("status", "Active"),
			"phone_numbers": [
				{
					"number": kwargs.get("phone", "+91 9876543210"),
					"is_primary": 1,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			"email_address": [
				{
					"email_address": kwargs.get("email", "test@example.com"),
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
		}
	)
	if kwargs.get("save", True):
		doc.insert()
	return doc


def create_test_client(**kwargs):
	individual = kwargs.get("individual") or create_test_individual(
		first_name="Client", last_name="User", save=True
	)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_CLIENT,
			"client_type": kwargs.get("client_type", "Individual"),
			"individual": individual.name,
			"client_name": kwargs.get("client_name", "Test Client"),
			"primary_phone": kwargs.get("phone"),
			"primary_whatsapp": kwargs.get("phone"),
			"primary_email": kwargs.get("email"),
		}
	)
	if kwargs.get("save", True):
		doc.insert()
	return doc, individual


class IntegrationTestKNAPSOpportunity(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_opportunity_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_opportunity_sp")
		super().tearDown()

	def _make_opportunity(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_OPPORTUNITY,
			"status": "New",
			"source": "Walk-In",
		}
		data = {**defaults, **kwargs}
		doc = frappe.get_doc(data)
		doc.insert()
		return doc

	def test_client_syncs_contact_fields(self):
		individual = create_test_individual(
			first_name="Jane",
			last_name="Doe",
			phone="+91 7777777777",
			email="jane@example.com",
		)
		client, _ = create_test_client(individual=individual)

		opp = self._make_opportunity(
			client=client.name,
			opportunity_type=[{"product": "Mutual Funds"}],
		)

		self.assertEqual(opp.client_name, client.client_name)
		self.assertEqual(opp.phone, client.primary_phone)
		self.assertEqual(opp.whatsapp, client.primary_whatsapp)
		self.assertEqual(opp.email, client.primary_email)

	@unittest.skip("Propagation not implemented")
	def test_propagates_client_name_change_to_opportunity(self):
		individual = create_test_individual(
			first_name="Alice",
			last_name="Brown",
			phone="+91 6666666666",
			email="alice@example.com",
		)
		client, _ = create_test_client(individual=individual)

		opp = self._make_opportunity(
			client=client.name,
			opportunity_type=[{"product": "Mutual Funds"}],
		)

		client.client_name = "Alice B. Updated"
		client.save()

		opp.reload()
		self.assertEqual(opp.client_name, "Alice B. Updated")

	@unittest.skip("Propagation not implemented")
	def test_propagates_client_phone_change_to_opportunity(self):
		individual = create_test_individual(
			first_name="Bob",
			last_name="Lee",
			phone="+91 7777777777",
			email="bob@example.com",
		)
		client, _ = create_test_client(individual=individual)

		opp = self._make_opportunity(
			client=client.name,
			opportunity_type=[{"product": "Life Insurance"}],
		)

		client.primary_phone = "+91 5555555555"
		client.primary_whatsapp = "+91 5555555555"
		client.save()

		opp.reload()
		self.assertEqual(opp.phone, "+91 5555555555")
		self.assertEqual(opp.whatsapp, "+91 5555555555")

	def test_duplicate_opportunity_rejected(self):
		client, _ = create_test_client()
		self._make_opportunity(
			client=client.name,
			opportunity_type=[{"product": "Mutual Funds"}],
		)

		with self.assertRaises(frappe.ValidationError):
			self._make_opportunity(
				client=client.name,
				opportunity_type=[{"product": "Life Insurance"}],
			)

	def test_duplicate_allowed_for_terminal_status(self):
		client, _ = create_test_client()
		self._make_opportunity(
			client=client.name,
			status="Lost",
			opportunity_type=[{"product": "Mutual Funds"}],
		)

		opp2 = self._make_opportunity(
			client=client.name,
			status="New",
			opportunity_type=[{"product": "Life Insurance"}],
		)
		self.assertTrue(opp2.name)

	def test_duplicate_allowed_on_same_doc(self):
		client, _ = create_test_client()
		opp = self._make_opportunity(
			client=client.name,
			opportunity_type=[{"product": "Mutual Funds"}],
		)

		opp.opportunity_type = []
		opp.append("opportunity_type", {"product": "Life Insurance"})
		opp.save()
		self.assertEqual(len(opp.opportunity_type), 1)
