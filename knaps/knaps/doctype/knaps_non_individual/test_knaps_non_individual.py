# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


def create_knaps_non_individual(**kwargs):
    """Helper function to create a KNAPS Non Individual for testing."""
    doc = frappe.get_doc({
        "doctype": "KNAPS Non Individual",
        "non_individual_name": kwargs.get("non_individual_name", "Test Entity"),
        "non_individual_type": kwargs.get("non_individual_type", "Company"),
        "status": kwargs.get("status", "Active"),
        "pan": kwargs.get("pan", ""),
        "date_of_incoporation": kwargs.get("date_of_incoporation", None),
        "phone_numbers": kwargs.get("phone_numbers", []),
        "email_addresses": kwargs.get("email_addresses", []),
        "signatories": kwargs.get("signatories", [])
    })

    if kwargs.get("save", True):
        doc.insert()

    return doc


def create_knaps_non_individual(**kwargs):
    """Helper function to create a KNAPS Non Individual for testing."""
    doc = frappe.get_doc({
        "doctype": "KNAPS Non Individual",
        "non_individual_name": kwargs.get("non_individual_name", "Test Entity"),
        "non_individual_type": kwargs.get("non_individual_type", "Company"),
        "status": kwargs.get("status", "Active"),
        "pan": kwargs.get("pan", ""),
        "date_of_incoporation": kwargs.get("date_of_incoporation", None),
        "phone_numbers": kwargs.get("phone_numbers", []),
        "email_addresses": kwargs.get("email_addresses", []),
        "signatories": kwargs.get("signatories", [])
    })

    if kwargs.get("save", True):
        doc.insert()

    return doc


class TestKNAPSNonIndividual(IntegrationTestCase):
    """Integration tests for KNAPS Non Individual doctype."""

    doctype = "KNAPS Non Individual"

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
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(entity.pan, "ABCCP1234F")
        entity.delete()

    def test_pan_valid_for_trust(self):
        """Test valid PAN format for Trust (4th char = T)"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Trust",
            non_individual_type="Trust",
            pan="ABCTT1234F",  # 4th char = T for Trust
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@trust.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(entity.pan, "ABCTT1234F")
        entity.delete()

    def test_pan_4th_char_mismatch_for_company(self):
        """Test that PAN with wrong 4th character throws error for Company"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="ABCBP1234F",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_4th_char_mismatch_for_huf(self):
        """Test that PAN with wrong 4th character throws error for HUF"""
        entity = create_knaps_non_individual(
            non_individual_name="Test HUF",
            non_individual_type="Hindu Undivided Family",
            pan="ABCAP1234F",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@huf.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Personal"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_format_first_3_not_letters(self):
        """Test that PAN with non-letter first 3 chars throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="123CP1234F",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_format_6_to_9_not_digits(self):
        """Test that PAN with non-digit chars 6-9 throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="ABCCPXABCD",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_unique_validation(self):
        """Test that duplicate PAN throws error"""
        entity1 = create_knaps_non_individual(
            non_individual_name="Entity One",
            non_individual_type="Company",
            pan="ABCCP1234A",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "entity1@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity1.insert()

        entity2 = create_knaps_non_individual(
            non_individual_name="Entity Two",
            non_individual_type="Company",
            pan="ABCCP1234A",
            phone_numbers=[
                {"number": "+91 9876543211", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "entity2@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity2.insert)
        entity1.delete()

    def test_pan_normalized_on_save(self):
        """Test that PAN is normalized to uppercase"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Company",
            non_individual_type="Company",
            pan="abccp1234f",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(entity.pan, "ABCCP1234F")
        entity.delete()

    def test_no_pan_is_valid(self):
        """Test that entity without PAN is valid"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(entity.pan, "")
        entity.delete()

    # =====================================================
    # DATE OF INCORPORATION VALIDATION TESTS
    # =====================================================

    def test_doi_valid_past_date(self):
        """Test that valid past date of incorporation is accepted"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Company",
            non_individual_type="Company",
            date_of_incoporation=frappe.utils.add_years(frappe.utils.today(), -5),
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertIsNotNone(entity.date_of_incoporation)
        entity.delete()

    def test_doi_future_throws_error(self):
        """Test that future date of incorporation throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Company",
            non_individual_type="Company",
            date_of_incoporation=frappe.utils.add_years(frappe.utils.today(), 1),
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_doi_today_is_valid(self):
        """Test that today's date is valid"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Company",
            non_individual_type="Company",
            date_of_incoporation=frappe.utils.today(),
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertIsNotNone(entity.date_of_incoporation)
        entity.delete()

    def test_doi_optional(self):
        """Test that entity without DOI is valid"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            date_of_incoporation=None,
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertIsNone(entity.date_of_incoporation)
        entity.delete()

    # =====================================================
    # PHONE/EMAIL VALIDATION TESTS
    # =====================================================

    def test_phone_without_primary_throws_error(self):
        """Test that phone rows without primary throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 0, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_email_without_primary_throws_error(self):
        """Test that email rows without primary throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 0, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_multiple_primary_phones_throws_error(self):
        """Test that multiple primary phones throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"},
                {"number": "+91 9876543211", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Office"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_multiple_primary_emails_throws_error(self):
        """Test that multiple primary emails throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test1@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"},
                {"email_address": "test2@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Personal"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_valid_phone_and_email_primary(self):
        """Test that valid phone and email with single primary works"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(len(entity.phone_numbers), 1)
        self.assertEqual(len(entity.email_addresses), 1)
        entity.delete()

    # =====================================================
    # SIGNATORIES VALIDATION TESTS
    # =====================================================

    def get_test_person_names(self):
        """Get test person names from database"""
        # Query directly for test persons created
        persons = frappe.db.get_all("KNAPS Person", 
            filters={"first_name": "Test"},
            pluck="name",
            limit=2
        )
        return persons

    def test_signatory_without_primary_throws_error(self):
        """Test that signatories without primary contact throws error"""
        test_persons = self.get_test_person_names()
        if len(test_persons) < 1:
            self.skipTest("KNAPS Person test records not available")

        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            signatories=[
                {"signatory": test_persons[0], "is_primary_contact": 0, "is_active": 1, "role": "Director"}
            ],
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_multiple_primary_signatories_throws_error(self):
        """Test that multiple primary signatories throws error"""
        test_persons = self.get_test_person_names()
        if len(test_persons) < 2:
            self.skipTest("Need at least 2 KNAPS Person test records")

        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            signatories=[
                {"signatory": test_persons[0], "is_primary_contact": 1, "is_active": 1, "role": "Director"},
                {"signatory": test_persons[1], "is_primary_contact": 1, "is_active": 1, "role": "Director"}
            ],
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_valid_single_primary_signatory_works(self):
        """Test that valid single primary signatory works"""
        test_persons = self.get_test_person_names()
        if len(test_persons) < 1:
            self.skipTest("KNAPS Person test records not available")

        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            signatories=[
                {"signatory": test_persons[0], "is_primary_contact": 1, "is_active": 1, "role": "Director"}
            ],
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(len(entity.signatories), 1)
        entity.delete()

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
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_10th_char_not_letter_throws_error(self):
        """Test that PAN with non-letter 10th character throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="ABCCP12341",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )

        self.assertRaises(frappe.ValidationError, entity.insert)

    def test_pan_less_than_10_chars_throws_error(self):
        """Test that PAN with less than 10 characters throws error"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            pan="ABCCP123",
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
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
            "Artificial Judicial Person": "ABCJP1234F"
        }

        for entity_type, pan in pan_mapping.items():
            entity = create_knaps_non_individual(
                non_individual_name=f"Test {entity_type}",
                non_individual_type=entity_type,
                pan=pan,
                phone_numbers=[
                    {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
                ],
                email_addresses=[
                    {"email_address": f"test@{entity_type.replace(' ', '').lower()}.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
                ],
                save=False
            )
            entity.insert()
            entity.delete()

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
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(entity.status, "Inactive")
        entity.delete()

    def test_empty_signatories_valid(self):
        """Test that empty signatories table is valid (no validation error for missing primary)"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            signatories=[],
            phone_numbers=[
                {"number": "+91 9876543210", "is_primary": 1, "is_whatsapp": 0, "is_active": 1, "ownership": "Self", "type": "Mobile"}
            ],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            save=False
        )
        entity.insert()

        self.assertEqual(len(entity.signatories), 0)
        entity.delete()

    def test_empty_phone_table_valid(self):
        """Test that empty phone table is valid"""
        entity = create_knaps_non_individual(
            non_individual_name="Test Entity",
            non_individual_type="Company",
            phone_numbers=[],
            email_addresses=[
                {"email_address": "test@example.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}
            ],
            signatories=[],
            save=False
        )
        entity.insert()

        self.assertEqual(len(entity.phone_numbers), 0)
        entity.delete()