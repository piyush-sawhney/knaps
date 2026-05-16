# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSEmail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		email_address: DF.Data
		is_active: DF.Check
		is_primary: DF.Check
		ownership: DF.Literal["Self", "Spouse", "PoA", "Children", "Parent"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		type: DF.Literal["Personal", "Official", "Others"]
	# end: auto-generated types

	pass
