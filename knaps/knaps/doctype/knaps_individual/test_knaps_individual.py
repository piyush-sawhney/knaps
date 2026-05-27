# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase

from knaps.utils.constants import (
	DOCTYPE_INDIVIDUAL,
)

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender"]


def create_knaps_individual(**kwargs):
	"""Helper function to create a KNAPS Individual for testing."""
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_INDIVIDUAL,
			"first_name": kwargs.get("first_name", "Test"),
			"middle_name": kwargs.get("middle_name", ""),
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


class IntegrationTestKNAPSIndividual(IntegrationTestCase):
	"""Integration tests for KNAPS Individual doctype."""

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_individual_sp")

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_individual_sp")
		super().tearDown()

	# =====================================================
	# FULL NAME AUTO-CALCULATION TESTS
	# =====================================================

	def test_full_name_first_and_last(self):
		"""Test full name calculation with first and last name only."""
		individual = create_knaps_individual(first_name="John", last_name="Doe", save=False)
		individual.insert()

		self.assertEqual(individual.full_name, "Mr John Doe")

	def test_full_name_all_three(self):
		"""Test full name calculation with first, middle, and last name."""
		individual = create_knaps_individual(
			first_name="John", middle_name="Michael", last_name="Doe", save=False
		)
		individual.insert()

		self.assertEqual(individual.full_name, "Mr John Michael Doe")

	def test_full_name_only_first(self):
		"""Test full name when only first name is provided."""
		individual = create_knaps_individual(first_name="John", save=False)
		individual.insert()

		self.assertEqual(individual.full_name, "Mr John")

	def test_full_name_whitespace_trimmed(self):
		"""Test that whitespace is properly trimmed from name components."""
		individual = create_knaps_individual(
			first_name="  John  ", middle_name="  Michael  ", last_name="  Doe  ", save=False
		)
		individual.insert()

		self.assertEqual(individual.full_name, "Mr John Michael Doe")

	# =====================================================
	# PRIMARY PHONE SYNC TESTS
	# =====================================================

	# =====================================================
	# VALIDATION TESTS - SINGLE PRIMARY
	# =====================================================

	def test_duplicate_primary_phone_throws_error(self):
		"""Test that saving with multiple primary phones throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
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
					"type": "Mobile",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_duplicate_whatsapp_throws_error(self):
		"""Test that saving with multiple WhatsApp phones throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543211",
					"is_primary": 0,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_duplicate_primary_email_throws_error(self):
		"""Test that saving with multiple primary emails throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			email_address=[
				{
					"email_address": "john1@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				},
				{
					"email_address": "john2@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	# =====================================================
	# VALIDATION TESTS - AT LEAST ONE PRIMARY
	# =====================================================

	def test_phone_without_primary_throws_error(self):
		"""Test that saving phone rows without any primary throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
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
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_email_without_primary_throws_error(self):
		"""Test that saving email rows without any primary throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	# =====================================================
	# VALIDATION TESTS - INACTIVE CANNOT BE PRIMARY
	# =====================================================

	def test_inactive_phone_cannot_be_primary(self):
		"""Test that inactive phone with is_primary throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 0,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_inactive_phone_cannot_be_whatsapp(self):
		"""Test that inactive phone with is_whatsapp throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 1,
					"is_active": 0,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_inactive_email_cannot_be_primary(self):
		"""Test that inactive email with is_primary throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 0,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_inactive_row_without_flags_is_valid(self):
		"""Test that inactive row without primary/whatsapp flags passes validation."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543211",
					"is_primary": 0,
					"is_whatsapp": 0,
					"is_active": 0,
					"ownership": "Self",
					"type": "Home",
				},
			],
			save=False,
		)
		individual.insert()

		self.assertEqual(len(individual.phone_numbers), 2)

	# =====================================================
	# VALIDATION TESTS - DUPLICATE CONTACTS
	# =====================================================

	def test_duplicate_phone_number_throws_error(self):
		"""Test that duplicate phone numbers throw ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_duplicate_phone_number_whitespace_trimmed(self):
		"""Test that duplicate phones with different spacing throw ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "  +91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_duplicate_email_throws_error(self):
		"""Test that duplicate email addresses throw ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				},
				{
					"email_address": "john@example.com",
					"is_primary": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_duplicate_email_case_insensitive(self):
		"""Test that duplicate emails with different case throw ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			email_address=[
				{
					"email_address": "John@Example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				},
				{
					"email_address": "john@example.com",
					"is_primary": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				},
			],
			save=False,
		)

		self.assertRaises(frappe.ValidationError, individual.insert)

	# =====================================================
	# VALIDATION TESTS - PREFERRED CONTACT MODE
	# =====================================================

	def test_preferred_phone_mode_no_phone_rows(self):
		"""Test preferred Phone throws when no phone rows exist."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
			save=False,
		)
		individual.preferred_contact_mode = "Phone"

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_preferred_whatsapp_mode_no_phone_rows(self):
		"""Test preferred Whatsapp throws when no phone rows exist."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
			save=False,
		)
		individual.preferred_contact_mode = "Whatsapp"

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_preferred_whatsapp_mode_phones_no_whatsapp(self):
		"""Test preferred Whatsapp throws when phones exist but none is whatsapp."""
		individual = create_knaps_individual(
			first_name="John",
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
			save=False,
		)
		individual.preferred_contact_mode = "Whatsapp"

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_preferred_email_mode_no_email_rows(self):
		"""Test preferred Email throws when no email rows exist."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
			save=False,
		)
		individual.preferred_contact_mode = "Email"

		self.assertRaises(frappe.ValidationError, individual.insert)

	# =====================================================
	# INTEGRATION TESTS
	# =====================================================

	def test_complete_individual_creation(self):
		"""Test creating a complete individual with all fields populated, including multi-row selection."""
		individual = create_knaps_individual(
			first_name="John",
			middle_name="Michael",
			last_name="Doe",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 0,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
				{
					"number": "+91 9876543211",
					"is_primary": 1,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				},
			],
			email_address=[
				{
					"email_address": "john.personal@example.com",
					"is_primary": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				},
				{
					"email_address": "john.doe@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				},
			],
			save=False,
		)
		individual.insert()

		self.assertEqual(individual.full_name, "Mr John Michael Doe")

		self.assertEqual(individual.primary_phone, "+91 9876543211")

		self.assertEqual(individual.primary_whatsapp, "+91 9876543211")

		self.assertEqual(individual.primary_email, "john.doe@example.com")

	def test_individual_with_no_contacts(self):
		"""Test that individual without phone/email contacts is valid."""
		individual = create_knaps_individual(first_name="John", last_name="Doe", save=False)
		individual.insert()

		# Individual should be valid without any contacts
		self.assertEqual(individual.first_name, "John")
		self.assertEqual(individual.last_name, "Doe")
		self.assertEqual(individual.primary_phone, "")
		self.assertEqual(individual.primary_whatsapp, "")
		self.assertEqual(individual.primary_email, "")

	def test_individual_update_primary_phone(self):
		"""Test updating primary phone on existing individual."""
		individual = create_knaps_individual(
			first_name="John",
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
			save=False,
		)
		individual.insert()

		old_phone = individual.primary_phone

		# Update phone number
		individual.phone_numbers[0].number = "+91 9876543211"
		individual.save()

		# Verify updated
		self.assertEqual(individual.primary_phone, "+91 9876543211")
		self.assertNotEqual(old_phone, individual.primary_phone)

	# =====================================================
	# PRIMARY FIELD RESET TESTS
	# =====================================================

	def test_primary_fields_cleared_when_rows_removed(self):
		"""Test that removing all child rows clears parent primary fields."""
		individual = create_knaps_individual(
			first_name="John",
			phone_numbers=[
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_whatsapp": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.insert()

		self.assertEqual(individual.primary_phone, "+91 9876543210")
		self.assertEqual(individual.primary_whatsapp, "+91 9876543210")
		self.assertEqual(individual.primary_email, "john@example.com")

		individual.phone_numbers = []
		individual.email_address = []
		individual.save()

		self.assertEqual(individual.primary_phone, "")
		self.assertEqual(individual.primary_whatsapp, "")
		self.assertEqual(individual.primary_email, "")

	# =====================================================
	# PAN VALIDATION TESTS
	# =====================================================

	def test_pan_unique_validation(self):
		"""Test that duplicate PAN throws ValidationError."""
		# Create first individual with PAN
		individual1 = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual1.pan = "ABCPX1234A"
		individual1.insert()

		# Try to create second individual with same PAN
		individual2 = create_knaps_individual(
			first_name="Jane",
			last_name="Doe",
			phone_numbers=[
				{
					"number": "+91 9876543211",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_address=[
				{
					"email_address": "jane@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual2.pan = "ABCPX1234A"  # Same PAN

		self.assertRaises(frappe.ValidationError, individual2.insert)

	def test_pan_case_insensitive(self):
		"""Test that PAN validation is case insensitive."""
		# Create first individual with PAN (uppercase)
		individual1 = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual1.pan = "ABCPX1234B"
		individual1.insert()

		# Try to create second individual with same PAN (lowercase)
		individual2 = create_knaps_individual(
			first_name="Jane",
			last_name="Doe",
			phone_numbers=[
				{
					"number": "+91 9876543211",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_address=[
				{
					"email_address": "jane@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual2.pan = "abcpX1234b"  # Same PAN but lowercase

		self.assertRaises(frappe.ValidationError, individual2.insert)

	def test_pan_normalized_on_save(self):
		"""Test that PAN is normalized to uppercase on save."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "abcpf1234f"  # lowercase
		individual.insert()

		# Verify PAN is stored in uppercase
		self.assertEqual(individual.pan, "ABCPF1234F")

	def test_no_pan_is_valid(self):
		"""Test that individual without PAN is valid."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = ""
		individual.insert()

		# Should be valid without PAN
		self.assertEqual(individual.pan, "")

	# =====================================================
	# PAN FORMAT VALIDATION TESTS
	# =====================================================

	def test_pan_valid_format(self):
		"""Test that valid PAN format passes validation."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCPF1234F"  # Valid format: ABC(1-3) P(4th='P') F(5) 1234(6-9) F(10)
		individual.insert()

		self.assertEqual(individual.pan, "ABCPF1234F")

	def test_pan_4th_character_not_p(self):
		"""Test that PAN with 4th character not 'P' throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCXA1234F"  # 4th character is 'X' instead of 'P'

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_pan_first_3_not_letters(self):
		"""Test that PAN with non-letter first 3 characters throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "123PF1234F"  # First 3 are digits

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_pan_5th_not_letter(self):
		"""Test that PAN with non-letter 5th character throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCD11234F"  # 5th character is digit

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_pan_6_to_9_not_digits(self):
		"""Test that PAN with non-digit characters 6-9 throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCDE1ABCD"  # Characters 6-9 are letters

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_pan_10th_not_letter(self):
		"""Test that PAN with non-letter 10th character throws ValidationError."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCDE12341"  # 10th character is digit

		self.assertRaises(frappe.ValidationError, individual.insert)

	# =====================================================
	# DATE OF BIRTH VALIDATION TESTS
	# =====================================================

	def test_dob_valid_past_date(self):
		"""Test that valid past date of birth is accepted."""
		import datetime

		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		# Set DOB to 10 years ago
		individual.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -10)
		individual.insert()

		self.assertIsNotNone(individual.date_of_birth)

	def test_dob_future_throws_error(self):
		"""Test that future date of birth throws ValidationError."""
		import datetime

		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		# Set DOB to 1 year in the future
		individual.date_of_birth = frappe.utils.add_years(frappe.utils.today(), 1)

		self.assertRaises(frappe.ValidationError, individual.insert)

	def test_dob_today_is_valid(self):
		"""Test that today's date is valid (not in future)."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		# Set DOB to today
		individual.date_of_birth = frappe.utils.today()
		individual.insert()

		self.assertIsNotNone(individual.date_of_birth)

	# =====================================================
	# AGE VIRTUAL FIELD TESTS
	# =====================================================

	def test_age_adult(self):
		"""Test that age is calculated correctly for adult"""
		individual = create_knaps_individual(
			first_name="Adult",
			last_name="Individual",
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
			email_address=[
				{
					"email_address": "adult@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -30)
		individual.insert()

		self.assertIsNotNone(individual.age)
		self.assertGreaterEqual(individual.age, 30)

	def test_age_minor(self):
		"""Test that age is calculated correctly for minor"""
		individual = create_knaps_individual(
			first_name="Child",
			last_name="Individual",
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
			email_address=[
				{
					"email_address": "child@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -10)
		individual.insert()

		self.assertIsNotNone(individual.age)
		self.assertLess(individual.age, 18)

	def test_age_no_dob(self):
		"""Test that age is None when no DOB is set"""
		individual = create_knaps_individual(
			first_name="NoDOB",
			last_name="Individual",
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
			email_address=[
				{
					"email_address": "nodob@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.date_of_birth = None
		individual.insert()

		self.assertIsNone(individual.age)

	# =====================================================
	# AGE EDGE CASE TESTS
	# =====================================================

	def test_age_newborn(self):
		"""Test that DOB = today shows 'Newborn'."""
		individual = create_knaps_individual(
			first_name="Baby",
			last_name="Newborn",
			save=False,
		)
		individual.date_of_birth = frappe.utils.today()
		individual.insert()

		self.assertEqual(individual.age, 0)
		self.assertEqual(individual.age_formatted, "Newborn")

	# =====================================================
	# ADDRESS DELETION TESTS
	# =====================================================

	def test_address_deleted_when_individual_deleted(self):
		"""Test that exclusively-linked Address is deleted when Individual is deleted"""
		individual = create_knaps_individual(
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
			email_address=[
				{
					"email_address": "test@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
		)

		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Test Address",
				"address_line1": "123 Test Street",
				"city": "Mumbai",
				"links": [{"link_doctype": individual.doctype, "link_name": individual.name}],
			}
		).insert()

		self.assertTrue(frappe.db.exists("Address", address.name))
		individual.delete()
		self.assertFalse(frappe.db.exists("Address", address.name))

	def test_shared_address_not_deleted_when_one_individual_deleted(self):
		"""Test that shared Address only loses the link row when one Individual is deleted"""
		individual_a = create_knaps_individual(
			first_name="Alice",
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
			email_address=[
				{
					"email_address": "alice@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
		)
		individual_b = create_knaps_individual(
			first_name="Bob",
			phone_numbers=[
				{
					"number": "+91 9876543211",
					"is_primary": 1,
					"is_whatsapp": 0,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			email_address=[
				{
					"email_address": "bob@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
		)

		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Shared Address",
				"address_line1": "456 Shared Lane",
				"city": "Delhi",
				"links": [
					{"link_doctype": individual_a.doctype, "link_name": individual_a.name},
					{"link_doctype": individual_b.doctype, "link_name": individual_b.name},
				],
			}
		).insert()

		individual_a.delete()

		self.assertTrue(frappe.db.exists("Address", address.name))
		address.reload()
		self.assertEqual(len(address.links), 1)
		self.assertEqual(address.links[0].link_name, individual_b.name)
		individual_b.delete()

	def test_delete_individual_without_address_succeeds(self):
		"""Test that deleting a Individual with no linked Address does not raise"""
		individual = create_knaps_individual(
			first_name="NoAddress",
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
			email_address=[
				{
					"email_address": "noaddress@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
		)
		individual.delete()

	def test_pan_update_on_existing_individual(self):
		"""Test that PAN can be updated on an existing individual."""
		individual = create_knaps_individual(
			first_name="John",
			last_name="Doe",
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
			email_address=[
				{
					"email_address": "john@example.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Personal",
				}
			],
			save=False,
		)
		individual.pan = "ABCPE1234F"
		individual.insert()

		self.assertEqual(individual.pan, "ABCPE1234F")

		individual.pan = "ABCPF5678G"
		individual.save()

		self.assertEqual(individual.pan, "ABCPF5678G")

	def test_dob_exactly_18_years_is_adult(self):
		"""Test that an individual with DOB exactly 18 years ago is adult (not minor)."""
		individual = create_knaps_individual(
			first_name="Edge",
			last_name="Case",
			save=False,
		)
		individual.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -18)
		individual.insert()

		self.assertEqual(individual.age, 18)
		self.assertEqual(individual.age_formatted, "18 Years")

	def test_age_formatted_years_and_months_only(self):
		from frappe.utils import add_days, add_years, today

		individual = create_knaps_individual(first_name="YM", last_name="Case", save=False)
		individual.date_of_birth = add_years(add_days(today(), -90), -18)
		individual.insert()

		self.assertIn("18 Years", individual.age_formatted)
		self.assertIn("3 Months", individual.age_formatted)
		self.assertNotIn("0 Days", individual.age_formatted)
