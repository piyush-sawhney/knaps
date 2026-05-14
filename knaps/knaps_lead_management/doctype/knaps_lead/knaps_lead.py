# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
class KNAPSLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps_lead_management.doctype.knaps_lead_interest.knaps_lead_interest import KNAPSLeadInterest

		age: DF.Int
		email: DF.Data | None
		gender: DF.Link | None
		internal_notes: DF.TextEditor | None
		lead: DF.Link
		lead_interested_in: DF.TableMultiSelect[KNAPSLeadInterest]
		lead_name: DF.Data | None
		lead_type: DF.Literal["", "Individual", "Non-Individual"]
		organisation_name: DF.Link | None
		phone: DF.Phone | None
		preferred_contact_mode: DF.Data | None
		source: DF.Link
		status: DF.Literal["", "New", "Qualified", "Nurture", "Prospect", "Won", "Lost", "Junk"]
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		whatsapp: DF.Phone | None
	# end: auto-generated types

	pass