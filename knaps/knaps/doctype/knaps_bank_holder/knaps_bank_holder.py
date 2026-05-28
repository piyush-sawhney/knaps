# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSBankHolder(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		holder: DF.DynamicLink
		holder_type: DF.Link
		is_minor: DF.Check
		is_primary: DF.Check
		name: DF.Int | None
		order: DF.Literal["", "First", "Second", "Third", "Guardian"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
