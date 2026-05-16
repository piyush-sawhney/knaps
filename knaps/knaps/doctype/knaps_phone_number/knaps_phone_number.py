# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSPhoneNumber(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_active: DF.Check
		is_primary: DF.Check
		is_whatsapp: DF.Check
		number: DF.Phone
		ownership: DF.Literal["Self", "Spouse", "PoA", "Children", "Parent"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		type: DF.Literal["Mobile", "Office", "Home"]
	# end: auto-generated types

	pass
