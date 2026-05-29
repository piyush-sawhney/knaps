import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, getdate, today

from knaps.utils.constants import (
	DOCTYPE_CLIENT,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_INSURANCE_PLAN,
	DOCTYPE_NON_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
	DOCTYPE_PAYMENT_TYPE,
	DOCTYPE_PRODUCT,
	DOCTYPE_PRODUCT_PROVIDER,
	DOCTYPE_RELATIONSHIP,
	DOCTYPE_VEHICLE_INSURANCE,
)


class TestKNAPSVehicleInsurance(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_vehicle_insurance_sp")
		self.adult_individual = self._create_individual("Adult", "Male", "Mr", "1990-01-01")
		self.minor_individual = self._create_individual("Minor", "Male", "Mr", "2015-01-01")
		self.minor_guardian_individual = self._create_individual(
			"Minor Guardian", "Female", "Ms", "2010-01-01"
		)
		self.guardian_individual = self._create_individual("Guardian", "Female", "Mrs", "1985-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.adult_client = self._create_client("Individual", self.adult_individual)
		self.nominee_client = self._create_client("Individual", self.nominee_individual)
		self.product_provider = self._create_product_provider()
		self.insurance_plan = self._create_insurance_plan("Gold Plan", "GOLD-001")
		self.payment_type = self._create_payment_type("Cash")
		self.relationship = self._create_relationship("Spouse")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_vehicle_insurance_sp")
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
		if not frappe.db.exists(DOCTYPE_PRODUCT, "Vehicle Insurance"):
			frappe.get_doc({"doctype": DOCTYPE_PRODUCT, "product_name": "Vehicle Insurance"}).insert()
		if not frappe.db.exists(DOCTYPE_NON_INDIVIDUAL_TYPE, "Company"):
			frappe.get_doc(
				{"doctype": DOCTYPE_NON_INDIVIDUAL_TYPE, "non_individual_type": "Company"}
			).insert()
		provider = frappe.get_doc(
			{
				"doctype": DOCTYPE_NON_INDIVIDUAL,
				"legal_name": "Test Insurance Co",
				"non_individual_type": "Company",
				"status": "Active",
			}
		)
		provider.insert()
		pp = frappe.get_doc(
			{
				"doctype": DOCTYPE_PRODUCT_PROVIDER,
				"product": "Vehicle Insurance",
				"provider": provider.name,
			}
		)
		pp.insert()
		return pp.name

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

	def _make_policy(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_VEHICLE_INSURANCE,
			"entry_date": today(),
			"status": "Proposal",
			"holding_type": "Private Car",
			"investment_company": self.product_provider,
			"insurance_plan_name": self.insurance_plan,
			"period_in_months": 12,
			"premium": 10000,
			"currency": "INR",
			"primary_client": self.adult_client,
			"vehicle_number": "MH-01-AB-1234",
			"vehicle_make": "Toyota",
			"vehicle_model": "Camry",
			"idv": 500000,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _add_nominee(self, doc, individual: str, percent: int = 100):
		doc.append(
			"nominees",
			{
				"nominee_name": individual,
				"nominee_percent": percent,
				"nominee_relation": self.relationship,
			},
		)

	def _add_payment(self, doc, amount: float = 10000):
		doc.append(
			"payments",
			{
				"payment_date": today(),
				"payment_amount": amount,
				"payment_type": self.payment_type,
				"status": "Collected",
			},
		)

	def test_autoname_format(self):
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(len(parts), 5)
		self.assertEqual(parts[0], "KNAPS")
		self.assertEqual(parts[1], "VIN")
		self.assertEqual(len(parts[4]), 8)
		self.assertTrue(parts[4].isdigit())

	def test_autoname_tax_year_april_onwards(self):
		doc = self._make_policy(entry_date="2026-04-15")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "26")
		self.assertEqual(parts[3], "27")

	def test_autoname_tax_year_before_april(self):
		doc = self._make_policy(entry_date="2026-03-15")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "25")
		self.assertEqual(parts[3], "26")

	def test_title_computed(self):
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - MH-01-AB-1234")

	def test_title_without_client_name(self):
		doc = self._make_policy(primary_client=None, client_name=None)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.title, "MH-01-AB-1234")

	def test_maturity_date_computed(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_months(getdate("2026-06-01"), 12)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_premium_must_be_positive(self):
		doc = self._make_policy(premium=0)
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_period_must_be_positive(self):
		doc = self._make_policy(period_in_months=0)
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_entry_date_not_future(self):
		doc = self._make_policy(entry_date="2099-01-01")
		self._add_nominee(doc, self.nominee_individual)

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
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_proposal_requires_no_policy_number(self):
		doc = self._make_policy(status="Proposal", policy_number="POL-001")
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_proposal_requires_no_policy_document(self):
		doc = self._make_policy(status="Proposal", policy_document="/assets/test.pdf")
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_rejected_requires_no_policy_number(self):
		doc = self._make_policy(status="Rejected", policy_number="POL-001")
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_rejected_requires_no_policy_document(self):
		doc = self._make_policy(status="Rejected", policy_document="/assets/test.pdf")
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_start_date(self):
		doc = self._make_policy(
			status="Active",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_number(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_requires_policy_document(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
		)
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_active_succeeds_with_all_fields(self):
		doc = self._make_policy(
			status="Active",
			start_date="2026-06-01",
			policy_number="POL-001",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Active")
		self.assertEqual(doc.policy_number, "POL-001")

	def test_nominee_percent_must_sum_to_100(self):
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_percent_100_succeeds(self):
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual, percent=100)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(len(doc.nominees), 1)

	def test_nominee_minor_guardian_required(self):
		doc = self._make_policy()
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

	def test_nominee_minor_guardian_succeeds(self):
		doc = self._make_policy()
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
		doc = self._make_policy()
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
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual, percent=50)
		self._add_nominee(doc, self.nominee_individual, percent=50)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_payments_required(self):
		doc = self._make_policy()
		self._add_nominee(doc, self.nominee_individual)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_existing_policy_skips_payment(self):
		doc = self._make_policy(is_existing_policy=1)
		self._add_nominee(doc, self.nominee_individual)
		doc.insert()

		self.assertEqual(doc.is_existing_policy, 1)

	def test_surrendered_requires_all_fields(self):
		doc = self._make_policy(
			status="Surrendered",
			start_date="2026-01-01",
			policy_number="POL-002",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Surrendered")

	def test_proposal_succeeds_without_policy_fields(self):
		doc = self._make_policy(status="Proposal")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Proposal")

	def test_renewed_succeeds_with_all_fields(self):
		doc = self._make_policy(
			status="Renewed",
			start_date="2026-07-01",
			policy_number="POL-003",
			policy_document="/assets/test.pdf",
		)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Renewed")
