import frappe
from frappe.exceptions import ValidationError
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, getdate, today

from knaps.utils.constants import (
	DOCTYPE_CLIENT,
	DOCTYPE_FIXED_INVESTMENT,
	DOCTYPE_HOLDING_TYPE,
	DOCTYPE_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL,
	DOCTYPE_NON_INDIVIDUAL_TYPE,
	DOCTYPE_PAYMENT_TYPE,
	DOCTYPE_PRODUCT,
	DOCTYPE_PRODUCT_CATEGORY,
	DOCTYPE_PRODUCT_PROVIDER,
	DOCTYPE_RELATIONSHIP,
)


class TestKNAPSFixedInvestment(IntegrationTestCase):
	doctype = None

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("knaps_fixed_investment_sp")
		self.holding_type_single = self._create_holding_type("Single")
		self.holding_type_joint = self._create_holding_type("Joint")
		self.product_category = self._create_product_category("Fixed Income")
		self.product = self._create_product("Test FD Product", self.product_category)
		self.non_individual_type = self._create_non_individual_type("Company")
		self.adult_individual = self._create_individual("Adult", "Male", "Mr", "1990-01-01")
		self.minor_individual = self._create_individual("Minor", "Male", "Mr", "2015-01-01")
		self.minor_guardian_individual = self._create_individual(
			"Minor Guardian", "Female", "Ms", "2010-01-01"
		)
		self.guardian_individual = self._create_individual("Guardian", "Female", "Mrs", "1985-01-01")
		self.nominee_individual = self._create_individual("Nominee", "Female", "Ms", "1988-01-01")
		self.provider = self._create_non_individual("Test Provider", self.non_individual_type)
		self.product_provider = self._create_product_provider(self.product, self.provider)
		self.adult_client = self._create_client("Individual", self.adult_individual)
		self.minor_client = self._create_client("Individual", self.minor_individual)
		self.guardian_client = self._create_client("Individual", self.guardian_individual)
		self.nominee_client = self._create_client("Individual", self.nominee_individual)
		self.relationship = self._create_relationship("Spouse")
		self.payment_type = self._create_payment_type("Cash")

	def tearDown(self) -> None:
		frappe.db.rollback(save_point="knaps_fixed_investment_sp")
		super().tearDown()

	def _create_holding_type(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_HOLDING_TYPE, name):
			return name
		doc = frappe.get_doc({"doctype": DOCTYPE_HOLDING_TYPE, "holding_type": name})
		doc.insert()
		return name

	def _create_product_category(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_PRODUCT_CATEGORY, name):
			return name
		doc = frappe.get_doc({"doctype": DOCTYPE_PRODUCT_CATEGORY, "category_name": name})
		doc.insert()
		return name

	def _create_product(self, name: str, category: str) -> str:
		if frappe.db.exists(DOCTYPE_PRODUCT, name):
			return name
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_PRODUCT,
				"product_name": name,
				"category": category,
			}
		)
		doc.insert()
		return name

	def _create_non_individual_type(self, name: str) -> str:
		if frappe.db.exists(DOCTYPE_NON_INDIVIDUAL_TYPE, name):
			return name
		doc = frappe.get_doc({"doctype": DOCTYPE_NON_INDIVIDUAL_TYPE, "non_individual_type": name})
		doc.insert()
		return name

	def _create_non_individual(self, legal_name: str, ni_type: str) -> str:
		existing = frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, {"legal_name": legal_name}, "name")
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_NON_INDIVIDUAL,
				"legal_name": legal_name,
				"non_individual_type": ni_type,
				"status": "Active",
			}
		)
		doc.insert()
		return doc.name

	def _create_product_provider(self, product: str, provider: str) -> str:
		existing = frappe.db.get_value(
			DOCTYPE_PRODUCT_PROVIDER,
			{"product": product, "provider": provider},
			"name",
		)
		if existing:
			return existing
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_PRODUCT_PROVIDER,
				"product": product,
				"provider": provider,
			}
		)
		doc.insert()
		return doc.name

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

	def _make_investment(self, **kwargs):
		defaults = {
			"doctype": DOCTYPE_FIXED_INVESTMENT,
			"entry_date": today(),
			"status": "Entry Done",
			"holding_type": self.holding_type_single,
			"holding_mode": "Physical",
			"investment_type": "FD- Fixed Deposit",
			"investment_company": self.product_provider,
			"investment_mode": "Yearly",
			"passbook_status": "Not Created",
			"period_in_months": 12,
			"rate_of_interest": 7.5,
			"amount": 10000,
			"currency": "INR",
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def _add_holder(self, doc, client: str, order: str, is_minor: bool = False):
		doc.append(
			"holders",
			{
				"holder": client,
				"order": order,
				"is_minor": 1 if is_minor else 0,
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

	def _add_payment(self, doc):
		doc.append(
			"payments",
			{
				"payment_date": today(),
				"payment_amount": 10000,
				"payment_type": self.payment_type,
				"status": "Pending",
			},
		)

	def test_autoname_format(self):
		doc = self._make_investment(entry_date=today())
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(len(parts), 5)
		self.assertEqual(parts[0], "KNAPS")
		self.assertEqual(parts[1], "FI")
		self.assertEqual(len(parts[4]), 8)
		self.assertTrue(parts[4].isdigit())

	def test_autoname_tax_year_april_onwards(self):
		doc = self._make_investment(entry_date="2026-04-15")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "26")
		self.assertEqual(parts[3], "27")

	def test_autoname_tax_year_before_april(self):
		doc = self._make_investment(entry_date="2026-03-15")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		parts = doc.name.split("-")
		self.assertEqual(parts[2], "25")
		self.assertEqual(parts[3], "26")

	def test_title_computed(self):
		doc = self._make_investment(investment_type="BOND")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - BOND")

	def test_title_computed_fd(self):
		doc = self._make_investment(investment_type="FD- Fixed Deposit")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - FD")

	def test_title_computed_ncd(self):
		doc = self._make_investment(investment_type="NCD - Non Convertible Debentures")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.title, f"{client_name} - NCD")

	def test_primary_client_from_first_holder(self):
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.primary_client, self.adult_client)
		client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.adult_client, "client_name")
		self.assertEqual(doc.client_name, client_name)

	def test_maturity_date_from_start_date(self):
		doc = self._make_investment(
			status="Active",
			start_date="2026-06-01",
			account_number="123456789",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		expected = add_months(getdate("2026-06-01"), 12)
		self.assertEqual(getdate(doc.maturity_date), expected)

	def test_no_start_date_clears_maturity(self):
		doc = self._make_investment(
			status="Active",
			start_date="2026-06-01",
			account_number="123456789",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertIsNotNone(doc.maturity_date)

		doc.status = "Submitted"
		doc.start_date = None
		doc.account_number = None
		doc.save()

		self.assertIsNone(doc.maturity_date)

	def test_nominee_cannot_be_holder(self):
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.adult_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError) as ctx:
			doc.insert()

		self.assertIn("investment", str(ctx.exception))

	def test_unique_holder_order(self):
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_rate_of_interest_must_be_positive(self):
		doc = self._make_investment(rate_of_interest=0)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_period_in_months_must_be_positive(self):
		doc = self._make_investment(period_in_months=0)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_no_dates_for_entry_done(self):
		doc = self._make_investment(
			status="Entry Done",
			start_date="2026-06-01",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_no_account_number_for_entry_done(self):
		doc = self._make_investment(
			status="Entry Done",
			account_number="123456789",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_dates_allowed_for_active(self):
		doc = self._make_investment(
			status="Active",
			start_date="2026-06-01",
			account_number="123456790",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.status, "Active")
		self.assertEqual(doc.account_number, "123456790")

	def test_account_number_required_for_active(self):
		doc = self._make_investment(
			status="Active",
			start_date="2026-06-01",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_nominee_minor_guardian_required(self):
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
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
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
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
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
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

	def test_amount_must_be_positive(self):
		doc = self._make_investment(amount=0)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_amount_negative_rejected(self):
		doc = self._make_investment(amount=-1000)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_start_date_required_with_account_number(self):
		doc = self._make_investment(
			status="Active",
			account_number="123456791",
		)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_entry_date_not_future(self):
		from frappe.utils import add_days

		doc = self._make_investment(entry_date=add_days(today(), 1))
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_single_holding_type_rejects_second_holder(self):
		doc = self._make_investment()
		self._add_holder(doc, self.adult_client, "First")
		self._add_holder(doc, self.guardian_client, "Second")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_holding_type_requires_minimum_two_for_joint(self):
		doc = self._make_investment(holding_type=self.holding_type_joint)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_minor_holder_only_as_first(self):
		doc = self._make_investment()
		self._add_holder(doc, self.minor_client, "Second", is_minor=True)
		self._add_holder(doc, self.adult_client, "First")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_guardian_required_for_minor_first(self):
		doc = self._make_investment()
		self._add_holder(doc, self.minor_client, "First", is_minor=True)
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)

		with self.assertRaises(ValidationError):
			doc.insert()

	def test_guardian_allowed_for_minor_first(self):
		doc = self._make_investment()
		self._add_holder(doc, self.minor_client, "First", is_minor=True)
		self._add_holder(doc, self.guardian_client, "Guardian")
		self._add_nominee(doc, self.nominee_individual)
		self._add_payment(doc)
		doc.insert()

		self.assertEqual(doc.primary_client, self.minor_client)
