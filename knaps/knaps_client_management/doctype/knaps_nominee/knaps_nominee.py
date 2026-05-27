# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSNominee(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		guardian: DF.Link | None
		guardian_name_capture: DF.Data | None
		is_minor: DF.Check
		nominee_date_of_birth: DF.Date | None
		nominee_name: DF.Link
		nominee_name_capture: DF.Data | None
		nominee_percent: DF.Float
		nominee_relation: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
