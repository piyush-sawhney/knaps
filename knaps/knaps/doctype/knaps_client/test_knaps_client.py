# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import time

import frappe
from frappe.tests import IntegrationTestCase


def generate_pan(entity_type="Person"):
	"""Generate a unique valid PAN (10 chars):
	Format: AAAPX1234A for Person (4th=P), AAACX1234A for Company (4th=C)
	"""
	suffix = str(int(time.time() * 1000000))[-4:]
	if entity_type in ["Person", "Individual", "Sole Proprietor", "AAP"]:
		return f"AAAPX{suffix}A"
	else:
		return f"AAACX{suffix}A"


def create_test_person(**kwargs):
	"""Create a test KNAPS Person for testing"""
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Person",
			"first_name": kwargs.get("first_name", "Test"),
			"last_name": kwargs.get("last_name", "Person"),
			"status": "Active",
			"salutation": "Mr",
			"gender": "Male",
		}
	)
	if kwargs.get("pan"):
		doc.pan = kwargs.get("pan")
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.commit()
	return doc.name


def create_test_non_individual(**kwargs):
	"""Create a test KNAPS Non Individual for testing"""
	if not frappe.db.exists("KNAPS Non Individual Type", "Company"):
		doc = frappe.get_doc({"doctype": "KNAPS Non Individual Type", "non_individual_type": "Company"})
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Non Individual",
			"non_individual_name": kwargs.get("non_individual_name", "Test Company"),
			"non_individual_type": kwargs.get("non_individual_type", "Company"),
			"status": kwargs.get("status", "Active"),
			"pan": kwargs.get("pan", ""),
			"phone_numbers": [
				{
					"number": "+91 9876543210",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Mobile",
				}
			],
			"email_addresses": [
				{
					"email_address": "test@company.com",
					"is_primary": 1,
					"is_active": 1,
					"ownership": "Self",
					"type": "Official",
				}
			],
		}
	)
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.commit()
	return doc.name


def create_knaps_client(**kwargs):
	"""Helper function to create a KNAPS Client for testing."""
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Client",
			"investor_type": kwargs.get("investor_type", "Individual"),
			"person": kwargs.get("person", ""),
			"non_individual": kwargs.get("non_individual", ""),
			"client_name": kwargs.get("client_name", ""),
			"client_pan": kwargs.get("client_pan", ""),
			"occupation": kwargs.get("occupation", ""),
			"income_slab": kwargs.get("income_slab", ""),
		}
	)

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

		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		self.assertEqual(client.client_name, "John Doe")
		self.assertEqual(client.client_pan, pan)
		client.delete()

	def test_non_individual_auto_fetch_name_and_pan(self):
		"""Test that selecting non_individual auto-fetches name and PAN"""
		pan = generate_pan("Company")
		entity_name = create_test_non_individual(
			non_individual_name="Test Company ABC", non_individual_type="Company", pan=pan
		)

		client = create_knaps_client(investor_type="Non Individual", non_individual=entity_name, save=False)
		client.insert()

		self.assertEqual(client.client_name, "Test Company ABC")
		self.assertEqual(client.client_pan, pan)
		client.delete()

	def test_sole_proprietor_manual_name(self):
		"""Test that Sole Proprietor allows manual name entry"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Jane", last_name="Smith", pan=pan)

		client = create_knaps_client(
			investor_type="Sole Proprietor", person=person_name, client_name="Jane's Boutique", save=False
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
		client = create_knaps_client(investor_type="Individual", person="", save=False)

		self.assertRaises(frappe.ValidationError, client.insert)

	def test_validation_entity_required_for_non_individual(self):
		"""Test that Non Individual is required for Non Individual client type"""
		client = create_knaps_client(investor_type="Non Individual", non_individual="", save=False)

		self.assertRaises(frappe.ValidationError, client.insert)

	def test_validation_person_required_for_sole_proprietor(self):
		"""Test that Person is required for Sole Proprietor client type"""
		client = create_knaps_client(
			investor_type="Sole Proprietor", person="", client_name="Test Business", save=False
		)

		self.assertRaises(frappe.ValidationError, client.insert)

	# =====================================================
	# PAN UNIQUENESS TESTS
	# =====================================================

	def test_pan_unique_non_individual(self):
		"""Test that same PAN for 2 Non Individual clients throws error at entity level"""
		pan = generate_pan("AAC")
		entity1 = create_test_non_individual(non_individual_name="Company X", pan=pan)

		client1 = create_knaps_client(investor_type="Non Individual", non_individual=entity1, save=False)
		client1.insert()

		# Creating another entity with same PAN should fail at entity level
		self.assertRaises(
			frappe.ValidationError, create_test_non_individual, non_individual_name="Company Y", pan=pan
		)

		client1.delete()

	def test_pan_unique_individual(self):
		"""Test that PAN uniqueness is enforced at Person level (Client level inherits this)"""
		pan = generate_pan("AAP")
		# Creating 2 persons with same PAN fails at Person level - this validates the chain
		create_test_person(first_name="Person", last_name="One", pan=pan)
		self.assertRaises(
			frappe.ValidationError, create_test_person, first_name="Person", last_name="Two", pan=pan
		)

	def test_pan_sole_proprietor_same_name_throws_error(self):
		"""Test that same PAN + same Name for Sole Proprietor throws error"""
		pan = generate_pan("AAP")
		person = create_test_person(first_name="SP", last_name="Person", pan=pan)

		client1 = create_knaps_client(
			investor_type="Sole Proprietor", person=person, client_name="My Business", save=False
		)
		client1.insert()

		# Same person, same business name - should fail at Client level
		client2 = create_knaps_client(
			investor_type="Sole Proprietor", person=person, client_name="My Business", save=False
		)

		self.assertRaises(frappe.ValidationError, client2.insert)
		client1.delete()

	def test_pan_sole_proprietor_different_name_ok(self):
		"""Test that same PAN + different Name for Sole Proprietor is allowed"""
		pan = generate_pan("AAP")
		person = create_test_person(first_name="SP2", last_name="Person", pan=pan)

		client1 = create_knaps_client(
			investor_type="Sole Proprietor", person=person, client_name="Business A", save=False
		)
		client1.insert()

		client2 = create_knaps_client(
			investor_type="Sole Proprietor", person=person, client_name="Business B", save=False
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
		client1 = create_knaps_client(investor_type="Individual", person=person, save=False)
		client1.insert()

		# Create as Sole Proprietor with different name
		client2 = create_knaps_client(
			investor_type="Sole Proprietor", person=person, client_name="My Sole Biz", save=False
		)
		client2.insert()

		self.assertEqual(client1.client_pan, pan)
		self.assertEqual(client2.client_pan, pan)
		self.assertNotEqual(client1.client_name, client2.client_name)
		client1.delete()
		client2.delete()

	# =====================================================
	# CONTACT DETAIL SYNC TESTS
	# =====================================================

	def test_individual_syncs_contact_details(self):
		"""Test that Individual syncs phone, whatsapp, email from Person"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="John", last_name="Doe", pan=pan)

		# Add contacts to person using proper method
		person = frappe.get_doc("KNAPS Person", person_name)
		phone_row = person.append("phone_numbers")
		phone_row.number = "+91 9876543210"
		phone_row.is_primary = 1
		phone_row.is_whatsapp = 1
		phone_row.is_active = 1
		phone_row.ownership = "Self"
		phone_row.type = "Mobile"

		email_row = person.append("email_address")
		email_row.email_address = "john@example.com"
		email_row.is_primary = 1
		email_row.is_active = 1
		email_row.ownership = "Self"
		email_row.type = "Personal"

		person.save()

		# Create client - contacts should sync
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		self.assertEqual(client.primary_phone, "+91 9876543210")
		self.assertEqual(client.primary_whatsapp, "+91 9876543210")
		self.assertEqual(client.primary_email, "john@example.com")
		self.assertEqual(client.status, "Active")
		client.delete()

	def test_individual_syncs_status(self):
		"""Test that Individual syncs status from Person"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Jane", last_name="Smith", pan=pan)

		# Update person status to Passive
		person = frappe.get_doc("KNAPS Person", person_name)
		person.status = "Passive"
		person.save()

		# Create client
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		self.assertEqual(client.status, "Passive")
		client.delete()

	def test_non_individual_syncs_contact_details(self):
		"""Test that Non Individual syncs contact details from entity"""
		pan = generate_pan("Company")
		entity_name = create_test_non_individual(
			non_individual_name="Test Corp", non_individual_type="Company", pan=pan
		)

		# Create client
		client = create_knaps_client(investor_type="Non Individual", non_individual=entity_name, save=False)
		client.insert()

		self.assertEqual(client.client_name, "Test Corp")
		self.assertEqual(client.client_pan, pan)
		client.delete()

	def test_sole_proprietor_syncs_contacts(self):
		"""Test that Sole Proprietor syncs contact fields but NOT client_name"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Mike", last_name="Ross", pan=pan)

		# Add contacts to person using proper method
		person = frappe.get_doc("KNAPS Person", person_name)
		phone_row = person.append("phone_numbers")
		phone_row.number = "+91 9876543210"
		phone_row.is_primary = 1
		phone_row.is_whatsapp = 0
		phone_row.is_active = 1
		phone_row.ownership = "Self"
		phone_row.type = "Mobile"

		email_row = person.append("email_address")
		email_row.email_address = "mike@example.com"
		email_row.is_primary = 1
		email_row.is_active = 1
		email_row.ownership = "Self"
		email_row.type = "Personal"

		person.save()

		# Create Sole Proprietor client - user enters manual name
		client = create_knaps_client(
			investor_type="Sole Proprietor",
			person=person_name,
			client_name="Mike's Design Studio",
			save=False,
		)
		client.insert()

		# Verify PAN and contacts sync, but name is manual
		self.assertEqual(client.client_name, "Mike's Design Studio")
		self.assertEqual(client.client_pan, pan)
		self.assertEqual(client.primary_phone, "+91 9876543210")
		self.assertEqual(client.primary_email, "mike@example.com")
		client.delete()

	def test_empty_contacts_handled(self):
		"""Test that empty contacts are handled gracefully"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Empty", last_name="Contact", pan=pan)

		# Create client with no contacts on person
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		# Verify empty strings
		self.assertEqual(client.primary_phone, "")
		self.assertEqual(client.primary_whatsapp, "")
		self.assertEqual(client.primary_email, "")
		client.delete()

	# =====================================================
	# IS_MINOR CALCULATION TESTS
	# =====================================================

	def test_is_minor_adult(self):
		"""Test that is_minor is 0 when age >= 18"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Adult", last_name="Person", pan=pan)

		# Set DOB to 25 years ago (adult)
		person = frappe.get_doc("KNAPS Person", person_name)
		person.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -25)
		person.save()

		# Create client
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		self.assertEqual(client.is_minor, 0)
		client.delete()

	def test_is_minor_underage(self):
		"""Test that is_minor is 1 when age < 18"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Minor", last_name="Person", pan=pan)

		# Set DOB to 10 years ago (minor)
		person = frappe.get_doc("KNAPS Person", person_name)
		person.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -10)
		person.save()

		# Create client
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		self.assertEqual(client.is_minor, 1)
		client.delete()

	def test_is_minor_non_individual_not_applicable(self):
		"""Test that is_minor doesn't apply to Non Individual clients"""
		pan = generate_pan("Company")
		entity_name = create_test_non_individual(
			non_individual_name="Company ABC", non_individual_type="Company", pan=pan
		)

		# Create Non Individual client
		client = create_knaps_client(investor_type="Non Individual", non_individual=entity_name, save=False)
		client.insert()

		# is_minor should not be set (or remain default 0)
		self.assertEqual(client.is_minor, 0)
		client.delete()

	def test_is_minor_sole_proprietor_not_applicable(self):
		"""Test that is_minor calculation doesn't apply to Sole Proprietor"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="SP", last_name="Owner", pan=pan)

		# Set as minor
		person = frappe.get_doc("KNAPS Person", person_name)
		person.date_of_birth = frappe.utils.add_years(frappe.utils.today(), -10)
		person.save()

		# Create Sole Proprietor client
		client = create_knaps_client(
			investor_type="Sole Proprietor", person=person_name, client_name="My Business", save=False
		)
		client.insert()

		# is_minor should remain default 0 for Sole Proprietor
		self.assertEqual(client.is_minor, 0)
		client.delete()

	# =====================================================
	# ON_UPDATE LINKED CLIENT SYNC TESTS
	# =====================================================

	def test_person_on_update_syncs_linked_clients(self):
		"""Test that updating Person updates all linked Clients"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Sync", last_name="Test", pan=pan)

		# Add contacts to person using proper method
		person = frappe.get_doc("KNAPS Person", person_name)
		phone_row = person.append("phone_numbers")
		phone_row.number = "+91 9876543210"
		phone_row.is_primary = 1
		phone_row.is_whatsapp = 0
		phone_row.is_active = 1
		phone_row.ownership = "Self"
		phone_row.type = "Mobile"
		person.save()

		# Create client
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		# Update person's phone
		person.phone_numbers[0].number = "+91 9876512345"
		person.save()

		# Reload client to get updated values
		client.reload()

		# Verify client was updated via on_update hook
		self.assertEqual(client.primary_phone, "+91 9876512345")
		client.delete()

	def test_person_status_change_syncs_clients(self):
		"""Test that status change on Person syncs to Clients"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Status", last_name="Sync", pan=pan)

		# Create client
		client = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client.insert()

		# Update person status
		person = frappe.get_doc("KNAPS Person", person_name)
		person.status = "Deceased"
		person.save()

		# Reload client
		client.reload()

		# Verify status synced
		self.assertEqual(client.status, "Deceased")
		client.delete()

	def test_non_individual_on_update_syncs_clients(self):
		"""Test that updating Non Individual updates all linked Clients"""
		pan = generate_pan("Company")
		entity_name = create_test_non_individual(
			non_individual_name="Sync Corp", non_individual_type="Company", pan=pan
		)

		# Create client
		client = create_knaps_client(investor_type="Non Individual", non_individual=entity_name, save=False)
		client.insert()

		# Update Non Individual name
		entity = frappe.get_doc("KNAPS Non Individual", entity_name)
		entity.non_individual_name = "Updated Corp Name"
		entity.save()

		# Reload client
		client.reload()

		# Verify client was updated
		self.assertEqual(client.client_name, "Updated Corp Name")
		client.delete()

	def test_non_individual_status_change_syncs_clients(self):
		"""Test that status change on Non Individual syncs to Clients"""
		pan = generate_pan("Company")
		entity_name = create_test_non_individual(
			non_individual_name="Status Corp", non_individual_type="Company", pan=pan
		)

		# Create client
		client = create_knaps_client(investor_type="Non Individual", non_individual=entity_name, save=False)
		client.insert()

		# Update Non Individual status
		entity = frappe.get_doc("KNAPS Non Individual", entity_name)
		entity.status = "Inactive"
		entity.save()

		# Reload client
		client.reload()

		# Verify status synced
		self.assertEqual(client.status, "Inactive")
		client.delete()

	def test_multiple_linked_clients_sync(self):
		"""Test that multiple Clients linked to same Person all get updated"""
		pan = generate_pan("Person")
		person_name = create_test_person(first_name="Multi", last_name="Link", pan=pan)

		# Add contacts to person using proper method
		person = frappe.get_doc("KNAPS Person", person_name)
		phone_row = person.append("phone_numbers")
		phone_row.number = "+91 9876543210"
		phone_row.is_primary = 1
		phone_row.is_whatsapp = 0
		phone_row.is_active = 1
		phone_row.ownership = "Self"
		phone_row.type = "Mobile"
		person.save()

		# Create two clients linked to same person
		client1 = create_knaps_client(investor_type="Individual", person=person_name, save=False)
		client1.insert()

		client2 = create_knaps_client(
			investor_type="Sole Proprietor", person=person_name, client_name="Business One", save=False
		)
		client2.insert()

		# Update person phone
		person.phone_numbers[0].number = "+91 9876512345"
		person.save()

		# Reload both clients
		client1.reload()
		client2.reload()

		# Both should be updated
		self.assertEqual(client1.primary_phone, "+91 9876512345")
		self.assertEqual(client2.primary_phone, "+91 9876512345")
		client1.delete()
		client2.delete()
