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
		number_of_dependents: DF.Int
		occupation: DF.Literal["", "Business", "Service", "Professional", "Agriculture", "Retired", "Housewife", "Student", "Others"]
		occupational_details: DF.Data | None
		person: DF.Link
		place_of_birth: DF.Data | None
		politically_exposed_person: DF.Literal["", "Yes", "No", "Related to PEP"]
		title: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.person:
			person_title = frappe.db.get_value("KNAPS Person", self.person, "full_name")
			self.title = f"{person_title} Profile"
