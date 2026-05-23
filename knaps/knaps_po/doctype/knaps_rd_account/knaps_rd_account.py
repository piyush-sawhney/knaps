# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSRDAccount(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_number: DF.Data | None
		account_opening_date: DF.Date | None
		amount: DF.Currency
		bank: DF.Link | None
		card_number: DF.Data | None
		client_name: DF.Data | None
		currency: DF.Link | None
		default_fee: DF.Currency
		default_installments: DF.Int
		denomination: DF.Currency
		effective_card_number: DF.Data | None
		extension_card_number: DF.Data | None
		holder_name: DF.Data | None
		is_updated: DF.Check
		last_deposit_date: DF.Date | None
		pending_installments: DF.Int
		po_rd_investment: DF.Link | None
		rebate: DF.Currency
		start_date: DF.Date | None
		status: DF.Data | None
		total_deposit_amount: DF.Currency
		total_months_paid: DF.Int
	# end: auto-generated types

	pass
