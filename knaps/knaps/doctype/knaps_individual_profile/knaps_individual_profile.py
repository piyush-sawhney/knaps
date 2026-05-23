# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class KNAPSIndividualProfile(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		country_of_birth: DF.Link | None
		educational_qualification: DF.Literal["", "7th Pass", "10th Pass", "12th Pass", "Graduate", "Post Graduate", "Doctorate Holder", "Professional"]
		income_slab: DF.Literal["", "Below 1 Lakh", "1 - 5 Lakh", "5 - 10 Lakh", "10- 25 Lakh", "25 Lakh - 1 Crore", "Above 1 Cr"]
		marital_status: DF.Literal["", "Single", "Married", "Divorced", "Widowed", "Separated"]
		nationality: DF.Link | None
		occupation: DF.Literal["", "Business", "Service", "Professional", "Agriculture", "Retired", "Housewife", "Student", "Others"]
		occupational_details: DF.Data | None
		individual: DF.Link
		place_of_birth: DF.Data | None
		politically_exposed_individual: DF.Literal["", "Yes", "No", "Related to PEP"]
		title: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.individual:
			individual_title = frappe.db.get_value("KNAPS Individual", self.individual, "full_name")
			self.title = f"{individual_title} Profile"

	def after_insert(self):
		frappe.has_permission("KNAPS Individual", "write", self.individual, throw=True)
		frappe.db.set_value("KNAPS Individual", self.individual, "profile_link", self.name)

	def on_trash(self):
		if self.individual:
			frappe.has_permission("KNAPS Individual", "write", self.individual, throw=True)
			frappe.db.set_value("KNAPS Individual", self.individual, "profile_link", None)
