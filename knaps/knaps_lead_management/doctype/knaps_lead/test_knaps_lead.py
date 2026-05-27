# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase

from knaps.utils.constants import (
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_LEAD,
	DOCTYPE_NON_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
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
			"preferred_contact_mode": kwargs.get("preferred_contact_mode", "Phone"),
		}
	)
	if kwargs.get("save", True):
		doc.insert()
	return doc


def create_test_non_individual(**kwargs):
	individual = kwargs.get("primary_contact") or create_test_individual(
		first_name="Primary", last_name="Contact", save=True
	)
	entity = frappe.get_doc(
		{
			"doctype": DOCTYPE_NON_INDIVIDUAL,
			"legal_name": kwargs.get("legal_name", "Test Entity Pvt Ltd"),
			"non_individual_type": kwargs.get("non_individual_type", "Company"),
			"status": kwargs.get("status", "Active"),
			"contacts": [
				{
					"individual": individual.name,
					"designation": "Director",
					"is_primary_contact": 1,
				}
			],
			"phone_numbers": [
				{
					"number": "+91 9876543000",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			"email_addresses": [
				{
					"email_address": "entity@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
		}
	)
	if kwargs.get("save", True):
		entity.insert()
	return entity, individual


class IntegrationTestKNAPSLead(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_lead_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_lead_sp")
		super().tearDown()

	def _make_lead(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_LEAD,
			"status": "New",
			"source": "Walk-In",
		}
		data = {**defaults, **kwargs}
		doc = frappe.get_doc(data)
		doc.insert()
		return doc

	def test_individual_lead_syncs_contact_fields(self):
		individual = create_test_individual(
			first_name="John",
			last_name="Doe",
			phone="+91 9999999999",
			email="john@example.com",
			preferred_contact_mode="Phone",
		)

		lead = self._make_lead(
			lead_type=DOCTYPE_INDIVIDUAL,
			lead=individual.name,
			lead_interested_in=[{"product": "Mutual Funds"}],
		)

		self.assertEqual(lead.lead_name, "Mr John Doe")
		self.assertEqual(lead.phone, "+91 9999999999")
		self.assertEqual(lead.whatsapp, "+91 9999999999")
		self.assertEqual(lead.email, "john@example.com")
		self.assertEqual(lead.preferred_contact_mode, "Phone")
		self.assertIsNone(lead.primary_contact)

	def test_non_individual_lead_syncs_primary_contact_fields(self):
		individual = create_test_individual(
			first_name="Jane",
			last_name="Doe",
			phone="+91 8888888888",
			email="jane@example.com",
			preferred_contact_mode="Email",
		)
		entity, _ = create_test_non_individual(
			legal_name="Acme Corp",
			primary_contact=individual,
		)

		lead = self._make_lead(
			lead_type=DOCTYPE_NON_INDIVIDUAL,
			lead=entity.name,
			lead_interested_in=[{"product": "Life Insurance"}],
		)

		self.assertEqual(lead.lead_name, "Acme Corp")
		self.assertEqual(lead.primary_contact, individual.name)
		self.assertEqual(lead.phone, "+91 8888888888")
		self.assertEqual(lead.whatsapp, "+91 8888888888")
		self.assertEqual(lead.email, "jane@example.com")
		self.assertEqual(lead.preferred_contact_mode, "Email")
