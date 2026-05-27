import frappe
from frappe.tests import IntegrationTestCase

from knaps.utils.constants import (
	DOCTYPE_LEAD_SOURCE,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestKNAPSLeadSource(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_lead_source_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_lead_source_sp")
		super().tearDown()

	def test_create_lead_source(self):
		source = frappe.get_doc(
			{
				"doctype": DOCTYPE_LEAD_SOURCE,
				"source_name": "Online Ad",
			}
		)
		source.insert()

		self.assertEqual(source.source_name, "Online Ad")
		self.assertTrue(source.name)
