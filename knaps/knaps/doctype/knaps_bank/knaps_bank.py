# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSBank(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bank_account_number: DF.Data
		bank_branch: DF.Data | None
		bank_name: DF.Data
		first_holder_name: DF.Data | None
		holder_name: DF.DynamicLink
		holder_type: DF.Link
		holding_type: DF.Link | None
		ifsc: DF.Data
		second_holder: DF.Link | None
	# end: auto-generated types

	pass
