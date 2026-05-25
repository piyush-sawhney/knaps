# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSRDTransaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bank_account_number: DF.Data | None
		cheque_number: DF.Data | None
		denomination: DF.Float
		holder_name: DF.Data | None
		number_of_installments: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		rd_account_number: DF.Link
		rd_amount: DF.Float
		rd_deposit_amount: DF.Float
		rebate: DF.Float
		surcharge: DF.Float
	# end: auto-generated types

	pass
