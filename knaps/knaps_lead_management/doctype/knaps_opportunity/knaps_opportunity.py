# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSOpportunity(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps_lead_management.doctype.knaps_lead_interest.knaps_lead_interest import KNAPSLeadInterest

		client: DF.Link
		client_name: DF.Data | None
		email: DF.Data | None
		internal_notes: DF.TextEditor | None
		opportunity_type: DF.TableMultiSelect[KNAPSLeadInterest]
		phone: DF.Phone | None
		source: DF.Link
		status: DF.Literal["New", "Qualified", "Nurture", "Prospect", "Won", "Lost", "Junk"]
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		whatsapp: DF.Phone | None
	# end: auto-generated types

	pass
