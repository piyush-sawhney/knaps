# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSNonIndividualProfile(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		country_of_incorporation: DF.Link | None
		date_of_incorporation: DF.Date | None
		industry_sector: DF.Link | None
		is_listed_entity: DF.Check
		is_politcally_exposed_entity: DF.Check
		non_individual_entity: DF.Link
		place_of_incorporation: DF.Data | None
		registration_number: DF.Data | None
		stock_exchange: DF.Literal["", "NSE", "BSE", "MSE"]
		title: DF.Data | None
	# end: auto-generated types

	pass
