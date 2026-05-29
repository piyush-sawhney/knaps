import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_months, add_years, getdate, today

from knaps.utils.constants import (
	DOCTYPE_CLIENT,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_INSURANCE_PLAN,
	DOCTYPE_LIFE_INSURANCE,
	DOCTYPE_NON_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
	DOCTYPE_PAYMENT_TYPE,
	DOCTYPE_PRODUCT,
	DOCTYPE_PRODUCT_PROVIDER,
	DOCTYPE_RELATIONSHIP,
)


class TestKNAPSLifeInsurance(IntegrationTestCase):
	doctype = None

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_life_insurance_sp")
		self.adult_individual = self._create_individual("Adult", "Male", "Mr", "1990-01-01")
		self.minor_individual = self._create_individual("Minor", "Male", "Mr", "2015-01-01")
		self.minor_guardian_individual = self._create_individual(
			"Minor Guardian", "Female", "Ms", "2010-01-01"
		)
		self.guardian_individual = self._create_individual("Guardian", "Female", "Mrs", "1985-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.other_individual = self._create_individual("Other", "Male", "Mr", "1992-06-15")
		self.adult_client = self._create_client("Individual", self.adult_individual)
		self.minor_client = self._create_client("Individual", self.minor_individual)
		self.nominee_client = self._create_client("Individual", self.nominee_individual)
		self.other_client = self._create_client("Individual", self.other_individual)
		self.product_provider = self._create_product_provider()
		self.insurance_plan = self._create_insurance_plan("Gold Life", "GOLD-001")
		self.payment_type = self._create_payment_type("Cash")
		self.relationship = self._create_relationship("Spouse")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_life_insurance_sp")
		super().tearDown()

	def _create_individual(self, first_name: str, gender: str, salutation: str, dob: str) -> str:
		self._ensure_doctype_exists("Gender", gender)
		self._ensure_doctype_exists("Salutation", salutation)
		ind = frappe.get_doc(
			{
				"doctype": DOCTYPE_INDIVIDUAL,
				"first_name": first_name,
				"gender": gender,
				"salutation": salutation,
				"date_of_birth": dob,
				"status": "Active",
			}
		)
		ind.insert()
		return ind.name

	def _ensure_doctype_exists(self, doctype: str, name: str) -> None:
		if not frappe.db.exists(doctype, name):
			frappe.get_doc({"doctype": doctype, "name": name}).insert()

	def _create_client(self, client_type: str, individual: str) -> str:
		client = frappe.get_doc(
			{
				"doctype": DOCTYPE_CLIENT,
				"client_type": client_type,
				"individual": individual,
			}
		)
		client.insert()
		return client.name

	def _create_product_provider(self) -> str:
		if not frappe.db.exists(DOCTYPE_PRODUCT, "Life Insurance"):
			frappe.get_doc({"doctype": DOCTYPE_PRODUCT, "product_name": "Life Insurance"}).insert()
		if not frappe.db.exists(DOCTYPE_NON_INDIVIDUAL_TYPE, "Company"):
			frappe.get_doc(
				{"doctype": DOCTYPE_NON_INDIVIDUAL_TYPE, "non_individual_type": "Company"}
			).insert()
		provider = frappe.get_doc(
			{
				"doctype": DOCTYPE_NON_INDIVIDUAL,
				"legal_name": "Test Life Insurer Co",
				"non_individual_type": "Company",
				"status": "Active",
			}
		)
		provider.insert()
		pp = frappe.get_doc(
			{
				"doctype": DOCTYPE_PRODUCT_PROVIDER,
				"product": "Life Insurance",
				"provider": provider.name,
			}
		)
		pp.insert()
		return pp.name

	def _create_insurance_plan(self, plan_name: str, uin: str) -> str:
		plan = frappe.get_doc(
			{
				"doctype": DOCTYPE_INSURANCE_PLAN,
				"insurer": self.product_provider,
				"plan_name": plan_name,
				"uin": uin,
				"is_active": 1,
			}
		)
		plan.insert()
		return plan.name

	def _create_payment_type(self, name: str) -> str:
		existing = frappe.db.get_value(DOCTYPE_PAYMENT_TYPE, {"payment_type": name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_PAYMENT_TYPE,
				"payment_type": name,
			}
		)
		doc.insert()
		return doc.name

	def _create_relationship(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_RELATIONSHIP, name):
			return name
		frappe.get_doc(
			{
				"doctype": DOCTYPE_RELATIONSHIP,
				"relationship_name": name,
			}
		).insert()
		return name

	def _make_policy(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_LIFE_INSURANCE,
			"entry_date": today(),
			"status": "Proposal",
			"policy_type": "Term",
			"insurance_plan_name": self.insurance_plan,
			"period_type": "Years",
			"period": 10,
			"premium": 5000,
			"premium_mode": "Single",
			"currency": "INR",
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _add_member(self, doc, client: str, role: str = "Insured Member", is_primary: bool = False):
		doc.append(
			"holders",
			{
				"member": client,
				"role": role,
				"is_primary_member": 1 if is_primary else 0,
			},
		)

	def _add_nominee(self, doc, individual: str, percent: int = 100):
		doc.append(
			"nominees",
			{
				"nominee_name": individual,
				"nominee_percent": percent,
				"nominee_relation": self.relationship,
			},
		)

	def _add_payment(self, doc, amount: float = 5000):
		doc.append(
			"payments",
			{
				"payment_date": today(),
				"payment_amount": amount,
				"payment_type": self.payment_type,
				"status": "Collected",
			},
		)

	# --- Auto-naming ---

	def test_autoname_format(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(len(parts), 5)
		self.assertEqual(parts[0], "KNAPS")
		self.assertEqual(parts[1], "LI")
		self.assertEqual(len(parts[4]), 8)
		self.assertTrue(parts[4].isdigit())

	def test_autoname_tax_year_april_onwards(self):
		doc = self._make_policy(entry_date="2026-04-15", primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "26")
		self.assertEqual(parts[3], "27")

	def test_autoname_tax_year_before_april(self):
		doc = self._make_policy(entry_date="2026-03-15", primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "25")
		self.assertEqual(parts[3], "26")

	# --- Title ---

	def test_title_computed(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - Term")

	def test_title_endowment_policy(self):
		doc = self._make_policy(policy_type="Endowment", primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - Endowment")

	# --- Primary Client (single member, no holders table) ---

	def test_primary_client_direct(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.primary_client, self.adult_client)
		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.client_name, client_name)

	# --- Primary Client (multiple members) ---

	def test_primary_client_from_primary_member(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.other_client, "Insured Member", is_primary=True)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.primary_client, self.other_client)

	def test_primary_client_no_primary_member_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.other_client, "Insured Member")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multiple_primary_members_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer", is_primary=True)
		self._add_member(doc, self.other_client, "Insured Member", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_primary_member_minor_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.minor_client, "Insured Member", is_primary=True)
		self._add_member(doc, self.adult_client, "Proposer")

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Maturity Date ---

	def test_maturity_date_years(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			period_type="Years",
			period=10,
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_years(getdate("2026-06-01"), 10)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_maturity_date_months(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			period_type="Months",
			period=24,
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_months(getdate("2026-06-01"), 24)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_maturity_date_days(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			period_type="Days",
			period=365,
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_days(getdate("2026-06-01"), 365)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_maturity_date_no_start_date(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertIsNone(doc.maturity_date)

	# --- Total Premium ---

	def test_total_premium_single_mode(self):
		doc = self._make_policy(premium=100000, premium_mode="Single", primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc, amount=100000)
		doc.insert()

		self.assertEqual(doc.total_premium, 100000)

	def test_total_premium_yearly_mode(self):
		doc = self._make_policy(
			premium=5000,
			premium_mode="Yearly",
			period_type="Years",
			period=10,
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc, amount=5000)
		doc.insert()

		self.assertEqual(doc.total_premium, 50000)

	def test_total_premium_monthly_mode(self):
		doc = self._make_policy(
			premium=1000,
			premium_mode="Monthly",
			period_type="Years",
			period=5,
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc, amount=1000)
		doc.insert()

		self.assertEqual(doc.total_premium, 60000)

	def test_total_premium_quarterly_mode(self):
		doc = self._make_policy(
			premium=3000,
			premium_mode="Quarterly",
			period_type="Years",
			period=10,
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc, amount=3000)
		doc.insert()

		self.assertEqual(doc.total_premium, 120000)

	def test_total_premium_half_yearly_mode(self):
		doc = self._make_policy(
			premium=6000,
			premium_mode="Half-Yearly",
			period_type="Years",
			period=10,
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc, amount=6000)
		doc.insert()

		self.assertEqual(doc.total_premium, 120000)

	# --- Member Validation ---

	def test_proposer_required(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.other_client, "Insured Member", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_insured_member_required(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_duplicate_member_same_role_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer", is_primary=True)
		self._add_member(doc, self.adult_client, "Proposer")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_same_member_different_roles_allowed(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.adult_client, "Insured Member", is_primary=True)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(len(doc.holders), 2)

	def test_has_multiple_members_false_with_holders_throws(self):
		doc = self._make_policy(has_multiple_members=0)
		self._add_member(doc, self.adult_client, "Proposer", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_members_required_when_has_multiple_members(self):
		doc = self._make_policy(has_multiple_members=1)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Minor Restrictions ---

	def test_minor_proposer_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.minor_client, "Proposer", is_primary=True)
		self._add_member(doc, self.adult_client, "Insured Member")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_minor_primary_member_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.minor_client, "Insured Member", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_all_members_minor_throws(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.minor_client, "Insured Member", is_primary=True)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Period Validation ---

	def test_period_type_required(self):
		doc = self._make_policy(period_type="", primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_period_must_be_positive(self):
		doc = self._make_policy(period=0, primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Premium Validation ---

	def test_premium_must_be_positive(self):
		doc = self._make_policy(premium=0, primary_client=self.adult_client)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Entry Date ---

	def test_entry_date_not_future(self):
		doc = self._make_policy(entry_date="2099-01-01", primary_client=self.adult_client)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Start/Maturity Date ---

	def test_start_date_before_maturity_date(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-12-01",
			maturity_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Status Validation ---

	def test_lapsed_requires_start_date(self):
		doc = self._make_policy(
			status="Lapsed",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_lapsed_requires_policy_number(self):
		doc = self._make_policy(
			status="Lapsed",
			start_date="2026-06-01",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_lapsed_requires_policy_document(self):
		doc = self._make_policy(
			status="Lapsed",
			start_date="2026-06-01",
			policy_number="POL-001",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_lapsed_succeeds_with_all_fields(self):
		doc = self._make_policy(
			status="Lapsed",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Lapsed")

	def test_proposal_no_policy_number(self):
		doc = self._make_policy(status="Proposal", policy_number="POL-001", primary_client=self.adult_client)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_proposal_no_policy_document(self):
		doc = self._make_policy(
			status="Proposal", policy_document="/assets/test.pdf", primary_client=self.adult_client
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_start_date(self):
		doc = self._make_policy(
			status="Active",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_number(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_document(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			primary_client=self.adult_client,
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_succeeds_with_all_fields(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
			primary_client=self.adult_client,
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Active")
		self.assertEqual(doc.policy_number, "POL-001")

	# --- Nominee Validation ---

	def test_nominee_percent_must_sum_to_100(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_percent_100_succeeds(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual, percent=100)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(len(doc.nominees), 1)

	def test_nominee_minor_guardian_required(self):
		doc = self._make_policy(primary_client=self.adult_client)
		doc.append(
			"nominees",
			{
				"nominee_name": self.minor_individual,
				"nominee_date_of_birth": "2015-01-01",
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
			},
		)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_minor_guardian_succeeds(self):
		doc = self._make_policy(primary_client=self.adult_client)
		doc.append(
			"nominees",
			{
				"nominee_name": self.minor_individual,
				"nominee_date_of_birth": "2015-01-01",
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
				"guardian": self.guardian_individual,
			},
		)
		self._add_payment(doc)
		doc.insert()
		self.assertEqual(len(doc.nominees), 1)
		self.assertEqual(doc.nominees[0].is_minor, 1)

	def test_guardian_is_minor_rejected(self):
		doc = self._make_policy(primary_client=self.adult_client)
		doc.append(
			"nominees",
			{
				"nominee_name": self.minor_individual,
				"nominee_date_of_birth": "2015-01-01",
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
				"guardian": self.minor_guardian_individual,
			},
		)
		self._add_payment(doc)
		with self.assertRaises(ValidationError):
			doc.insert()

	def test_unique_nominees(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual, percent=50)
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_not_member(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.other_client, "Insured Member", is_primary=True)
		doc.append(
			"nominees",
			{
				"nominee_name": self.adult_individual,
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
			},
		)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	# --- Payment Validation ---

	def test_payments_required(self):
		doc = self._make_policy(primary_client=self.adult_client)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_existing_policy_skips_payment(self):
		doc = self._make_policy(is_existing_policy=1, primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		doc.insert()

		self.assertEqual(doc.is_existing_policy, 1)

	def test_existing_policy_skips_nominee_warning(self):
		doc = self._make_policy(is_existing_policy=1, primary_client=self.adult_client)
		doc.insert()

		self.assertEqual(doc.is_existing_policy, 1)

	# --- Successful Creation ---

	def test_proposal_creation_succeeds(self):
		doc = self._make_policy(primary_client=self.adult_client)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Proposal")
		self.assertIsNotNone(doc.name)

	def test_policy_with_multiple_members_succeeds(self):
		doc = self._make_policy(has_multiple_members=1)
		self._add_member(doc, self.adult_client, "Proposer")
		self._add_member(doc, self.other_client, "Insured Member", is_primary=True)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(len(doc.holders), 2)
		self.assertEqual(doc.primary_client, self.other_client)
