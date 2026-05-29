# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt
import frappe
from frappe.tests import IntegrationTestCase

from knaps.utils.constants import (
	DOCTYPE_FAMILY,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
	DOCTYPE_RELATIONSHIP,
)

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender"]

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


def create_knaps_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_INDIVIDUAL,
			"first_name": kwargs.get("first_name", "Test"),
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


def create_knaps_non_individual(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE_NON_INDIVIDUAL,
			"legal_name": kwargs.get("legal_name", "Test Entity"),
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


def create_knaps_family(**kwargs):
	head = kwargs.get("head_of_family")
	members = kwargs.get("members")
	if members is None:
		member_individual = create_knaps_individual(
			first_name="Default", last_name="Member", phone_numbers=[], email_address=[]
		)
		members = [
			{
				"member_type": DOCTYPE_INDIVIDUAL,
				"member_name": member_individual.name,
				"relation_with_head": "Self",
				"membership_type": "Secondary",
			}
		]
	family = frappe.get_doc(
		{
			"doctype": DOCTYPE_FAMILY,
			"family_name": kwargs.get("family_name", "Test Family"),
			"head_of_family": head.name if head else None,
			"members": members,
		}
	)
	if kwargs.get("save", True):
		family.insert()
	return family


def create_relationship(name):
	if not frappe.db.exists(DOCTYPE_RELATIONSHIP, name):
		frappe.get_doc({"doctype": DOCTYPE_RELATIONSHIP, "relationship_name": name}).insert()
	return name


class IntegrationTestKNAPSFamily(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for t in NON_INDIVIDUAL_TYPES:
			if not frappe.db.exists(DOCTYPE_NON_INDIVIDUAL_TYPE, t):
				frappe.get_doc({"doctype": DOCTYPE_NON_INDIVIDUAL_TYPE, "non_individual_type": t}).insert()

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_family_sp")
		self.relation = create_relationship("Self")
		self.phone = [
			{
				"number": "+91 9876543210",
				"is_primary": 1,
				"is_whatsapp": 0,
				"is_active": 1,
				"ownership": "Self",
				"type": "Mobile",
			}
		]
		self.email = [
			{
				"email_address": "test@example.com",
				"is_primary": 1,
				"is_active": 1,
				"ownership": "Self",
				"type": "Personal",
			}
		]

	def tearDown(self):
		frappe.db.rollback(save_point="knaps_family_sp")
		super().tearDown()

	# =====================================================
	# DUPLICATE MEMBER VALIDATION
	# =====================================================

	def test_duplicate_individual_rejected(self):
		individual = create_knaps_individual(
			first_name="John", phone_numbers=self.phone, email_address=self.email
		)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=create_knaps_individual(
					first_name="Head", phone_numbers=self.phone, email_address=self.email
				),
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": individual.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": individual.name,
						"relation_with_head": self.relation,
						"membership_type": "Secondary",
					},
				],
			)
		self.assertIn("already added", str(cm.exception).lower())

	def test_duplicate_non_individual_rejected(self):
		entity = create_knaps_non_individual(
			legal_name="Duplicate Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		with self.assertRaises(frappe.ValidationError):
			create_knaps_family(
				head_of_family=create_knaps_individual(
					first_name="Head", phone_numbers=self.phone, email_address=self.email
				),
				members=[
					{
						"member_type": DOCTYPE_NON_INDIVIDUAL,
						"member_name": entity.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
					{
						"member_type": DOCTYPE_NON_INDIVIDUAL,
						"member_name": entity.name,
						"relation_with_head": self.relation,
						"membership_type": "Beneficial",
					},
				],
			)

	def test_same_name_different_type_allowed(self):
		individual = create_knaps_individual(
			first_name="Test", last_name="Entity", phone_numbers=self.phone, email_address=self.email
		)
		entity = create_knaps_non_individual(
			legal_name=individual.name, phone_numbers=self.phone, email_addresses=self.email
		)
		family = create_knaps_family(
			head_of_family=create_knaps_individual(
				first_name="Head", phone_numbers=self.phone, email_address=self.email
			),
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": individual.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": entity.name,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family.members), 2)

	def test_all_unique_members_passes(self):
		p1 = create_knaps_individual(first_name="Alice", phone_numbers=self.phone, email_address=self.email)
		p2 = create_knaps_individual(first_name="Bob", phone_numbers=self.phone, email_address=self.email)
		e1 = create_knaps_non_individual(
			legal_name="Corp A", phone_numbers=self.phone, email_addresses=self.email
		)
		family = create_knaps_family(
			head_of_family=create_knaps_individual(
				first_name="Head", phone_numbers=self.phone, email_address=self.email
			),
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": e1.name,
					"membership_type": "Beneficial",
				},
			],
		)
		self.assertEqual(len(family.members), 3)

	# =====================================================
	# HEAD NOT IN MEMBERS VALIDATION
	# =====================================================

	def test_head_listed_as_member_rejected(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=head,
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": head.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)
		self.assertIn("head of family", str(cm.exception).lower())

	def test_head_not_in_members_passes(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Member", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family.members), 1)

	def test_family_with_only_head_passes(self):
		head = create_knaps_individual(first_name="Solo", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Member", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(family.head_of_family, head.name)
		self.assertEqual(len(family.members), 1)

	# =====================================================
	# HEAD OF FAMILY PRIMARY FAMILY SYNC
	# =====================================================

	def test_head_primary_family_set_on_create(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head)
		primary_family = frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family")
		self.assertEqual(primary_family, family.name)

	def test_head_primary_family_unchanged_on_same_head_resave(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head)
		family.family_name = "Renamed Family"
		family.save()
		primary_family = frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family")
		self.assertEqual(primary_family, family.name)

	def test_head_change_clears_old_and_sets_new(self):
		old_head = create_knaps_individual(
			first_name="Old Head", phone_numbers=self.phone, email_address=self.email
		)
		new_head = create_knaps_individual(
			first_name="New Head", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(head_of_family=old_head)
		family.head_of_family = new_head.name
		family.save()
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, old_head.name, "family"), None)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, new_head.name, "family"), family.name)

	def test_head_change_does_not_clear_old_if_not_pointing_here(self):
		old_head = create_knaps_individual(
			first_name="Old Head", phone_numbers=self.phone, email_address=self.email
		)
		new_head = create_knaps_individual(
			first_name="New Head", phone_numbers=self.phone, email_address=self.email
		)
		another = create_knaps_individual(
			first_name="Another", phone_numbers=self.phone, email_address=self.email
		)
		family_a = create_knaps_family(head_of_family=old_head)
		family_a.head_of_family = another.name
		family_a.save()
		family_b = create_knaps_family(
			head_of_family=new_head,
			family_name="Family B",
		)
		family_b.head_of_family = old_head.name
		family_b.save()
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, old_head.name, "family"),
			family_b.name,
		)

	def test_head_change_rejected_if_new_head_is_primary_elsewhere(self):
		primary_individual = create_knaps_individual(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(head_of_family=primary_individual, family_name="Other Family")
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head)
		with self.assertRaises(frappe.ValidationError) as cm:
			family.head_of_family = primary_individual.name
			family.save()
		self.assertIn("already a primary member", str(cm.exception).lower())

	def test_primary_member_promoted_to_head_keeps_primary_family(self):
		head = create_knaps_individual(
			first_name="OldHead", phone_numbers=self.phone, email_address=self.email
		)
		member = create_knaps_individual(
			first_name="Promoted", phone_numbers=self.phone, email_address=self.email
		)
		other = create_knaps_individual(
			first_name="Other", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": other.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"),
			family.name,
		)
		family.head_of_family = member.name
		family.members = [row for row in family.members if row.member_name != member.name]
		family.save()
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"),
			family.name,
		)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family"),
			None,
		)

	# =====================================================
	# PRIMARY MEMBER SYNC — ADD
	# =====================================================

	def test_add_primary_individual_sets_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Member", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"),
			family.name,
		)

	def test_add_primary_non_individual_sets_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(
			legal_name="Primary Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": entity.name,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, entity.name, "family"),
			family.name,
		)

	def test_add_secondary_member_does_not_set_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Secondary", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_add_beneficial_member_does_not_set_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Beneficial", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Beneficial",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_multiple_primary_members_all_set(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		p1 = create_knaps_individual(
			first_name="Primary1", phone_numbers=self.phone, email_address=self.email
		)
		p2 = create_knaps_individual(
			first_name="Primary2", phone_numbers=self.phone, email_address=self.email
		)
		e1 = create_knaps_non_individual(
			legal_name="Primary Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": e1.name,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p1.name, "family"), family.name)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p2.name, "family"), family.name)
		self.assertEqual(frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, e1.name, "family"), family.name)

	# =====================================================
	# PRIMARY MEMBER SYNC — CHANGE / REMOVE
	# =====================================================

	def test_change_primary_to_secondary_clears_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="ChangeMe", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"), family.name)
		family.members[0].membership_type = "Secondary"
		family.save()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_change_secondary_to_primary_sets_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Promoted", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))
		family.members[0].membership_type = "Primary"
		family.save()
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"), family.name)

	def test_delete_primary_member_clears_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="RemoveMe", phone_numbers=self.phone, email_address=self.email
		)
		other = create_knaps_individual(
			first_name="Other", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": other.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"), family.name)
		family.members = [row for row in family.members if row.member_name != member.name]
		family.save()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_delete_secondary_member_does_not_affect_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="KeepMe", phone_numbers=self.phone, email_address=self.email
		)
		other = create_knaps_individual(
			first_name="Other", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": other.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		family.members = [row for row in family.members if row.member_name != member.name]
		family.save()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_clear_only_if_matching_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Shared", phone_numbers=self.phone, email_address=self.email
		)
		other = create_knaps_individual(
			first_name="Other", phone_numbers=self.phone, email_address=self.email
		)
		family_a = create_knaps_family(head_of_family=head, family_name="Family A")
		frappe.db.set_value(DOCTYPE_INDIVIDUAL, member.name, "family", family_a.name)
		head2 = create_knaps_individual(
			first_name="Head2", phone_numbers=self.phone, email_address=self.email
		)
		family_b = create_knaps_family(
			head_of_family=head2,
			family_name="Family B",
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": other.name,
					"relation_with_head": self.relation,
					"membership_type": "Beneficial",
				},
			],
		)
		family_b.members = [row for row in family_b.members if row.member_name != member.name]
		family_b.save()
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"),
			family_a.name,
		)

	# =====================================================
	# CROSS-FAMILY PRIMARY CONFLICT
	# =====================================================

	def test_add_primary_member_who_is_already_primary_elsewhere_rejected(self):
		head_a = create_knaps_individual(
			first_name="HeadA", phone_numbers=self.phone, email_address=self.email
		)
		member = create_knaps_individual(
			first_name="Conflict", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(
			head_of_family=head_a,
			family_name="First Family",
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		head_b = create_knaps_individual(
			first_name="HeadB", phone_numbers=self.phone, email_address=self.email
		)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=head_b,
				family_name="Second Family",
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": member.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)
		self.assertIn("already a primary member", str(cm.exception).lower())

	def test_set_head_who_is_already_primary_elsewhere_rejected(self):
		primary_individual = create_knaps_individual(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		other_family_head = create_knaps_individual(
			first_name="OtherHead", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(
			head_of_family=other_family_head,
			family_name="Other Family",
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": primary_individual.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		create_knaps_individual(first_name="NewHead", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError):
			create_knaps_family(head_of_family=primary_individual)

	def test_add_as_secondary_when_primary_elsewhere_allowed(self):
		primary_individual = create_knaps_individual(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		head_a = create_knaps_individual(
			first_name="HeadA", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_family(
			head_of_family=head_a,
			family_name="First Family",
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": primary_individual.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		head_b = create_knaps_individual(
			first_name="HeadB", phone_numbers=self.phone, email_address=self.email
		)
		family_b = create_knaps_family(
			head_of_family=head_b,
			family_name="Second Family",
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": primary_individual.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family_b.members), 1)

	# =====================================================
	# DECEASED MEMBER VALIDATION
	# =====================================================

	def test_deceased_head_rejected(self):
		deceased = create_knaps_individual(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(head_of_family=deceased)
		self.assertIn("deceased", str(cm.exception).lower())

	def test_deceased_member_rejected(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		deceased = create_knaps_individual(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=head,
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": deceased.name,
						"relation_with_head": self.relation,
						"membership_type": "Secondary",
					},
				],
			)
		self.assertIn("deceased", str(cm.exception).lower())

	def test_deceased_member_rejected_even_as_primary(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		deceased = create_knaps_individual(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError):
			create_knaps_family(
				head_of_family=head,
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": deceased.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)

	def test_deceased_non_individual_allowed(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(legal_name="Dead Entity", status="Inactive")
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": entity.name,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family.members), 1)

	def test_active_member_allowed(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Alive", status="Active", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(len(family.members), 1)

	# =====================================================
	# RELATION WITH HEAD VALIDATION
	# =====================================================

	def test_individual_member_without_relation_rejected(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="NoRelation", phone_numbers=self.phone, email_address=self.email
		)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=head,
				members=[
					{
						"member_type": DOCTYPE_INDIVIDUAL,
						"member_name": member.name,
						"membership_type": "Secondary",
					},
				],
			)
		self.assertIn("Relation with Head", str(cm.exception))

	def test_non_individual_member_without_relation_allowed(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(
			legal_name="No Relation Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": entity.name,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family.members), 1)

	def test_non_individual_member_with_relation_rejected(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(
			legal_name="Entity With Relation", phone_numbers=self.phone, email_addresses=self.email
		)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(
				head_of_family=head,
				members=[
					{
						"member_type": DOCTYPE_NON_INDIVIDUAL,
						"member_name": entity.name,
						"relation_with_head": self.relation,
						"membership_type": "Secondary",
					},
				],
			)
		self.assertIn("not applicable", str(cm.exception).lower())

	def test_individual_member_with_relation_allowed(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="WithRelation", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(family.members), 1)

	# =====================================================
	# EDGE CASES
	# =====================================================

	def test_new_family_without_before_save(self):
		head = create_knaps_individual(first_name="New", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head, save=True)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family"),
			family.name,
		)

	def test_family_without_members_rejected(self):
		head = create_knaps_individual(first_name="Alone", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_family(head_of_family=head, members=[])
		self.assertIn("at least one member", str(cm.exception).lower())

	def test_all_members_deleted_in_one_edit(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		p1 = create_knaps_individual(first_name="M1", phone_numbers=self.phone, email_address=self.email)
		p2 = create_knaps_individual(first_name="M2", phone_numbers=self.phone, email_address=self.email)
		p3 = create_knaps_individual(first_name="M3", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": p3.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p1.name, "family"), family.name)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p2.name, "family"), family.name)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p3.name, "family"), family.name)
		family.members = [row for row in family.members if row.member_name != p1.name]
		family.save()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p1.name, "family"))
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, p2.name, "family"), family.name)
		self.assertEqual(
			frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family"),
			family.name,
		)

	# =====================================================
	# FAMILY DELETION CLEARS LINKS
	# =====================================================

	def test_delete_family_clears_head_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family"), family.name)
		family.delete()
		self.assertFalse(frappe.db.exists(DOCTYPE_FAMILY, family.name))
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, head.name, "family"))

	def test_delete_family_clears_primary_member_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_individual(
			first_name="Primary", phone_numbers=self.phone, email_address=self.email
		)
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_INDIVIDUAL,
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"), family.name)
		family.delete()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_INDIVIDUAL, member.name, "family"))

	def test_delete_family_clears_non_individual_primary_family(self):
		head = create_knaps_individual(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(legal_name="Test Entity", pan="ABCCC1234F")
		family = create_knaps_family(
			head_of_family=head,
			members=[
				{
					"member_type": DOCTYPE_NON_INDIVIDUAL,
					"member_name": entity.name,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, entity.name, "family"), family.name)
		family.delete()
		self.assertIsNone(frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, entity.name, "family"))

	def test_delete_family_with_no_linked_members_succeeds(self):
		head = create_knaps_individual(first_name="Temp", phone_numbers=self.phone, email_address=self.email)
		family = create_knaps_family(head_of_family=head)
		frappe.db.set_value(DOCTYPE_INDIVIDUAL, head.name, "family", None)
		family.delete()
		self.assertFalse(frappe.db.exists(DOCTYPE_FAMILY, family.name))
