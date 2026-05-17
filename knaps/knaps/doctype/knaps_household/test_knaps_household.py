# Copyright (c) 2026, KNAPS and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

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


def create_knaps_person(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": "KNAPS Person",
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
			"doctype": "KNAPS Non Individual",
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


def create_knaps_household(**kwargs):
	head = kwargs.get("head_of_household")
	members = kwargs.get("members", [])
	household = frappe.get_doc(
		{
			"doctype": "KNAPS Household",
			"household_name": kwargs.get("household_name", "Test Household"),
			"head_of_household": head.name if head else None,
			"members": members,
		}
	)
	if kwargs.get("save", True):
		household.insert()
	return household


def create_relationship(name):
	if not frappe.db.exists("KNAPS Relationship", name):
		frappe.get_doc({"doctype": "KNAPS Relationship", "relationship_name": name}).insert()
	return name


class IntegrationTestKNAPSHousehold(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for t in NON_INDIVIDUAL_TYPES:
			if not frappe.db.exists("KNAPS Non Individual Type", t):
				frappe.get_doc({"doctype": "KNAPS Non Individual Type", "non_individual_type": t}).insert()

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_household_sp")
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
		frappe.db.rollback(save_point="knaps_household_sp")
		super().tearDown()

	# =====================================================
	# DUPLICATE MEMBER VALIDATION
	# =====================================================

	def test_duplicate_person_rejected(self):
		person = create_knaps_person(first_name="John", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_household(
				head_of_household=create_knaps_person(
					first_name="Head", phone_numbers=self.phone, email_address=self.email
				),
				members=[
					{
						"member_type": "KNAPS Person",
						"member_name": person.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
					{
						"member_type": "KNAPS Person",
						"member_name": person.name,
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
			create_knaps_household(
				head_of_household=create_knaps_person(
					first_name="Head", phone_numbers=self.phone, email_address=self.email
				),
				members=[
					{
						"member_type": "KNAPS Non Individual",
						"member_name": entity.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
					{
						"member_type": "KNAPS Non Individual",
						"member_name": entity.name,
						"relation_with_head": self.relation,
						"membership_type": "Beneficial",
					},
				],
			)

	def test_same_name_different_type_allowed(self):
		person = create_knaps_person(
			first_name="Test", last_name="Entity", phone_numbers=self.phone, email_address=self.email
		)
		entity = create_knaps_non_individual(
			legal_name=person.name, phone_numbers=self.phone, email_addresses=self.email
		)
		household = create_knaps_household(
			head_of_household=create_knaps_person(
				first_name="Head", phone_numbers=self.phone, email_address=self.email
			),
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": person.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": "KNAPS Non Individual",
					"member_name": entity.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(household.members), 2)

	def test_all_unique_members_passes(self):
		p1 = create_knaps_person(first_name="Alice", phone_numbers=self.phone, email_address=self.email)
		p2 = create_knaps_person(first_name="Bob", phone_numbers=self.phone, email_address=self.email)
		e1 = create_knaps_non_individual(
			legal_name="Corp A", phone_numbers=self.phone, email_addresses=self.email
		)
		household = create_knaps_household(
			head_of_household=create_knaps_person(
				first_name="Head", phone_numbers=self.phone, email_address=self.email
			),
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": "KNAPS Person",
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
				{
					"member_type": "KNAPS Non Individual",
					"member_name": e1.name,
					"relation_with_head": self.relation,
					"membership_type": "Beneficial",
				},
			],
		)
		self.assertEqual(len(household.members), 3)

	# =====================================================
	# HEAD NOT IN MEMBERS VALIDATION
	# =====================================================

	def test_head_listed_as_member_rejected(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_household(
				head_of_household=head,
				members=[
					{
						"member_type": "KNAPS Person",
						"member_name": head.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)
		self.assertIn("head of household", str(cm.exception).lower())

	def test_head_not_in_members_passes(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(first_name="Member", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(household.members), 1)

	def test_household_with_only_head_passes(self):
		head = create_knaps_person(first_name="Solo", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head, members=[])
		self.assertEqual(household.head_of_household, head.name)
		self.assertEqual(len(household.members), 0)

	# =====================================================
	# HEAD OF HOUSEHOLD PRIMARY HOUSEHOLD SYNC
	# =====================================================

	def test_head_primary_household_set_on_create(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head)
		primary_hh = frappe.db.get_value("KNAPS Person", head.name, "primary_household")
		self.assertEqual(primary_hh, household.name)

	def test_head_primary_household_unchanged_on_same_head_resave(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head)
		household.household_name = "Renamed Household"
		household.save()
		primary_hh = frappe.db.get_value("KNAPS Person", head.name, "primary_household")
		self.assertEqual(primary_hh, household.name)

	def test_head_change_clears_old_and_sets_new(self):
		old_head = create_knaps_person(
			first_name="Old Head", phone_numbers=self.phone, email_address=self.email
		)
		new_head = create_knaps_person(
			first_name="New Head", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(head_of_household=old_head)
		household.head_of_household = new_head.name
		household.save()
		self.assertEqual(frappe.db.get_value("KNAPS Person", old_head.name, "primary_household"), None)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", new_head.name, "primary_household"), household.name
		)

	def test_head_change_does_not_clear_old_if_not_pointing_here(self):
		old_head = create_knaps_person(
			first_name="Old Head", phone_numbers=self.phone, email_address=self.email
		)
		new_head = create_knaps_person(
			first_name="New Head", phone_numbers=self.phone, email_address=self.email
		)
		another = create_knaps_person(
			first_name="Another", phone_numbers=self.phone, email_address=self.email
		)
		household_a = create_knaps_household(head_of_household=old_head)
		household_a.head_of_household = another.name
		household_a.save()
		household_b = create_knaps_household(
			head_of_household=new_head,
			household_name="Household B",
		)
		household_b.head_of_household = old_head.name
		household_b.save()
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", old_head.name, "primary_household"),
			household_b.name,
		)

	def test_head_change_rejected_if_new_head_is_primary_elsewhere(self):
		primary_person = create_knaps_person(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_household(head_of_household=primary_person, household_name="Other HH")
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head)
		with self.assertRaises(frappe.ValidationError) as cm:
			household.head_of_household = primary_person.name
			household.save()
		self.assertIn("already a primary member", str(cm.exception).lower())

	def test_primary_member_promoted_to_head_keeps_primary_household(self):
		head = create_knaps_person(first_name="OldHead", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Promoted", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"),
			household.name,
		)
		household.head_of_household = member.name
		household.members = []
		household.save()
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"),
			household.name,
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", head.name, "primary_household"),
			None,
		)

	# =====================================================
	# PRIMARY MEMBER SYNC — ADD
	# =====================================================

	def test_add_primary_person_sets_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(first_name="Member", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"),
			household.name,
		)

	def test_add_primary_non_individual_sets_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(
			legal_name="Primary Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Non Individual",
					"member_name": entity.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Non Individual", entity.name, "primary_household"),
			household.name,
		)

	def test_add_secondary_member_does_not_set_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Secondary", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_add_beneficial_member_does_not_set_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Beneficial", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Beneficial",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_multiple_primary_members_all_set(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		p1 = create_knaps_person(first_name="Primary1", phone_numbers=self.phone, email_address=self.email)
		p2 = create_knaps_person(first_name="Primary2", phone_numbers=self.phone, email_address=self.email)
		e1 = create_knaps_non_individual(
			legal_name="Primary Entity", phone_numbers=self.phone, email_addresses=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": "KNAPS Person",
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": "KNAPS Non Individual",
					"member_name": e1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value("KNAPS Person", p1.name, "primary_household"), household.name)
		self.assertEqual(frappe.db.get_value("KNAPS Person", p2.name, "primary_household"), household.name)
		self.assertEqual(
			frappe.db.get_value("KNAPS Non Individual", e1.name, "primary_household"), household.name
		)

	# =====================================================
	# PRIMARY MEMBER SYNC — CHANGE / REMOVE
	# =====================================================

	def test_change_primary_to_secondary_clears_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="ChangeMe", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"), household.name
		)
		household.members[0].membership_type = "Secondary"
		household.save()
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_change_secondary_to_primary_sets_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Promoted", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))
		household.members[0].membership_type = "Primary"
		household.save()
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"), household.name
		)

	def test_delete_primary_member_clears_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="RemoveMe", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"), household.name
		)
		household.members = []
		household.save()
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_delete_secondary_member_does_not_affect_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(first_name="KeepMe", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		household.members = []
		household.save()
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_clear_only_if_matching_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(first_name="Shared", phone_numbers=self.phone, email_address=self.email)
		household_a = create_knaps_household(head_of_household=head, household_name="Household A")
		frappe.db.set_value("KNAPS Person", member.name, "primary_household", household_a.name)
		head2 = create_knaps_person(first_name="Head2", phone_numbers=self.phone, email_address=self.email)
		household_b = create_knaps_household(
			head_of_household=head2,
			household_name="Household B",
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		household_b.members = []
		household_b.save()
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"),
			household_a.name,
		)

	# =====================================================
	# CROSS-HOUSEHOLD PRIMARY CONFLICT
	# =====================================================

	def test_add_primary_member_who_is_already_primary_elsewhere_rejected(self):
		head_a = create_knaps_person(first_name="HeadA", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Conflict", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_household(
			head_of_household=head_a,
			household_name="First Household",
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		head_b = create_knaps_person(first_name="HeadB", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_household(
				head_of_household=head_b,
				household_name="Second Household",
				members=[
					{
						"member_type": "KNAPS Person",
						"member_name": member.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)
		self.assertIn("already a primary member", str(cm.exception).lower())

	def test_set_head_who_is_already_primary_elsewhere_rejected(self):
		primary_person = create_knaps_person(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		other_hh_head = create_knaps_person(
			first_name="OtherHead", phone_numbers=self.phone, email_address=self.email
		)
		create_knaps_household(
			head_of_household=other_hh_head,
			household_name="Other HH",
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": primary_person.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		create_knaps_person(first_name="NewHead", phone_numbers=self.phone, email_address=self.email)
		with self.assertRaises(frappe.ValidationError):
			create_knaps_household(head_of_household=primary_person)

	def test_add_as_secondary_when_primary_elsewhere_allowed(self):
		primary_person = create_knaps_person(
			first_name="Primary Elsewhere", phone_numbers=self.phone, email_address=self.email
		)
		head_a = create_knaps_person(first_name="HeadA", phone_numbers=self.phone, email_address=self.email)
		create_knaps_household(
			head_of_household=head_a,
			household_name="First HH",
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": primary_person.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		head_b = create_knaps_person(first_name="HeadB", phone_numbers=self.phone, email_address=self.email)
		household_b = create_knaps_household(
			head_of_household=head_b,
			household_name="Second HH",
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": primary_person.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(household_b.members), 1)

	# =====================================================
	# DECEASED MEMBER VALIDATION
	# =====================================================

	def test_deceased_head_rejected(self):
		deceased = create_knaps_person(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_household(head_of_household=deceased)
		self.assertIn("deceased", str(cm.exception).lower())

	def test_deceased_member_rejected(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		deceased = create_knaps_person(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError) as cm:
			create_knaps_household(
				head_of_household=head,
				members=[
					{
						"member_type": "KNAPS Person",
						"member_name": deceased.name,
						"relation_with_head": self.relation,
						"membership_type": "Secondary",
					},
				],
			)
		self.assertIn("deceased", str(cm.exception).lower())

	def test_deceased_member_rejected_even_as_primary(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		deceased = create_knaps_person(first_name="Dead", status="Deceased")
		with self.assertRaises(frappe.ValidationError):
			create_knaps_household(
				head_of_household=head,
				members=[
					{
						"member_type": "KNAPS Person",
						"member_name": deceased.name,
						"relation_with_head": self.relation,
						"membership_type": "Primary",
					},
				],
			)

	def test_deceased_non_individual_allowed(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(legal_name="Dead Entity", status="Inactive")
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Non Individual",
					"member_name": entity.name,
					"relation_with_head": self.relation,
					"membership_type": "Secondary",
				},
			],
		)
		self.assertEqual(len(household.members), 1)

	def test_active_member_allowed(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(
			first_name="Alive", status="Active", phone_numbers=self.phone, email_address=self.email
		)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(len(household.members), 1)

	# =====================================================
	# EDGE CASES
	# =====================================================

	def test_new_household_without_before_save(self):
		head = create_knaps_person(first_name="New", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head, save=True)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", head.name, "primary_household"),
			household.name,
		)

	def test_household_with_zero_members_saves_ok(self):
		head = create_knaps_person(first_name="Alone", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head, members=[])
		self.assertEqual(len(household.members), 0)

	def test_all_members_deleted_in_one_edit(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		p1 = create_knaps_person(first_name="M1", phone_numbers=self.phone, email_address=self.email)
		p2 = create_knaps_person(first_name="M2", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": p1.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
				{
					"member_type": "KNAPS Person",
					"member_name": p2.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(frappe.db.get_value("KNAPS Person", p1.name, "primary_household"), household.name)
		self.assertEqual(frappe.db.get_value("KNAPS Person", p2.name, "primary_household"), household.name)
		household.members = []
		household.save()
		self.assertIsNone(frappe.db.get_value("KNAPS Person", p1.name, "primary_household"))
		self.assertIsNone(frappe.db.get_value("KNAPS Person", p2.name, "primary_household"))
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", head.name, "primary_household"),
			household.name,
		)

	# =====================================================
	# HOUSEHOLD DELETION CLEARS LINKS
	# =====================================================

	def test_delete_household_clears_head_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head)
		self.assertEqual(frappe.db.get_value("KNAPS Person", head.name, "primary_household"), household.name)
		household.delete()
		self.assertFalse(frappe.db.exists("KNAPS Household", household.name))
		self.assertIsNone(frappe.db.get_value("KNAPS Person", head.name, "primary_household"))

	def test_delete_household_clears_primary_member_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		member = create_knaps_person(first_name="Primary", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Person",
					"member_name": member.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Person", member.name, "primary_household"), household.name
		)
		household.delete()
		self.assertIsNone(frappe.db.get_value("KNAPS Person", member.name, "primary_household"))

	def test_delete_household_clears_non_individual_primary_household(self):
		head = create_knaps_person(first_name="Head", phone_numbers=self.phone, email_address=self.email)
		entity = create_knaps_non_individual(legal_name="Test Entity", pan="ABCCC1234F")
		household = create_knaps_household(
			head_of_household=head,
			members=[
				{
					"member_type": "KNAPS Non Individual",
					"member_name": entity.name,
					"relation_with_head": self.relation,
					"membership_type": "Primary",
				},
			],
		)
		self.assertEqual(
			frappe.db.get_value("KNAPS Non Individual", entity.name, "primary_household"), household.name
		)
		household.delete()
		self.assertIsNone(frappe.db.get_value("KNAPS Non Individual", entity.name, "primary_household"))

	def test_delete_household_with_no_linked_members_succeeds(self):
		head = create_knaps_person(first_name="Temp", phone_numbers=self.phone, email_address=self.email)
		household = create_knaps_household(head_of_household=head)
		frappe.db.set_value("KNAPS Person", head.name, "primary_household", None)
		household.delete()
		self.assertFalse(frappe.db.exists("KNAPS Household", household.name))
