import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender", "KNAPS Non Individual Type"]
IGNORE_TEST_RECORD_DEPENDENCIES = []


def create_test_individual(**kwargs):
    doc = frappe.get_doc(
        {
            "doctype": "KNAPS Individual",
            "first_name": kwargs.get("first_name", "Test"),
            "last_name": kwargs.get("last_name", "Individual"),
            "salutation": kwargs.get("salutation", "Mr"),
            "gender": kwargs.get("gender", "Male"),
            "status": kwargs.get("status", "Active"),
            "phone_numbers": [
                {
                    "number": kwargs.get("phone", "+91 9876543210"),
                    "is_primary": 1,
                    "is_whatsapp": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Mobile",
                }
            ],
            "email_address": [
                {
                    "email_address": kwargs.get("email", "test@example.com"),
                    "is_primary": 1,
                    "is_active": 1,
                    "ownership": "Self",
                    "type": "Personal",
                }
            ],
        }
    )
    if kwargs.get("save", True):
        doc.insert()
    return doc


def create_test_client(**kwargs):
    individual = kwargs.get("individual") or create_test_individual(
        first_name="Client", last_name="User", save=True
    )
    doc = frappe.get_doc(
        {
            "doctype": "KNAPS Client",
            "client_type": kwargs.get("client_type", "Individual"),
            "individual": individual.name,
            "client_name": kwargs.get("client_name", "Test Client"),
            "primary_phone": kwargs.get("phone"),
            "primary_whatsapp": kwargs.get("phone"),
            "primary_email": kwargs.get("email"),
        }
    )
    if kwargs.get("save", True):
        doc.insert()
    return doc, individual


class IntegrationTestKNAPSOpportunity(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.savepoint("knaps_opportunity_sp")

    def tearDown(self):
        frappe.db.rollback(save_point="knaps_opportunity_sp")
        super().tearDown()

    def _make_opportunity(self, **kwargs):
        defaults = {
            "doctype": "KNAPS Opportunity",
            "status": "New",
            "source": "Walk-In",
        }
        data = {**defaults, **kwargs}
        doc = frappe.get_doc(data)
        doc.insert()
        return doc

    def test_client_syncs_contact_fields(self):
        client, individual = create_test_client(
            client_name="Jane Doe",
            phone="+91 7777777777",
            email="jane@example.com",
        )

        opp = self._make_opportunity(
            client=client.name,
            opportunity_type=[{"product": "Mutual Funds"}],
        )

        self.assertEqual(opp.client_name, "Jane Doe")
        self.assertEqual(opp.phone, "+91 7777777777")
        self.assertEqual(opp.whatsapp, "+91 7777777777")
        self.assertEqual(opp.email, "jane@example.com")

    def test_duplicate_opportunity_rejected(self):
        client, _ = create_test_client()
        self._make_opportunity(
            client=client.name,
            opportunity_type=[{"product": "Mutual Funds"}],
        )

        with self.assertRaises(frappe.ValidationError):
            self._make_opportunity(
                client=client.name,
                opportunity_type=[{"product": "Life Insurance"}],
            )

    def test_duplicate_allowed_for_terminal_status(self):
        client, _ = create_test_client()
        self._make_opportunity(
            client=client.name,
            status="Lost",
            opportunity_type=[{"product": "Mutual Funds"}],
        )

        opp2 = self._make_opportunity(
            client=client.name,
            status="New",
            opportunity_type=[{"product": "Life Insurance"}],
        )
        self.assertTrue(opp2.name)

    def test_duplicate_allowed_on_same_doc(self):
        client, _ = create_test_client()
        opp = self._make_opportunity(
            client=client.name,
            opportunity_type=[{"product": "Mutual Funds"}],
        )

        opp.opportunity_type = []
        opp.append("opportunity_type", {"product": "Life Insurance"})
        opp.save()
        self.assertEqual(len(opp.opportunity_type), 1)
