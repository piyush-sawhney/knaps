# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
import unittest
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender"]


def create_knaps_person(**kwargs):
    """Helper function to create a KNAPS Person for testing."""
    doc = frappe.get_doc({
        "doctype": "KNAPS Person",
        "first_name": kwargs.get("first_name", "Test"),
        "middle_name": kwargs.get("middle_name", ""),
        "last_name": kwargs.get("last_name", ""),
        "salutation": kwargs.get("salutation", "Mr"),
        "gender": kwargs.get("gender", "Male"),
        "status": kwargs.get("status", "Active"),
        "phone_numbers": kwargs.get("phone_numbers", []),
        "email_address": kwargs.get("email_address", [])
    })

    if kwargs.get("save", True):
        doc.insert()

    return doc


class TestKNAPSPerson(IntegrationTestCase):
    """Integration tests for KNAPS Person doctype."""

    # =====================================================
    # FULL NAME AUTO-CALCULATION TESTS
    # =====================================================

    def test_full_name_first_and_last(self):
        """Test full name calculation with first and last name only."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            save=False
        )
        person.insert()

        self.assertEqual(person.full_name, "John Doe")
        person.delete()

    def test_full_name_all_three(self):
        """Test full name calculation with first, middle, and last name."""
        person = create_knaps_person(
            first_name="John",
            middle_name="Michael",
            last_name="Doe",
            save=False
        )
        person.insert()

        self.assertEqual(person.full_name, "John Michael Doe")
        person.delete()

    def test_full_name_only_first(self):
        """Test full name when only first name is provided."""
        person = create_knaps_person(
            first_name="John",
            save=False
        )
        person.insert()

        self.assertEqual(person.full_name, "John")
        person.delete()

    def test_full_name_whitespace_trimmed(self):
        """Test that whitespace is properly trimmed from name components."""
        person = create_knaps_person(
            first_name="  John  ",
            middle_name="  Michael  ",
            last_name="  Doe  ",
            save=False
        )
        person.insert()

        self.assertEqual(person.full_name, "John Michael Doe")
        person.delete()

    # =====================================================
    # PRIMARY PHONE SYNC TESTS
    # =====================================================

    def test_primary_phone_synced(self):
        """Test that primary phone is synced from child table."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )
        person.insert()

        self.assertEqual(person.primary_phone, "+91 9876543210")
        person.delete()

    def test_primary_phone_multiple_phones(self):
        """Test that only the primary phone is synced when multiple phones exist."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 0,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                },
                {
                    "number": "+91 9876543211",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )
        person.insert()

        self.assertEqual(person.primary_phone, "+91 9876543211")
        person.delete()

    # =====================================================
    # PRIMARY WHATSAPP SYNC TESTS
    # =====================================================

    def test_primary_whatsapp_synced(self):
        """Test that primary WhatsApp is synced from child table."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )
        person.insert()

        self.assertEqual(person.primary_whatsapp, "+91 9876543210")
        person.delete()

    # =====================================================
    # PRIMARY EMAIL SYNC TESTS
    # =====================================================

    def test_primary_email_synced(self):
        """Test that primary email is synced from child table."""
        person = create_knaps_person(
            first_name="John",
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.insert()

        self.assertEqual(person.primary_email, "john@example.com")
        person.delete()

    def test_primary_email_multiple_emails(self):
        """Test that only the primary email is synced when multiple emails exist."""
        person = create_knaps_person(
            first_name="John",
            email_address=[
                {
                    "email_address": "john.personal@example.com",
                    "is_primary": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                },
                {
                    "email_address": "john.official@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Official"
                }
            ],
            save=False
        )
        person.insert()

        self.assertEqual(person.primary_email, "john.official@example.com")
        person.delete()

    # =====================================================
    # VALIDATION TESTS - SINGLE PRIMARY
    # =====================================================

    def test_duplicate_primary_phone_throws_error(self):
        """Test that saving with multiple primary phones throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                },
                {
                    "number": "+91 9876543211",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_duplicate_whatsapp_throws_error(self):
        """Test that saving with multiple WhatsApp phones throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 0,
                    "is_whatsapp": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                },
                {
                    "number": "+91 9876543211",
                    "is_primary": 0,
                    "is_whatsapp": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_duplicate_primary_email_throws_error(self):
        """Test that saving with multiple primary emails throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            email_address=[
                {
                    "email_address": "john1@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                },
                {
                    "email_address": "john2@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Official"
                }
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, person.insert)

    # =====================================================
    # VALIDATION TESTS - AT LEAST ONE PRIMARY
    # =====================================================

    def test_phone_without_primary_throws_error(self):
        """Test that saving phone rows without any primary throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 0,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_email_without_primary_throws_error(self):
        """Test that saving email rows without any primary throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, person.insert)

    # =====================================================
    # INTEGRATION TESTS
    # =====================================================

    def test_complete_person_creation(self):
        """Test creating a complete person with all fields populated."""
        person = create_knaps_person(
            first_name="John",
            middle_name="Michael",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john.doe@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.insert()

        # Verify full name
        self.assertEqual(person.full_name, "John Michael Doe")

        # Verify primary phone
        self.assertEqual(person.primary_phone, "+91 9876543210")

        # Verify primary WhatsApp
        self.assertEqual(person.primary_whatsapp, "+91 9876543210")

        # Verify primary email
        self.assertEqual(person.primary_email, "john.doe@example.com")

        person.delete()

    def test_person_with_no_contacts(self):
        """Test that person without phone/email contacts is valid."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            save=False
        )
        person.insert()

        # Person should be valid without any contacts
        self.assertEqual(person.first_name, "John")
        self.assertEqual(person.last_name, "Doe")
        self.assertEqual(person.primary_phone, "")
        self.assertEqual(person.primary_whatsapp, "")
        self.assertEqual(person.primary_email, "")

        person.delete()

    def test_person_update_primary_phone(self):
        """Test updating primary phone on existing person."""
        person = create_knaps_person(
            first_name="John",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            save=False
        )
        person.insert()

        old_phone = person.primary_phone

        # Update phone number
        person.phone_numbers[0].number = "+91 9876543211"
        person.save()

        # Verify updated
        self.assertEqual(person.primary_phone, "+91 9876543211")
        self.assertNotEqual(old_phone, person.primary_phone)

        person.delete()

    # =====================================================
    # PAN VALIDATION TESTS
    # =====================================================

    def test_pan_unique_validation(self):
        """Test that duplicate PAN throws ValidationError."""
        # Create first person with PAN
        person1 = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person1.pan = "ABCPX1234A"
        person1.insert()

        # Try to create second person with same PAN
        person2 = create_knaps_person(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543211",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "jane@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person2.pan = "ABCPX1234A"  # Same PAN

        self.assertRaises(frappe.ValidationError, person2.insert)

        person1.delete()

    def test_pan_case_insensitive(self):
        """Test that PAN validation is case insensitive."""
        # Create first person with PAN (uppercase)
        person1 = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person1.pan = "ABCPX1234B"
        person1.insert()

        # Try to create second person with same PAN (lowercase)
        person2 = create_knaps_person(
            first_name="Jane",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543211",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "jane@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person2.pan = "abcpX1234b"  # Same PAN but lowercase

        self.assertRaises(frappe.ValidationError, person2.insert)

        person1.delete()

    def test_pan_normalized_on_save(self):
        """Test that PAN is normalized to uppercase on save."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "abcpf1234f"  # lowercase

        person.insert()

        # Verify PAN is stored in uppercase
        self.assertEqual(person.pan, "ABCPF1234F")

        person.delete()

    def test_no_pan_is_valid(self):
        """Test that person without PAN is valid."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = ""

        person.insert()

        # Should be valid without PAN
        self.assertEqual(person.pan, "")

        person.delete()

    # =====================================================
    # PAN FORMAT VALIDATION TESTS
    # =====================================================

    def test_pan_valid_format(self):
        """Test that valid PAN format passes validation."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "ABCPF1234F"  # Valid format: ABC(1-3) P(4th='P') F(5) 1234(6-9) F(10)

        person.insert()

        self.assertEqual(person.pan, "ABCPF1234F")
        person.delete()

    def test_pan_4th_character_not_p(self):
        """Test that PAN with 4th character not 'P' throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "ABCXA1234F"  # 4th character is 'X' instead of 'P'

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_pan_first_3_not_letters(self):
        """Test that PAN with non-letter first 3 characters throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "123PF1234F"  # First 3 are digits

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_pan_5th_not_letter(self):
        """Test that PAN with non-letter 5th character throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "ABCD11234F"  # 5th character is digit

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_pan_6_to_9_not_digits(self):
        """Test that PAN with non-digit characters 6-9 throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "ABCDE1ABCD"  # Characters 6-9 are letters

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_pan_10th_not_letter(self):
        """Test that PAN with non-letter 10th character throws ValidationError."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        person.pan = "ABCDE12341"  # 10th character is digit

        self.assertRaises(frappe.ValidationError, person.insert)

    # =====================================================
    # DATE OF BIRTH VALIDATION TESTS
    # =====================================================

    def test_dob_valid_past_date(self):
        """Test that valid past date of birth is accepted."""
        import datetime
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        # Set DOB to 10 years ago
        person.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -10)

        person.insert()

        self.assertIsNotNone(person.date_of_birth)
        person.delete()

    def test_dob_future_throws_error(self):
        """Test that future date of birth throws ValidationError."""
        import datetime
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        # Set DOB to 1 year in the future
        person.date_of_birth = frappe.utils.add_years(frappe.utils.today(), 1)

        self.assertRaises(frappe.ValidationError, person.insert)

    def test_dob_today_is_valid(self):
        """Test that today's date is valid (not in future)."""
        person = create_knaps_person(
            first_name="John",
            last_name="Doe",
            phone_numbers=[
                {
                    "number": "+91 9876543210",
                    "is_primary": 1,
                    "is_whatsapp": 0,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile"
                }
            ],
            email_address=[
                {
                    "email_address": "john@example.com",
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal"
                }
            ],
            save=False
        )
        # Set DOB to today
        person.date_of_birth = frappe.utils.today()

        person.insert()

        self.assertIsNotNone(person.date_of_birth)
        person.delete()