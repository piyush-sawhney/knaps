import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, getdate, today


class TestKNAPSHealthInsurance(IntegrationTestCase):
	doctype = None

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_health_insurance_sp")
		self.adult_individual = self._create_individual("Adult", "Male", "Mr", "1990-01-01")
		self.minor_individual = self._create_individual("Minor", "Male", "Mr", "2015-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.other_individual = self._create_individual("Other", "Male", "Mr", "1992-06-15")
		self.adult_client = self._create_client("Individual", self.adult_individual)
		self.minor_client = self._create_client("Individual", self.minor_individual)
		self.nominee_client = self._create_client("Individual", self.nominee_individual)
		self.other_client = self._create_client("Individual", self.other_individual)
		self.product_provider = self._create_product_provider()
		self.payment_type = self._create_payment_type("Cash")
		self.relationship = self._create_relationship("Spouse")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_health_insurance_sp")
		super().tearDown()

	def _create_individual(self, first_name: str, gender: str, salutation: str, dob: str) -> str:
		self._ensure_doctype_exists("Gender", gender)
		self._ensure_doctype_exists("Salutation", salutation)
		ind = frappe.get_doc(
			{
				"doctype": "KNAPS Individual",
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
				"doctype": "KNAPS Client",
				"client_type": client_type,
				"individual": individual,
			}
		)
		client.insert()
		return client.name

	def _create_product_provider(self) -> str:
		self._ensure_doctype_exists("KNAPS Product Category", "Insurance")
		self._ensure_doctype_exists("KNAPS Product", "Health Insurance")
		self._ensure_doctype_exists("KNAPS Non Individual Type", "Company")
		provider = frappe.get_doc(
			{
				"doctype": "KNAPS Non Individual",
				"legal_name": "Test Insurance Co",
				"non_individual_type": "Company",
				"status": "Active",
			}
		)
		provider.insert()
		pp = frappe.get_doc(
			{
				"doctype": "KNAPS Product Provider",
				"product": "Health Insurance",
				"provider": provider.name,
			}
		)
		pp.insert()
		return pp.name

	def _create_payment_type(self, name: str) -> str:
		existing = frappe.db.get_value("KNAPS Payment Type", {"payment_type": name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": "KNAPS Payment Type",
				"payment_type": name,
			}
		)
		doc.insert()
		return doc.name

	def _create_relationship(self, name: str) -> str:
		if frappe.db.exists("KNAPS Relationship", name):
			return name
		frappe.get_doc(
			{
				"doctype": "KNAPS Relationship",
				"relationship_name": name,
			}
		).insert()
		return name

	def _make_policy(self, **kwargs):
		defaults = {
			"doctype": "KNAPS Health Insurance",
			"entry_date": today(),
			"status": "Proposal",
			"holding_type": "Multi-Individual",
			"investment_company": self.product_provider,
			"insurance_plan_name": "Gold Plan",
			"period_in_months": 12,
			"premium": 5000,
			"currency": "INR",
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _add_member(
		self, doc, client: str, role: str = "Insured", is_primary: bool = False, sum_insured: float = 0
	):
		doc.append(
			"holders",
			{
				"holder": client,
				"order": role,
				"is_primary": 1 if is_primary else 0,
				"sum_insured": sum_insured,
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
				"status": "Pending",
			},
		)

	def test_autoname_format(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(len(parts), 5)
		self.assertEqual(parts[0], "KNAPS")
		self.assertEqual(parts[1], "HI")
		self.assertEqual(len(parts[4]), 8)
		self.assertTrue(parts[4].isdigit())

	def test_autoname_tax_year_april_onwards(self):
		doc = self._make_policy(entry_date="2026-04-15")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "26")
		self.assertEqual(parts[3], "27")

	def test_autoname_tax_year_before_april(self):
		doc = self._make_policy(entry_date="2026-03-15")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "25")
		self.assertEqual(parts[3], "26")

	def test_title_computed(self):
		doc = self._make_policy(insurance_plan_name="Gold Plan")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value("KNAPS Client", self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - Gold Plan")

	def test_title_without_plan_name(self):
		doc = self._make_policy(insurance_plan_name=None)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value("KNAPS Client", self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - Health Insurance")

	def test_primary_client_from_is_primary(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.primary_client, self.adult_client)
		client_name = frappe.db.get_value("KNAPS Client", self.adult_client, "client_name")
		self.assertEqual(doc.client_name, client_name)

	def test_primary_client_null_when_no_primary(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=False, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertIsNone(doc.primary_client)

	def test_primary_client_minor_throws(self):
		doc = self._make_policy()
		self._add_member(doc, self.minor_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multiple_primary_throws(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_member(doc, self.nominee_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_maturity_date_computed(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_months(getdate("2026-06-01"), 12)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_date_of_birth_fetched(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		member = doc.holders[0]
		self.assertEqual(str(member.date_of_birth), "1990-01-01")

	def test_multi_individual_requires_at_least_one_insured(self):
		doc = self._make_policy()

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multi_individual_with_insured_succeeds(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.holding_type, "Multi-Individual")

	def test_floater_requires_two_insured(self):
		doc = self._make_policy(holding_type="Floater")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_floater_with_two_insured_succeeds(self):
		doc = self._make_policy(holding_type="Floater", floater_sum_insured=1000000)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True)
		self._add_member(doc, self.other_client, "Insured")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.holding_type, "Floater")

	def test_duplicate_holder_throws(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Proposer", is_primary=True)
		self._add_member(doc, self.adult_client, "Insured")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_floater_member_sum_insured_must_be_empty(self):
		doc = self._make_policy(holding_type="Floater", floater_sum_insured=1000000)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_member(doc, self.nominee_client, "Insured")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multi_individual_member_sum_insured_required(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=0)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multi_individual_member_sum_insured_positive_succeeds(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.holders[0].sum_insured, 500000)

	def test_floater_sum_insured_required(self):
		doc = self._make_policy(holding_type="Floater")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True)
		self._add_member(doc, self.nominee_client, "Insured")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_floater_sum_insured_positive(self):
		doc = self._make_policy(holding_type="Floater", floater_sum_insured=0)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True)
		self._add_member(doc, self.nominee_client, "Insured")

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_multi_individual_floater_sum_insured_zero(self):
		doc = self._make_policy(floater_sum_insured=1000000)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_premium_must_be_positive(self):
		doc = self._make_policy(premium=0)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_period_must_be_positive(self):
		doc = self._make_policy(period_in_months=0)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_entry_date_not_future(self):
		doc = self._make_policy(entry_date="2099-01-01")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_start_date_before_maturity_date(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-12-01",
			maturity_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_proposal_rejected_no_policy_number(self):
		doc = self._make_policy(status="Proposal", policy_number="POL-001")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_proposal_rejected_no_policy_document(self):
		doc = self._make_policy(status="Rejected", policy_document="/assets/test.pdf")
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_start_date(self):
		doc = self._make_policy(
			status="Active",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_number(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_document="/assets/test.pdf",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_document(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_succeeds_with_all_fields(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Active")
		self.assertEqual(doc.policy_number, "POL-001")

	def test_nominee_percent_must_sum_to_100(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_percent_100_succeeds(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual, percent=100)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(len(doc.nominees), 1)

	def test_nominee_minor_guardian_required(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		doc.append(
			"nominees",
			{
				"nominee_name": self.minor_individual,
				"nominee_date_of_birth": "2015-01-01",
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
			},
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_unique_nominees(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual, percent=50)
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_not_holder(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		doc.append(
			"nominees",
			{
				"nominee_name": self.adult_individual,
				"nominee_percent": 100,
				"nominee_relation": self.relationship,
			},
		)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_payments_required(self):
		doc = self._make_policy()
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_existing_policy_skips_payment(self):
		doc = self._make_policy(is_existing_policy=1)
		self._add_member(doc, self.adult_client, "Insured", is_primary=True, sum_insured=500000)
		self._add_nominee(doc, self.nominee_individual)
		doc.insert()

		self.assertEqual(doc.is_existing_policy, 1)
