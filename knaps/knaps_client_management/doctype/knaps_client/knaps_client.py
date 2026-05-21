# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSClient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		client_name: DF.Data | None
		client_type: DF.Literal["Individual", "Sole Proprietor", "Non Individual"]
		is_minor: DF.Check
		non_individual: DF.Link | None
		pan: DF.Data | None
		individual: DF.Link | None
		preferred_contact_mode: DF.Data | None
		primary_email: DF.Data | None
		primary_phone: DF.Phone | None
		primary_whatsapp: DF.Phone | None
		status: DF.Data | None
	# end: auto-generated types

	pass
