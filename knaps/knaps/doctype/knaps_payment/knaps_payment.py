# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		payment_amount: DF.Currency
		payment_bank: DF.Link | None
		payment_currency: DF.Link | None
		payment_date: DF.Date | None
		payment_reference_number: DF.Data | None
		payment_type: DF.Link | None
		status: DF.Literal[None]
	# end: auto-generated types

	pass
