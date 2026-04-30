# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
import time


def generate_pan(entity_type="Person"):
    """Generate a unique valid PAN (10 chars):
    Format: AAAPX1234A (1-3=letters, 4=P/C, 5=letter, 6-9=digits, 10=letter)
    """
    suffix = str(int(time.time() * 1000000))[-4:]  # 4 digits
    if entity_type == "Person":
        return f"AAAPX{suffix}A"  # AAA + P + X + 4 digits + A = 10 chars
    else:
        return f"AAACX{suffix}A"


def create_test_person(**kwargs):
    """Create a test KNAPS Person for testing"""
    unique_suffix = str(int(time.time() * 1000))[-4:]
    doc = frappe.get_doc({
        "doctype": "KNAPS Person",
        "first_name": kwargs.get("first_name", "Test"),
        "last_name": kwargs.get("last_name", "Person"),
        "status": "Active",
        "salutation": "Mr",
        "gender": "Male"
    })
    if kwargs.get("pan"):
        doc.pan = kwargs.get("pan")
    doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.db.commit()
    return doc.name


def create_test_non_individual(**kwargs):
    """Create a test KNAPS Non Individual for testing"""
    # First ensure Non Individual Type exists
    if not frappe.db.exists("KNAPS Non Individual Type", "Company"):
        doc = frappe.get_doc({
            "doctype": "KNAPS Non Individual Type",
            "non_individual_type": "Company"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

    unique_suffix = str(int(time.time() * 1000))[-6:]
    doc = frappe.get_doc({
        "doctype": "KNAPS Non Individual",
        "non_individual_name": kwargs.get("non_individual_name", "Test Company") + unique_suffix,
        "non_individual_type": kwargs.get("non_individual_type", "Company"),
        "status": "Active",
        "pan": kwargs.get("pan", ""),
        "phone_numbers": [{"number": "+91 9876543210", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Mobile"}],
        "email_addresses": [{"email_address": "test@company.com", "is_primary": 1, "is_active": 1, "ownership": "Self", "type": "Official"}]
    })
    doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.db.commit()
    return doc.name


def create_knaps_client(**kwargs):
    """Helper function to create a KNAPS Client for testing."""
    doc = frappe.get_doc({
        "doctype": "KNAPS Client",
        "investor_type": kwargs.get("investor_type", "Individual"),
        "person": kwargs.get("person", ""),
        "non_individual": kwargs.get("non_individual", ""),
        "client_name": kwargs.get("client_name", ""),
        "client_pan": kwargs.get("client_pan", ""),
        "occupation": kwargs.get("occupation", ""),
        "income_slab": kwargs.get("income_slab", "")
    })

    if kwargs.get("save", True):
        doc.insert()

    return doc


class TestKNAPSClient(IntegrationTestCase):
    """Integration tests for KNAPS Client doctype."""

    doctype = "KNAPS Client"

    # =====================================================
    # AUTO-FETCH TESTS
    # =====================================================

    def test_individual_auto_fetch_name_and_pan(self):
        """Test that selecting person auto-fetches name and PAN for Individual"""
        pan = generate_pan("Person")
        person_name = create_test_person(first_name="John", last_name="Doe", pan=pan)
        
        client = create_knaps_client(
            investor_type="Individual",
            person=person_name,
            save=False
        )
        client.insert()
        
        self.assertEqual(client.client_name, "John Doe")
        self.assertEqual(client.client_pan, pan)
        client.delete()

    def test_non_individual_auto_fetch_name_and_pan(self):
        """Test that selecting non_individual auto-fetches name and PAN"""
        pan = generate_pan("Company")
        entity_name = create_test_non_individual(
            non_individual_name="Test Company ABC",
            non_individual_type="Company",
            pan=pan
        )
        
        client = create_knaps_client(
            investor_type="Non Individual",
            non_individual=entity_name,
            save=False
        )
        client.insert()
        
        self.assertEqual(client.client_name, "Test Company ABC")
        self.assertEqual(client.client_pan, pan)
        client.delete()

    def test_sole_proprietor_manual_name(self):
        """Test that Sole Proprietor allows manual name entry"""
        pan = generate_pan("Person")
        person_name = create_test_person(first_name="Jane", last_name="Smith", pan=pan)
        
        client = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person_name,
            client_name="Jane's Boutique",
            save=False
        )
        client.insert()
        
        self.assertEqual(client.client_name, "Jane's Boutique")
        self.assertEqual(client.client_pan, pan)
        client.delete()

    # =====================================================
    # VALIDATION TESTS
    # =====================================================

    def test_validation_person_required_for_individual(self):
        """Test that Person is required for Individual client type"""
        client = create_knaps_client(
            investor_type="Individual",
            person="",
            save=False
        )
        
        self.assertRaises(frappe.ValidationError, client.insert)

    def test_validation_entity_required_for_non_individual(self):
        """Test that Non Individual is required for Non Individual client type"""
        client = create_knaps_client(
            investor_type="Non Individual",
            non_individual="",
            save=False
        )
        
        self.assertRaises(frappe.ValidationError, client.insert)

    def test_validation_person_required_for_sole_proprietor(self):
        """Test that Person is required for Sole Proprietor client type"""
        client = create_knaps_client(
            investor_type="Sole Proprietor",
            person="",
            client_name="Test Business",
            save=False
        )
        
        self.assertRaises(frappe.ValidationError, client.insert)

    # =====================================================
    # PAN UNIQUENESS TESTS
    # Note: PAN uniqueness is also enforced at Person/Non Individual level,
    # so we test what we can at Client level
    # =====================================================

    def test_pan_unique_non_individual(self):
        """Test that same PAN for 2 Non Individual clients throws error at entity level"""
        pan = generate_pan("AAC")
        entity1 = create_test_non_individual(non_individual_name="Company X", pan=pan)
        
        client1 = create_knaps_client(
            investor_type="Non Individual",
            non_individual=entity1,
            save=False
        )
        client1.insert()
        
        # Creating another entity with same PAN should fail at entity level
        self.assertRaises(frappe.ValidationError, create_test_non_individual, 
            non_individual_name="Company Y", pan=pan)
        
        client1.delete()

    def test_pan_unique_individual(self):
        """Test that PAN uniqueness is enforced at Person level (Client level inherits this)"""
        pan = generate_pan("AAP")
        # Creating 2 persons with same PAN fails at Person level - this validates the chain
        person1 = create_test_person(first_name="Person", last_name="One", pan=pan)
        self.assertRaises(frappe.ValidationError, create_test_person, 
            first_name="Person", last_name="Two", pan=pan)

    def test_pan_sole_proprietor_same_name_throws_error(self):
        """Test that same PAN + same Name for Sole Proprietor throws error"""
        pan = generate_pan("AAP")
        person = create_test_person(first_name="SP", last_name="Person", pan=pan)
        
        client1 = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person,
            client_name="My Business",
            save=False
        )
        client1.insert()
        
        # Same person, same business name - should fail at Client level
        client2 = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person,
            client_name="My Business",
            save=False
        )
        
        self.assertRaises(frappe.ValidationError, client2.insert)
        client1.delete()

    def test_pan_sole_proprietor_different_name_ok(self):
        """Test that same PAN + different Name for Sole Proprietor is allowed"""
        pan = generate_pan("AAP")
        person = create_test_person(first_name="SP2", last_name="Person", pan=pan)
        
        client1 = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person,
            client_name="Business A",
            save=False
        )
        client1.insert()
        
        client2 = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person,
            client_name="Business B",
            save=False
        )
        client2.insert()
        
        self.assertEqual(client1.client_pan, pan)
        self.assertEqual(client2.client_pan, pan)
        client1.delete()
        client2.delete()

    def test_pan_sole_proprietor_and_individual_ok(self):
        """Test that same PAN for Sole Proprietor and Individual is allowed"""
        pan = generate_pan("AAP")
        person = create_test_person(first_name="Dual", last_name="Role", pan=pan)
        
        # Create as Individual
        client1 = create_knaps_client(
            investor_type="Individual",
            person=person,
            save=False
        )
        client1.insert()
        
        # Create as Sole Proprietor with different name
        client2 = create_knaps_client(
            investor_type="Sole Proprietor",
            person=person,
            client_name="My Sole Biz",
            save=False
        )
        client2.insert()
        
        self.assertEqual(client1.client_pan, pan)
        self.assertEqual(client2.client_pan, pan)
        self.assertNotEqual(client1.client_name, client2.client_name)
        client1.delete()
        client2.delete()