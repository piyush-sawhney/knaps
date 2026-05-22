# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class KNAPSPhysicalHolding(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps_physical_securities.doctype.knaps_physical_certificate.knaps_physical_certificate import KNAPSPhysicalCertificate
		from knaps.knaps_physical_securities.doctype.knaps_physical_claimant.knaps_physical_claimant import KNAPSPhysicalClaimant
		from knaps.knaps_physical_securities.doctype.knaps_physical_holder.knaps_physical_holder import KNAPSPhysicalHolder

		certificate_details: DF.Table[KNAPSPhysicalCertificate]
		claimants: DF.Table[KNAPSPhysicalClaimant]
		folio_number: DF.Data
		holders: DF.Table[KNAPSPhysicalHolder]
		holding_company: DF.Link
		primary_client: DF.Link
	# end: auto-generated types

	def validate(self):
		for row in self.get("certificate_details"):
			row.run_method("validate")
