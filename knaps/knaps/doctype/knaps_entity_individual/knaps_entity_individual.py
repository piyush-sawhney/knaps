# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSEntityIndividual(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from_date: DF.Date | None
		individual_name: DF.Link
		is_active: DF.Check
		ownership_percent: DF.Percent
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Link
		to_date: DF.Date | None
	# end: auto-generated types

	pass
