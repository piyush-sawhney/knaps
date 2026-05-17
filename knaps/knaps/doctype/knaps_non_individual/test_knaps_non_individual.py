# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender"]


def create_knaps_non_individual(**kwargs):
	"""Helper function to create a KNAPS Non Individual for testing."""
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Non Individual",
			"legal_name": kwargs.get("legal_name", kwargs.get("non_individual_name", "Test Entity")),
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


NON_INDIVIDUAL_TYPES = [
	"Body of Individuals",
	"Association of Persons",
	"Hindu Undivided Family",
	"Company",
	"Limited Liability Partnership",
	"Partnership Firm",
	"Trust",
	"Government Agency",
	"Local Authority",
	"Artificial Judicial Person",
]


class IntegrationTestKNAPSNonIndividual(IntegrationTestCase):
	"""Integration tests for KNAPS Non Individual doctype."""

	doctype = "KNAPS Non Individual"

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for t in NON_INDIVIDUAL_TYPES:
			if not frappe.db.exists("KNAPS Non Individual Type", t):
				frappe.get_doc({"doctype": "KNAPS Non Individual Type", "non_individual_type": t}).insert()

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_non_individual_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_non_individual_sp")
		super().tearDown()

	# =====================================================
	# PAN VALIDATION TESTS
	# =====================================================

	def test_pan_valid_for_company(self):
		"""Test valid PAN format for Company (4th char = C)"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Company",
			non_individual_type="Company",
			pan="ABCCP1234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@company.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(entity.pan, "ABCCP1234F")

	def test_pan_valid_for_trust(self):
		"""Test valid PAN format for Trust (4th char = T)"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Trust",
			non_individual_type="Trust",
			pan="ABCTT1234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@trust.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(entity.pan, "ABCTT1234F")

	def test_pan_4th_char_mismatch_for_company(self):
		"""Test that PAN with wrong 4th character throws error for Company"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="ABCBP1234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_4th_char_mismatch_for_huf(self):
		"""Test that PAN with wrong 4th character throws error for HUF"""
		entity = create_knaps_non_individual(
			non_individual_name="Test HUF",
			non_individual_type="Hindu Undivided Family",
			pan="ABCAP1234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@huf.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_format_first_3_not_letters(self):
		"""Test that PAN with non-letter first 3 chars throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="123CP1234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_format_6_to_9_not_digits(self):
		"""Test that PAN with non-digit chars 6-9 throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="ABCCPXABCD",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_unique_validation(self):
		"""Test that duplicate PAN throws error"""
		entity1 = create_knaps_non_individual(
			non_individual_name="Entity One",
			non_individual_type="Company",
			pan="ABCCP1234A",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "entity1@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity1.insert()

		entity2 = create_knaps_non_individual(
			non_individual_name="Entity Two",
			non_individual_type="Company",
			pan="ABCCP1234A",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "entity2@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity2.insert)

	def test_pan_normalized_on_save(self):
		"""Test that PAN is normalized to uppercase"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Company",
			non_individual_type="Company",
			pan="abccp1234f",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@company.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(entity.pan, "ABCCP1234F")

	def test_no_pan_is_valid(self):
		"""Test that entity without PAN is valid"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(entity.pan, "")

	# =====================================================
	# PHONE/EMAIL VALIDATION TESTS
	# =====================================================

	def test_phone_without_primary_throws_error(self):
		"""Test that phone rows without primary throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_email_without_primary_throws_error(self):
		"""Test that email rows without primary throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_multiple_primary_phones_throws_error(self):
		"""Test that multiple primary phones throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543211",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Office",
				},
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_multiple_primary_emails_throws_error(self):
		"""Test that multiple primary emails throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test1@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				},
				{
					"email_address": "test2@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_valid_phone_and_email_primary(self):
		"""Test that valid phone and email with single primary works"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(len(entity.phone_numbers), 1)
		self.assertEqual(len(entity.email_addresses), 1)

	# =====================================================
	# PAN EDGE CASE TESTS
	# =====================================================

	def test_pan_5th_char_not_letter_throws_error(self):
		"""Test that PAN with non-letter 5th character throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="ABCC11234F",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_10th_char_not_letter_throws_error(self):
		"""Test that PAN with non-letter 10th character throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="ABCCP12341",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_less_than_10_chars_throws_error(self):
		"""Test that PAN with less than 10 characters throws error"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			pan="ABCCP123",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_pan_all_entity_types_valid(self):
		"""Test valid PAN for all entity types"""
		pan_mapping = {
			"Body of Individuals": "ABCBP1234F",
			"Association of Persons": "ABCAP1234F",
			"Hindu Undivided Family": "ABCHP1234F",
			"Company": "ABCCP1234F",
			"Limited Liability Partnership": "ABCEL1234F",
			"Partnership Firm": "ABCFP1234F",
			"Trust": "ABCTT1234F",
			"Government Agency": "ABCGP1234F",
			"Local Authority": "ABCLP1234F",
			"Artificial Judicial Person": "ABCJP1234F",
		}

		for entity_type, pan in pan_mapping.items():
			entity = create_knaps_non_individual(
				non_individual_name=f"Test {entity_type}",
				non_individual_type=entity_type,
				pan=pan,
				phone_numbers=[
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				email_addresses=[
					{
						"email_address": f"test@{entity_type.replace(' ', '').lower()}.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
				save=False,
			)
			entity.insert()

	# =====================================================
	# FIELD VALIDATION TESTS
	# =====================================================

	def test_status_inactive_valid(self):
		"""Test that status can be Inactive"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			status="Inactive",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(entity.status, "Inactive")

	def test_empty_phone_table_valid(self):
		"""Test that empty phone table is valid"""
		entity = create_knaps_non_individual(
			non_individual_name="Test Entity",
			non_individual_type="Company",
			phone_numbers=[],
			email_addresses=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
			save=False,
		)
		entity.insert()

		self.assertEqual(len(entity.phone_numbers), 0)

	# =====================================================
	# LEGAL NAME NORMALIZATION TESTS
	# =====================================================

	def test_legal_name_normalized(self):
		"""Test that legal name is trimmed and internal spaces collapsed"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "  HDFC   Mutual  Fund  ",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@hdfc.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()

		self.assertEqual(entity.legal_name, "HDFC Mutual Fund")

	# =====================================================
	# PRIMARY CONTACT VALIDATION TESTS
	# =====================================================

	def test_primary_contact_deceased_rejected(self):
		"""Test that a deceased person cannot be set as primary contact"""
		person = frappe.get_doc(
			{
				"doctype": "KNAPS Person",
				"first_name": "Deceased Person",
				"salutation": "Mr",
				"gender": "Male",
				"status": "Deceased",
			}
		).insert()

		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Corp",
				"non_individual_type": "Company",
				"status": "Active",
				"primary_contact": person.name,
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@corp.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_primary_contact_active_accepted(self):
		"""Test that an active person can be set as primary contact"""
		person = frappe.get_doc(
			{
				"doctype": "KNAPS Person",
				"first_name": "Active Person",
				"salutation": "Mr",
				"gender": "Male",
				"status": "Active",
			}
		).insert()

		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Corp",
				"non_individual_type": "Company",
				"status": "Active",
				"primary_contact": person.name,
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@corp.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()

		self.assertEqual(entity.primary_contact, person.name)

	def test_primary_contact_empty_valid(self):
		"""Test that entity without primary contact is valid"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "No Contact Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@nocontact.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()

		self.assertIsNone(entity.primary_contact)

	# =====================================================
	# INACTIVE CHILD TABLE VALIDATION TESTS
	# =====================================================

	def test_inactive_phone_cannot_be_primary(self):
		"""Test that inactive phone marked as primary throws error"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 0,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@example.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_inactive_email_cannot_be_primary(self):
		"""Test that inactive email marked as primary throws error"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@example.com",
						"is_primary": 1,
						"is_active": 0,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	# =====================================================
	# DUPLICATE CHILD TABLE TESTS
	# =====================================================

	def test_duplicate_phone_rejected(self):
		"""Test that duplicate phone numbers in child table throw error"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					},
					{
						"number": "+91 9876543210",
						"is_primary": 0,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Office",
					},
				],
				"email_addresses": [
					{
						"email_address": "test@example.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	def test_duplicate_email_rejected(self):
		"""Test that duplicate email addresses in child table throw error"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@example.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					},
					{
						"email_address": "test@example.com",
						"is_primary": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Personal",
					},
				],
			}
		)

		self.assertRaises(frappe.ValidationError, entity.insert)

	# =====================================================
	# ADDRESS DELETION TESTS
	# =====================================================

	def test_address_deleted_when_non_individual_deleted(self):
		"""Test that exclusively-linked Address is deleted when Non Individual is deleted"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Corp Address Delete",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "test@corp.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()

		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Corporate Office",
				"address_line1": "789 Business Park",
				"city": "Bangalore",
				"links": [{"link_doctype": entity.doctype, "link_name": entity.name}],
			}
		).insert()

		self.assertTrue(frappe.db.exists("Address", address.name))
		entity.delete()
		self.assertFalse(frappe.db.exists("Address", address.name))

	def test_shared_address_not_deleted_when_one_non_individual_deleted(self):
		"""Test that shared Address only loses the link row when one Non Individual is deleted"""
		entity_a = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Company A",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "a@company.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()
		entity_b = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Company B",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543211",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "b@company.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()

		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Co-working Space",
				"address_line1": "100 Shared Ave",
				"city": "Mumbai",
				"links": [
					{"link_doctype": entity_a.doctype, "link_name": entity_a.name},
					{"link_doctype": entity_b.doctype, "link_name": entity_b.name},
				],
			}
		).insert()

		entity_a.delete()

		self.assertTrue(frappe.db.exists("Address", address.name))
		address.reload()
		self.assertEqual(len(address.links), 1)
		self.assertEqual(address.links[0].link_name, entity_b.name)

	def test_delete_non_individual_without_address_succeeds(self):
		"""Test that deleting a Non Individual with no linked Address does not raise"""
		entity = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Minimal Entity",
				"non_individual_type": "Company",
				"status": "Active",
				"phone_numbers": [
					{
						"number": "+91 9876543210",
						"is_primary": 1,
						"is_whatsapp": 0,
						"is_active": 1,
						"ownership": "Self",
						"type": "Mobile",
					}
				],
				"email_addresses": [
					{
						"email_address": "minimal@corp.com",
						"is_primary": 1,
						"is_active": 1,
						"ownership": "Self",
						"type": "Official",
					}
				],
			}
		).insert()
		entity.delete()
