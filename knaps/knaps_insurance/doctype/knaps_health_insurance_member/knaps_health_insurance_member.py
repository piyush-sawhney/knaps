# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSHealthInsuranceMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		currency: DF.Link | None
		date_of_birth: DF.Date | None
		holder: DF.Link
		is_primary: DF.Check
		order: DF.Literal["", "Proposer", "Insured"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		sum_insured: DF.Currency
	# end: auto-generated types

	pass
