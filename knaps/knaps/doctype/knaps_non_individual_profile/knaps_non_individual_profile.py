# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class KNAPSNonIndividualProfile(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_entity_individual.knaps_entity_individual import KNAPSEntityIndividual

		country_of_incorporation: DF.Link | None
		date_of_incorporation: DF.Date | None
		industry_sector: DF.Link | None
		is_listed_entity: DF.Check
		is_politcally_exposed_entity: DF.Check
		members: DF.Table[KNAPSEntityIndividual]
		non_individual_entity: DF.Link
		place_of_incorporation: DF.Data | None
		registration_number: DF.Data | None
		stock_exchange: DF.Literal["", "NSE", "BSE", "MSE"]
		title: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.non_individual_entity:
			entity_title = frappe.db.get_value(
				"KNAPS Non Individual", self.non_individual_entity, "legal_name"
			)
			self.title = f"{entity_title} Profile"

	def after_insert(self):
		frappe.has_permission("KNAPS Non Individual", "write", self.non_individual_entity, throw=True)
		frappe.db.set_value("KNAPS Non Individual", self.non_individual_entity, "entity_profile", self.name)

	def on_trash(self):
		if self.non_individual_entity:
			frappe.has_permission("KNAPS Non Individual", "write", self.non_individual_entity, throw=True)
			frappe.db.set_value("KNAPS Non Individual", self.non_individual_entity, "entity_profile", None)
